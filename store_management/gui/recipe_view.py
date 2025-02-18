# gui/recipe_view.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import uuid
import json
from datetime import datetime

from database.db_manager import DatabaseManager
from utils.logger import logger
from utils.error_handler import ErrorHandler
from utils.notifications import StatusNotification
from config import DATABASE_PATH, TABLES, COLORS
from gui.dialogs.search_dialog import SearchDialog


class RecipeView(ttk.Frame):
    def show_filter_dialog(self):
        """Show filter dialog for recipe view"""
        from tkinter import simpledialog, messagebox

        # Create a custom dialog for filtering
        dialog = tk.Toplevel(self)
        dialog.title("Filter Recipes")
        dialog.geometry("400x300")

        # Filter options frame
        filter_frame = ttk.Frame(dialog, padding="10")
        filter_frame.pack(fill=tk.BOTH, expand=True)

        # Filter by type
        ttk.Label(filter_frame, text="Filter by Type:").pack(anchor='w')
        type_var = tk.StringVar()

        # Get unique types from the database
        self.db.connect()
        try:
            types = self.db.execute_query("SELECT DISTINCT type FROM recipe_index ORDER BY type")
            type_choices = ["All"] + [t[0] for t in types if t[0]]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch types: {str(e)}")
            type_choices = ["All"]
        finally:
            self.db.disconnect()

        type_combo = ttk.Combobox(filter_frame, textvariable=type_var, values=type_choices)
        type_combo.pack(fill=tk.X, pady=(0, 10))
        type_combo.set("All")

        # Filter by collection
        ttk.Label(filter_frame, text="Filter by Collection:").pack(anchor='w')
        collection_var = tk.StringVar()

        # Get unique collections from the database
        self.db.connect()
        try:
            collections = self.db.execute_query("SELECT DISTINCT collection FROM recipe_index ORDER BY collection")
            collection_choices = ["All"] + [c[0] for c in collections if c[0]]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch collections: {str(e)}")
            collection_choices = ["All"]
        finally:
            self.db.disconnect()

        collection_combo = ttk.Combobox(filter_frame, textvariable=collection_var, values=collection_choices)
        collection_combo.pack(fill=tk.X, pady=(0, 10))
        collection_combo.set("All")

        def apply_filter():
            """Apply the selected filters"""
            selected_type = type_var.get()
            selected_collection = collection_var.get()

            # Clear existing selections
            for item in self.index_tree.get_children():
                self.index_tree.delete(item)

            # Reconnect to database and fetch filtered results
            self.db.connect()
            try:
                # Build dynamic query
                query = "SELECT * FROM recipe_index WHERE 1=1"
                params = []

                if selected_type != "All":
                    query += " AND type = ?"
                    params.append(selected_type)

                if selected_collection != "All":
                    query += " AND collection = ?"
                    params.append(selected_collection)

                query += " ORDER BY name"

                # Execute query
                results = self.db.execute_query(query, params)

                # Populate treeview
                for row in results:
                    self.index_tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

                # Update recipe count
                self.recipe_count.configure(text=f"Recipes: {len(results)}")

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply filter: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons frame
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Apply", command=apply_filter).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, expand=True, padx=5)
    def show_search_dialog(self):
        """Show search dialog for recipe view"""
        from gui.dialogs.search_dialog import SearchDialog
        from tkinter import messagebox

        # Define the columns to search in
        search_columns = [
            'unique_id_product',  # ID column from recipe index
            'name',  # Name column from recipe index
            'type',  # Type column from recipe index
            'collection'  # Collection column from recipe index
        ]

        def perform_search(search_params):
            """
            Perform search based on parameters

            :param search_params: Dictionary containing search parameters
            """
            column = search_params['column']
            search_text = search_params['text']
            match_case = search_params['match_case']

            # Clear existing selections
            for item in self.index_tree.selection():
                self.index_tree.selection_remove(item)

            # Perform case-sensitive or case-insensitive search
            matching_items = []
            for item in self.index_tree.get_children():
                item_values = self.index_tree.item(item)['values']

                # Determine which columns to search
                if column == 'All':
                    search_columns_to_check = range(len(item_values))
                else:
                    search_columns_to_check = [search_columns.index(column)]

                # Check each specified column
                for col_index in search_columns_to_check:
                    value = str(item_values[col_index])

                    # Perform search with or without case sensitivity
                    if match_case:
                        match = search_text in value
                    else:
                        match = search_text.lower() in value.lower()

                    if match:
                        matching_items.append(item)
                        break

            # Highlight matching items
            if matching_items:
                # Select matching items
                for item in matching_items:
                    self.index_tree.selection_add(item)

                # Ensure the first matching item is visible
                first_match = matching_items[0]
                self.index_tree.see(first_match)

                # Optional: Load details of the first matching recipe
                self.load_recipe_details(self.index_tree.item(first_match)['values'][0])

                messagebox.showinfo("Search Results",
                                    f"Found {len(matching_items)} matching items")
            else:
                messagebox.showinfo("Search Results", "No matching items found")

        # Open the search dialog
        SearchDialog(self, search_columns, perform_search)
    def show_add_item_dialog(self):
        """Show dialog for adding item to recipe"""
        if not self.current_recipe:
            messagebox.showwarning("Warning", "Please select a recipe first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Recipe")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("800x600")

        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel for item selection and preview
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Right panel for batch items list
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # === Left Panel Components ===
        # Dropdown frame
        dropdown_frame = ttk.LabelFrame(left_panel, text="Select Item")
        dropdown_frame.pack(fill=tk.X, pady=(0, 10))

        def refresh_items_list():
            """Refresh the items list from database"""
            self.db.connect()
            try:
                parts = self.db.execute_query("""
                    SELECT unique_id_parts, name, color, in_storage, bin 
                    FROM sorting_system ORDER BY name
                """)
                leather = self.db.execute_query("""
                    SELECT unique_id_leather, name, color, size, shelf
                    FROM shelf ORDER BY name
                """)

                items = []
                items.append(("create_part", "➕ Add New Part"))
                items.append(("create_leather", "➕ Add New Leather"))
                items.extend((p[0], f"{p[1]} ({p[0]}) - Stock: {p[3]} - Bin: {p[4]}") for p in parts)
                items.extend((l[0], f"{l[1]} ({l[0]}) - Size: {l[3]} - Shelf: {l[4]}") for l in leather)

                return items
            finally:
                self.db.disconnect()

        ttk.Label(dropdown_frame, text="Item:").pack(side=tk.LEFT, padx=5)
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(
            dropdown_frame,
            textvariable=item_var,
            width=60
        )
        item_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Initial items load
        items = refresh_items_list()
        item_combo['values'] = [item[1] for item in items]

        # Preview frame
        preview_frame = ttk.LabelFrame(left_panel, text="Item Details")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create preview labels with grid layout
        preview_labels = {}
        preview_fields = [
            ('name', 'Name'),
            ('type', 'Type'),
            ('color', 'Color'),
            ('size', 'Size'),
            ('in_storage', 'In Storage'),
            ('location', 'Location')
        ]

        for i, (field, label) in enumerate(preview_fields):
            ttk.Label(preview_frame, text=f"{label}:").grid(
                row=i, column=0, sticky='w', padx=5, pady=2
            )
            preview_labels[field] = ttk.Label(preview_frame, text="", font=('', 9, 'bold'))
            preview_labels[field].grid(
                row=i, column=1, sticky='w', padx=5, pady=2
            )

        # Details frame for new item
        details_frame = ttk.LabelFrame(left_panel, text="Add Details")
        details_frame.pack(fill=tk.X, pady=(0, 10))

        # Create entry fields
        entries = {}
        required_fields = {
            'amount': 'Amount',
            'size': 'Size',
            'pattern_id': 'Pattern ID',
            'notes': 'Notes'
        }

        for i, (field, label) in enumerate(required_fields.items()):
            ttk.Label(details_frame, text=f"{label}:").grid(
                row=i, column=0, sticky='w', padx=5, pady=2
            )
            entries[field] = ttk.Entry(details_frame)
            entries[field].grid(
                row=i, column=1, sticky='ew', padx=5, pady=2
            )

            if field in ['amount']:
                ttk.Label(details_frame, text="*", foreground="red").grid(
                    row=i, column=2, sticky='w'
                )

        details_frame.columnconfigure(1, weight=1)

        # === Right Panel Components ===
        batch_frame = ttk.LabelFrame(right_panel, text="Items to Add")
        batch_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview for batch items
        columns = ["id", "name", "amount", "size"]
        batch_tree = ttk.Treeview(
            batch_frame,
            columns=columns,
            show="headings",
            height=10
        )

        for col in columns:
            batch_tree.heading(col, text=col.title())
            batch_tree.column(col, width=100)

        batch_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def update_preview(*args):
            """Update preview when item selection changes"""
            selection = item_var.get()

            # Clear preview fields
            for label in preview_labels.values():
                label.configure(text="")

            # Handle special cases
            if selection.startswith("➕"):
                if "Part" in selection:
                    dialog.withdraw()
                    messagebox.showinfo("Add Part", "This will open the Add Part dialog")
                    dialog.deiconify()
                elif "Leather" in selection:
                    dialog.withdraw()
                    messagebox.showinfo("Add Leather", "This will open the Add Leather dialog")
                    dialog.deiconify()
                return

            # Get selected item ID
            selected_id = None
            for item_id, item_text in items:
                if item_text == selection:
                    selected_id = item_id
                    break

            if not selected_id:
                return

            # Query database for item details
            self.db.connect()
            try:
                if selected_id.startswith('L'):  # Leather item
                    result = self.db.execute_query("""
                        SELECT name, 'Leather' as type, color, size, 
                               NULL as in_storage, shelf as location
                        FROM shelf 
                        WHERE unique_id_leather = ?
                    """, (selected_id,))
                else:  # Part item
                    result = self.db.execute_query("""
                        SELECT name, 'Part' as type, color, NULL as size,
                               in_storage, bin as location
                        FROM sorting_system 
                        WHERE unique_id_parts = ?
                    """, (selected_id,))

                if result:
                    # Update preview labels
                    for field, value in zip(
                            ['name', 'type', 'color', 'size', 'in_storage', 'location'],
                            result[0]
                    ):
                        preview_labels[field].configure(
                            text=str(value) if value is not None else "N/A"
                        )

                    # Update stock level color
                    if 'in_storage' in preview_labels:
                        in_storage = preview_labels['in_storage'].cget('text')
                        if in_storage != "N/A":
                            if int(in_storage) <= 5:
                                preview_labels['in_storage'].configure(foreground="red")
                            else:
                                preview_labels['in_storage'].configure(foreground="black")

            finally:
                self.db.disconnect()

        def add_to_batch():
            """Add current item to batch list"""
            selection = item_var.get()

            # Validate selection
            if not selection or selection.startswith("➕"):
                messagebox.showerror("Error", "Please select an item")
                return

            # Get selected item ID
            selected_id = None
            for item_id, item_text in items:
                if item_text == selection:
                    selected_id = item_id
                    break

            if not selected_id:
                return

            # Validate required fields
            if not entries['amount'].get():
                messagebox.showerror("Error", "Amount is required")
                return

            try:
                amount = int(entries['amount'].get())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                return

            # Check storage availability
            in_storage = preview_labels['in_storage'].cget('text')
            if in_storage != "N/A" and int(in_storage) < amount:
                if not messagebox.askyesno(
                        "Warning",
                        "Required amount exceeds available stock. Continue anyway?"
                ):
                    return

            # Add to batch list
            batch_tree.insert('', 'end', values=[
                selected_id,
                preview_labels['name'].cget('text'),
                amount,
                entries['size'].get() or "N/A"
            ])

            # Clear entry fields
            for entry in entries.values():
                entry.delete(0, tk.END)

        def remove_from_batch():
            """Remove selected items from batch"""
            selected = batch_tree.selection()
            if not selected:
                return

            for item in selected:
                batch_tree.delete(item)

        def clear_batch():
            """Clear all items from batch"""
            if batch_tree.get_children():
                if messagebox.askyesno("Confirm", "Clear all items from the list?"):
                    for item in batch_tree.get_children():
                        batch_tree.delete(item)

        # Batch operations frame
        batch_ops_frame = ttk.Frame(right_panel)
        batch_ops_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            batch_ops_frame,
            text="Remove Selected",
            command=remove_from_batch
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            batch_ops_frame,
            text="Clear All",
            command=clear_batch
        ).pack(side=tk.LEFT, padx=5)

        # Add to List button
        ttk.Button(
            details_frame,
            text="Add to List →",
            command=add_to_batch
        ).grid(row=len(required_fields), column=0, columnspan=3, pady=10)

        # Bind preview update to combobox selection
        item_var.trace('w', update_preview)

        def save_batch():
            """Save all items in batch to recipe"""
            batch_items = batch_tree.get_children()
            if not batch_items:
                messagebox.showwarning("Warning", "No items to add")
                return

            try:
                added_items = []
                self.db.connect()
                self.db.begin_transaction()

                for item in batch_items:
                    values = batch_tree.item(item)['values']
                    item_id = values[0]
                    amount = int(values[2])
                    size = values[3] if values[3] != "N/A" else None

                    # Query item details
                    if item_id.startswith('L'):
                        result = self.db.execute_query("""
                            SELECT name, color
                            FROM shelf 
                            WHERE unique_id_leather = ?
                        """, (item_id,))
                    else:
                        result = self.db.execute_query("""
                            SELECT name, color, in_storage
                            FROM sorting_system 
                            WHERE unique_id_parts = ?
                        """, (item_id,))

                    if not result:
                        raise ValueError(f"Item {item_id} not found in database")

                    # Prepare data
                    data = {
                        'recipe_id': self.current_recipe,
                        'unique_id_parts': item_id,
                        'name': result[0][0],
                        'color': result[0][1],
                        'amount': amount,
                        'size': size,
                        'in_storage': result[0][2] if len(result[0]) > 2 else None,
                        'pattern_id': entries['pattern_id'].get(),
                        'notes': entries['notes'].get()
                    }

                    # Insert into database
                    if self.db.insert_record(TABLES['RECIPE_DETAILS'], data):
                        added_items.append(data)
                    else:
                        raise Exception(f"Failed to add item {item_id}")

                # Commit transaction
                self.db.commit_transaction()

                # Add to undo stack
                self.undo_stack.append(('add_items', self.current_recipe, added_items))
                self.redo_stack.clear()

                # Refresh recipe details
                self.load_recipe_details(self.current_recipe)

                messagebox.showinfo(
                    "Success",
                    f"Successfully added {len(added_items)} items to recipe"
                )
                dialog.destroy()

            except Exception as e:
                self.db.rollback_transaction()
                messagebox.showerror("Error", f"Failed to add items: {str(e)}")
            finally:
                self.db.disconnect()

        # Button frame
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Save All",
            command=save_batch
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Add required fields note
        ttk
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Initialize database manager
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize notifications
        self.notifications = StatusNotification(self)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Track modified state
        self.modified = False

        # Track current recipe
        self.current_recipe = None

        # Create UI components
        self.create_ui()

        # Load initial data
        self.load_data()

        # Bind events
        self.bind_events()

    def create_ui(self):
        """Create the user interface"""
        # Create toolbar
        self.create_toolbar()

        # Create main content area
        self.create_main_content()

        # Create status bar
        self.create_status_bar()

    def create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT)

        ttk.Button(
            left_frame,
            text="ADD Recipe",
            command=self.show_add_recipe_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            left_frame,
            text="ADD Item to Recipe",
            command=self.show_add_item_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            left_frame,
            text="Search",
            command=self.show_search_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            left_frame,
            text="Filter",
            command=self.show_filter_dialog
        ).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT)

        ttk.Button(
            right_frame,
            text="Undo",
            command=self.undo
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Redo",
            command=self.redo
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Save",
            command=self.save_table
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Load",
            command=self.load_table
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Reset View",
            command=self.reset_view
        ).pack(side=tk.RIGHT, padx=2)

    def create_main_content(self):
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

    def create_status_bar(self):
        """Create the status bar"""
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Status label
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Recipe count
        self.recipe_count = ttk.Label(status_frame, text="Recipes: 0")
        self.recipe_count.pack(side=tk.RIGHT, padx=5)

    def bind_events(self):
        """Bind global events"""
        # Keyboard shortcuts
        self.bind_all('<Control-z>', self.undo)
        self.bind_all('<Control-y>', self.redo)
        self.bind_all('<Control-s>', self.save_table)
        self.bind_all('<Control-o>', self.load_table)
        self.bind_all('<F5>', self.reset_view)

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

            # Update recipe count
            self.recipe_count.configure(text=f"Recipes: {len(results)}")

        finally:
            self.db.disconnect()

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
                    # Add to undo stack
                    self.undo_stack.append(('add_recipe', data))
                    self.redo_stack.clear()

                    # Refresh view and select new recipe
                    self.load_data()
                    self.current_recipe = unique_id

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    self.notifications.show_success("Recipe added successfully")

                else:
                    raise Exception("Failed to add recipe")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add recipe: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Continue", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Set focus to name field
        entries['name'].focus_set()

        # Bind enter to save
        dialog.bind('<Return>', lambda e: save())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def sort_column(self, tree, col):
        """Sort treeview column"""
        items = [(tree.set(k, col), k) for k in tree.get_children('')]

        # Determine sort direction
        reverse = False
        if hasattr(tree, '_last_sort') and tree._last_sort == (col, False):
            reverse = True

        # Store sort state
        tree._last_sort = (col, reverse)

        # Sort items
        try:
            # Try numeric sort for appropriate columns
            if col in ['amount', 'in_storage']:
                items.sort(key=lambda x: float(x[0]) if x[0] and x[0] != "N/A" else 0, reverse=reverse)
            else:
                items.sort(reverse=reverse)
        except ValueError:
            items.sort(reverse=reverse)

        # Rearrange items
        for index, (_, k) in enumerate(items):
            tree.move(k, '', index)

        # Update header arrow
        for column in tree['columns']:
            if column != col:
                tree.heading(column, text=column.replace('_', ' ').title())
        arrow = "▼" if reverse else "▲"
        tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

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

        # Create edit widget
        if col_name == 'type' and tree == self.index_tree:
            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)

            # Get unique types from database
            self.db.connect()
            types = self.db.execute_query(
                "SELECT DISTINCT type FROM recipe_index WHERE type IS NOT NULL ORDER BY type"
            )
            self.db.disconnect()

            widget['values'] = [t[0] for t in types]

        else:
            var = tk.StringVar(value=current_value)
            widget = ttk.Entry(frame)
            widget.insert(0, current_value)
            widget.select_range(0, tk.END)

        widget.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = tree.bbox(item, column)
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

                # Update preview if needed
                if tree == self.index_tree and self.current_recipe == unique_id:
                    self.load_recipe_details(unique_id)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        # Bind events
        widget.bind('<Return>', save_edit)
        widget.bind('<Escape>', cancel_edit)
        widget.bind('<FocusOut>', save_edit)
        widget.focus_set()

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

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete the selected items?"):
            return

        self.db.connect()
        try:
            deleted_items = []

            for item in selected:
                values = {col: tree.set(item, col) for col in tree['columns']}
                deleted_items.append((item, values))

                unique_id = values[tree['columns'][0]]

                if tree == self.index_tree:
                    # Delete recipe and its details
                    self.db.delete_record(
                        TABLES['RECIPE_INDEX'],
                        "unique_id_product = ?",
                        (unique_id,)
                    )
                    self.db.delete_record(
                        TABLES['RECIPE_DETAILS'],
                        "recipe_id = ?",
                        (unique_id,)
                    )

                    # Clear details if deleted current recipe
                    if self.current_recipe == unique_id:
                        for detail_item in self.details_tree.get_children():
                            self.details_tree.delete(detail_item)
                        self.current_recipe = None

                else:  # details tree
                    self.db.delete_record(
                        TABLES['RECIPE_DETAILS'],
                        "recipe_id = ? AND unique_id_parts = ?",
                        (self.current_recipe, unique_id)
                    )

                tree.delete(item)

            self.undo_stack.append(('delete', tree, deleted_items))
            self.redo_stack.clear()

            self.notifications.show_success(f"Deleted {len(deleted_items)} items")

        except Exception as e:
            self.notifications.show_error(f"Failed to delete items: {str(e)}")
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
            for col, value in old_values.items():
                tree.set(item, col, value)
                if tree == self.index_tree:
                    self.update_record(
                        TABLES['RECIPE_INDEX'],
                        'unique_id_product',
                        old_values['unique_id_product'],
                        col,
                        value
                    )
                else:
                    self.update_record(
                        TABLES['RECIPE_DETAILS'],
                        'recipe_id',
                        self.current_recipe,
                        col,
                        value
                    )

        elif action_type == 'delete':
            tree, deleted_items = action[1:]
            restored_items = []

            self.db.connect()
            try:
                for item_id, values in deleted_items:
                    if tree == self.index_tree:
                        # Restore recipe index
                        self.db.insert_record(TABLES['RECIPE_INDEX'], values)
                    else:
                        # Restore recipe detail
                        self.db.insert_record(TABLES['RECIPE_DETAILS'], values)

                    # Restore to tree
                    new_item = tree.insert('', 'end', values=list(values.values()))
                    restored_items.append((new_item, values))

                self.redo_stack.append(('undelete', tree, restored_items))

            finally:
                self.db.disconnect()

        elif action_type == 'add_recipe':
            data = action[1]
            # Remove recipe and its details
            self.db.connect()
            try:
                self.db.delete_record(
                    TABLES['RECIPE_INDEX'],
                    "unique_id_product = ?",
                    (data['unique_id_product'],)
                )
                self.db.delete_record(
                    TABLES['RECIPE_DETAILS'],
                    "recipe_id = ?",
                    (data['unique_id_product'],)
                )

                # Remove from tree
                for item in self.index_tree.get_children():
                    if self.index_tree.set(item, 'unique_id_product') == data['unique_id_product']:
                        self.index_tree.delete(item)
                        break

                self.redo_stack.append(('readd_recipe', data))

            finally:
                self.db.disconnect()

        elif action_type == 'add_items':
            recipe_id, items = action[1:]
            self.db.connect()
            try:
                # Remove items from database
                for item in items:
                    self.db.delete_record(
                        TABLES['RECIPE_DETAILS'],
                        "recipe_id = ? AND unique_id_parts = ?",
                        (recipe_id, item['unique_id_parts'])
                    )

                # Reload details view
                self.load_recipe_details(recipe_id)
                self.redo_stack.append(('readd_items', recipe_id, items))

            finally:
                self.db.disconnect()

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            tree, item, new_values = action[1:]
            # Store current values for undo
            current_values = {col: tree.set(item, col) for col in tree['columns']}
            self.undo_stack.append(('edit', tree, item, current_values))

            # Restore new values
            for col, value in new_values.items():
                tree.set(item, col, value)
                if tree == self.index_tree:
                    self.update_record(
                        TABLES['RECIPE_INDEX'],
                        'unique_id_product',
                        new_values['unique_id_product'],
                        col,
                        value
                    )
                else:
                    self.update_record(
                        TABLES['RECIPE_DETAILS'],
                        'recipe_id',
                        self.current_recipe,
                        col,
                        value
                    )

        elif action_type == 'undelete':
            tree, restored_items = action[1:]
            deleted_items = []

            self.db.connect()
            try:
                for item, values in restored_items:
                    # Delete from database
                    if tree == self.index_tree:
                        self.db.delete_record(
                            TABLES['RECIPE_INDEX'],
                            "unique_id_product = ?",
                            (values['unique_id_product'],)
                        )
                    else:
                        self.db.delete_record(
                            TABLES['RECIPE_DETAILS'],
                            "recipe_id = ? AND unique_id_parts = ?",
                            (self.current_recipe, values['unique_id_parts'])
                        )

                    # Delete from tree
                    tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', tree, deleted_items))

            finally:
                self.db.disconnect()

        elif action_type == 'readd_recipe':
            data = action[1]
            # Re-add recipe
            self.db.connect()
            try:
                if self.db.insert_record(TABLES['RECIPE_INDEX'], data):
                    # Add back to tree
                    self.index_tree.insert('', 'end', values=list(data.values()))
                    self.undo_stack.append(('add_recipe', data))

            finally:
                self.db.disconnect()

        elif action_type == 'readd_items':
            recipe_id, items = action[1:]
            self.db.connect()
            try:
                # Re-add items to database
                for item in items:
                    self.db.insert_record(TABLES['RECIPE_DETAILS'], item)

                # Reload details view
                self.load_recipe_details(recipe_id)
                self.undo_stack.append(('add_items', recipe_id, items))

            finally:
                self.db.disconnect()

    def save_table(self, event=None):
        """Save current recipe state to file"""
        if not self.current_recipe:
            messagebox.showwarning("Warning", "Please select a recipe to save")
            return

        try:
            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ],
                initialfile=f"recipe_{self.current_recipe}"
            )

            if not file_path:
                return

            # Get recipe data
            self.db.connect()
            recipe = self.db.execute_query(
                "SELECT * FROM recipe_index WHERE unique_id_product = ?",
                (self.current_recipe,)
            )[0]

            # Get recipe details
            details = self.db.execute_query(
                "SELECT * FROM recipe_details WHERE recipe_id = ?",
                (self.current_recipe,)
            )

            # Prepare data for saving
            save_data = {
                'recipe': dict(zip(self.index_columns, recipe[:-2])),  # Exclude timestamps
                'details': [dict(zip(self.details_columns, detail[:-2])) for detail in details]
            }

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)

            self.notifications.show_success("Recipe saved successfully")

        except Exception as e:
            self.notifications.show_error(f"Failed to save recipe: {str(e)}")
        finally:
            self.db.disconnect()

    def load_table(self, event=None):
        """Load recipe from file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )

            if not file_path:
                return

            # Read data from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate data structure
            if not isinstance(data, dict) or 'recipe' not in data or 'details' not in data:
                raise ValueError("Invalid recipe file format")

            # Create backup before loading
            self.db.connect()
            try:
                # Insert recipe
                if self.db.insert_record(TABLES['RECIPE_INDEX'], data['recipe']):
                    # Insert details
                    for detail in data['details']:
                        detail['recipe_id'] = data['recipe']['unique_id_product']
                        self.db.insert_record(TABLES['RECIPE_DETAILS'], detail)

                    # Refresh view and select loaded recipe
                    self.load_data()
                    self.current_recipe = data['recipe']['unique_id_product']

                    # Select the loaded recipe in the tree
                    for item in self.index_tree.get_children():
                        if self.index_tree.set(item, 'unique_id_product') == self.current_recipe:
                            self.index_tree.selection_set(item)
                            self.index_tree.see(item)
                            break

                    # Load recipe details
                    self.load_recipe_details(self.current_recipe)

                    self.notifications.show_success("Recipe loaded successfully")
                else:
                    raise Exception("Failed to load recipe")

            except Exception as e:
                self.notifications.show_error(f"Failed to load recipe: {str(e)}")
            finally:
                self.db.disconnect()

        except Exception as e:
            self.notifications.show_error(f"Failed to load recipe file: {str(e)}")

    def reset_view(self):
        """Reset view to default state"""
        self.load_data()
        if self.current_recipe:
            self.load_recipe_details(self.current_recipe)

        self.notifications.show_info("View reset to default state")