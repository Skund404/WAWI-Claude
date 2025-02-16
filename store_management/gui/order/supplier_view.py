import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS


class SupplierView(ttk.Frame):
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

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'company_name', 'contact_person', 'phone_number', 'email_address',
            'website', 'street_address', 'city', 'state_province', 'postal_code',
            'country', 'tax_id', 'business_type', 'payment_terms', 'currency',
            'bank_details', 'products_offered', 'lead_time', 'last_order_date', 'notes'
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
            # Adjust column width based on content type
            if col in ['notes', 'products_offered', 'bank_details']:
                width = 200
            elif col in ['street_address', 'email_address', 'website']:
                width = 150
            else:
                width = 100
            self.tree.column(col, width=width, minwidth=50)

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

    def show_add_dialog(self):
        """Show dialog for adding new supplier"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Supplier")
        dialog.transient(self)
        dialog.grab_set()

        # Set dialog size
        dialog.geometry("600x800")

        # Create main frame with scrollbar
        main_frame = ttk.Frame(dialog)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Create entry fields
        entries = {}
        row = 0

        # Group fields by category
        field_groups = {
            'Basic Information': [
                'company_name', 'business_type', 'tax_id'
            ],
            'Contact Information': [
                'contact_person', 'phone_number', 'email_address', 'website'
            ],
            'Address': [
                'street_address', 'city', 'state_province',
                'postal_code', 'country'
            ],
            'Financial Information': [
                'payment_terms', 'currency', 'bank_details'
            ],
            'Business Details': [
                'products_offered', 'lead_time', 'notes'
            ]
        }

        # Required fields
        required_fields = [
            'company_name', 'contact_person', 'phone_number',
            'email_address', 'payment_terms'
        ]

        # Create fields by group
        for group, fields in field_groups.items():
            # Add group label
            ttk.Label(scrollable_frame, text=group, font=('', 10, 'bold')).grid(
                row=row, column=0, columnspan=2, sticky='w', pady=(10, 5)
            )
            row += 1

            for field in fields:
                # Create label
                label_text = field.replace('_', ' ').title()
                if field in required_fields:
                    label_text += " *"
                ttk.Label(scrollable_frame, text=label_text).grid(
                    row=row, column=0, sticky='w', padx=5, pady=2
                )

                # Create appropriate widget based on field
                if field in ['notes', 'products_offered']:
                    # Multi-line text entry
                    entry = tk.Text(scrollable_frame, height=3, width=40)
                    entry.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
                    entries[field] = entry
                elif field == 'payment_terms':
                    # Dropdown for payment terms
                    var = tk.StringVar()
                    combo = ttk.Combobox(scrollable_frame, textvariable=var)
                    combo['values'] = [
                        'Net 30', 'Net 60', 'Net 90',
                        'Immediate', 'Custom'
                    ]
                    combo.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
                    entries[field] = var
                elif field == 'currency':
                    # Dropdown for currency
                    var = tk.StringVar()
                    combo = ttk.Combobox(scrollable_frame, textvariable=var)
                    combo['values'] = [
                        'USD', 'EUR', 'GBP', 'JPY', 'CNY',
                        'CAD', 'AUD', 'Other'
                    ]
                    combo.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
                    entries[field] = var
                else:
                    # Standard entry
                    var = tk.StringVar()
                    ttk.Entry(scrollable_frame, textvariable=var).grid(
                        row=row, column=1, sticky='ew', padx=5, pady=2
                    )
                    entries[field] = var

                row += 1

        def validate_and_save():
            """Validate fields and save supplier"""
            # Validate required fields
            for field in required_fields:
                value = entries[field].get() if isinstance(entries[field], tk.StringVar) \
                    else entries[field].get('1.0', tk.END).strip()
                if not value:
                    messagebox.showerror(
                        "Error",
                        f"{field.replace('_', ' ').title()} is required"
                    )
                    return

            # Validate email format
            email = entries['email_address'].get()
            if '@' not in email or '.' not in email:
                messagebox.showerror("Error", "Invalid email address")
                return

            # Create supplier data
            supplier_data = {}
            for field, entry in entries.items():
                if isinstance(entry, tk.StringVar):
                    supplier_data[field] = entry.get()
                else:  # Text widget
                    supplier_data[field] = entry.get('1.0', tk.END).strip()

            try:
                self.db.connect()
                # Check if company name exists
                existing = self.db.execute_query(
                    "SELECT company_name FROM supplier WHERE company_name = ?",
                    (supplier_data['company_name'],)
                )

                if existing:
                    messagebox.showerror("Error", "Company name already exists")
                    return

                # Insert supplier
                if self.db.insert_record(TABLES['SUPPLIER'], supplier_data):
                    self.undo_stack.append(('add', supplier_data))
                    self.redo_stack.clear()
                    self.load_data()
                    dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add supplier: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save",
                   command=validate_and_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """Load data from database into table"""
        self.db.connect()
        try:
            query = "SELECT * FROM supplier ORDER BY company_name"
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

            col_num = int(column[1]) - 1
            col_name = self.columns[col_num]

            # Don't allow editing company_name as it's the primary key
            if col_name == 'company_name':
                return

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing"""
        col_num = int(column[1]) - 1
        col_name = self.columns[col_num]
        current_value = self.tree.set(item, col_name)

        # Create edit frame
        frame = ttk.Frame(self.tree)

        # Create appropriate edit widget based on field type
        if col_name in ['notes', 'products_offered']:
            # Multi-line text entry
            widget = tk.Text(frame, height=3, width=40)
            widget.insert('1.0', current_value)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
            widget.configure(yscrollcommand=scrollbar.set)
            widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        elif col_name == 'payment_terms':
            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)
            widget['values'] = ['Net 30', 'Net 60', 'Net 90', 'Immediate', 'Custom']
            widget.pack(fill=tk.BOTH, expand=True)
        elif col_name == 'currency':
            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)
            widget['values'] = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'Other']
            widget.pack(fill=tk.BOTH, expand=True)
        else:
            var = tk.StringVar(value=current_value)
            widget = ttk.Entry(frame, textvariable=var)
            widget.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = self.tree.bbox(item, column)
        frame.place(x=bbox[0], y=bbox[1],
                    width=max(bbox[2], 200),  # Minimum width for better usability
                    height=max(bbox[3], 100) if col_name in ['notes', 'products_offered'] else bbox[3])

        def save_edit(event=None):
            """Save the edited value"""
            if isinstance(widget, tk.Text):
                new_value = widget.get('1.0', tk.END).strip()
            else:
                new_value = var.get()

            if new_value != current_value:
                # Validate field based on type
                if col_name == 'email_address':
                    if '@' not in new_value or '.' not in new_value:
                        messagebox.showerror("Error", "Invalid email address")
                        return
                elif col_name == 'phone_number':
                    # Basic phone number validation
                    if not any(c.isdigit() for c in new_value):
                        messagebox.showerror("Error", "Phone number must contain digits")
                        return

                # Store for undo
                old_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, old_values))
                self.redo_stack.clear()

                # Update database
                company_name = self.tree.set(item, 'company_name')
                self.update_record(company_name, col_name, new_value)

                # Update tree
                self.tree.set(item, col_name, new_value)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        # Bind events
        if isinstance(widget, tk.Text):
            widget.bind('<Control-Return>', save_edit)
        else:
            widget.bind('<Return>', save_edit)
        widget.bind('<Escape>', cancel_edit)
        widget.bind('<FocusOut>', save_edit)
        widget.focus_set()

    def update_record(self, company_name: str, column: str, value: str):
        """Update record in database"""
        self.db.connect()
        try:
            success = self.db.update_record(
                TABLES['SUPPLIER'],
                {column: value},
                "company_name = ?",
                (company_name,)
            )
            if not success:
                messagebox.showerror("Error", "Failed to update database")
        finally:
            self.db.disconnect()

    def delete_selected(self, event=None):
        """Delete selected suppliers"""
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm Delete",
                               "Are you sure you want to delete the selected suppliers?"):
            self.db.connect()
            try:
                # Check for dependencies
                dependencies = []
                for item in selected:
                    company_name = self.tree.set(item, 'company_name')
                    # Check orders
                    orders = self.db.execute_query(
                        "SELECT order_number FROM orders WHERE supplier = ?",
                        (company_name,)
                    )
                    if orders:
                        dependencies.append(f"{company_name} (has orders)")

                    # Check shopping lists
                    shopping_lists = self.db.execute_query(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopping_list_%'"
                    )
                    for list_table in shopping_lists:
                        items = self.db.execute_query(
                            f"SELECT COUNT(*) FROM {list_table[0]} WHERE supplier = ?",
                            (company_name,)
                        )
                        if items and items[0][0] > 0:
                            dependencies.append(f"{company_name} (in shopping lists)")
                            break

                if dependencies:
                    messagebox.showerror(
                        "Error",
                        "Cannot delete suppliers with dependencies:\n" +
                        "\n".join(dependencies)
                    )
                    return

                # Store for undo
                deleted_items = []
                for item in selected:
                    values = {col: self.tree.set(item, col) for col in self.columns}
                    deleted_items.append((item, values))

                    # Delete from database
                    company_name = values['company_name']
                    self.db.delete_record(
                        TABLES['SUPPLIER'],
                        "company_name = ?",
                        (company_name,)
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
                if col != 'company_name':  # Don't update primary key
                    self.update_record(old_values['company_name'], col, value)

        elif action_type == 'add':
            data = action[1]
            # Delete added record
            self.db.connect()
            try:
                self.db.delete_record(
                    TABLES['SUPPLIER'],
                    "company_name = ?",
                    (data['company_name'],)
                )

                # Find and delete tree item
                for item in self.tree.get_children():
                    if self.tree.set(item, 'company_name') == data['company_name']:
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
                    self.db.insert_record(TABLES['SUPPLIER'], values)

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
                if col != 'company_name':  # Don't update primary key
                    self.update_record(new_values['company_name'], col, value)

        elif action_type == 'readd':
            data = action[1]
            # Re-add the record
            self.db.connect()
            try:
                if self.db.insert_record(TABLES['SUPPLIER'], data):
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
                        TABLES['SUPPLIER'],
                        "company_name = ?",
                        (values['company_name'],)
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', deleted_items))

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

    def reset_view(self):
        """Reset table to default view"""
        self.load_data()
