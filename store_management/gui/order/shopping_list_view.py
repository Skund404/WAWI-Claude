import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import uuid

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS


class ShoppingListView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Current shopping list
        self.current_list = None

        # Setup UI components
        self.setup_toolbar()
        self.setup_table_selection()
        self.setup_table()
        self.load_shopping_lists()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD",
                   command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search",
                   command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter",
                   command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View",
                   command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table_selection(self):
        """Create shopping list selection dropdown"""
        selection_frame = ttk.Frame(self)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(selection_frame, text="Select Shopping List:").pack(side=tk.LEFT, padx=5)

        self.list_var = tk.StringVar()
        self.list_combo = ttk.Combobox(selection_frame, textvariable=self.list_var)
        self.list_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(selection_frame, text="New List",
                   command=self.create_new_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(selection_frame, text="Delete List",
                   command=self.delete_list).pack(side=tk.LEFT, padx=5)

        self.list_var.trace('w', self.on_list_select)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'supplier', 'unique_id', 'article', 'color', 'amount', 'price', 'notes'
        ]

        # Create scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        # Create treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Setup headers and columns
        for col in self.columns:
            self.tree.heading(col, text=col.replace('_', ' ').title(),
                              command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=100, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)

    def create_new_list(self):
        """Create a new shopping list"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # List name entry
        ttk.Label(main_frame, text="List Name:").grid(row=0, column=0, sticky='w')
        name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=name_var).grid(row=0, column=1, sticky='ew')

        def save():
            """Save new shopping list"""
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "List name is required")
                return

            # Check if name exists
            self.db.connect()
            try:
                existing = self.db.execute_query(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (f"shopping_list_{name}",)
                )

                if existing:
                    messagebox.showerror("Error", "List name already exists")
                    return

                # Create new table
                query = f"""
                    CREATE TABLE shopping_list_{name} (
                        supplier TEXT NOT NULL,
                        unique_id TEXT,
                        article TEXT NOT NULL,
                        color TEXT,
                        amount INTEGER NOT NULL,
                        price REAL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                self.db.execute_query(query)

                # Refresh shopping lists
                self.load_shopping_lists()
                self.list_var.set(name)

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to create list: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Create",
                   command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def delete_list(self):
        """Delete current shopping list"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list")
            return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete {self.current_list}?"):
            self.db.connect()
            try:
                self.db.execute_query(f"DROP TABLE shopping_list_{self.current_list}")
                self.load_shopping_lists()
                self.current_list = None
                self.list_var.set('')

                # Clear table
                for item in self.tree.get_children():
                    self.tree.delete(item)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete list: {str(e)}")
            finally:
                self.db.disconnect()

    def load_shopping_lists(self):
        """Load available shopping lists"""
        self.db.connect()
        try:
            tables = self.db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopping_list_%'"
            )

            lists = [table[0].replace('shopping_list_', '') for table in tables]
            self.list_combo['values'] = lists

        finally:
            self.db.disconnect()

    def on_list_select(self, *args):
        """Handle shopping list selection"""
        selected = self.list_var.get()
        if selected:
            self.current_list = selected
            self.load_data()
        else:
            self.current_list = None
            # Clear table
            for item in self.tree.get_children():
                self.tree.delete(item)

    def show_add_dialog(self):
        """Show dialog for adding new item to shopping list"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Get suppliers
        self.db.connect()
        suppliers = self.db.execute_query(
            "SELECT company_name FROM supplier ORDER BY company_name"
        )

        # Get parts and leather items
        parts = self.db.execute_query(
            "SELECT unique_id_parts, name, color FROM sorting_system ORDER BY name"
        )
        leather = self.db.execute_query(
            "SELECT unique_id_leather, name, color FROM shelf ORDER BY name"
        )
        self.db.disconnect()

        # Create fields
        row = 0
        entries = {}

        # Supplier selection
        ttk.Label(main_frame, text="Supplier:").grid(row=row, column=0, sticky='w')
        supplier_var = tk.StringVar()
        supplier_combo = ttk.Combobox(main_frame, textvariable=supplier_var)
        supplier_combo['values'] = ['Add Supplier'] + \
                                   [s[0] for s in suppliers] if suppliers else []
        supplier_combo.grid(row=row, column=1, sticky='ew')
        entries['supplier'] = supplier_var

        def handle_supplier_selection(*args):
            if supplier_var.get() == 'Add Supplier':
                # Call add supplier function
                pass

        supplier_var.trace('w', handle_supplier_selection)

        row += 1

        # Item selection
        ttk.Label(main_frame, text="Item:").grid(row=row, column=0, sticky='w')
        id_var = tk.StringVar()
        id_combo = ttk.Combobox(main_frame, textvariable=id_var)
        id_combo['values'] = ['Add Part', 'Add Leather'] + \
                             [f"{p[0]} - {p[1]}" for p in parts] + \
                             [f"{l[0]} - {l[1]}" for l in leather]
        id_combo.grid(row=row, column=1, sticky='ew')
        entries['unique_id'] = id_var

        # Create remaining fields
        fields = ['amount', 'price', 'notes']
        for field in fields:
            row += 1
            ttk.Label(main_frame, text=field.title() + ":").grid(
                row=row, column=0, sticky='w'
            )
            var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=var).grid(
                row=row, column=1, sticky='ew'
            )
            entries[field] = var

        def save():
            """Save item to shopping list"""
            try:
                # Validate required fields
                if not all([entries['supplier'].get(), entries['unique_id'].get(),
                            entries['amount'].get()]):
                    messagebox.showerror("Error",
                                         "Supplier, Item, and Amount are required")
                    return

                # Validate numeric fields
                try:
                    amount = int(entries['amount'].get())
                    price = float(entries['price'].get()) if entries['price'].get() else 0
                except ValueError:
                    messagebox.showerror("Error",
                                         "Amount must be an integer and Price must be a number")
                    return

                # Get item details
                item_id, item_name = entries['unique_id'].get().split(' - ')

                # Get color from database
                self.db.connect()
                if item_id.startswith('L'):
                    color = self.db.execute_query(
                        "SELECT color FROM shelf WHERE unique_id_leather = ?",
                        (item_id,)
                    )[0][0]
                else:
                    color = self.db.execute_query(
                        "SELECT color FROM sorting_system WHERE unique_id_parts = ?",
                        (item_id,)
                    )[0][0]

                # Create item data
                item_data = {
                    'supplier': entries['supplier'].get(),
                    'unique_id': item_id,
                    'article': item_name,
                    'color': color,
                    'amount': amount,
                    'price': price,
                    'notes': entries['notes'].get()
                }

                # Insert into database
                if self.db.insert_record(f"shopping_list_{self.current_list}",
                                         item_data):
                    self.undo_stack.append(('add', item_data))
                    self.redo_stack.clear()
                    self.load_data()
                    dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row + 1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Add",
                   command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """Load data for current shopping list"""
        if not self.current_list:
            return

        self.db.connect()
        try:
            query = f"SELECT * FROM shopping_list_{self.current_list} ORDER BY supplier, article"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new data
            for row in results:
                self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

        finally:
            self.db.disconnect()

    def on_double_click(self, event):
        """Handle double-click on cell"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if column == "#2":  # unique_id column
                return  # Don't allow editing of unique_id

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing"""
        col_num = int(column[1]) - 1
        col_name = self.columns[col_num]
        current_value = self.tree.set(item, col_name)

        # Create edit frame
        frame = ttk.Frame(self.tree)

        # Create edit widget based on column
        if col_name == 'supplier':
            # Get suppliers list
            self.db.connect()
            suppliers = self.db.execute_query(
                "SELECT company_name FROM supplier ORDER BY company_name"
            )
            self.db.disconnect()

            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)
            widget['values'] = [s[0] for s in suppliers] if suppliers else []
        else:
            var = tk.StringVar(value=current_value)
            widget = ttk.Entry(frame, textvariable=var)

        widget.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = self.tree.bbox(item, column)
        frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        def save_edit(event=None):
            """Save the edited value"""
            new_value = var.get()
            if new_value != current_value:
                # Validate numeric fields
                if col_name == 'amount':
                    try:
                        value = int(new_value)
                        if value < 0:
                            messagebox.showerror("Error", "Amount must be non-negative")
                            return
                    except ValueError:
                        messagebox.showerror("Error", "Amount must be a number")
                        return
                elif col_name == 'price':
                    try:
                        value = float(new_value)
                        if value < 0:
                            messagebox.showerror("Error", "Price must be non-negative")
                            return
                    except ValueError:
                        messagebox.showerror("Error", "Price must be a number")
                        return

                # Store for undo
                old_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, old_values))
                self.redo_stack.clear()

                # Update database
                self.update_record(old_values['unique_id'], col_name, new_value)

                # Update tree
                self.tree.set(item, col_name, new_value)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        widget.bind('<Return>', save_edit)
        widget.bind('<Escape>', cancel_edit)
        widget.bind('<FocusOut>', save_edit)
        widget.focus_set()

    def update_record(self, unique_id: str, column: str, value: str):
        """Update record in database"""
        if not self.current_list:
            return

        self.db.connect()
        try:
            success = self.db.update_record(
                f"shopping_list_{self.current_list}",
                {column: value},
                "unique_id = ?",
                (unique_id,)
            )
            if not success:
                messagebox.showerror("Error", "Failed to update database")
        finally:
            self.db.disconnect()

    def delete_selected(self, event=None):
        """Delete selected items"""
        if not self.current_list:
            return

        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm Delete",
                               "Are you sure you want to delete the selected items?"):
            self.db.connect()
            try:
                # Store for undo
                deleted_items = []
                for item in selected:
                    values = {col: self.tree.set(item, col) for col in self.columns}
                    deleted_items.append((item, values))

                    # Delete from database
                    unique_id = values['unique_id']
                    self.db.delete_record(
                        f"shopping_list_{self.current_list}",
                        "unique_id = ?",
                        (unique_id,)
                    )

                    # Delete from tree
                    self.tree.delete(item)

                self.undo_stack.append(('delete', deleted_items))
                self.redo_stack.clear()

            finally:
                self.db.disconnect()

    def sort_column(self, col):
        """Sort table by column"""
        # Get all items
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

        # Determine sort direction
        reverse = False
        if hasattr(self, '_last_sort') and self._last_sort == (col, False):
            reverse = True

        # Store sort state
        self._last_sort = (col, reverse)

        # Sort items
        try:
            # Try numeric sort for amount and price columns
            if col in ['amount', 'price']:
                l.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
            else:
                l.sort(reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        # Rearrange items
        for index, (_, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Update header arrow
        for column in self.columns:
            if column != col:
                self.tree.heading(column, text=column.replace('_', ' ').title())
        arrow = "▼" if reverse else "▲"
        self.tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            item, old_values = action[1:]
            # Store current values for redo
            current_values = {col: self.tree.set(item, col) for col in self.columns}
            self.redo_stack.append(('edit', item, current_values))

            # Restore old values
            for col, value in old_values.items():
                self.tree.set(item, col, value)
                self.update_record(old_values['unique_id'], col, value)

        elif action_type == 'add':
            data = action[1]
            # Delete added record
            self.db.connect()
            try:
                self.db.delete_record(
                    f"shopping_list_{self.current_list}",
                    "unique_id = ?",
                    (data['unique_id'],)
                )

                # Find and delete tree item
                for item in self.tree.get_children():
                    if self.tree.set(item, 'unique_id') == data['unique_id']:
                        self.tree.delete(item)
                        break

                self.redo_stack.append(('readd', data))

            finally:
                self.db.disconnect()

        elif action_type == 'delete':
            deleted_items = action[1]
            restored_items = []

            self.db.connect()
            try:
                for item_id, values in deleted_items:
                    # Restore to database
                    self.db.insert_record(f"shopping_list_{self.current_list}", values)

                    # Restore to tree
                    new_item = self.tree.insert('', 'end', values=list(values.values()))
                    restored_items.append((new_item, values))

                self.redo_stack.append(('undelete', restored_items))

            finally:
                self.db.disconnect()

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            item, new_values = action[1:]
            # Store current values for undo
            current_values = {col: self.tree.set(item, col) for col in self.columns}
            self.undo_stack.append(('edit', item, current_values))

            # Restore new values
            for col, value in new_values.items():
                self.tree.set(item, col, value)
                self.update_record(new_values['unique_id'], col, value)

        elif action_type == 'readd':
            data = action[1]
            # Re-add the record
            self.db.connect()
            try:
                if self.db.insert_record(f"shopping_list_{self.current_list}", data):
                    # Add to tree
                    item = self.tree.insert('', 'end', values=list(data.values()))
                    self.undo_stack.append(('add', data))

            finally:
                self.db.disconnect()

        elif action_type == 'undelete':
            restored_items = action[1]
            deleted_items = []

            self.db.connect()
            try:
                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        f"shopping_list_{self.current_list}",
                        "unique_id = ?",
                        (values['unique_id'],)
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', deleted_items))

            finally:
                self.db.disconnect()

    def reset_view(self):
        """Reset table to default view"""
        self.load_data()