# gui/storage_view.py
import tkinter as tk
from tkinter import ttk, messagebox
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
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'unique_id_product', 'name', 'type', 'collection', 
            'color', 'amount', 'bin', 'notes'
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
        self.tree.bind('<Return>', self.handle_return)
        self.tree.bind('<Escape>', self.handle_escape)

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

    def show_add_dialog(self):
        """Show dialog for adding new item"""
        dialog = AddDialog(self, self.columns[1:], self.add_item)  # Exclude ID column
        self.wait_window(dialog)

    def add_item(self, data: Dict[str, str]):
        """Add new item to database and table"""
        try:
            # Generate unique ID
            unique_id = f"P{str(uuid.uuid4())[:8]}"
            data['unique_id_product'] = unique_id

            self.db.connect()
            success = self.db.insert_record(TABLES['STORAGE'], data)
            if success:
                # Add to undo stack
                self.undo_stack.append(('add', unique_id, data))
                self.redo_stack.clear()

                # Refresh table
                self.load_data()
                return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {str(e)}")
            return False
        finally:
            self.db.disconnect()

    def show_search_dialog(self):
        """Show search dialog"""
        dialog = SearchDialog(self, self.columns, self.search_items)
        self.wait_window(dialog)

    def search_items(self, search_params: Dict):
        """Search items based on search parameters"""
        column = search_params['column']
        search_text = search_params['text']
        match_case = search_params['match_case']

        # Clear current selection
        self.tree.selection_remove(*self.tree.selection())

        for item in self.tree.get_children():
            values = self.tree.item(item)['values']

            # Get the value to search in
            if column == 'All':
                search_in = ' '.join(str(v) for v in values)
            else:
                col_idx = self.columns.index(column)
                search_in = str(values[col_idx])

            # Perform search
            if not match_case:
                search_in = search_in.lower()
                search_text = search_text.lower()

            if search_text in search_in:
                self.tree.selection_add(item)
                self.tree.see(item)

    def show_filter_dialog(self):
        """Show filter dialog"""
        dialog = FilterDialog(self, self.columns, self.apply_filters)
        self.wait_window(dialog)

    def apply_filters(self, filters: List[Dict]):
        """Apply filters to the table view"""
        query = "SELECT * FROM storage WHERE "
        conditions = []
        params = []

        for filter_condition in filters:
            column = filter_condition['column']
            operator = filter_condition['operator']
            value = filter_condition['value']

            if operator == 'equals':
                conditions.append(f"{column} = ?")
                params.append(value)
            elif operator == 'contains':
                conditions.append(f"{column} LIKE ?")
                params.append(f"%{value}%")
            elif operator == 'greater than':
                conditions.append(f"{column} > ?")
                params.append(value)
            elif operator == 'less than':
                conditions.append(f"{column} < ?")
                params.append(value)

        query += " AND ".join(conditions)
        query += " ORDER BY bin"

        self.db.connect()
        try:
            results = self.db.execute_query(query, tuple(params))

            # Update table
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in results:
                self.tree.insert('', 'end', values=row[:-2])

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
            # Try numeric sort for amount column
            if col == 'amount':
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

    def on_double_click(self, event):
        """Handle double-click on cell"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if column == "#1":  # ID column
                return  # Don't allow editing of ID

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing"""
        col_num = int(column[1]) - 1
        col_name = self.columns[col_num]
        current_value = self.tree.set(item, col_name)

        # Create edit frame
        frame = ttk.Frame(self.tree)

        # Create entry widget
        entry = ttk.Entry(frame)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = self.tree.bbox(item, column)
        frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        def save_edit(event=None):
            """Save the edited value"""
            new_value = entry.get()
            if new_value != current_value:
                # Store for undo
                old_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, old_values))
                self.redo_stack.clear()

                # Update database
                unique_id = self.tree.set(item, 'unique_id_product')
                self.update_record(unique_id, col_name, new_value)

                # Update tree
                self.tree.set(item, col_name, new_value)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', save_edit)
        entry.focus_set()

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
                messagebox.showerror("Error", "Failed to update database")
        finally:
            self.db.disconnect()

    def delete_selected(self, event=None):
        """Delete selected items"""
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

        elif action_type == 'add':
            unique_id, data = action[1], action[2]
            # Remove from database
            self.db.delete_record(
                TABLES['STORAGE'],
                "unique_id_product = ?",
                (unique_id,)
            )

            # Remove from tree
            for item in self.tree.get_children():
                if self.tree.set(item, 'unique_id_product') == unique_id:
                    self.tree.delete(item)
                    break

            self.redo_stack.append(('readd', data))

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        try:
            self.db.connect()

            if action_type == 'edit':
                item, current_values = action[1:]
                # Store old values for potential undo
                old_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, old_values))

                # Restore current values
                for col, value in current_values.items():
                    self.tree.set(item, col, value)
                    self.update_record(current_values['unique_id_product'], col, value)

            elif action_type == 'readd':
                # Re-add the item
                data = action[1]

                # Insert back into database
                success = self.db.insert_record(TABLES['STORAGE'], data)

                if success:
                    # Add back to tree
                    self.tree.insert('', 'end', values=list(data.values()))

                    # Add to undo stack for potential future undo
                    self.undo_stack.append(('add', data['unique_id_product'], data))

            elif action_type == 'undelete':
                restored_items = action[1]
                deleted_items = []

                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        TABLES['STORAGE'],
                        "unique_id_product = ?",
                        (values['unique_id_product'],)
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', deleted_items))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to redo: {str(e)}")
        finally:
            self.db.disconnect()

    def handle_return(self, event=None):
        """Handle Return key press"""
        pass

    def handle_escape(self, event=None):
        """Handle Escape key press"""
        pass

    def save_table(self):
        """Save current table state"""
        pass

    def load_table(self):
        """Load saved table state"""
        pass

    def reset_view(self):
        """Reset table to default view"""
        self.load_data()