# shopping_list_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from database.database_manager import DatabaseManagerSQLAlchemy
from models.shopping_list import ShoppingList, ShoppingListItem
from models.supplier import Supplier
from models.part import Part
from models.leather import Leather

logger = logging.getLogger(__name__)

"""Shopping List View using SQLAlchemy ORM."""


class ShoppingListView(ttk.Frame):
    """View for managing shopping lists and items."""

    @inject(MaterialService)
    def __init__(self, parent):
        """
        Initialize the shopping list view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.parent = parent
        self.db = DatabaseManagerSQLAlchemy()
        self.undo_stack = []
        self.redo_stack = []
        self.current_list_id = None
        self.setup_table_selection()
        self.setup_toolbar()
        self.setup_table()
        self.load_shopping_lists()

    def setup_table_selection(self):
        """Create shopping list selection table view."""
        list_frame = ttk.LabelFrame(self, text='Shopping Lists')
        list_frame.pack(fill=tk.X, padx=5, pady=5)

        top_button_frame = ttk.Frame(list_frame)
        top_button_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(top_button_frame, text='New List', command=self.show_add_list_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_button_frame, text='Delete List', command=self.delete_list).pack(side=tk.LEFT, padx=2)

        self.list_tree_frame = ttk.Frame(list_frame)
        self.list_tree_frame.pack(expand=True, fill='both', padx=5, pady=5)
        self.list_columns = ['name', 'supplier', 'status', 'urgency', 'notes']
        list_vsb = ttk.Scrollbar(self.list_tree_frame, orient='vertical')
        list_hsb = ttk.Scrollbar(self.list_tree_frame, orient='horizontal')

        self.list_tree = ttk.Treeview(
            self.list_tree_frame,
            columns=self.list_columns,
            show='headings',
            selectmode='browse',
            height=5,
            yscrollcommand=list_vsb.set,
            xscrollcommand=list_hsb.set
        )

        list_vsb.configure(command=self.list_tree.yview)
        list_hsb.configure(command=self.list_tree.xview)

        for col in self.list_columns:
            self.list_tree.heading(col, text=col.title())
            width = 200 if col == 'supplier' else 100
            self.list_tree.column(col, width=width, minwidth=50)

        self.list_tree.tag_configure('urgency_green', background='#90EE90')
        self.list_tree.tag_configure('urgency_yellow', background='#FFFFE0')
        self.list_tree.tag_configure('urgency_red', background='#FFB6C1')

        self.list_tree.grid(row=0, column=0, sticky='nsew')
        list_vsb.grid(row=0, column=1, sticky='ns')
        list_hsb.grid(row=1, column=0, sticky='ew')
        self.list_tree_frame.grid_columnconfigure(0, weight=1)
        self.list_tree_frame.grid_rowconfigure(0, weight=1)

        self.list_tree.bind('<<TreeviewSelect>>', self.on_list_select)

    def setup_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text='Add Item', command=self.show_add_item_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Delete Item', command=self.delete_selected_items).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Undo', command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text='Redo', command=self.redo).pack(side=tk.RIGHT, padx=2)

    def setup_table(self):
        """Create main table for displaying shopping list items."""
        table_frame = ttk.LabelFrame(self, text='Shopping List Items')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.columns = ['name', 'unique_id', 'color', 'amount', 'price', 'notes']
        vsb = ttk.Scrollbar(table_frame, orient='vertical')
        hsb = ttk.Scrollbar(table_frame, orient='horizontal')

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        for col in self.columns:
            self.tree.heading(col, text=col.title())
            width = 150 if col == 'notes' else 100
            self.tree.column(col, width=width, minwidth=50)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vsb.pack(fill=tk.Y, side=tk.RIGHT)
        hsb.pack(fill=tk.X, side=tk.BOTTOM)

    def load_shopping_lists(self):
        """Load available shopping lists."""
        try:
            with self.db.session_scope() as session:
                shopping_lists = session.query(ShoppingList).join(ShoppingList.supplier).order_by(
                    ShoppingList.created_at.desc()).all()

                self.clear_tree(self.list_tree)

                for shopping_list in shopping_lists:
                    values = [
                        shopping_list.name,
                        shopping_list.supplier.company_name,
                        shopping_list.status,
                        shopping_list.urgency,
                        shopping_list.notes
                    ]
                    item = self.list_tree.insert('', 'end', values=values)

                    if shopping_list.urgency == 'Green':
                        self.list_tree.item(item, tags=('urgency_green',))
                    elif shopping_list.urgency == 'Yellow':
                        self.list_tree.item(item, tags=('urgency_yellow',))
                    elif shopping_list.urgency == 'Red':
                        self.list_tree.item(item, tags=('urgency_red',))

                logger.info(f"Loaded {len(shopping_lists)} shopping lists.")

        except SQLAlchemyError as e:
            messagebox.showerror('Error', f'Failed to load shopping lists: {str(e)}')
            logger.error(f"Failed to load shopping lists: {e}")

    def clear_tree(self, tree):
        """Clear all items from a treeview."""
        for item in tree.get_children():
            tree.delete(item)

    def show_add_list_dialog(self):
        """Show dialog for creating a new shopping list."""
        dialog = tk.Toplevel(self)
        dialog.title('Create New Shopping List')
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)

        suppliers = []
        try:
            with self.db.session_scope() as session:
                suppliers = session.query(Supplier).order_by(Supplier.company_name).all()
                supplier_names = [s.company_name for s in suppliers]

                ttk.Label(main_frame, text='List Name:').grid(row=0, column=0, sticky='w')
                name_var = tk.StringVar()
                ttk.Entry(main_frame, textvariable=name_var).grid(row=0, column=1, sticky='ew')

                ttk.Label(main_frame, text='Supplier:').grid(row=1, column=0, sticky='w')
                supplier_var = tk.StringVar()
                ttk.Combobox(main_frame, textvariable=supplier_var, values=supplier_names).grid(row=1, column=1,
                                                                                                sticky='ew')

                ttk.Label(main_frame, text='Status:').grid(row=2, column=0, sticky='w')
                status_var = tk.StringVar(value='not ordered')
                ttk.Combobox(main_frame, textvariable=status_var, values=['not ordered', 'ordered', 'template']).grid(
                    row=2, column=1, sticky='ew')

                ttk.Label(main_frame, text='Urgency:').grid(row=3, column=0, sticky='w')
                urgency_var = tk.StringVar(value='None')
                ttk.Combobox(main_frame, textvariable=urgency_var, values=['None', 'Green', 'Yellow', 'Red']).grid(
                    row=3, column=1, sticky='ew')

                ttk.Label(main_frame, text='Notes:').grid(row=4, column=0, sticky='w')
                notes_var = tk.StringVar()
                ttk.Entry(main_frame, textvariable=notes_var).grid(row=4, column=1, sticky='ew')
        except SQLAlchemyError as e:
            messagebox.showerror('Error', f'Failed to load suppliers: {str(e)}')
            logger.error(f"Failed to load suppliers: {e}")
            dialog.destroy()
            return

        def save():
            try:
                with self.db.session_scope() as session:
                    supplier = session.query(Supplier).filter(Supplier.company_name == supplier_var.get()).first()
                    if not supplier:
                        messagebox.showerror('Error', 'Please select a supplier')
                        return

                    shopping_list = ShoppingList(
                        name=name_var.get() or supplier.company_name,
                        supplier_id=supplier.id,
                        status=status_var.get(),
                        urgency=urgency_var.get(),
                        notes=notes_var.get()
                    )
                    session.add(shopping_list)
                    session.commit()

                    self.undo_stack.append(('add_list', shopping_list.id))
                    self.redo_stack.clear()
                    self.load_shopping_lists()
                    dialog.destroy()

                    logger.info(f"Created new shopping list: {shopping_list.name}")

            except SQLAlchemyError as e:
                messagebox.showerror('Error', f'Failed to create list: {str(e)}')
                logger.error(f"Failed to create shopping list: {e}")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text='Save', command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Cancel', command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        main_frame.columnconfigure(1, weight=1)
    def delete_list(self):
        """Delete the currently selected shopping list."""
        if not self.current_list_id:
            messagebox.showwarning('Warning', 'Please select a shopping list')
            return

        if not messagebox.askyesno('Confirm Delete', 'Are you sure you want to delete this shopping list?'):
            return

        try:
            with self.db.session_scope() as session:
                shopping_list = session.query(ShoppingList).get(self.current_list_id)
                if shopping_list:
                    # Save data for undo
                    list_data = {
                        'name': shopping_list.name,
                        'supplier_id': shopping_list.supplier_id,
                        'status': shopping_list.status,
                        'urgency': shopping_list.urgency,
                        'notes': shopping_list.notes
                    }

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

                    session.delete(shopping_list)
                    session.commit()

                    self.undo_stack.append(('delete_list', list_data, items_data))
                    self.redo_stack.clear()
                    self.current_list_id = None

                    self.load_shopping_lists()
                    self.clear_tree(self.tree)

                    logger.info(f"Deleted shopping list: {shopping_list.name}")

        except SQLAlchemyError as e:
            messagebox.showerror('Error', f'Failed to delete list: {str(e)}')
            logger.error(f"Failed to delete shopping list: {e}")

    def delete_selected_items(self):
        """Delete selected items from the current shopping list."""
        if not self.current_list_id:
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Warning', 'Please select items to delete')
            return

        if not messagebox.askyesno('Confirm Delete', f'Delete {len(selected)} items?'):
            return

        try:
            with self.db.session_scope() as session:
                deleted_items = []
                for item_id in selected:
                    values = self.tree.item(item_id)['values']
                    unique_id = values[1]

                    item = session.query(ShoppingListItem).filter(
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

                if deleted_items:
                    self.undo_stack.append(('delete_items', self.current_list_id, deleted_items))
                    self.redo_stack.clear()
                    self.load_list_items(self.current_list_id)

                logger.info(f"Deleted {len(deleted_items)} items from shopping list {self.current_list_id}")

        except SQLAlchemyError as e:
            messagebox.showerror('Error', f'Failed to delete items: {str(e)}')
            logger.error(f"Failed to delete shopping list items: {e}")

    def undo(self, event=None):
        """Undo the last action."""
        if not self.undo_stack:
            messagebox.showinfo('Info', 'Nothing to undo')
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        try:
            with self.db.session_scope() as session:
                if action_type == 'add_list':
                    list_id = action[1]
                    shopping_list = session.query(ShoppingList).get(list_id)
                    if shopping_list:
                        session.delete(shopping_list)
                        self.redo_stack.append(('readd_list', {
                            'name': shopping_list.name,
                            'supplier_id': shopping_list.supplier_id,
                            'status': shopping_list.status,
                            'urgency': shopping_list.urgency,
                            'notes': shopping_list.notes
                        }))

                elif action_type == 'delete_list':
                    list_data, items_data = action[1:]
                    new_list = ShoppingList(**list_data)
                    session.add(new_list)
                    session.flush()

                    for item_data in items_data:
                        item_data['shopping_list_id'] = new_list.id
                        new_item = ShoppingListItem(**item_data)
                        session.add(new_item)

                    self.redo_stack.append(('redelete_list', new_list.id))

                elif action_type == 'delete_items':
                    list_id, items_data = action[1:]
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
                self.load_shopping_lists()

                if self.current_list_id:
                    self.load_list_items(self.current_list_id)

                logger.info(f"Undid action: {action_type}")

        except SQLAlchemyError as e:
            messagebox.showerror('Error', f'Undo failed: {str(e)}')
            logger.error(f"Undo operation failed: {e}")

    def redo(self, event=None):
        """Redo the last undone action."""
        if not self.redo_stack:
            messagebox.showinfo('Info', 'Nothing to redo')
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
                        item_data['shopping_list_id'] = list_id
                        new_item = ShoppingListItem(**item_data)
                        session.add(new_item)

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
                self.load_shopping_lists()

                if self.current_list_id:
                    self.load_list_items(self.current_list_id)

                logger.info(f"Redid action: {action_type}")

        except SQLAlchemyError as e:
            messagebox.showerror('Error', f'Redo failed: {str(e)}')
            logger.error(f"Redo operation failed: {e}")
