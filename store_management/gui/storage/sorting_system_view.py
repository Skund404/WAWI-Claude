

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class SortingSystemView(ttk.Frame):

    @inject(MaterialService)
        def __init__(self, parent, session_factory=SessionLocal):
    """
        Initialize the Sorting System View with SQLAlchemy integration

        Args:
            parent (tk.Widget): Parent widget
            session_factory (callable): SQLAlchemy session factory
        """
    super().__init__(parent)
    self.session_factory = session_factory
    self.undo_stack = []
    self.redo_stack = []
    self.setup_toolbar()
    self.setup_table()
    self.load_data()

    @inject(MaterialService)
        def setup_toolbar(self):
    """Create the toolbar with all buttons"""
    toolbar = ttk.Frame(self)
    toolbar.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(toolbar, text='ADD', command=self.show_add_dialog).pack(
        side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text='Search', command=self.show_search_dialog
               ).pack(side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text='Filter', command=self.show_filter_dialog
               ).pack(side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text='Batch Update', command=self.
               show_batch_update_dialog).pack(side=tk.LEFT, padx=2)
    ttk.Button(toolbar, text='Undo', command=self.undo).pack(side=tk.
                                                             RIGHT, padx=2)
    ttk.Button(toolbar, text='Redo', command=self.redo).pack(side=tk.
                                                             RIGHT, padx=2)
    ttk.Button(toolbar, text='Save', command=self.save_table).pack(
        side=tk.RIGHT, padx=2)
    ttk.Button(toolbar, text='Load', command=self.load_table).pack(
        side=tk.RIGHT, padx=2)
    ttk.Button(toolbar, text='Reset View', command=self.reset_view).pack(
        side=tk.RIGHT, padx=2)

    @inject(MaterialService)
        def setup_table(self):
    """Create the main table view"""
    self.tree_frame = ttk.Frame(self)
    self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)
    self.columns = ['id', 'unique_id', 'name', 'amount',
                    'warning_threshold', 'bin', 'notes']
    vsb = ttk.Scrollbar(self.tree_frame, orient='vertical')
    hsb = ttk.Scrollbar(self.tree_frame, orient='horizontal')
    self.tree = ttk.Treeview(self.tree_frame, columns=self.columns,
                             show='headings', selectmode='extended', yscrollcommand=vsb.set,
                             xscrollcommand=hsb.set)
    vsb.configure(command=self.tree.yview)
    hsb.configure(command=self.tree.xview)
    for col in self.columns:
        self.tree.heading(col, text=col.replace('_', ' ').title(),
                          command=lambda c=col: self.sort_column(c))
        self.tree.column(col, width=100, minwidth=50)
    self.tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    hsb.grid(row=1, column=0, sticky='ew')
    self.tree_frame.grid_columnconfigure(0, weight=1)
    self.tree_frame.grid_rowconfigure(0, weight=1)
    self.tree.tag_configure('critical_stock', background='#ff8080')
    self.tree.tag_configure('low_stock', background='#ffcccc')
    self.tree.tag_configure('warning_stock', background='#ffe6cc')
    self.tree.bind('<Double-1>', self.on_double_click)
    self.tree.bind('<Delete>', self.delete_selected)
    self.tree.bind('<Return>', self.handle_return)
    self.tree.bind('<Escape>', self.handle_escape)

    @inject(MaterialService)
        def load_data(self):
    """Load data from database into table"""
    session = self.session_factory()
    try:
        for item in self.tree.get_children():
            self.tree.delete(item)
        storages = session.execute(select(Storage).options(joinedload(
            Storage.product)).order_by(Storage.bin)).scalars().all()
        for storage in storages:
            row_values = [storage.id, storage.product.unique_id if
                          storage.product else '', storage.product.name if
                          storage.product else '', storage.amount, storage.
                          warning_threshold, storage.bin, storage.notes]
            item = self.tree.insert('', 'end', values=row_values)
            warning_tag = self.get_warning_tag(storage.amount, storage.
                                               warning_threshold)
            if warning_tag:
                self.tree.item(item, tags=(warning_tag,))
    except Exception as e:
        handle_error(f'Error loading sorting system data: {e}')
        messagebox.showerror('Database Error', str(e))
    finally:
        session.close()

    @inject(MaterialService)
        def get_warning_tag(self, amount: int, warning_threshold: int) -> str:
    """
        Determine the warning level tag based on stock level

        Args:
            amount (int): Current stock level
            warning_threshold (int): Warning threshold level

        Returns:
            str: Warning tag level or empty string if no warning
        """
    try:
        amount = int(amount)
        warning_threshold = int(warning_threshold)
        if amount <= warning_threshold * 0.5:
            return 'critical_stock'
        elif amount <= warning_threshold * 0.75:
            return 'low_stock'
        elif amount <= warning_threshold:
            return 'warning_stock'
        return ''
    except (ValueError, TypeError):
        return ''

    @inject(MaterialService)
        def show_add_dialog(self):
    """Show dialog for adding a new storage item"""
    dialog = AddDialog(self, title='Add Storage Item', columns=[(
        'unique_id', 'Unique ID', False), ('name', 'Product Name', True
                                           ), ('amount', 'Amount', True), ('warning_threshold',
                                                                           'Warning Threshold', True), ('bin', 'Bin Location', True), (
        'notes', 'Notes', False)], on_submit=self.save_new_item)
    dialog.grab_set()

    @inject(MaterialService)
        def save_new_item(self, data: Dict):
    """
        Save a new storage item to the database

        Args:
            data (Dict): Dictionary of item data
        """
    session = self.session_factory()
    try:
        product = session.execute(select(Product).where(Product.name ==
                                                        data['name'])).scalar_one_or_none()
        if not product:
            product = Product(unique_id=data.get('unique_id') or self.
                              generate_unique_id(data['name']), name=data['name'])
            session.add(product)
        storage = Storage(product=product, amount=int(data['amount']),
                          warning_threshold=int(data['warning_threshold']), bin=data[
            'bin'], notes=data.get('notes'))
        session.add(storage)
        session.commit()
        log_action(f'Added storage item: {product.name}')
        self.load_data()
        messagebox.showinfo('Success',
                            f'Storage item for {product.name} added successfully')
    except Exception as e:
        session.rollback()
        handle_error(f'Error saving storage item: {e}')
        messagebox.showerror('Error', str(e))
    finally:
        session.close()

    @inject(MaterialService)
        def generate_unique_id(self, name: str) -> str:
    """
        Generate a unique product ID based on the name

        Args:
            name (str): Product name

        Returns:
            str: Generated unique ID
        """
    import uuid
    prefix = ''.join(word[0].upper() for word in name.split()[:2])
    unique_id = f'{prefix}-{str(uuid.uuid4())[:8].upper()}'
    return unique_id

    @inject(MaterialService)
        def on_double_click(self, event):
    """
        Handle double-click event for cell editing

        Args:
            event (tk.Event): Tkinter event object
        """
    region = self.tree.identify('region', event.x, event.y)
    if region == 'cell':
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        col_index = int(column[1:]) - 1
        if self.columns[col_index] == 'id':
            return
        self.start_cell_edit(item, column)

    @inject(MaterialService)
        def start_cell_edit(self, item, column):
    """
        Start inline cell editing

        Args:
            item (str): Treeview item identifier
            column (str): Column identifier
        """
    pass

    @inject(MaterialService)
        def delete_selected(self, event=None):
    """Delete selected storage items"""
    selected = self.tree.selection()
    if not selected:
        return
    if not messagebox.askyesno('Confirm Delete',
                               'Are you sure you want to delete the selected items?'):
        return
    session = self.session_factory()
    try:
        deleted_items = []
        for item in selected:
            storage_id = self.tree.set(item, 'id')
            storage = session.get(Storage, int(storage_id))
            if storage:
                deleted_items.append({'id': storage.id, 'product_id':
                                      storage.product_id, 'amount': storage.amount,
                                      'warning_threshold': storage.warning_threshold,
                                      'bin': storage.bin, 'notes': storage.notes})
                session.delete(storage)
        session.commit()
        for item in selected:
            self.tree.delete(item)
        self.undo_stack.append(('delete', deleted_items))
        self.redo_stack.clear()
        log_action(f'Deleted {len(selected)} storage items')
        messagebox.showinfo('Success', f'Deleted {len(selected)} items')
    except Exception as e:
        session.rollback()
        handle_error(f'Error deleting storage items: {e}')
        messagebox.showerror('Error', str(e))
    finally:
        session.close()

    @inject(MaterialService)
        def undo(self):
    """Undo the last action"""
    if not self.undo_stack:
        return
    action_type, data = self.undo_stack.pop()
    session = self.session_factory()
    try:
        if action_type == 'delete':
            restored_items = []
            for item_data in data:
                storage = Storage(id=item_data['id'], product_id=item_data['product_id'], amount=item_data['amount'],
                                  warning_threshold=item_data['warning_threshold'],
                                  bin=item_data['bin'], notes=item_data['notes'])
                session.add(storage)
                restored_items.append(storage)
            session.commit()
            self.load_data()
            self.redo_stack.append(('undelete', restored_items))
    except Exception as e:
        session.rollback()
        handle_error(f'Undo error: {e}')
        messagebox.showerror('Undo Error', str(e))
    finally:
        session.close()

    @inject(MaterialService)
        def redo(self):
    """Redo the last undone action"""
    if not self.redo_stack:
        return
    action_type, data = self.redo_stack.pop()
    session = self.session_factory()
    try:
        if action_type == 'undelete':
            for storage in data:
                session.delete(storage)
            session.commit()
            self.load_data()
            self.undo_stack.append(('delete', [{'id': item.id,
                                                'product_id': item.product_id, 'amount': item.amount,
                                                'warning_threshold': item.warning_threshold, 'bin':
                                                item.bin, 'notes': item.notes} for item in data]))
    except Exception as e:
        session.rollback()
        handle_error(f'Redo error: {e}')
        messagebox.showerror('Redo Error', str(e))
    finally:
        session.close()
