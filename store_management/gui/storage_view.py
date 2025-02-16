import tkinter as tk
from tkinter import ttk
from typing import Dict, List
import uuid

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS
from gui.dialogs.add_dialog import AddDialog
from gui.dialogs.search_dialog import SearchDialog
from gui.dialogs.filter_dialog import FilterDialog


class StorageView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Setup UI components
        self.setup_toolbar()
        self.setup_table()
        self.load_data()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter", command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View", command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table(self):
        """Create the main table view"""
        # Create scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")

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
        self.tree.bind('<Return>', self.handle_return)
        self.tree.bind('<Escape>', self.handle_escape)

    def show_add_dialog(self):
        """Show specialized add dialog with product preview"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Storage Item")
        dialog.transient(self)
        dialog.grab_set()

        # Create frames
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        # Create entry fields
        entries = {}
        preview_labels = {}

        # Get existing product IDs
        self.db.connect()
        product_ids = self.db.execute_query("SELECT unique_id_product FROM storage")
        self.db.disconnect()

        # Product ID dropdown
        ttk.Label(input_frame, text="Product ID:").grid(row=0, column=0, sticky='w')
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(input_frame, textvariable=product_var)
        product_combo['values'] = [id[0] for id in product_ids] if product_ids else []
        product_combo.grid(row=0, column=1, sticky='ew')

        # Other entry fields
        fields = ['name', 'type', 'collection', 'color', 'amount', 'bin', 'notes']
        for i, field in enumerate(fields, start=1):
            ttk.Label(input_frame, text=field.title() + ":").grid(row=i, column=0, sticky='w')
            entries[field] = ttk.Entry(input_frame)
            entries[field].grid(row=i, column=1, sticky='ew')

            # Create corresponding preview label
            preview_labels[field] = ttk.Label(preview_frame, text="")
            preview_labels[field].grid(row=i, column=0, sticky='w')

        def update_preview(*args):
            """Update preview when product ID changes"""
            product_id = product_var.get()
            if product_id:
                self.db.connect()
                result = self.db.execute_query(
                    "SELECT * FROM storage WHERE unique_id_product = ?",
                    (product_id,)
                )
                self.db.disconnect()

                if result:
                    data = result[0]
                    for i, field in enumerate(fields):
                        preview_labels[field].configure(
                            text=f"{field.title()}: {data[i + 1]}"
                        )
                        if field != 'amount' and field != 'bin':
                            entries[field].delete(0, tk.END)
                            entries[field].insert(0, data[i + 1])
                            entries[field].configure(state='readonly')
                        else:
                            entries[field].configure(state='normal')

        product_var.trace('w', update_preview)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        def save():
            """Save the new storage item"""
            try:
                data = {
                    'unique_id_product': product_var.get(),
                    **{field: entries[field].get() for field in fields}
                }

                if not all([data['unique_id_product'], data['amount'], data['bin']]):
                    tk.messagebox.showerror("Error", "Product ID, Amount, and Bin are required")
                    return

                self.db.connect()
                if self.db.insert_record(TABLES['STORAGE'], data):
                    self.undo_stack.append(('add', data))
                    self.redo_stack.clear()
                    self.load_data()
                    dialog.destroy()
                self.db.disconnect()

            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to add item: {str(e)}")

        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def sort_column(self, col):
        """Sort table by column"""
        # Get all items with their values in the specified column
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]

        # Determine if we're reversing the sort
        reverse = False
        if hasattr(self, '_last_sort') and self._last_sort == (col, False):
            reverse = True

        # Store sort state
        self._last_sort = (col, reverse)

        # Sort items
        items.sort(reverse=reverse, key=lambda x: self.sort_key(x[0]))

        # Rearrange items in sorted positions
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)

        # Update header arrow
        for column in self.columns:
            if column != col:
                self.tree.heading(column, text=column.replace('_', ' ').title())
        arrow = "▼" if reverse else "▲"
        self.tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

    def sort_key(self, value):
        """Create sort key based on value type"""
        try:
            # Try to convert to float for numeric sorting
            return float(value)
        except ValueError:
            # Fall back to string sorting
            return str(value).lower()

    def load_data(self):
        """Load data from database into table"""
        self.db.connect()
        try:
            query = "SELECT * FROM storage ORDER BY bin"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new data
            for row in results:
                self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

        finally:
            self.db.disconnect()

    # The remaining methods (update_record, delete_selected, undo, redo, etc.)
    # follow the same pattern as ShelfView but with appropriate modifications
    # for the storage table.

    def update_record(self, unique_id: str, column: str, value: str):
        """Update record in database"""
        self.db.connect()
        try:
            success = self.db.update_record(
                TABLES['STORAGE'],
                {column: value},
                "unique_id_product = ?",
                (unique_id,)
            )
            if not success:
                tk.messagebox.showerror("Error", "Failed to update database")
        finally:
            self.db.disconnect()

    def delete_selected(self, event=None):
        """Delete selected items"""
        selected = self.tree.selection()
        if not selected:
            return

        if tk.messagebox.askyesno("Confirm Delete",
                                  "Are you sure you want to delete the selected items?"):
            self.db.connect()
            try:
                # Store for undo
                deleted_items = []
                for item in selected:
                    values = {col: self.tree.set(item, col) for col in self.columns}
                    deleted_items.append((item, values))

                    # Delete from database
                    unique_id = values['unique_id_product']
                    self.db.delete_record(
                        TABLES['STORAGE'],
                        "unique_id_product = ?",
                        (unique_id,)
                    )

                    # Delete from tree
                    self.tree.delete(item)

                self.undo_stack.append(('delete', deleted_items))
                self.redo_stack.clear()

            finally:
                self.db.disconnect()

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
                self.update_record(old_values['unique_id_product'], col, value)

        elif action_type == 'delete':
            deleted_items = action[1]
            restored_items = []

            for item_id, values in deleted_items:
                # Restore to database
                self.db.insert_record(TABLES['STORAGE'], values)

                # Restore to tree
                new_item = self.tree.insert('', 'end', values=list(values.values()))
                restored_items.append((new_item, values))

            self.redo_stack.append(('undelete', restored_items))