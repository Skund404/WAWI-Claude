"""Storage View using SQLAlchemy ORM."""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from typing import Optional, Dict, Any
import uuid

from database.sqlalchemy.models_file import (
    Storage, Product, Project
)
from database.sqlalchemy.manager import DatabaseManagerSQLAlchemy


class StorageView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManagerSQLAlchemy()

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
        ttk.Button(toolbar, text="Undo",
                   command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo",
                   command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View",
                   command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'unique_id', 'name', 'type', 'collection',
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
            width = 200 if col in ['name', 'notes'] else 100
            self.tree.column(col, width=width, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Configure warning colors
        self.tree.tag_configure('low_stock', background='#FFB6C1')

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)

    def load_data(self):
        """Load storage data using SQLAlchemy"""
        try:
            with self.db.session_scope() as session:
                # Query all storage items with products and patterns
                storage_items = session.query(Storage) \
                    .join(Storage.product) \
                    .join(Product.pattern) \
                    .order_by(Storage.bin) \
                    .all()

                # Clear existing items
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Insert items
                for storage in storage_items:
                    values = [
                        storage.product.unique_id,
                        storage.product.name,
                        storage.product.pattern.type,
                        storage.product.pattern.collection,
                        storage.product.pattern.color,
                        storage.amount,
                        storage.bin,
                        storage.notes
                    ]
                    item = self.tree.insert('', 'end', values=values)

                    # Add low stock warning if needed
                    if storage.amount <= storage.warning_threshold:
                        self.tree.item(item, tags=('low_stock',))

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to load storage data: {str(e)}")

    def show_add_dialog(self):
        """Show dialog for adding new storage item"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Storage Item")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Get patterns for dropdown
        with self.db.session_scope() as session:
            patterns = session.query(Project.unique_id, Project.name).all()

        # Create fields
        ttk.Label(main_frame, text="Project:").grid(row=0, column=0, sticky='w')
        recipe_var = tk.StringVar()
        recipe_combo = ttk.Combobox(
            main_frame,
            textvariable=recipe_var,
            values=[f"{r[1]} ({r[0]})" for r in patterns]
        )
        recipe_combo.grid(row=0, column=1, sticky='ew')

        ttk.Label(main_frame, text="Amount:").grid(row=1, column=0, sticky='w')
        amount_var = tk.StringVar(value="1")
        ttk.Spinbox(
            main_frame,
            from_=1,
            to=1000,
            textvariable=amount_var
        ).grid(row=1, column=1, sticky='ew')

        ttk.Label(main_frame, text="Bin:").grid(row=2, column=0, sticky='w')
        bin_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=bin_var).grid(row=2, column=1, sticky='ew')

        ttk.Label(main_frame, text="Warning Threshold:").grid(row=3, column=0, sticky='w')
        threshold_var = tk.StringVar(value="5")
        ttk.Spinbox(
            main_frame,
            from_=1,
            to=100,
            textvariable=threshold_var
        ).grid(row=3, column=1, sticky='ew')

        ttk.Label(main_frame, text="Notes:").grid(row=4, column=0, sticky='w')
        notes_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=notes_var).grid(row=4, column=1, sticky='ew')

        def save():
            """Save new storage item"""
            try:
                recipe_text = recipe_var.get()
                if not recipe_text:
                    messagebox.showerror("Error", "Please select a pattern")
                    return

                # Get pattern ID from selection
                recipe_id = recipe_text.split('(')[1].strip(')')

                # Validate numeric inputs
                try:
                    amount = int(amount_var.get())
                    threshold = int(threshold_var.get())
                    if amount < 0 or threshold < 0:
                        raise ValueError("Values must be non-negative")
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                    return

                with self.db.session_scope() as session:
                    # Get or create product
                    pattern = session.query(Project) \
                        .filter(Project.unique_id == recipe_id) \
                        .first()

                    if not pattern:
                        messagebox.showerror("Error", "Project not found")
                        return

                    product = Product(
                        unique_id=f"P{str(uuid.uuid4())[:8]}",
                        name=pattern.name,
                        recipe_id=pattern.id
                    )
                    session.add(product)
                    session.flush()  # Get product ID

                    # Create storage item
                    storage = Storage(
                        product_id=product.id,
                        amount=amount,
                        warning_threshold=threshold,
                        bin=bin_var.get().strip(),
                        notes=notes_var.get().strip()
                    )
                    session.add(storage)
                    session.commit()

                    # Add to undo stack
                    self.undo_stack.append(('add', storage.id))
                    self.redo_stack.clear()

                    # Refresh view
                    self.load_data()
                    dialog.destroy()

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

    def show_search_dialog(self):
        """Show search dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Search Storage")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Search options
        ttk.Label(main_frame, text="Search in:").pack(anchor='w')
        target_var = tk.StringVar(value="all")
        ttk.Radiobutton(
            main_frame,
            text="All Fields",
            value="all",
            variable=target_var
        ).pack(anchor='w')

        for col in ['name', 'type', 'bin']:
            ttk.Radiobutton(
                main_frame,
                text=col.title(),
                value=col,
                variable=target_var
            ).pack(anchor='w')

        # Search text
        ttk.Label(main_frame, text="Search for:").pack(anchor='w', pady=(10, 0))
        search_var = tk.StringVar()
        ttk.Entry(
            main_frame,
            textvariable=search_var
        ).pack(fill='x', pady=5)

        # Match case option
        match_case = tk.BooleanVar()
        ttk.Checkbutton(
            main_frame,
            text="Match case",
            variable=match_case
        ).pack(anchor='w')

        def search():
            """Perform search"""
            try:
                search_text = search_var.get().strip()
                if not search_text:
                    messagebox.showwarning("Warning", "Please enter search text")
                    return

                with self.db.session_scope() as session:
                    query = session.query(Storage) \
                        .join(Storage.product) \
                        .join(Product.pattern)

                    # Build search conditions
                    if target_var.get() == "all":
                        conditions = [
                            Product.name.ilike(f"%{search_text}%"),
                            Project.type.ilike(f"%{search_text}%"),
                            Storage.bin.ilike(f"%{search_text}%")
                        ]
                        query = query.filter(or_(*conditions))
                    else:
                        if target_var.get() == 'name':
                            query = query.filter(Product.name.ilike(f"%{search_text}%"))
                        elif target_var.get() == 'type':
                            query = query.filter(Project.type.ilike(f"%{search_text}%"))
                        elif target_var.get() == 'bin':
                            query = query.filter(Storage.bin.ilike(f"%{search_text}%"))

                    results = query.all()

                    # Update view with results
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    for storage in results:
                        values = [
                            storage.product.unique_id,
                            storage.product.name,
                            storage.product.pattern.type,
                            storage.product.pattern.collection,
                            storage.product.pattern.color,
                            storage.amount,
                            storage.bin,
                            storage.notes
                        ]
                        item = self.tree.insert('', 'end', values=values)
                        if storage.amount <= storage.warning_threshold:
                            self.tree.item(item, tags=('low_stock',))

                    dialog.destroy()

                    if not results:
                        messagebox.showinfo("Search", "No matches found")

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Search failed: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Search",
            command=search
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def show_filter_dialog(self):
        """Show filter dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Filter Storage")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Filter options
        filter_frame = ttk.LabelFrame(main_frame, text="Filter Conditions")
        filter_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Type filter
        ttk.Label(filter_frame, text="Type:").grid(row=0, column=0, sticky='w', padx=5)
        # Get unique types from database
        with self.db.session_scope() as session:
            types = session.query(Project.type) \
                .distinct() \
                .order_by(Project.type) \
                .all()
            type_list = ['All'] + [t[0] for t in types if t[0]]

        type_var = tk.StringVar(value='All')
        ttk.Combobox(
            filter_frame,
            textvariable=type_var,
            values=type_list
        ).grid(row=0, column=1, sticky='ew', padx=5)

        # Amount filter
        ttk.Label(filter_frame, text="Amount:").grid(row=1, column=0, sticky='w', padx=5)
        amount_frame = ttk.Frame(filter_frame)
        amount_frame.grid(row=1, column=1, sticky='ew', padx=5)

        amount_op_var = tk.StringVar(value='>=')
        ttk.Combobox(
            amount_frame,
            textvariable=amount_op_var,
            values=['>=', '<=', '='],
            width=5
        ).pack(side=tk.LEFT, padx=2)

        amount_var = tk.StringVar()
        ttk.Entry(
            amount_frame,
            textvariable=amount_var,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        # Low stock filter
        low_stock_var = tk.BooleanVar()
        ttk.Checkbutton(
            filter_frame,
            text="Show only low stock items",
            variable=low_stock_var
        ).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        def apply_filters():
            """Apply the selected filters"""
            try:
                with self.db.session_scope() as session:
                    # Start with base query
                    query = session.query(Storage) \
                        .join(Storage.product) \
                        .join(Product.pattern)

                    # Apply type filter
                    if type_var.get() != 'All':
                        query = query.filter(Project.type == type_var.get())

                    # Apply amount filter
                    if amount_var.get().strip():
                        try:
                            amount = int(amount_var.get())
                            op = amount_op_var.get()
                            if op == '>=':
                                query = query.filter(Storage.amount >= amount)
                            elif op == '<=':
                                query = query.filter(Storage.amount <= amount)
                            elif op == '=':
                                query = query.filter(Storage.amount == amount)
                        except ValueError:
                            messagebox.showerror("Error", "Invalid amount value")
                            return

                    # Apply low stock filter
                    if low_stock_var.get():
                        query = query.filter(Storage.amount <= Storage.warning_threshold)

                    # Get results
                    results = query.order_by(Storage.bin).all()

                    # Update view
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Insert filtered results
                    for storage in results:
                        values = [
                            storage.product.unique_id,
                            storage.product.name,
                            storage.product.pattern.type,
                            storage.product.pattern.collection,
                            storage.product.pattern.color,
                            storage.amount,
                            storage.bin,
                            storage.notes
                        ]
                        item = self.tree.insert('', 'end', values=values)
                        if storage.amount <= storage.warning_threshold:
                            self.tree.item(item, tags=('low_stock',))

                    dialog.destroy()

                    if not results:
                        messagebox.showinfo("Filter", "No items match the selected criteria")

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Filter failed: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="Apply", command=apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        filter_frame.columnconfigure(1, weight=1)

    def delete_selected(self, event=None):
        """Delete selected storage items"""
        selected = self.tree.selection()
        if not selected:
            return

        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete {len(selected)} items?"):
            return

        try:
            with self.db.session_scope() as session:
                deleted_items = []
                for item_id in selected:
                    values = self.tree.item(item_id)['values']
                    unique_id = values[0]  # product unique_id

                    # Find and delete storage item
                    storage = session.query(Storage) \
                        .join(Storage.product) \
                        .filter(Product.unique_id == unique_id) \
                        .first()

                    if storage:
                        # Store data for undo
                        data = {
                            'product_data': {
                                column.name: getattr(storage.product, column.name)
                                for column in Product.__table__.columns
                            },
                            'storage_data': {
                                column.name: getattr(storage, column.name)
                                for column in Storage.__table__.columns
                            }
                        }
                        deleted_items.append(data)

                        # Delete storage and product
                        session.delete(storage.product)  # Will cascade to storage

                session.commit()

                if deleted_items:
                    self.undo_stack.append(('delete', deleted_items))
                    self.redo_stack.clear()

                    # Refresh view
                    self.load_data()

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to delete items: {str(e)}")

    def on_double_click(self, event):
        """Handle double-click for cell editing"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            # Only allow editing certain columns
            col_num = int(column[1]) - 1
            col_name = self.columns[col_num]
            if col_name not in ['amount', 'bin', 'notes']:
                return

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start editing a cell"""
        col_num = int(column[1]) - 1
        col_name = self.columns[col_num]
        current_value = self.tree.set(item, col_name)

        # Create edit frame
        frame = ttk.Frame(self.tree)

        # Create appropriate widget based on column
        if col_name == 'amount':
            widget = ttk.Spinbox(frame, from_=0, to=1000)
            widget.set(current_value)
        else:
            widget = ttk.Entry(frame)
            widget.insert(0, current_value)
            widget.select_range(0, tk.END)

        widget.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = self.tree.bbox(item, column)
        frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        def save_edit(event=None):
            try:
                new_value = widget.get().strip()
                if new_value == current_value:
                    frame.destroy()
                    return

                # Validate amount
                if col_name == 'amount':
                    try:
                        new_value = int(new_value)
                        if new_value < 0:
                            raise ValueError("Amount must be non-negative")
                    except ValueError as e:
                        messagebox.showerror("Error", str(e))
                        return

                with self.db.session_scope() as session:
                    # Get storage item
                    unique_id = self.tree.set(item, 'unique_id')
                    storage = session.query(Storage) \
                        .join(Storage.product) \
                        .filter(Product.unique_id == unique_id) \
                        .first()

                    if storage:
                        # Store old value for undo
                        old_value = getattr(storage, col_name)
                        self.undo_stack.append(('edit', storage.id, col_name, old_value))
                        self.redo_stack.clear()

                        # Update value
                        setattr(storage, col_name, new_value)
                        session.commit()

                        # Update tree
                        self.tree.set(item, col_name, str(new_value))

                        # Update warning tag if needed
                        if col_name == 'amount':
                            if new_value <= storage.warning_threshold:
                                self.tree.item(item, tags=('low_stock',))
                            else:
                                self.tree.item(item, tags=())

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to save edit: {str(e)}")
            finally:
                frame.destroy()

        def cancel_edit(event=None):
            frame.destroy()

        # Bind events
        widget.bind('<Return>', save_edit)
        widget.bind('<Escape>', cancel_edit)
        widget.bind('<FocusOut>', save_edit)
        widget.focus_set()

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        try:
            with self.db.session_scope() as session:
                if action_type == 'add':
                    storage_id = action[1]
                    storage = session.query(Storage).get(storage_id)
                    if storage:
                        # Store for redo
                        data = {
                            'product_data': {
                                column.name: getattr(storage.product, column.name)
                                for column in Product.__table__.columns
                            },
                            'storage_data': {
                                column.name: getattr(storage, column.name)
                                for column in Storage.__table__.columns
                            }
                        }
                        session.delete(storage.product)  # Will cascade to storage
                        self.redo_stack.append(('readd', data))

                elif action_type == 'edit':
                    storage_id, col_name, old_value = action[1:]
                    storage = session.query(Storage).get(storage_id)
                    if storage:
                        # Store current value for redo
                        current_value = getattr(storage, col_name)
                        self.redo_stack.append(('reedit', storage_id, col_name, current_value))

                        # Restore old value
                        setattr(storage, col_name, old_value)

                elif action_type == 'delete':
                    deleted_items = action[1]
                    restored_items = []
                    for data in deleted_items:
                        # Recreate product and storage
                        product = Product(**data['product_data'])
                        session.add(product)
                        session.flush()

                        storage_data = data['storage_data']
                        storage_data['product_id'] = product.id
                        storage = Storage(**storage_data)
                        session.add(storage)
                        session.flush()

                        restored_items.append((product.id, storage.id))

                    self.redo_stack.append(('redelete', restored_items))

                session.commit()
                self.load_data()

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Undo failed: {str(e)}")

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        try:
            with self.db.session_scope() as session:
                if action_type == 'readd':
                    data = action[1]
                    # Recreate product and storage
                    product = Product(**data['product_data'])
                    session.add(product)
                    session.flush()

                    storage_data = data['storage_data']
                    storage_data['product_id'] = product.id
                    storage = Storage(**storage_data)
                    session.add(storage)
                    session.flush()

                    self.undo_stack.append(('add', storage.id))

                elif action_type == 'reedit':
                    storage_id, col_name, new_value = action[1:]
                    storage = session.query(Storage).get(storage_id)
                    if storage:
                        # Store current value for undo
                        old_value = getattr(storage, col_name)
                        self.undo_stack.append(('edit', storage_id, col_name, old_value))

                        # Apply new value
                        setattr(storage, col_name, new_value)

                elif action_type == 'redelete':
                    restored_items = action[1]
                    deleted_items = []
                    for product_id, storage_id in restored_items:
                        storage = session.query(Storage).get(storage_id)
                        if storage:
                            data = {
                                'product_data': {
                                    column.name: getattr(storage.product, column.name)
                                    for column in Product.__table__.columns
                                },
                                'storage_data': {
                                    column.name: getattr(storage, column.name)
                                    for column in Storage.__table__.columns
                                }
                            }
                            deleted_items.append(data)
                            session.delete(storage.product)  # Will cascade to storage

                    self.undo_stack.append(('delete', deleted_items))

                session.commit()
                self.load_data()

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Redo failed: {str(e)}")

    def reset_view(self):
        """Reset view to default state"""
        self.load_data()