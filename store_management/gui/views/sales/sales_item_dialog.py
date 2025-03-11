# gui/views/sales/sales_item_dialog.py
"""
Dialog for managing sales line items.

This dialog provides an interface for adding and editing sales line items,
allowing selection of products or creation of custom items.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Any, Dict, Optional

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from gui.utils.service_access import get_service


class SalesItemDialog(BaseDialog):
    """
    Dialog for adding and editing sales line items.

    This dialog allows users to select products from inventory or create
    custom items with pricing and quantity.
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize the sales item dialog.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                item: The item to edit (None for new items)
                create_new: Whether to create a new item
        """
        self.logger = logging.getLogger(__name__)

        # Extract parameters
        self.item = kwargs.pop('item', None)
        self.create_new = kwargs.pop('create_new', False) if not self.item else False

        # Set dialog title
        title = "Edit Line Item" if self.item else "Add Line Item"

        # Initialize base dialog
        super().__init__(
            parent,
            title=title,
            width=550,
            height=450,
            modal=True
        )

        # Initialize services
        self.product_service = get_service("product_service")
        self.inventory_service = get_service("inventory_service")

        # Initialize item data
        self._initialize_item_data()

        # Initialize result
        self.result = None

    def _initialize_item_data(self):
        """Initialize form variables for data binding."""
        # Initialize item type - product or custom
        self.is_product = tk.BooleanVar(value=True)

        # Product selection variables
        self.product_id = tk.StringVar()
        self.product_name = tk.StringVar()
        self.product_price = tk.StringVar(value="0.00")

        # Item details variables
        self.description = tk.StringVar()
        self.quantity = tk.StringVar(value="1")
        self.unit_price = tk.StringVar(value="0.00")
        self.total = tk.StringVar(value="0.00")

        # Stock availability
        self.stock_level = tk.StringVar()

        # If editing existing item, populate fields
        if self.item:
            # Check if it's a product or custom item
            self.is_product.set(hasattr(self.item, 'product_id') and self.item.product_id is not None)

            # Set product info if applicable
            if self.is_product.get():
                if hasattr(self.item, 'product_id'):
                    self.product_id.set(str(self.item.product_id))

                if hasattr(self.item, 'product_name'):
                    self.product_name.set(self.item.product_name)

            # Set item details
            if hasattr(self.item, 'description'):
                self.description.set(self.item.description)

            if hasattr(self.item, 'quantity'):
                self.quantity.set(str(self.item.quantity))

            if hasattr(self.item, 'price') and self.item.price is not None:
                self.unit_price.set(f"{self.item.price:.2f}")
                self.product_price.set(f"{self.item.price:.2f}")

            # Calculate total
            self._update_total()

    def create_layout(self):
        """Create the dialog layout."""
        # Create main container with padding
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create item type selection
        type_frame = ttk.Frame(container)
        type_frame.pack(fill=tk.X, pady=5)

        ttk.Label(type_frame, text="Item Type:", style="Bold.TLabel").pack(side=tk.LEFT)

        # Product radio button
        product_radio = ttk.Radiobutton(
            type_frame,
            text="Product",
            variable=self.is_product,
            value=True,
            command=self._update_item_type
        )
        product_radio.pack(side=tk.LEFT, padx=10)

        # Custom item radio button
        custom_radio = ttk.Radiobutton(
            type_frame,
            text="Custom Item",
            variable=self.is_product,
            value=False,
            command=self._update_item_type
        )
        custom_radio.pack(side=tk.LEFT, padx=10)

        # Create product selection section
        self.product_frame = ttk.LabelFrame(container, text="Product Selection")
        self.product_frame.pack(fill=tk.X, pady=10)

        # Product selection
        product_selection_frame = ttk.Frame(self.product_frame)
        product_selection_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(product_selection_frame, text="Product:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        # Product name entry (readonly)
        product_entry = ttk.Entry(
            product_selection_frame,
            textvariable=self.product_name,
            state="readonly",
            width=30
        )
        product_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Browse button
        browse_button = ttk.Button(
            product_selection_frame,
            text="Browse",
            command=self._browse_products
        )
        browse_button.pack(side=tk.LEFT, padx=5)

        # Product ID hidden field
        product_id_entry = ttk.Entry(
            product_selection_frame,
            textvariable=self.product_id,
            width=5
        )

        # Product price
        price_frame = ttk.Frame(self.product_frame)
        price_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(price_frame, text="Price:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        price_entry = ttk.Entry(
            price_frame,
            textvariable=self.product_price,
            state="readonly",
            width=10
        )
        price_entry.pack(side=tk.LEFT, padx=5)

        # Stock availability
        stock_frame = ttk.Frame(self.product_frame)
        stock_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(stock_frame, text="In Stock:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        stock_label = ttk.Label(stock_frame, textvariable=self.stock_level)
        stock_label.pack(side=tk.LEFT, padx=5)

        # Create custom item section
        self.custom_frame = ttk.LabelFrame(container, text="Custom Item")
        self.custom_frame.pack(fill=tk.X, pady=10)

        # Custom item description
        description_frame = ttk.Frame(self.custom_frame)
        description_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(description_frame, text="Description:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        description_entry = ttk.Entry(
            description_frame,
            textvariable=self.description,
            width=40
        )
        description_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Custom item price
        custom_price_frame = ttk.Frame(self.custom_frame)
        custom_price_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(custom_price_frame, text="Unit Price:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        price_entry = ttk.Entry(
            custom_price_frame,
            textvariable=self.unit_price,
            width=10
        )
        price_entry.pack(side=tk.LEFT, padx=5)

        # Create quantity and total frame
        quantity_frame = ttk.LabelFrame(container, text="Quantity and Total")
        quantity_frame.pack(fill=tk.X, pady=10)

        # Quantity
        qty_frame = ttk.Frame(quantity_frame)
        qty_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(qty_frame, text="Quantity:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        # Create a spinbox for quantity
        spinbox = ttk.Spinbox(
            qty_frame,
            from_=1,
            to=1000,
            textvariable=self.quantity,
            width=5,
            command=self._update_total
        )
        spinbox.pack(side=tk.LEFT, padx=5)

        # Bind entry field of spinbox to update total on value change
        spinbox.bind("<KeyRelease>", lambda e: self._update_total())

        # Total
        total_frame = ttk.Frame(quantity_frame)
        total_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(total_frame, text="Total:", width=12, anchor=tk.E, style="Bold.TLabel").pack(side=tk.LEFT)

        total_entry = ttk.Entry(
            total_frame,
            textvariable=self.total,
            state="readonly",
            width=10,
            font=("Arial", 10, "bold")
        )
        total_entry.pack(side=tk.LEFT, padx=5)

        # Create buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=15)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Save",
            style="Accent.TButton",
            command=self.on_ok
        ).pack(side=tk.RIGHT, padx=5)

        # Update UI based on item type
        self._update_item_type()

        # Bind price entry to update total
        price_entry.bind("<KeyRelease>", lambda e: self._update_total())

        # Initial update of total
        self._update_total()

    def _update_item_type(self):
        """Update UI based on selected item type."""
        if self.is_product.get():
            # Product selected
            self.product_frame.pack(fill=tk.X, pady=10)
            self.custom_frame.pack_forget()

            # Update unit price from product price
            if self.product_price.get():
                self.unit_price.set(self.product_price.get())

            # Check stock if product is selected
            if self.product_id.get():
                self._check_stock()
        else:
            # Custom item selected
            self.product_frame.pack_forget()
            self.custom_frame.pack(fill=tk.X, pady=10)

            # Update description if empty and editing product
            if self.item and hasattr(self.item, 'product_name') and not self.description.get():
                self.description.set(self.item.product_name)

    def _browse_products(self):
        """Open product selection dialog."""
        self.logger.debug("Opening product selection dialog")

        # Create product selection dialog
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Select Product")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Set dialog size and position
        dialog.geometry("700x500")
        dialog.resizable(True, True)

        # Create search section
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        search_btn = ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self._search_products(search_var.get(), product_tree)
        )
        search_btn.pack(side=tk.LEFT, padx=5)

        # Create products treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "price", "stock", "description")
        product_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        product_tree.heading("id", text="ID")
        product_tree.heading("name", text="Product Name")
        product_tree.heading("price", text="Price")
        product_tree.heading("stock", text="In Stock")
        product_tree.heading("description", text="Description")

        # Define columns
        product_tree.column("id", width=50)
        product_tree.column("name", width=150)
        product_tree.column("price", width=80, anchor=tk.E)
        product_tree.column("stock", width=80, anchor=tk.E)
        product_tree.column("description", width=250)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=product_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=product_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        product_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        product_tree.pack(fill=tk.BOTH, expand=True)

        # Create buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Select",
            style="Accent.TButton",
            command=lambda: self._select_product(product_tree, dialog)
        ).pack(side=tk.RIGHT, padx=5)

        # Load initial product data
        self._search_products("", product_tree)

        # Set focus to search entry
        search_entry.focus_set()

        # Bind double-click to select
        product_tree.bind("<Double-1>", lambda e: self._select_product(product_tree, dialog))

        # Bind Enter key in search entry
        search_entry.bind("<Return>", lambda e: self._search_products(search_var.get(), product_tree))

        # Wait for dialog to close
        dialog.wait_window()

    def _search_products(self, search_text, tree):
        """
        Search products based on search text.

        Args:
            search_text: Text to search for
            tree: Treeview to display results
        """
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)

            # Search products
            products = self.product_service.search_products(
                search_text=search_text,
                include_inventory=True,
                limit=100
            )

            # Display results
            for product in products:
                # Format price
                price_str = f"${product.price:.2f}" if hasattr(product,
                                                               'price') and product.price is not None else "$0.00"

                # Get stock level
                stock = 0
                if hasattr(product, 'inventory') and product.inventory:
                    stock = product.inventory.get('quantity', 0)

                tree.insert(
                    "",
                    "end",
                    iid=str(product.id),
                    values=(
                        product.id,
                        product.name,
                        price_str,
                        stock,
                        product.description if hasattr(product, 'description') else ""
                    )
                )

        except Exception as e:
            self.logger.error(f"Error searching products: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to search products: {str(e)}")

    def _select_product(self, tree, dialog):
        """
        Select the highlighted product.

        Args:
            tree: Treeview with product data
            dialog: Dialog to close after selection
        """
        # Get selected item
        selected_id = tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a product.")
            return

        # Get selected item data
        item_data = tree.item(selected_id)
        values = item_data["values"]

        if not values or len(values) < 5:
            messagebox.showwarning("Selection Error", "Invalid product data.")
            return

        # Set product variables
        self.product_id.set(str(values[0]))
        self.product_name.set(values[1])

        # Set price without $ sign
        price_str = values[2].replace('$', '')
        self.product_price.set(price_str)
        self.unit_price.set(price_str)

        # Set description if it's empty
        if not self.description.get():
            self.description.set(values[4] if len(values) > 4 else "")

        # Update stock label
        stock = values[3] if len(values) > 3 else 0
        self.stock_level.set(str(stock))

        # Update total
        self._update_total()

        # Close dialog
        dialog.destroy()

    def _check_stock(self):
        """Check stock level for selected product."""
        if not self.product_id.get():
            return

        try:
            # Get product with inventory data
            product = self.product_service.get_product(
                int(self.product_id.get()),
                include_inventory=True
            )

            # Update stock level
            stock = 0
            if product and hasattr(product, 'inventory') and product.inventory:
                stock = product.inventory.get('quantity', 0)

            self.stock_level.set(str(stock))

        except Exception as e:
            self.logger.error(f"Error checking stock: {e}", exc_info=True)
            self.stock_level.set("Error")

    def _update_total(self):
        """Update the total based on quantity and price."""
        try:
            # Get quantity
            quantity = float(self.quantity.get())

            # Get unit price based on item type
            if self.is_product.get():
                unit_price = float(self.product_price.get())
            else:
                unit_price = float(self.unit_price.get())

            # Calculate total
            total = quantity * unit_price

            # Update total field
            self.total.set(f"${total:.2f}")

        except ValueError:
            # Invalid numbers, set to zero
            self.total.set("$0.00")

    def validate_form(self):
        """
        Validate form data.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if product selected or custom item described
        if self.is_product.get() and not self.product_id.get():
            return False, "Please select a product."

        if not self.is_product.get() and not self.description.get():
            return False, "Please provide a description for the custom item."

        # Check quantity
        try:
            quantity = float(self.quantity.get())
            if quantity <= 0:
                return False, "Quantity must be greater than zero."
        except ValueError:
            return False, "Please enter a valid quantity."

        # Check price
        try:
            if self.is_product.get():
                price = float(self.product_price.get())
            else:
                price = float(self.unit_price.get())

            if price < 0:
                return False, "Price cannot be negative."
        except ValueError:
            return False, "Please enter a valid price."

        # All validations passed
        return True, ""

    def create_item_data(self):
        """
        Create item data object from form fields.

        Returns:
            Dictionary with item data
        """
        # Parse quantity
        quantity = 1
        try:
            quantity = float(self.quantity.get())
        except ValueError:
            pass

        # Parse price
        price = 0.0
        try:
            if self.is_product.get():
                price = float(self.product_price.get())
            else:
                price = float(self.unit_price.get())
        except ValueError:
            pass

        # Create item data
        item_data = {}

        # If editing existing item, preserve its ID
        if self.item and hasattr(self.item, 'id'):
            item_data['id'] = self.item.id

        # Add common fields
        item_data['quantity'] = quantity
        item_data['price'] = price

        # Add description
        if self.is_product.get():
            item_data['description'] = self.product_name.get()
        else:
            item_data['description'] = self.description.get()

        # Add product specific fields if this is a product
        if self.is_product.get() and self.product_id.get():
            item_data['product_id'] = int(self.product_id.get())
            item_data['product_name'] = self.product_name.get()
        else:
            item_data['product_id'] = None
            item_data['product_name'] = None

        return item_data

    def on_ok(self):
        """Handle OK button click."""
        # Validate form
        valid, message = self.validate_form()
        if not valid:
            messagebox.showwarning("Validation Error", message)
            return

        # Create item data
        self.result = self.create_item_data()

        # Close dialog
        self.close()