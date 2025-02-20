"""Shopping List View using SQLAlchemy ORM."""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from datetime import datetime

from store_management.database.sqlalchemy.models import (
    ShoppingList, ShoppingListItem, Supplier, Part, Leather
)
from store_management.database.sqlalchemy.manager import DatabaseManagerSQLAlchemy


class ShoppingListView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = DatabaseManagerSQLAlchemy()

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Track current list
        self.current_list_id = None

        # Setup UI components
        self.setup_table_selection()
        self.setup_toolbar()
        self.setup_table()
        self.load_shopping_lists()

    def setup_table_selection(self):
        """Create shopping list selection table view"""
        # Create list frame with label
        list_frame = ttk.LabelFrame(self, text="Shopping Lists")
        list_frame.pack(fill=tk.X, padx=5, pady=5)

        # Top button frame
        top_button_frame = ttk.Frame(list_frame)
        top_button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(top_button_frame, text="New List",
                   command=self.show_add_list_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_button_frame, text="Delete List",
                   command=self.delete_list).pack(side=tk.LEFT, padx=2)

        # List tree frame
        self.list_tree_frame = ttk.Frame(list_frame)
        self.list_tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.list_columns = ['name', 'supplier', 'status', 'urgency', 'notes']

        # Create scrollbars
        list_vsb = ttk.Scrollbar(self.list_tree_frame, orient="vertical")
        list_hsb = ttk.Scrollbar(self.list_tree_frame, orient="horizontal")

        # Create list tree
        self.list_tree = ttk.Treeview(
            self.list_tree_frame,
            columns=self.list_columns,
            show='headings',
            selectmode='browse',
            height=5,
            yscrollcommand=list_vsb.set,
            xscrollcommand=list_hsb.set
        )

        # Configure scrollbars
        list_vsb.configure(command=self.list_tree.yview)
        list_hsb.configure(command=self.list_tree.xview)

        # Setup headers
        for col in self.list_columns:
            self.list_tree.heading(col, text=col.title())
            width = 200 if col == 'supplier' else 100
            self.list_tree.column(col, width=width, minwidth=50)

        # Configure urgency color tags
        self.list_tree.tag_configure('urgency_green', background='#90EE90')
        self.list_tree.tag_configure('urgency_yellow', background='#FFFFE0')
        self.list_tree.tag_configure('urgency_red', background='#FFB6C1')

        # Grid layout
        self.list_tree.grid(row=0, column=0, sticky='nsew')
        list_vsb.grid(row=0, column=1, sticky='ns')
        list_hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        self.list_tree_frame.grid_columnconfigure(0, weight=1)
        self.list_tree_frame.grid_rowconfigure(0, weight=1)

        # Bind selection event
        self.list_tree.bind('<<TreeviewSelect>>', self.on_list_select)

    def load_shopping_lists(self):
        """Load available shopping lists"""
        try:
            with self.db.session_scope() as session:
                shopping_lists = session.query(ShoppingList) \
                    .join(ShoppingList.supplier) \
                    .order_by(ShoppingList.created_at.desc()) \
                    .all()

                # Clear existing items
                for item in self.list_tree.get_children():
                    self.list_tree.delete(item)

                # Insert lists
                for shopping_list in shopping_lists:
                    values = [
                        shopping_list.name,
                        shopping_list.supplier.company_name,
                        shopping_list.status,
                        shopping_list.urgency,
                        shopping_list.notes
                    ]
                    item = self.list_tree.insert('', 'end', values=values)

                    # Apply urgency tag
                    if shopping_list.urgency == 'Green':
                        self.list_tree.item(item, tags=('urgency_green',))
                    elif shopping_list.urgency == 'Yellow':
                        self.list_tree.item(item, tags=('urgency_yellow',))
                    elif shopping_list.urgency == 'Red':
                        self.list_tree.item(item, tags=('urgency_red',))

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to load shopping lists: {str(e)}")

    def show_add_list_dialog(self):
        """Show dialog for creating new shopping list"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Get suppliers
        with self.db.session_scope() as session:
            suppliers = session.query(Supplier).order_by(Supplier.company_name).all()
            supplier_names = [s.company_name for s in suppliers]

        # Create fields
        ttk.Label(main_frame, text="List Name:").grid(row=0, column=0, sticky='w')
        name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=name_var).grid(row=0, column=1, sticky='ew')

        ttk.Label(main_frame, text="Supplier:").grid(row=1, column=0, sticky='w')
        supplier_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=supplier_var, values=supplier_names) \
            .grid(row=1, column=1, sticky='ew')

        ttk.Label(main_frame, text="Status:").grid(row=2, column=0, sticky='w')
        status_var = tk.StringVar(value="not ordered")
        ttk.Combobox(main_frame, textvariable=status_var,
                     values=["not ordered", "ordered", "template"]) \
            .grid(row=2, column=1, sticky='ew')

        ttk.Label(main_frame, text="Urgency:").grid(row=3, column=0, sticky='w')
        urgency_var = tk.StringVar(value="None")
        ttk.Combobox(main_frame, textvariable=urgency_var,
                     values=["None", "Green", "Yellow", "Red"]) \
            .grid(row=3, column=1, sticky='ew')

        ttk.Label(main_frame, text="Notes:").grid(row=4, column=0, sticky='w')
        notes_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=notes_var).grid(row=4, column=1, sticky='ew')

        def save():
            try:
                with self.db.session_scope() as session:
                    # Get supplier
                    supplier = session.query(Supplier) \
                        .filter(Supplier.company_name == supplier_var.get()) \
                        .first()

                    if not supplier:
                        messagebox.showerror("Error", "Please select a supplier")
                        return

                    # Create shopping list
                    shopping_list = ShoppingList(
                        name=name_var.get() or supplier.company_name,
                        supplier_id=supplier.id,
                        status=status_var.get(),
                        urgency=urgency_var.get(),
                        notes=notes_var.get()
                    )

                    session.add(shopping_list)
                    session.commit()

                    # Add to undo stack
                    self.undo_stack.append(('add_list', shopping_list.id))
                    self.redo_stack.clear()

                    # Refresh lists
                    self.load_shopping_lists()
                    dialog.destroy()

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to create list: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

    def on_list_select(self, event):
        """Handle shopping list selection"""
        selected = self.list_tree.selection()
        if not selected:
            return

        try:
            with self.db.session_scope() as session:
                # Get selected list name and supplier
                values = self.list_tree.item(selected[0])['values']
                name = values[0]
                supplier_name = values[1]

                # Find shopping list
                shopping_list = session.query(ShoppingList) \
                    .join(ShoppingList.supplier) \
                    .filter(
                    ShoppingList.name == name,
                    Supplier.company_name == supplier_name
                ).first()

                if shopping_list:
                    self.current_list_id = shopping_list.id
                    self.load_list_items(shopping_list.id)
                else:
                    self.current_list_id = None
                    # Clear items table
                    for item in self.tree.get_children():
                        self.tree.delete(item)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to select list: {str(e)}")

    def load_list_items(self, list_id: int):
        """Load items for selected shopping list"""
        try:
            with self.db.session_scope() as session:
                # Clear existing items
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Get list items with parts and leather
                items = session.query(ShoppingListItem) \
                    .filter(ShoppingListItem.shopping_list_id == list_id) \
                    .outerjoin(ShoppingListItem.part) \
                    .outerjoin(ShoppingListItem.leather) \
                    .all()

                for item in items:
                    if item.part:
                        name = item.part.name
                        unique_id = item.part.unique_id
                        color = item.part.color
                    elif item.leather:
                        name = item.leather.name
                        unique_id = item.leather.unique_id
                        color = item.leather.color
                    else:
                        continue

                    values = [
                        name,
                        unique_id,
                        color,
                        item.amount,
                        item.price or 0.0,
                        item.notes or ''
                    ]
                    self.tree.insert('', 'end', values=values)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to load list items: {str(e)}")

    def show_add_item_dialog(self):
        """Show dialog for adding item to shopping list"""
        if not self.current_list_id:
            messagebox.showwarning("Warning", "Please select a shopping list")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Get available items
        with self.db.session_scope() as session:
            parts = session.query(Part.unique_id, Part.name).all()
            leathers = session.query(Leather.unique_id, Leather.name).all()

        # Create items list for combobox
        items = ['+ Add New Part', '+ Add New Leather']
        items.extend([f"{p[1]} ({p[0]})" for p in parts])
        items.extend([f"{l[1]} ({l[0]})" for l in leathers])

        # Create fields
        ttk.Label(main_frame, text="Item:").grid(row=0, column=0, sticky='w')
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(main_frame, textvariable=item_var, values=items)
        item_combo.grid(row=0, column=1, sticky='ew')

        ttk.Label(main_frame, text="Amount:").grid(row=1, column=0, sticky='w')
        amount_var = tk.StringVar(value="1")
        ttk.Spinbox(main_frame, from_=1, to=1000,
                    textvariable=amount_var).grid(row=1, column=1, sticky='ew')

        ttk.Label(main_frame, text="Price:").grid(row=2, column=0, sticky='w')
        price_var = tk.StringVar(value="0.0")
        ttk.Entry(main_frame, textvariable=price_var).grid(row=2, column=1, sticky='ew')

        ttk.Label(main_frame, text="Notes:").grid(row=3, column=0, sticky='w')
        notes_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=notes_var).grid(row=3, column=1, sticky='ew')

        def save():
            try:
                item_text = item_var.get()
                if item_text.startswith('+ Add New'):
                    if 'Part' in item_text:
                        # Show add part dialog
                        dialog.destroy()
                        self.show_add_part_dialog(self)
                    else:
                        # Show add leather dialog
                        dialog.destroy()
                        self.show_add_leather_dialog(self)
                    return

                # Get unique_id from selected item
                unique_id = item_text.split('(')[1].strip(')')

                with self.db.session_scope() as session:
                    # Create new item
                    item_data = {
                        'shopping_list_id': self.current_list_id,
                        'amount': int(amount_var.get()),
                        'price': float(price_var.get()),
                        'notes': notes_var.get()
                    }

                    # Link to part or leather based on unique_id
                    if unique_id.startswith('P'):
                        part = session.query(Part) \
                            .filter(Part.unique_id == unique_id) \
                            .first()
                        item_data['part_id'] = part.id
                    else:
                        leather = session.query(Leather) \
                            .filter(Leather.unique_id == unique_id) \
                            .first()
                        item_data['leather_id'] = leather.id

                    # Create and add item
                    item = ShoppingListItem(**item_data)
                    session.add(item)
                    session.commit()

                    # Add to undo stack
                    self.undo_stack.append(('add_item', item.id))
                    self.redo_stack.clear()

                    # Refresh items
                    self.load_list_items(self.current_list_id)
                    dialog.destroy()

            except (ValueError, SQLAlchemyError) as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")

                # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=4, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text="Add", command=save).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel",
                       command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Configure grid
            main_frame.columnconfigure(1, weight=1)

        def delete_list(self):
            """Delete current shopping list"""
            if not self.current_list_id:
                messagebox.showwarning("Warning", "Please select a shopping list")
                return

            if not messagebox.askyesno("Confirm Delete",
                                       "Are you sure you want to delete this shopping list?"):
                return

            try:
                with self.db.session_scope() as session:
                    shopping_list = session.query(ShoppingList).get(self.current_list_id)
                    if shopping_list:
                        # Store for undo
                        list_data = {
                            'name': shopping_list.name,
                            'supplier_id': shopping_list.supplier_id,
                            'status': shopping_list.status,
                            'urgency': shopping_list.urgency,
                            'notes': shopping_list.notes
                        }

                        # Get items for undo
                        items_data = []
                        for item in shopping_list.items:
                            item_data = {
                                'amount': item.amount,
                                'price': item.price,
                                'notes': item.notes,
                                'part_id': item.part_id,
                                'leather_id': item.leather_id
                            }
                            items_data.append(item_data)

                        # Delete list (cascade will handle items)
                        session.delete(shopping_list)
                        session.commit()

                        # Add to undo stack
                        self.undo_stack.append(('delete_list', list_data, items_data))
                        self.redo_stack.clear()

                        # Clear current list
                        self.current_list_id = None

                        # Refresh views
                        self.load_shopping_lists()
                        for item in self.tree.get_children():
                            self.tree.delete(item)

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to delete list: {str(e)}")

        def delete_selected_items(self):
            """Delete selected items from current list"""
            if not self.current_list_id:
                return

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
                        unique_id = values[1]  # unique_id column

                        # Find and delete item
                        item = session.query(ShoppingListItem) \
                            .filter(
                            ShoppingListItem.shopping_list_id == self.current_list_id,
                            ShoppingListItem.unique_id == unique_id
                        ).first()

                        if item:
                            item_data = {
                                'amount': item.amount,
                                'price': item.price,
                                'notes': item.notes,
                                'part_id': item.part_id,
                                'leather_id': item.leather_id
                            }
                            deleted_items.append(item_data)
                            session.delete(item)

                    session.commit()

                    # Add to undo stack
                    if deleted_items:
                        self.undo_stack.append(('delete_items', self.current_list_id, deleted_items))
                        self.redo_stack.clear()

                    # Refresh items
                    self.load_list_items(self.current_list_id)

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to delete items: {str(e)}")

        def update_list_status(self, list_id: int, new_status: str):
            """Update shopping list status"""
            try:
                with self.db.session_scope() as session:
                    shopping_list = session.query(ShoppingList).get(list_id)
                    if shopping_list:
                        old_status = shopping_list.status
                        shopping_list.status = new_status
                        session.commit()

                        # Add to undo stack
                        self.undo_stack.append(('update_status', list_id, old_status))
                        self.redo_stack.clear()

                        return True
                    return False

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to update status: {str(e)}")
                return False

        def update_list_urgency(self, list_id: int, new_urgency: str):
            """Update shopping list urgency"""
            try:
                with self.db.session_scope() as session:
                    shopping_list = session.query(ShoppingList).get(list_id)
                    if shopping_list:
                        old_urgency = shopping_list.urgency
                        shopping_list.urgency = new_urgency
                        session.commit()

                        # Add to undo stack
                        self.undo_stack.append(('update_urgency', list_id, old_urgency))
                        self.redo_stack.clear()

                        return True
                    return False

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to update urgency: {str(e)}")
                return False

        def undo(self, event=None):
            """Undo last action"""
            if not self.undo_stack:
                return

            action = self.undo_stack.pop()
            action_type = action[0]

            try:
                with self.db.session_scope() as session:
                    if action_type == 'add_list':
                        list_id = action[1]
                        shopping_list = session.query(ShoppingList).get(list_id)
                        if shopping_list:
                            # Store for redo
                            list_data = {
                                'name': shopping_list.name,
                                'supplier_id': shopping_list.supplier_id,
                                'status': shopping_list.status,
                                'urgency': shopping_list.urgency,
                                'notes': shopping_list.notes
                            }
                            session.delete(shopping_list)
                            self.redo_stack.append(('readd_list', list_data))

                    elif action_type == 'add_item':
                        item_id = action[1]
                        item = session.query(ShoppingListItem).get(item_id)
                        if item:
                            # Store for redo
                            item_data = {
                                'shopping_list_id': item.shopping_list_id,
                                'amount': item.amount,
                                'price': item.price,
                                'notes': item.notes,
                                'part_id': item.part_id,
                                'leather_id': item.leather_id
                            }
                            session.delete(item)
                            self.redo_stack.append(('readd_item', item_data))

                    elif action_type == 'delete_list':
                        list_data, items_data = action[1:]
                        # Recreate list
                        new_list = ShoppingList(**list_data)
                        session.add(new_list)
                        session.flush()  # Get new list ID

                        # Recreate items
                        for item_data in items_data:
                            item_data['shopping_list_id'] = new_list.id
                            new_item = ShoppingListItem(**item_data)
                            session.add(new_item)

                        self.redo_stack.append(('redelete_list', new_list.id))

                    elif action_type == 'delete_items':
                        list_id, items_data = action[1:]
                        # Recreate items
                        for item_data in items_data:
                            item_data['shopping_list_id'] = list_id
                            new_item = ShoppingListItem(**item_data)
                            session.add(new_item)

                        self.redo_stack.append(('redelete_items', list_id, items_data))

                    elif action_type == 'update_status':
                        list_id, old_status = action[1:]
                        shopping_list = session.query(ShoppingList).get(list_id)
                        if shopping_list:
                            current_status = shopping_list.status
                            shopping_list.status = old_status
                            self.redo_stack.append(('reupdate_status', list_id, current_status))

                    elif action_type == 'update_urgency':
                        list_id, old_urgency = action[1:]
                        shopping_list = session.query(ShoppingList).get(list_id)
                        if shopping_list:
                            current_urgency = shopping_list.urgency
                            shopping_list.urgency = old_urgency
                            self.redo_stack.append(('reupdate_urgency', list_id, current_urgency))

                    session.commit()

                    # Refresh views
                    self.load_shopping_lists()
                    if self.current_list_id:
                        self.load_list_items(self.current_list_id)

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
                    if action_type == 'readd_list':
                        list_data = action[1]
                        new_list = ShoppingList(**list_data)
                        session.add(new_list)
                        session.flush()
                        self.undo_stack.append(('add_list', new_list.id))

                    elif action_type == 'readd_item':
                        item_data = action[1]
                        new_item = ShoppingListItem(**item_data)
                        session.add(new_item)
                        session.flush()
                        self.undo_stack.append(('add_item', new_item.id))

                    elif action_type == 'redelete_list':
                        list_id = action[1]
                        shopping_list = session.query(ShoppingList).get(list_id)
                        if shopping_list:
                            list_data = {
                                'name': shopping_list.name,
                                'supplier_id': shopping_list.supplier_id,
                                'status': shopping_list.status,
                                'urgency': shopping_list.urgency,
                                'notes': shopping_list.notes
                            }
                            items_data = [{
                                'amount': item.amount,
                                'price': item.price,
                                'notes': item.notes,
                                'part_id': item.part_id,
                                'leather_id': item.leather_id
                            } for item in shopping_list.items]

                            session.delete(shopping_list)
                            self.undo_stack.append(('delete_list', list_data, items_data))

                    elif action_type == 'redelete_items':
                        list_id, items_data = action[1:]
                        for item_data in items_data:
                            item = ShoppingListItem(**item_data)
                            session.delete(item)
                        self.undo_stack.append(('delete_items', list_id, items_data))

                    elif action_type == 'reupdate_status':
                        list_id, new_status = action[1:]
                        shopping_list = session.query(ShoppingList).get(list_id)
                        if shopping_list:
                            old_status = shopping_list.status
                            shopping_list.status = new_status
                            self.undo_stack.append(('update_status', list_id, old_status))

                    elif action_type == 'reupdate_urgency':
                        list_id, new_urgency = action[1:]
                        shopping_list = session.query(ShoppingList).get(list_id)
                        if shopping_list:
                            old_urgency = shopping_list.urgency
                            shopping_list.urgency = new_urgency
                            self.undo_stack.append(('update_urgency', list_id, old_urgency))

                    session.commit()

                    # Refresh views
                    self.load_shopping_lists()
                    if self.current_list_id:
                        self.load_list_items(self.current_list_id)

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Redo failed: {str(e)}")