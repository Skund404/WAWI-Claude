# File: store_management/gui/order/order_dialog.py
# Description: Dialog for Adding and Editing Orders

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from store_management.gui.dialogs.base_dialog import BaseDialog


class AddOrderDialog(BaseDialog):
    """
    Flexible dialog for creating and editing orders.

    Supports:
    - Dynamic field generation
    - Supplier selection
    - Validation
    - Editing existing orders
    """

    def __init__(
            self,
            parent: tk.Tk,
            save_callback: Callable[[Dict[str, Any]], None],
            fields: Optional[List[tuple]] = None,
            suppliers: Optional[List[Dict[str, Any]]] = None,
            existing_data: Optional[Dict[str, Any]] = None,
            title: str = "Add Order"
    ):
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
        # Default fields if not provided
        if fields is None:
            fields = [
                ('supplier_id', 'Supplier', True, 'supplier'),
                ('order_date', 'Order Date', True, 'date'),
                ('status', 'Status', True, 'status'),
                ('total_amount', 'Total Amount', True, 'float'),
                ('notes', 'Notes', False, 'text')
            ]

        # Store parameters
        self._save_callback = save_callback
        self._suppliers = suppliers or []
        self._existing_data = existing_data or {}

        # Order items management
        self._order_items: List[Dict[str, Any]] = []

        # Initialize dialog
        super().__init__(parent, title, size=(600, 600))

        # Store field configurations
        self._fields = fields

        # Entries dictionary
        self._entries: Dict[str, Any] = {}

    def _create_main_frame(self) -> None:
        """
        Create dialog main frame with dynamic fields and order items section.
        """
        # Main notebook for different sections
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Order Details Frame
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="Order Details")

        # Order Items Frame
        items_frame = ttk.Frame(notebook)
        notebook.add(items_frame, text="Order Items")

        # Create order details fields
        self._create_order_details_fields(details_frame)

        # Create order items section
        self._create_order_items_section(items_frame)

    def _create_order_details_fields(self, parent: ttk.Frame) -> None:
        """
        Create dynamic fields for order details.

        Args:
            parent: Parent frame to add fields to
        """
        # Configure grid
        parent.columnconfigure(1, weight=1)

        # Create fields dynamically
        for i, (field_name, display_name, required, field_type) in enumerate(self._fields):
            # Label
            label = ttk.Label(parent, text=f"{display_name}:")
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)

            # Create appropriate entry widget
            if field_type == 'supplier':
                # Supplier dropdown
                supplier_var = tk.StringVar()
                supplier_dropdown = ttk.Combobox(
                    parent,
                    textvariable=supplier_var,
                    values=[s.get('name', '') for s in self._suppliers],
                    state="readonly" if self._suppliers else "normal"
                )
                supplier_dropdown.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = supplier_var

                # Set existing value if editing
                if field_name in self._existing_data:
                    supplier_var.set(self._existing_data[field_name])

            elif field_type == 'date':
                # Date entry with default to today
                date_var = tk.StringVar()
                date_entry = ttk.Entry(parent, textvariable=date_var)
                date_entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = date_var

                # Set default or existing value
                default_date = (
                    self._existing_data.get(field_name,
                                            datetime.now().strftime('%Y-%m-%d'))
                )
                date_var.set(default_date)

            elif field_type == 'status':
                # Status dropdown
                status_options = ['Pending', 'Processing', 'Completed', 'Cancelled']
                status_var = tk.StringVar()
                status_dropdown = ttk.Combobox(
                    parent,
                    textvariable=status_var,
                    values=status_options,
                    state="readonly"
                )
                status_dropdown.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = status_var

                # Set existing value if editing
                if field_name in self._existing_data:
                    status_var.set(self._existing_data[field_name])

            elif field_type == 'float':
                # Numeric entry
                float_var = tk.StringVar()
                float_entry = ttk.Entry(parent, textvariable=float_var)
                float_entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = float_var

                # Set existing value if editing
                if field_name in self._existing_data:
                    float_var.set(str(self._existing_data[field_name]))

            elif field_type == 'text':
                # Multiline text entry
                text_widget = tk.Text(parent, height=4, width=40)
                text_widget.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = text_widget

                # Set existing value if editing
                if field_name in self._existing_data:
                    text_widget.insert(tk.END, str(self._existing_data[field_name]))

    def _create_order_items_section(self, parent: ttk.Frame) -> None:
        """
        Create section for managing order items.

        Args:
            parent: Parent frame to add items section to
        """
        # Frame for items list
        items_frame = ttk.Frame(parent)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview for order items
        columns = ('Product', 'Quantity', 'Unit Price', 'Total')
        self.items_tree = ttk.Treeview(
            items_frame,
            columns=columns,
            show='headings'
        )

        # Configure columns
        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=100, anchor='center')

        # Pack treeview with scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscroll=scrollbar.set)

        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons frame
        buttons_frame = ttk.Frame(items_frame)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Add Item button
        add_item_btn = ttk.Button(buttons_frame, text="Add Item", command=self._show_add_item_dialog)
        add_item_btn.pack(side=tk.LEFT, padx=5)

        # Remove Item button
        remove_item_btn = ttk.Button(buttons_frame, text="Remove Item", command=self._remove_selected_item)
        remove_item_btn.pack(side=tk.LEFT, padx=5)

    def _show_add_item_dialog(self) -> None:
        """
        Show dialog to add a new order item.
        """
        # TODO: Implement add item dialog
        dialog = tk.Toplevel(self)
        dialog.title("Add Order Item")
        dialog.geometry("400x300")

        # Product selection
        ttk.Label(dialog, text="Product:").pack()
        product_var = tk.StringVar()
        product_dropdown = ttk.Combobox(dialog, textvariable=product_var)
        product_dropdown.pack()

        # Quantity
        ttk.Label(dialog, text="Quantity:").pack()
        quantity_var = tk.StringVar()
        quantity_entry = ttk.Entry(dialog, textvariable=quantity_var)
        quantity_entry.pack()

        # Unit Price
        ttk.Label(dialog, text="Unit Price:").pack()
        price_var = tk.StringVar()
        price_entry = ttk.Entry(dialog, textvariable=price_var)
        price_entry.pack()

        # Save button
        def save_item():
            try:
                item = {
                    'product': product_var.get(),
                    'quantity': float(quantity_var.get()),
                    'unit_price': float(price_var.get()),
                    'total': float(quantity_var.get()) * float(price_var.get())
                }

                # Add to treeview and items list
                self.items_tree.insert('', 'end', values=(
                    item['product'],
                    item['quantity'],
                    item['unit_price'],
                    item['total']
                ))

                self._order_items.append(item)
                dialog.destroy()

            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers")

        save_btn = ttk.Button(dialog, text="Save", command=save_item)
        save_btn.pack(pady=10)

    def _remove_selected_item(self) -> None:
        """
        Remove selected order item.
        """
        selected_item = self.items_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select an item to remove")
            return

        # Remove from treeview
        self.items_tree.delete(selected_item)

        # Remove from internal list
        del self._order_items[self.items_tree.index(selected_item)]

    def ok(self, event=None) -> None:
        """
        Save order data when OK is pressed.

        Args:
            event: Optional tkinter event
        """
        try:
            # Collect order data
            order_data = {}
            for field_name, entry in self._entries.items():
                # Get value based on entry type
                if isinstance(entry, tk.StringVar):
                    value = entry.get()
                elif isinstance(entry, tk.Text):
                    value = entry.get("1.0", tk.END).strip()
                else:
                    value = entry

                order_data[field_name] = value

            # Add order items
            order_data['items'] = self._order_items

            # Call save callback
            self._save_callback(order_data)

            # Close dialog
            self.destroy()

        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def validate(self) -> bool:
        """
        Validate order data before saving.

        Returns:
            True if validation passes, False otherwise
        """
        # Validate required fields
        for field_name, display_name, required, _ in self._fields:
            if required:
                value = self._entries.get(field_name)

                # Get value based on entry type
                if isinstance(value, tk.StringVar):
                    val = value.get()
                elif isinstance(value, tk.Text):
                    val = value.get("1.0", tk.END).strip()
                else:
                    val = value

                # Check if empty
                if not val:
                    messagebox.showerror("Validation Error", f"{display_name} is required")
                    return False

        # Additional validation for numeric fields
        try:
            # Validate total amount
            total_amount = float(self._entries['total_amount'].get())
            if total_amount < 0:
                messagebox.showerror("Validation Error", "Total amount must be non-negative")
                return False
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid total amount")
            return False

        return True