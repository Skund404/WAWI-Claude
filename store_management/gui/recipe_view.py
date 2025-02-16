import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import uuid

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS


class RecipeView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Currently selected recipe
        self.current_recipe = None

        # Setup UI components
        self.setup_toolbar()
        self.setup_tables()
        self.load_data()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD Recipe",
                   command=self.show_add_recipe_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="ADD Item to Recipe",
                   command=self.show_add_item_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search",
                   command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter",
                   command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        ttk.Button(toolbar, text="Undo",
                   command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo",
                   command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save",
                   command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load",
                   command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View",
                   command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_tables(self):
        """Create both table views"""
        # Create container for both tables
        tables_frame = ttk.Frame(self)
        tables_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Setup INDEX table
        index_frame = ttk.LabelFrame(tables_frame, text="Recipe Index")
        index_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.index_columns = [
            'unique_id_product', 'name', 'type', 'collection', 'notes'
        ]

        self.index_tree = self.create_treeview(
            index_frame,
            self.index_columns,
            self.on_index_select
        )

        # Setup Recipe Details table
        details_frame = ttk.LabelFrame(tables_frame, text="Recipe Details")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.details_columns = [
            'unique_id_parts', 'name', 'color', 'amount', 'size',
            'in_storage', 'pattern_id', 'notes'
        ]

        self.details_tree = self.create_treeview(
            details_frame,
            self.details_columns
        )

        # Configure warning colors for low storage
        self.details_tree.tag_configure('low_storage', background=COLORS['WARNING'])

    def create_treeview(self, parent, columns, select_callback=None):
        """Create a treeview with scrollbars"""
        # Create frame for treeview and scrollbars
        frame = ttk.Frame(parent)
        frame.pack(expand=True, fill='both')

        # Create scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        # Create treeview
        tree = ttk.Treeview(
            frame,
            columns=columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        # Setup headers and columns
        for col in columns:
            tree.heading(col, text=col.replace('_', ' ').title(),
                         command=lambda c=col: self.sort_column(tree, c))
            tree.column(col, width=100, minwidth=50)

        # Grid layout
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Bind events
        tree.bind('<Double-1>', lambda e: self.on_double_click(tree, e))
        tree.bind('<Delete>', lambda e: self.delete_selected(tree))

        if select_callback:
            tree.bind('<<TreeviewSelect>>', select_callback)

        return tree

    def on_index_select(self, event):
        """Handle selection in index table"""
        selection = self.index_tree.selection()
        if not selection:
            return

        # Get selected recipe ID
        item = selection[0]
        recipe_id = self.index_tree.item(item)['values'][0]

        # Load recipe details
        self.load_recipe_details(recipe_id)
        self.current_recipe = recipe_id

    def load_recipe_details(self, recipe_id: str):
        """Load details for selected recipe"""
        # Clear existing items
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

        self.db.connect()
        try:
            query = """
                SELECT rd.*, ss.in_storage 
                FROM recipe_details rd
                LEFT JOIN sorting_system ss 
                ON rd.unique_id_parts = ss.unique_id_parts
                WHERE rd.recipe_id = ?
            """
            results = self.db.execute_query(query, (recipe_id,))

            if results:
                for row in results:
                    # Check if storage is less than required amount
                    amount = row[3]  # amount column
                    in_storage = row[5]  # in_storage column

                    values = list(row[:-2])  # Exclude timestamps
                    item_id = self.details_tree.insert('', 'end', values=values)

                    if in_storage is not None and amount > in_storage:
                        self.details_tree.item(item_id, tags=('low_storage',))

        finally:
            self.db.disconnect()

    def show_add_recipe_dialog(self):
        """Show dialog for adding new recipe"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Recipe")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Create entry fields
        entries = {}
        fields = ['name', 'type', 'collection', 'notes']

        for i, field in enumerate(fields):
            ttk.Label(main_frame, text=field.title() + ":").grid(row=i, column=0, sticky='w')
            entries[field] = ttk.Entry(main_frame)
            entries[field].grid(row=i, column=1, sticky='ew')

        def save():
            """Save the new recipe"""
            try:
                # Generate unique ID from name and type
                name = entries['name'].get()
                type_ = entries['type'].get()
                if not name or not type_:
                    messagebox.showerror("Error", "Name and Type are required")
                    return

                prefix = ''.join(word[0].upper() for word in name.split())
                unique_id = f"{prefix}{str(uuid.uuid4())[:8]}"

                data = {
                    'unique_id_product': unique_id,
                    **{field: entries[field].get() for field in fields}
                }

                self.db.connect()
                if self.db.insert_record(TABLES['RECIPE_INDEX'], data):
                    # Create corresponding details table
                    self.undo_stack.append(('add_recipe', data))
                    self.redo_stack.clear()
                    self.load_data()
                    self.current_recipe = unique_id
                    dialog.destroy()
                self.db.disconnect()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add recipe: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Continue", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_add_item_dialog(self):
        """Show dialog for adding item to recipe"""
        if not self.current_recipe:
            messagebox.showwarning("Warning", "Please select a recipe first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Recipe")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Get parts from sorting system
        self.db.connect()
        parts = self.db.execute_query("SELECT unique_id_parts, name, color FROM sorting_system")
        leather = self.db.execute_query("SELECT unique_id_leather, name, color, size FROM shelf")
        self.db.disconnect()

        # Create combobox for parts selection
        ttk.Label(main_frame, text="Select Part:").grid(row=0, column=0, sticky='w')
        part_var = tk.StringVar()
        part_combo = ttk.Combobox(main_frame, textvariable=part_var)
        part_combo['values'] = ['Create New Part', 'Create New Leather'] + \
                               [f"{p[0]} - {p[1]}" for p in parts] + \
                               [f"{l[0]} - {l[1]}" for l in leather]
        part_combo.grid(row=0, column=1, sticky='ew')

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Preview")
        preview_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=10)

        preview_labels = {}
        preview_fields = ['name', 'color', 'size', 'in_storage']
        for i, field in enumerate(preview_fields):
            ttk.Label(preview_frame, text=field.title() + ":").grid(row=i, column=0, sticky='w')
            preview_labels[field] = ttk.Label(preview_frame, text="")
            preview_labels[field].grid(row=i, column=1, sticky='w')

        # Entry fields
        entry_frame = ttk.LabelFrame(main_frame, text="Details")
        entry_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=10)

        entries = {}
        entry_fields = ['amount', 'pattern_id', 'notes']
        for i, field in enumerate(entry_fields):
            ttk.Label(entry_frame, text=field.title() + ":").grid(row=i, column=0, sticky='w')
            entries[field] = ttk.Entry(entry_frame)
            entries[field].grid(row=i, column=1, sticky='ew')

        def update_preview(*args):
            """Update preview when part selection changes"""
            selection = part_var.get()
            if selection.startswith('Create New'):
                # Handle create new part/leather
                if selection == 'Create New Part':
                    self.show_add_dialog('sorting_system')
                else:
                    self.show_add_dialog('shelf')
                dialog.focus_set()
                return

            part_id = selection.split(' - ')[0]
            is_leather = part_id.startswith('L')

            self.db.connect()
            if is_leather:
                result = self.db.execute_query(
                    "SELECT name, color, size, NULL as in_storage FROM shelf WHERE unique_id_leather = ?",
                    (part_id,)
                )
            else:
                result = self.db.execute_query(
                    "SELECT name, color, NULL as size, in_storage FROM sorting_system WHERE unique_id_parts = ?",
                    (part_id,)
                )
            self.db.disconnect()

            if result:
                for field, value in zip(preview_fields, result[0]):
                    preview_labels[field].configure(text=str(value) if value is not None else "N/A")

        part_var.trace('w', update_preview)

        def save():
            """Save the new recipe item"""
            try:
                if not part_var.get() or not entries['amount'].get():
                    messagebox.showerror("Error", "Part and Amount are required")
                    return

                part_id = part_var.get().split(' - ')[0]

                data = {
                    'recipe_id': self.current_recipe,
                    'unique_id_parts': part_id,
                    'amount': entries['amount'].get(),
                    'pattern_id': entries['pattern_id'].get(),
                    'notes': entries['notes'].get()
                }

                self.db.connect()
                if self.db.insert_record(TABLES['RECIPE_DETAILS'], data):
                    self.undo_stack.append(('add_item', self.current_recipe, data))
                    self.redo_stack.clear()
                    self.load_recipe_details(self.current_recipe)
                    dialog.destroy()
                self.db.disconnect()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        def load_data(self):
            """Load data from database into index table"""
            self.db.connect()
            try:
                query = "SELECT * FROM recipe_index ORDER BY name"
                results = self.db.execute_query(query)

                # Clear existing items
                for item in self.index_tree.get_children():
                    self.index_tree.delete(item)

                # Insert new data
                for row in results:
                    self.index_tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

            finally:
                self.db.disconnect()

        def sort_column(self, tree, col):
            """Sort treeview column"""
            # Get current items
            items = [(tree.set(item, col), item) for item in tree.get_children('')]

            # Determine sort direction
            reverse = False
            if hasattr(tree, '_last_sort') and tree._last_sort == (col, False):
                reverse = True

            # Store sort state
            tree._last_sort = (col, reverse)

            # Sort items
            items.sort(reverse=reverse, key=lambda x: self.sort_key(x[0]))

            # Rearrange items
            for index, (_, item) in enumerate(items):
                tree.move(item, '', index)

            # Update header arrow
            for column in tree['columns']:
                if column != col:
                    tree.heading(column, text=column.replace('_', ' ').title())
            arrow = "▼" if reverse else "▲"
            tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

        def sort_key(self, value):
            """Create sort key based on value type"""
            try:
                return float(value)
            except ValueError:
                return str(value).lower()

        def on_double_click(self, tree, event):
            """Handle double-click on cell"""
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                column = tree.identify_column(event.x)
                item = tree.identify_row(event.y)

                if column == "#1":  # ID column
                    return  # Don't allow editing of ID

                self.start_cell_edit(tree, item, column)

        def start_cell_edit(self, tree, item, column):
            """Start cell editing"""
            col_num = int(column[1]) - 1
            col_name = tree['columns'][col_num]
            current_value = tree.set(item, col_name)

            # Create edit frame
            frame = ttk.Frame(tree)

            # Create entry widget
            entry = ttk.Entry(frame)
            entry.insert(0, current_value)
            entry.select_range(0, tk.END)
            entry.pack(fill=tk.BOTH, expand=True)

            # Position frame
            bbox = tree.bbox(item, column)
            frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

            def save_edit(event=None):
                """Save the edited value"""
                new_value = entry.get()
                if new_value != current_value:
                    # Store for undo
                    old_values = {col: tree.set(item, col) for col in tree['columns']}
                    self.undo_stack.append(('edit', tree, item, old_values))
                    self.redo_stack.clear()

                    # Update database
                    unique_id = tree.set(item, tree['columns'][0])
                    table_name = TABLES['RECIPE_INDEX'] if tree == self.index_tree else TABLES['RECIPE_DETAILS']
                    id_field = 'unique_id_product' if tree == self.index_tree else 'recipe_id'

                    self.update_record(table_name, id_field, unique_id, col_name, new_value)

                    # Update tree
                    tree.set(item, col_name, new_value)

                    # Update related data if necessary
                    if tree == self.index_tree and self.current_recipe == unique_id:
                        self.load_recipe_details(unique_id)

                frame.destroy()

            def cancel_edit(event=None):
                """Cancel the edit"""
                frame.destroy()

            entry.bind('<Return>', save_edit)
            entry.bind('<Escape>', cancel_edit)
            entry.bind('<FocusOut>', save_edit)
            entry.focus_set()

        def update_record(self, table: str, id_field: str, id_value: str, column: str, value: str):
            """Update record in database"""
            self.db.connect()
            try:
                success = self.db.update_record(
                    table,
                    {column: value},
                    f"{id_field} = ?",
                    (id_value,)
                )
                if not success:
                    messagebox.showerror("Error", "Failed to update database")
            finally:
                self.db.disconnect()

        def delete_selected(self, tree):
            """Delete selected items"""
            selected = tree.selection()
            if not selected:
                return

            if messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete the selected items?"):
                self.db.connect()
                try:
                    # Store for undo
                    deleted_items = []
                    for item in selected:
                        values = {col: tree.set(item, col) for col in tree['columns']}
                        deleted_items.append((item, values))

                        # Delete from database
                        unique_id = values[tree['columns'][0]]
                        table_name = TABLES['RECIPE_INDEX'] if tree == self.index_tree else TABLES['RECIPE_DETAILS']
                        id_field = 'unique_id_product' if tree == self.index_tree else 'recipe_id'

                        self.db.delete_record(
                            table_name,
                            f"{id_field} = ?",
                            (unique_id,)
                        )

                        # If deleting from index, also delete related details
                        if tree == self.index_tree:
                            self.db.delete_record(
                                TABLES['RECIPE_DETAILS'],
                                "recipe_id = ?",
                                (unique_id,)
                            )

                        # Delete from tree
                        tree.delete(item)

                    self.undo_stack.append(('delete', tree, deleted_items))
                    self.redo_stack.clear()

                    # Clear details if deleted from index
                    if tree == self.index_tree:
                        for item in self.details_tree.get_children():
                            self.details_tree.delete(item)
                        self.current_recipe = None

                finally:
                    self.db.disconnect()

        def undo(self, event=None):
            """Undo last action"""
            if not self.undo_stack:
                return

            action = self.undo_stack.pop()
            action_type = action[0]

            if action_type == 'edit':
                tree, item, old_values = action[1:]
                # Store current values for redo
                current_values = {col: tree.set(item, col) for col in tree['columns']}
                self.redo_stack.append(('edit', tree, item, current_values))

                # Restore old values
                table_name = TABLES['RECIPE_INDEX'] if tree == self.index_tree else TABLES['RECIPE_DETAILS']
                id_field = 'unique_id_product' if tree == self.index_tree else 'recipe_id'

                for col, value in old_values.items():
                    tree.set(item, col, value)
                    self.update_record(table_name, id_field, old_values[tree['columns'][0]], col, value)

            elif action_type in ['add_recipe', 'add_item']:
                # Implementation for undoing additions
                pass  # To be implemented

            elif action_type == 'delete':
                # Implementation for undoing deletions
                pass  # To be implemented

        def save_table(self):
            """Save current table state"""
            pass  # To be implemented

        def load_table(self):
            """Load saved table state"""
            pass  # To be implemented

        def reset_view(self):
            """Reset table to default view"""
            self.load_data()
            if self.current_recipe:
                self.load_recipe_details(self.current_recipe)