import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS
from gui.dialogs.add_dialog import AddDialog
from gui.dialogs.search_dialog import SearchDialog
from gui.dialogs.filter_dialog import FilterDialog


class ShelfView(ttk.Frame):
    def show_add_leather_dialog(self):
        """Show dialog for adding a new leather item to the shelf"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Leather")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entry fields
        entries = {}
        fields = [
            ('unique_id_leather', 'Leather ID', True),
            ('name', 'Leather Name', True),
            ('color', 'Color', True),
            ('size', 'Size', True),
            ('shelf', 'Shelf Location', False),
            ('notes', 'Notes', False)
        ]

        for i, (field, label, required) in enumerate(fields):
            ttk.Label(main_frame, text=f"{label}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)

            entries[field] = ttk.Entry(main_frame, width=40)
            entries[field].grid(row=i, column=1, sticky='ew', padx=5, pady=2)

            # Add required field indicator
            if required:
                ttk.Label(main_frame, text="*", foreground="red").grid(row=i, column=2, sticky='w')

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        def generate_leather_id():
            """Generate a unique leather ID"""
            import uuid
            prefix = ''.join(word[0].upper() for word in entries['name'].get().split()[:2])
            return f"L{prefix}{str(uuid.uuid4())[:8]}"

        def save_leather():
            """Save the new leather item to the database"""
            # Validate required fields
            required_fields = [field for field, _, req in fields if req]
            for field in required_fields:
                if not entries[field].get():
                    messagebox.showerror("Error", f"{field.replace('_', ' ').title()} is required")
                    return

            try:
                # Prepare data
                data = {field: entries[field].get() for field in entries}

                # Generate leather ID if not provided
                if not data['unique_id_leather']:
                    data['unique_id_leather'] = generate_leather_id()

                # Connect to database
                self.db.connect()
                try:
                    # Insert record
                    if self.db.insert_record(TABLES['SHELF'], data):
                        # Refresh the view
                        self.load_data()

                        # Show success message
                        messagebox.showinfo("Success", "Leather item added successfully")

                        # Close dialog
                        dialog.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to add leather item")
                finally:
                    self.db.disconnect()

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Save", command=save_leather).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Add required fields note
        ttk.Label(
            main_frame,
            text="* Required fields",
            foreground="red"
        ).grid(row=len(fields) + 1, column=0, columnspan=3, sticky='w', pady=(5, 0))

        # Set focus
        entries['name'].focus_set()
    def handle_return(self, event=None):
        """Handle Return key press - typically used for editing or confirming selection"""
        selected = self.tree.selection()
        if selected:
            # For example, you could start editing the first selected item
            self.start_cell_edit(selected[0], '#2')  # Start editing the second column

    def handle_escape(self, event=None):
        """Handle Escape key press - typically used to clear selection"""
        self.tree.selection_remove(self.tree.selection())
    def __init__(self, parent):
        super().__init__(parent)
        self.show_add_dialog = None
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
        ttk.Button(toolbar, text="ADD", command=self.show_add_leather_dialog).pack(side=tk.LEFT, padx=2)
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
        # Create treeview with scrollbars
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'unique_id_leather', 'name', 'type', 'color', 'thickness',
            'size_ft', 'area_sqft', 'shelf', 'notes'
        ]

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended'
        )

        # Setup scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

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
            query = "SELECT * FROM shelf ORDER BY shelf"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new data
            for row in results:
                self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

        finally:
            self.db.disconnect()


    def add_item(self, data: Dict[str, str]):
        """Add new item to database and table"""
        try:
            # Generate unique ID
            unique_id = f"L{str(uuid.uuid4())[:8]}"
            data['unique_id_leather'] = unique_id

            # Calculate area
            data['area_sqft'] = float(data['thickness']) * float(data['size_ft'])

            # Check if shelf is already in use
            self.db.connect()
            query = "SELECT shelf FROM shelf WHERE shelf = ?"
            result = self.db.execute_query(query, (data['shelf'],))

            if result:
                if not messagebox.askyesno("Warning",
                                           "Shelf already in use. Do you want to continue?"):
                    return False

            # Insert into database
            success = self.db.insert_record(TABLES['SHELF'], data)
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
        # Build SQL query
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

        # Execute query
        self.db.connect()
        try:
            query = "SELECT * FROM shelf"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY shelf"

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

    def on_double_click(self, event):
        """Handle double-click on cell"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if column == "#1":  # Unique ID column
                return  # Don't allow editing of ID

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing"""
        # Get column name and current value
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
                unique_id = self.tree.set(item, 'unique_id_leather')
                self.update_record(unique_id, col_name, new_value)

                # Update tree
                self.tree.set(item, col_name, new_value)

                # If thickness or size changed, update area
                if col_name in ['thickness', 'size_ft']:
                    self.update_area(item)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', save_edit)
        entry.focus_set()

    def update_area(self, item):
        """Update area calculation"""
        try:
            thickness = float(self.tree.set(item, 'thickness'))
            size_ft = float(self.tree.set(item, 'size_ft'))
            area = thickness * size_ft

            # Update database and tree
            unique_id = self.tree.set(item, 'unique_id_leather')
            self.update_record(unique_id, 'area_sqft', str(area))
            self.tree.set(item, 'area_sqft', str(area))

        except ValueError:
            messagebox.showerror("Error", "Invalid thickness or size values")

    def update_record(self, unique_id: str, column: str, value: str):
        """Update record in database"""
        self.db.connect()
        try:
            success = self.db.update_record(
                TABLES['SHELF'],
                {column: value},
                "unique_id_leather = ?",
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
                    unique_id = values['unique_id_leather']
                    self.db.delete_record(
                        TABLES['SHELF'],
                        "unique_id_leather = ?",
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
                self.update_record(old_values['unique_id_leather'], col, value)

        elif action_type == 'delete':
            deleted_items = action[1]
            restored_items = []

            for item_id, values in deleted_items:
                # Restore to database
                self.db.insert_record(TABLES['SHELF'], values)

                # Restore to tree
                new_item = self.tree.insert('', 'end', values=list(values.values()))
                restored_items.append((new_item, values))

            self.redo_stack.append(('undelete', restored_items))

        elif action_type == 'add':
            unique_id = action[1]
            values = action[2]

            # Remove from database
            self.db.delete_record(
                TABLES['SHELF'],
                "unique_id_leather = ?",
                (unique_id,)
            )

            # Remove from tree
            for item in self.tree.get_children():
                if self.tree.set(item, 'unique_id_leather') == unique_id:
                    self.tree.delete(item)
                    break

            self.redo_stack.append(('readd', values))

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        try:
            self.db.connect()

            if action_type == 'edit':
                # Store current values for undo
                item, old_values = action[1:]
                current_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, current_values))

                # Restore old values
                for col, value in old_values.items():
                    self.tree.set(item, col, value)
                    self.update_record(old_values['unique_id_leather'], col, value)

            elif action_type == 'readd':
                # Re-add the deleted item
                values = action[1]

                # Insert back into database
                success = self.db.insert_record(TABLES['SHELF'], values)

                if success:
                    # Add back to tree
                    new_item = self.tree.insert('', 'end', values=list(values.values()))

                    # Add to undo stack for potential future undo
                    self.undo_stack.append(('add', values))

            elif action_type == 'undelete':
                restored_items = action[1]
                deleted_items = []

                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        TABLES['SHELF'],
                        "unique_id_leather = ?",
                        (values['unique_id_leather'],)
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', deleted_items))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to redo: {str(e)}")
        finally:
            self.db.disconnect()

    def save_table(self):
        """Save current table state"""
        pass  # To be implemented

    def load_table(self):
        """Load saved table state"""
        pass  # To be implemented

    def reset_view(self):
        """Reset table to default view"""
        self.load_data()