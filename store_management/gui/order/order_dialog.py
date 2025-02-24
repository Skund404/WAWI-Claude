

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class AddOrderDialog(BaseDialog):
    """
    Flexible dialog for creating and editing orders.

    Supports:
    - Dynamic field generation
    - Supplier selection
    - Validation
    - Editing existing orders
    """

    @inject(MaterialService)
        def __init__(self, parent: tk.Tk, save_callback: Callable[[Dict[str,
                                                                    Any]], None], fields: Optional[List[tuple]] = None, suppliers:
                 Optional[List[Dict[str, Any]]] = None, existing_data: Optional[Dict[
                     str, Any]] = None, title: str = 'Add Order'):
        """
        Initialize the order dialog.

        Args:
            parent: Parent window
            save_callback: Function to call when saving order
            fields: Optional list of field configurations
            suppliers: List of available suppliers
            existing_data: Existing order data for editing
            title: Dialog title
        """
        if fields is None:
            fields = [('supplier_id', 'Supplier', True, 'supplier'), (
                'order_date', 'Order Date', True, 'date'), ('status',
                                                            'Status', True, 'status'), ('total_amount', 'Total Amount',
                                                                                        True, 'float'), ('notes', 'Notes', False, 'text')]
        self._save_callback = save_callback
        self._suppliers = suppliers or []
        self._existing_data = existing_data or {}
        self._order_items: List[Dict[str, Any]] = []
        super().__init__(parent, title, size=(600, 600))
        self._fields = fields
        self._entries: Dict[str, Any] = {}

        @inject(MaterialService)
            def _create_main_frame(self) -> None:
        """
        Create dialog main frame with dynamic fields and order items section.
        """
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text='Order Details')
        items_frame = ttk.Frame(notebook)
        notebook.add(items_frame, text='Order Items')
        self._create_order_details_fields(details_frame)
        self._create_order_items_section(items_frame)

        @inject(MaterialService)
            def _create_order_details_fields(self, parent: ttk.Frame) -> None:
        """
        Create dynamic fields for order details.

        Args:
            parent: Parent frame to add fields to
        """
        parent.columnconfigure(1, weight=1)
        for i, (field_name, display_name, required, field_type) in enumerate(
                self._fields):
            label = ttk.Label(parent, text=f'{display_name}:')
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            if field_type == 'supplier':
                supplier_var = tk.StringVar()
                supplier_dropdown = ttk.Combobox(parent, textvariable=supplier_var, values=[s.get('name', '') for s in self.
                                                                                            _suppliers], state='readonly' if self._suppliers else
                                                 'normal')
                supplier_dropdown.grid(
                    row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = supplier_var
                if field_name in self._existing_data:
                    supplier_var.set(self._existing_data[field_name])
            elif field_type == 'date':
                date_var = tk.StringVar()
                date_entry = ttk.Entry(parent, textvariable=date_var)
                date_entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = date_var
                default_date = self._existing_data.get(field_name, datetime
                                                       .now().strftime('%Y-%m-%d'))
                date_var.set(default_date)
            elif field_type == 'status':
                status_options = ['Pending', 'Processing', 'Completed',
                                  'Cancelled']
                status_var = tk.StringVar()
                status_dropdown = ttk.Combobox(
                    parent, textvariable=status_var, values=status_options, state='readonly')
                status_dropdown.grid(row=i, column=1, sticky=tk.EW, padx=5,
                                     pady=5)
                self._entries[field_name] = status_var
                if field_name in self._existing_data:
                    status_var.set(self._existing_data[field_name])
            elif field_type == 'float':
                float_var = tk.StringVar()
                float_entry = ttk.Entry(parent, textvariable=float_var)
                float_entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = float_var
                if field_name in self._existing_data:
                    float_var.set(str(self._existing_data[field_name]))
            elif field_type == 'text':
                text_widget = tk.Text(parent, height=4, width=40)
                text_widget.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = text_widget
                if field_name in self._existing_data:
                    text_widget.insert(tk.END, str(self._existing_data[
                        field_name]))

        @inject(MaterialService)
            def _create_order_items_section(self, parent: ttk.Frame) -> None:
        """
        Create section for managing order items.

        Args:
            parent: Parent frame to add items section to
        """
        items_frame = ttk.Frame(parent)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = 'Product', 'Quantity', 'Unit Price', 'Total'
        self.items_tree = ttk.Treeview(
            items_frame, columns=columns, show='headings')
        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=100, anchor='center')
        scrollbar = ttk.Scrollbar(
            items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscroll=scrollbar.set)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        buttons_frame = ttk.Frame(items_frame)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        add_item_btn = ttk.Button(
            buttons_frame, text='Add Item', command=self._show_add_item_dialog)
        add_item_btn.pack(side=tk.LEFT, padx=5)
        remove_item_btn = ttk.Button(buttons_frame, text='Remove Item',
                                     command=self._remove_selected_item)
        remove_item_btn.pack(side=tk.LEFT, padx=5)

        @inject(MaterialService)
            def _show_add_item_dialog(self) -> None:
        """
        Show dialog to add a new order item.
        """
        dialog = tk.Toplevel(self)
        dialog.title('Add Order Item')
        dialog.geometry('400x300')
        ttk.Label(dialog, text='Product:').pack()
        product_var = tk.StringVar()
        product_dropdown = ttk.Combobox(dialog, textvariable=product_var)
        product_dropdown.pack()
        ttk.Label(dialog, text='Quantity:').pack()
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(dialog, textvariable=quantity_var)
        quantity_entry.pack()
        ttk.Label(dialog, text='Unit Price:').pack()
        price_var = tk.StringVar()
        price_entry = ttk.Entry(dialog, textvariable=price_var)
        price_entry.pack()

        def save_item():
            try:
                item = {'product': product_var.get(), 'quantity': float(
                    quantity_var.get()), 'unit_price': float(price_var.get(
                    )), 'total': float(quantity_var.get()) * float(
                    price_var.get())}
                self.items_tree.insert('', 'end', values=(item['product'],
                                                          item['quantity'], item['unit_price'], item['total']))
                self._order_items.append(item)
                dialog.destroy()
            except ValueError:
                messagebox.showerror('Invalid Input',
                                     'Please enter valid numbers')
        save_btn = ttk.Button(dialog, text='Save', command=save_item)
        save_btn.pack(pady=10)

        @inject(MaterialService)
            def _remove_selected_item(self) -> None:
        """
        Remove selected order item.
        """
        selected_item = self.items_tree.selection()
        if not selected_item:
            messagebox.showwarning('Selection Required',
                                   'Please select an item to remove')
            return
        self.items_tree.delete(selected_item)
        del self._order_items[self.items_tree.index(selected_item)]

        @inject(MaterialService)
            def ok(self, event=None) -> None:
        """
        Save order data when OK is pressed.

        Args:
            event: Optional tkinter event
        """
        try:
            order_data = {}
            for field_name, entry in self._entries.items():
                if isinstance(entry, tk.StringVar):
                    value = entry.get()
                elif isinstance(entry, tk.Text):
                    value = entry.get('1.0', tk.END).strip()
                else:
                    value = entry
                order_data[field_name] = value
            order_data['items'] = self._order_items
            self._save_callback(order_data)
            self.destroy()
        except Exception as e:
            messagebox.showerror('Save Error', str(e))

        @inject(MaterialService)
            def validate(self) -> bool:
        """
        Validate order data before saving.

        Returns:
            True if validation passes, False otherwise
        """
        for field_name, display_name, required, _ in self._fields:
            if required:
                value = self._entries.get(field_name)
                if isinstance(value, tk.StringVar):
                    val = value.get()
                elif isinstance(value, tk.Text):
                    val = value.get('1.0', tk.END).strip()
                else:
                    val = value
                if not val:
                    messagebox.showerror('Validation Error',
                                         f'{display_name} is required')
                    return False
        try:
            total_amount = float(self._entries['total_amount'].get())
            if total_amount < 0:
                messagebox.showerror('Validation Error',
                                     'Total amount must be non-negative')
                return False
        except ValueError:
            messagebox.showerror('Validation Error', 'Invalid total amount')
            return False
        return True
