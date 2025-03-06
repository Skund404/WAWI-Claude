# sale_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import logging

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, SaleService  # Changed OrderService to SaleService

logger = logging.getLogger(__name__)


class BaseDialog(tk.Toplevel):
    """Base dialog for application dialogs."""

    def __init__(self, parent, title, size=(400, 300)):
        """
        Initialize the base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            size: Dialog size as (width, height) tuple
        """
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{size[0]}x{size[1]}")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Create main content frame
        self._create_main_frame()

        # Create button area at the bottom
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)

        # Bind events
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

    def _create_main_frame(self) -> None:
        """Create main content frame. Override in subclasses."""
        pass

    def ok(self, event=None) -> None:
        """Handle OK button or Return key."""
        if self.validate():
            self.destroy()

    def cancel(self, event=None) -> None:
        """Handle Cancel button or Escape key."""
        self.destroy()

    def validate(self) -> bool:
        """Validate dialog data before closing. Override in subclasses."""
        return True


class AddSaleDialog(BaseDialog):
    """
    Flexible dialog for creating and editing sales.

    Supports:
    - Dynamic field generation
    - Supplier selection (If needed - review code and adjust)
    - Validation
    - Editing existing sales
    """

    @inject(MaterialService)
    def __init__(self, parent: tk.Tk, save_callback: Callable[[Dict[str, Any]], None],
                 fields: Optional[List[tuple]] = None, suppliers: Optional[List[Dict[str, Any]]] = None,  # Consider if suppliers are still needed
                 existing_data: Optional[Dict[str, Any]] = None, title: str = 'Add Sale'):
        """
        Initialize the sale dialog.

        Args:
            parent: Parent window
            save_callback: Function to call when saving sale
            fields: Optional list of field configurations
            suppliers: List of available suppliers (Review if needed)
            existing_data: Existing sale data for editing
            title: Dialog title
        """
        if fields is None:
            fields = [
                # ('supplier_id', 'Supplier', True, 'supplier'),  # Removed supplier, adapt if needed
                ('sale_date', 'Sale Date', True, 'date'),
                ('status', 'Status', True, 'status'),
                ('total_amount', 'Total Amount', True, 'float'),
                ('notes', 'Notes', False, 'text'),
                ('customer_name', 'Customer Name', True, 'text')  #Example new field
            ]

        self._save_callback = save_callback
        self._suppliers = suppliers or []  # Review if needed
        self._existing_data = existing_data or {}
        self._sale_items: List[Dict[str, Any]] = []  # Changed _order_items to _sale_items
        self._fields = fields
        self._entries: Dict[str, Any] = {}

        super().__init__(parent, title, size=(600, 600))

    @inject(MaterialService)
    def _create_main_frame(self) -> None:
        """
        Create dialog main frame with dynamic fields and sale items section.
        """
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text='Sale Details')

        items_frame = ttk.Frame(notebook)
        notebook.add(items_frame, text='Sale Items')

        self._create_sale_details_fields(details_frame) # Changed _create_order_details_fields to _create_sale_details_fields
        self._create_sale_items_section(items_frame) # Changed _create_order_items_section to _create_sale_items_section

    @inject(MaterialService)
    def _create_sale_details_fields(self, parent: ttk.Frame) -> None: # Changed _create_order_details_fields to _create_sale_details_fields
        """
        Create dynamic fields for sale details.

        Args:
            parent: Parent frame to add fields to
        """
        parent.columnconfigure(1, weight=1)

        for i, (field_name, display_name, required, field_type) in enumerate(self._fields):
            label = ttk.Label(parent, text=f'{display_name}:')
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)

            if field_type == 'supplier': # Review if needed
                supplier_var = tk.StringVar()
                supplier_dropdown = ttk.Combobox(
                    parent,
                    textvariable=supplier_var,
                    values=[s.get('name', '') for s in self._suppliers],
                    state='readonly' if self._suppliers else 'normal'
                )
                supplier_dropdown.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = supplier_var

                if field_name in self._existing_data:
                    supplier_var.set(self._existing_data[field_name])

            elif field_type == 'date':
                date_var = tk.StringVar()
                date_entry = ttk.Entry(parent, textvariable=date_var)
                date_entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = date_var

                default_date = self._existing_data.get(field_name, datetime.now().strftime('%Y-%m-%d'))
                date_var.set(default_date)

            elif field_type == 'status':
                status_options = ['Pending', 'Processing', 'Completed', 'Cancelled']
                status_var = tk.StringVar()
                status_dropdown = ttk.Combobox(
                    parent,
                    textvariable=status_var,
                    values=status_options,
                    state='readonly'
                )
                status_dropdown.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
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
                    text_widget.insert(tk.END, str(self._existing_data[field_name]))

    @inject(MaterialService)
    def _create_sale_items_section(self, parent: ttk.Frame) -> None:  # Changed _create_order_items_section to _create_sale_items_section
        """
        Create section for managing sale items.

        Args:
            parent: Parent frame to add items section to
        """
        items_frame = ttk.Frame(parent)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ('Product', 'Quantity', 'Unit Price', 'Total')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings')

        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=100, anchor='center')

        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscroll=scrollbar.set)

        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        buttons_frame = ttk.Frame(items_frame)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        add_item_btn = ttk.Button(buttons_frame, text='Add Item', command=self._show_add_item_dialog)
        add_item_btn.pack(side=tk.LEFT, padx=5)

        remove_item_btn = ttk.Button(buttons_frame, text='Remove Item', command=self._remove_selected_item)
        remove_item_btn.pack(side=tk.LEFT, padx=5)

    @inject(MaterialService)
    def _show_add_item_dialog(self) -> None:
        """
        Show dialog to add a new sale item.
        """
        dialog = tk.Toplevel(self)
        dialog.title('Add Sale Item')  # Changed title
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
                item = {
                    'product': product_var.get(),
                    'quantity': float(quantity_var.get()),
                    'unit_price': float(price_var.get()),
                    'total': float(quantity_var.get()) * float(price_var.get())
                }
                self.items_tree.insert('', 'end', values=(
                    item['product'],
                    item['quantity'],
                    item['unit_price'],
                    item['total']
                ))
                self._sale_items.append(item)  # Changed _order_items to _sale_items
                dialog.destroy()
            except ValueError:
                messagebox.showerror('Invalid Input', 'Please enter valid numbers')

        save_btn = ttk.Button(dialog, text='Save', command=save_item)
        save_btn.pack(pady=10)

    @inject(MaterialService)
    def _remove_selected_item(self) -> None:
        """
        Remove selected sale item.
        """
        selected_item = self.items_tree.selection()
        if not selected_item:
            messagebox.showwarning('Selection Required', 'Please select an item to remove')
            return

        # Find the index in the internal list based on tree selection
        selection_id = self.items_tree.index(selected_item[0])

        # Remove from UI and internal storage
        self.items_tree.delete(selected_item[0])
        if 0 <= selection_id < len(self._sale_items):  # Changed _order_items to _sale_items
            del self._sale_items[selection_id]

    @inject(MaterialService)
    def ok(self, event=None) -> None:
        """
        Save sale data when OK is pressed.

        Args:
            event: Optional tkinter event
        """
        try:
            if not self.validate():
                return

            sale_data = {}  # Changed order_data to sale_data
            for field_name, entry in self._entries.items():
                if isinstance(entry, tk.StringVar):
                    value = entry.get()
                elif isinstance(entry, tk.Text):
                    value = entry.get('1.0', tk.END).strip()
                else:
                    value = entry
                sale_data[field_name] = value

            sale_data['items'] = self._sale_items  # Changed _order_items to _sale_items
            self._save_callback(sale_data) # Changed order_data to sale_data
            self.destroy()
        except Exception as e:
            messagebox.showerror('Save Error', str(e))
            logger.error(f"Error saving sale data: {e}")

    @inject(MaterialService)
    def validate(self) -> bool:
        """
        Validate sale data before saving.

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
                    messagebox.showerror('Validation Error', f'{display_name} is required')
                    return False

        try:
            total_amount = float(self._entries['total_amount'].get())
            if total_amount < 0:
                messagebox.showerror('Validation Error', 'Total amount must be non-negative')
                return False
        except ValueError:
            messagebox.showerror('Validation Error', 'Invalid total amount')
            return False

        return True