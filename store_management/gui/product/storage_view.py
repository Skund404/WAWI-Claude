# storage_view.py
"""
Storage View module using SQLAlchemy ORM for managing storage items in a tkinter-based GUI.

This module provides a comprehensive view for managing storage items, including
functionalities like adding, editing, deleting, searching, and filtering items.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
import uuid
from typing import Optional, List, Tuple

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.storage import Storage
from models.product import Product
from models.project import Project
from utils.database import DatabaseManagerSQLAlchemy

# Configure logging
logger = logging.getLogger(__name__)


class StorageView(ttk.Frame):
    """
    A view for managing storage items with comprehensive CRUD operations.

    Attributes:
        db (DatabaseManagerSQLAlchemy): Database connection manager.
        undo_stack (List[Tuple]): Stack for undo operations.
        redo_stack (List[Tuple]): Stack for redo operations.
        tree (ttk.Treeview): Treeview widget for displaying storage items.
        columns (List[str]): List of column names for the treeview.
    """

    @inject(MaterialService)
    def __init__(self, parent: ttk.Frame):
        """
        Initialize the StorageView.

        Args:
            parent (ttk.Frame): Parent frame for the view.
        """
        try:
            super().__init__(parent)

            self.db = DatabaseManagerSQLAlchemy()
            self.undo_stack: List[Tuple] = []
            self.redo_stack: List[Tuple] = []

            self.setup_toolbar()
            self.setup_table()
            self.load_data()

            logger.info('StorageView initialized successfully')

        except Exception as e:
            logger.exception(f'Failed to initialize StorageView: {e}')
            raise

    @inject(MaterialService)
    def setup_toolbar(self) -> None:
        """Create the toolbar with action buttons."""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text='ADD', command=self.show_add_dialog).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Search', command=self.show_search_dialog).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Filter', command=self.show_filter_dialog).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Undo', command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text='Redo', command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text='Reset View', command=self.reset_view).pack(
            side=tk.RIGHT, padx=2)

    @inject(MaterialService)
    def setup_table(self) -> None:
        """Create the main table view."""
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        self.columns = ['unique_id', 'name', 'type', 'collection', 'color',
                        'amount', 'bin', 'notes']

        vsb = ttk.Scrollbar(self.tree_frame, orient='vertical')
        hsb = ttk.Scrollbar(self.tree_frame, orient='horizontal')

        self.tree = ttk.Treeview(self.tree_frame, columns=self.columns,
                                 show='headings', selectmode='extended',
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        for col in self.columns:
            self.tree.heading(col, text=col.replace('_', ' ').title(),
                              command=lambda c=col: self.sort_column(c))
            width = 200 if col in ['name', 'notes'] else 100
            self.tree.column(col, width=width, minwidth=50)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        self.tree.tag_configure('low_stock', background='#FFB6C1')
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)

    @inject(MaterialService)
    def load_data(self) -> None:
        """Load storage data using SQLAlchemy."""
        try:
            with self.db.session_scope() as session:
                storage_items = session.query(Storage).join(Storage.product).join(
                    Product.pattern).order_by(Storage.bin).all()

                self.tree.delete(*self.tree.get_children())

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
                    if storage.amount <= storage.warning_threshold:
                        self.tree.item(item, tags=('low_stock',))

        except SQLAlchemyError as e:
            logger.exception(f'Failed to load storage data: {e}')
            messagebox.showerror('Error', f'Failed to load storage data: {str(e)}')

    @inject(MaterialService)
    def show_add_dialog(self) -> None:
        """Show dialog for adding a new storage item."""
        try:
            dialog = tk.Toplevel(self)
            dialog.title('Add New Storage Item')
            dialog.transient(self)
            dialog.grab_set()

            main_frame = ttk.Frame(dialog, padding='10')
            main_frame.pack(fill=tk.BOTH, expand=True)

            with self.db.session_scope() as session:
                patterns = session.query(Project.unique_id, Project.name).all()

            ttk.Label(main_frame, text='Project:').grid(row=0, column=0, sticky='w')
            recipe_var = tk.StringVar()
            recipe_combo = ttk.Combobox(main_frame, textvariable=recipe_var,
                                        values=[f'{r[1]} ({r[0]})' for r in patterns])
            recipe_combo.grid(row=0, column=1, sticky='ew')

            ttk.Label(main_frame, text='Amount:').grid(row=1, column=0, sticky='w')
            amount_var = tk.StringVar(value='1')
            ttk.Spinbox(main_frame, from_=1, to=1000, textvariable=amount_var).grid(
                row=1, column=1, sticky='ew')

            ttk.Label(main_frame, text='Bin:').grid(row=2, column=0, sticky='w')
            bin_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=bin_var).grid(row=2, column=1, sticky='ew')

            ttk.Label(main_frame, text='Warning Threshold:').grid(row=3, column=0, sticky='w')
            threshold_var = tk.StringVar(value='5')
            ttk.Spinbox(main_frame, from_=1, to=100, textvariable=threshold_var).grid(
                row=3, column=1, sticky='ew')

            ttk.Label(main_frame, text='Notes:').grid(row=4, column=0, sticky='w')
            notes_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=notes_var).grid(row=4, column=1, sticky='ew')

            def save() -> None:
                """Save new storage item."""
                try:
                    recipe_text = recipe_var.get()
                    if not recipe_text:
                        messagebox.showerror('Error', 'Please select a pattern')
                        return

                    recipe_id = recipe_text.split('(')[1].strip(')')

                    try:
                        amount = int(amount_var.get())
                        threshold = int(threshold_var.get())
                        if amount < 0 or threshold < 0:
                            raise ValueError('Values must be non-negative')
                    except ValueError as e:
                        messagebox.showerror('Error', str(e))
                        return

                    with self.db.session_scope() as session:
                        pattern = session.query(Project).filter(
                            Project.unique_id == recipe_id).first()
                        if not pattern:
                            messagebox.showerror('Error', 'Project not found')
                            return

                        product = Product(
                            unique_id=f'P{str(uuid.uuid4())[:8]}',
                            name=pattern.name,
                            recipe_id=pattern.id
                        )
                        session.add(product)
                        session.flush()

                        storage = Storage(
                            product_id=product.id,
                            amount=amount,
                            warning_threshold=threshold,
                            bin=bin_var.get().strip(),
                            notes=notes_var.get().strip()
                        )
                        session.add(storage)
                        session.commit()

                        self.undo_stack.append(('add', storage.id))
                        self.redo_stack.clear()

                    self.load_data()
                    dialog.destroy()

                except SQLAlchemyError as e:
                    logger.exception(f'Failed to add item: {e}')
                    messagebox.showerror('Error', f'Failed to add item: {str(e)}')

            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=5, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text='Save', command=save).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=dialog.destroy).pack(
                side=tk.LEFT, padx=5)

            main_frame.columnconfigure(1, weight=1)

        except Exception as e:
            logger.exception(f'Failed to show add dialog: {e}')
            messagebox.showerror('Error', f'Failed to show add dialog: {str(e)}')

    @inject(MaterialService)
    def show_search_dialog(self) -> None:
        """Show search dialog for storage items."""
        try:
            dialog = tk.Toplevel(self)
            dialog.title('Search Storage')
            dialog.transient(self)
            dialog.grab_set()

            main_frame = ttk.Frame(dialog, padding='10')
            main_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(main_frame, text='Search in:').pack(anchor='w')
            target_var = tk.StringVar(value='all')

            ttk.Radiobutton(main_frame, text='All Fields', value='all',
                            variable=target_var).pack(anchor='w')
            for col in ['name', 'type', 'bin']:
                ttk.Radiobutton(main_frame, text=col.title(), value=col,
                                variable=target_var).pack(anchor='w')

            ttk.Label(main_frame, text='Search for:').pack(anchor='w', pady=(10, 0))
            search_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=search_var).pack(fill='x', pady=5)

            match_case_var = tk.BooleanVar()
            ttk.Checkbutton(main_frame, text='Match case', variable=match_case_var).pack(anchor='w')

            def search() -> None:
                """Perform search on storage items."""
                try:
                    search_text = search_var.get().strip()
                    if not search_text:
                        messagebox.showwarning('Warning', 'Please enter search text')
                        return

                    with self.db.session_scope() as session:
                        query = session.query(Storage).join(Storage.product).join(Product.pattern)

                        if target_var.get() == 'all':
                            conditions = [
                                Product.name.ilike(f'%{search_text}%'),
                                Project.type.ilike(f'%{search_text}%'),
                                Storage.bin.ilike(f'%{search_text}%')
                            ]
                            query = query.filter(or_(*conditions))
                        elif target_var.get() == 'name':
                            query = query.filter(Product.name.ilike(f'%{search_text}%'))
                        elif target_var.get() == 'type':
                            query = query.filter(Project.type.ilike(f'%{search_text}%'))
                        elif target_var.get() == 'bin':
                            query = query.filter(Storage.bin.ilike(f'%{search_text}%'))

                        if match_case_var.get():
                            query = query.filter(or_(
                                Product.name.like(f'%{search_text}%'),
                                Project.type.like(f'%{search_text}%'),
                                Storage.bin.like(f'%{search_text}%')
                            ))

                        results = query.all()

                        self.tree.delete(*self.tree.get_children())

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
                        messagebox.showinfo('Search', 'No matches found')

                except SQLAlchemyError as e:
                    logger.exception(f'Search failed: {e}')
                    messagebox.showerror('Error', f'Search failed: {str(e)}')

            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=10)

            ttk.Button(button_frame, text='Search', command=search).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=dialog.destroy).pack(
                side=tk.LEFT, padx=5)

        except Exception as e:
            logger.exception(f'Failed to show search dialog: {e}')
            messagebox.showerror('Error', f'Failed to show search dialog: {str(e)}')

    @inject(MaterialService)
    def show_filter_dialog(self) -> None:
        """Show filter dialog for storage items."""
        try:
            dialog = tk.Toplevel(self)
            dialog.title('Filter Storage')
            dialog.transient(self)
            dialog.grab_set()

            main_frame = ttk.Frame(dialog, padding='10')
            main_frame.pack(fill=tk.BOTH, expand=True)

            filter_frame = ttk.LabelFrame(main_frame, text='Filter Conditions')
            filter_frame.pack(fill='both', expand=True, padx=5, pady=5)

            ttk.Label(filter_frame, text='Type:').grid(row=0, column=0, sticky='w', padx=5)
            with self.db.session_scope() as session:
                types = session.query(Project.type).distinct().order_by(Project.type).all()
                type_list = ['All'] + [t[0] for t in types if t[0]]

            type_var = tk.StringVar(value='All')
            ttk.Combobox(filter_frame, textvariable=type_var, values=type_list).grid(
                row=0, column=1, sticky='ew', padx=5)

            ttk.Label(filter_frame, text='Amount:').grid(row=1, column=0, sticky='w', padx=5)
            amount_frame = ttk.Frame(filter_frame)
            amount_frame.grid(row=1, column=1, sticky='ew', padx=5)

            amount_op_var = tk.StringVar(value='>=')
            ttk.Combobox(amount_frame, textvariable=amount_op_var,
                         values=['>=', '<=', '='], width=5).pack(side=tk.LEFT, padx=2)
            amount_var = tk.StringVar()
            ttk.Entry(amount_frame, textvariable=amount_var, width=10).pack(
                side=tk.LEFT, padx=2)

            low_stock_var = tk.BooleanVar()
            ttk.Checkbutton(filter_frame, text='Show only low stock items',
                            variable=low_stock_var).grid(row=2, column=0, columnspan=2,
                                                         sticky='w', padx=5, pady=5)

            def apply_filters() -> None:
                """Apply the selected filters to storage items."""
                try:
                    with self.db.session_scope() as session:
                        query = session.query(Storage).join(Storage.product).join(Product.pattern)

                        if type_var.get() != 'All':
                            query = query.filter(Project.type == type_var.get())

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
                                messagebox.showerror('Error', 'Invalid amount value')
                                return

                        if low_stock_var.get():
                            query = query.filter(Storage.amount <= Storage.warning_threshold)

                        results = query.order_by(Storage.bin).all()

                        self.tree.delete(*self.tree.get_children())

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
                        messagebox.showinfo('Filter', 'No items match the selected criteria')

                except SQLAlchemyError as e:
                    logger.exception(f'Filter failed: {e}')
                    messagebox.showerror('Error', f'Filter failed: {str(e)}')

            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=10)

            ttk.Button(button_frame, text='Apply', command=apply_filters).pack(
                side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=dialog.destroy).pack(
                side=tk.LEFT, padx=5)

            filter_frame.columnconfigure(1, weight=1)

        except Exception as e:
            logger.exception(f'Failed to show filter dialog: {e}')
            messagebox.showerror('Error', f'Failed to show filter dialog: {str(e)}')

        @inject(MaterialService)
        def delete_selected(self, event: Optional[tk.Event] = None) -> None:
            """
            Delete selected storage items.

            Args:
                event (Optional[tk.Event]): Optional event triggering the deletion.
            """
            selected = self.tree.selection()
            if not selected:
                return

            if not messagebox.askyesno('Confirm Delete',
                                       f'Delete {len(selected)} items?'):
                return

            try:
                with self.db.session_scope() as session:
                    deleted_items = []
                    for item_id in selected:
                        values = self.tree.item(item_id)['values']
                        unique_id = values[0]
                        storage = session.query(Storage).join(Storage.product).filter(
                            Product.unique_id == unique_id).first()

                        if storage:
                            data = {
                                'product_data': {column.name: getattr(storage.product, column.name)
                                                 for column in Product.__table__.columns},
                                'storage_data': {column.name: getattr(storage, column.name)
                                                 for column in Storage.__table__.columns}
                            }
                            deleted_items.append(data)
                            session.delete(storage.product)

                    session.commit()

                    if deleted_items:
                        self.undo_stack.append(('delete', deleted_items))
                        self.redo_stack.clear()

                    self.load_data()

            except SQLAlchemyError as e:
                logger.exception(f'Failed to delete items: {e}')
                messagebox.showerror('Error', f'Failed to delete items: {str(e)}')

        @inject(MaterialService)
        def on_double_click(self, event: tk.Event) -> None:
            """
            Handle double-click event for cell editing.

            Args:
                event (tk.Event): Double-click event.
            """
            region = self.tree.identify('region', event.x, event.y)
            if region == 'cell':
                column = self.tree.identify_column(event.x)
                item = self.tree.identify_row(event.y)
                col_num = int(column[1]) - 1
                col_name = self.columns[col_num]
                if col_name in ['amount', 'bin', 'notes']:
                    self.start_cell_edit(item, column)

        @inject(MaterialService)
        def start_cell_edit(self, item: str, column: str) -> None:
            """
            Start editing a cell.

            Args:
                item (str): Item identifier.
                column (str): Column identifier.
            """
            col_num = int(column[1]) - 1
            col_name = self.columns[col_num]
            current_value = self.tree.set(item, col_name)

            frame = ttk.Frame(self.tree)

            if col_name == 'amount':
                widget = ttk.Spinbox(frame, from_=0, to=1000)
                widget.set(current_value)
            else:
                widget = ttk.Entry(frame)
                widget.insert(0, current_value)
                widget.select_range(0, tk.END)

            widget.pack(fill=tk.BOTH, expand=True)

            bbox = self.tree.bbox(item, column)
            frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

            def save_edit(event: Optional[tk.Event] = None) -> None:
                """Save edited cell value."""
                try:
                    new_value = widget.get().strip()
                    if new_value == current_value:
                        frame.destroy()
                        return

                    if col_name == 'amount':
                        try:
                            new_value = int(new_value)
                            if new_value < 0:
                                raise ValueError('Amount must be non-negative')
                        except ValueError as e:
                            messagebox.showerror('Error', str(e))
                            return

                    with self.db.session_scope() as session:
                        unique_id = self.tree.set(item, 'unique_id')
                        storage = session.query(Storage).join(Storage.product).filter(
                            Product.unique_id == unique_id).first()

                        if storage:
                            old_value = getattr(storage, col_name)
                            self.undo_stack.append(('edit', storage.id, col_name, old_value))
                            self.redo_stack.clear()

                            setattr(storage, col_name, new_value)
                            session.commit()

                            self.tree.set(item, col_name, str(new_value))

                            if col_name == 'amount':
                                if new_value <= storage.warning_threshold:
                                    self.tree.item(item, tags=('low_stock',))
                                else:
                                    self.tree.item(item, tags=())

                except SQLAlchemyError as e:
                    logger.exception(f'Failed to save edit: {e}')
                    messagebox.showerror('Error', f'Failed to save edit: {str(e)}')
                finally:
                    frame.destroy()

            def cancel_edit(event: Optional[tk.Event] = None) -> None:
                """Cancel cell editing."""
                frame.destroy()

            widget.bind('<Return>', save_edit)
            widget.bind('<Escape>', cancel_edit)
            widget.bind('<FocusOut>', save_edit)
            widget.focus_set()

        @inject(MaterialService)
        def undo(self, event: Optional[tk.Event] = None) -> None:
            """
            Undo the last action.

            Args:
                event (Optional[tk.Event]): Optional event triggering undo.
            """
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
                            data = {
                                'product_data': {column.name: getattr(storage.product, column.name)
                                                 for column in Product.__table__.columns},
                                'storage_data': {column.name: getattr(storage, column.name)
                                                 for column in Storage.__table__.columns}
                            }
                            session.delete(storage.product)
                            self.redo_stack.append(('readd', data))

                    elif action_type == 'edit':
                        storage_id, col_name, old_value = action[1:]
                        storage = session.query(Storage).get(storage_id)
                        if storage:
                            current_value = getattr(storage, col_name)
                            self.redo_stack.append(('reedit', storage_id, col_name, current_value))
                            setattr(storage, col_name, old_value)

                    elif action_type == 'delete':
                        deleted_items = action[1]
                        restored_items = []
                        for data in deleted_items:
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
                logger.exception(f'Undo failed: {e}')
                messagebox.showerror('Error', f'Undo failed: {str(e)}')

        @inject(MaterialService)
        def redo(self, event: Optional[tk.Event] = None) -> None:
            """
            Redo the last undone action.

            Args:
                event (Optional[tk.Event]): Optional event triggering redo.
            """
            if not self.redo_stack:
                return

            action = self.redo_stack.pop()
            action_type = action[0]

            try:
                with self.db.session_scope() as session:
                    if action_type == 'readd':
                        data = action[1]
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
                            old_value = getattr(storage, col_name)
                            self.undo_stack.append(('edit', storage_id, col_name, old_value))
                            setattr(storage, col_name, new_value)

                    elif action_type == 'redelete':
                        restored_items = action[1]
                        deleted_items = []
                        for product_id, storage_id in restored_items:
                            storage = session.query(Storage).get(storage_id)
                            if storage:
                                data = {
                                    'product_data': {column.name: getattr(storage.product, column.name)
                                                     for column in Product.__table__.columns},
                                    'storage_data': {column.name: getattr(storage, column.name)
                                                     for column in Storage.__table__.columns}
                                }
                                deleted_items.append(data)
                                session.delete(storage.product)

                        self.undo_stack.append(('delete', deleted_items))

                    session.commit()
                    self.load_data()

            except SQLAlchemyError as e:
                logger.exception(f'Redo failed: {e}')
                messagebox.showerror('Error', f'Redo failed: {str(e)}')

        @inject(MaterialService)
        def reset_view(self) -> None:
            """Reset the view to the default state."""
            self.load_data()