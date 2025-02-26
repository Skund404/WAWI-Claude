# gui/order/order_view.py
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import tkinter as tk
from tkinter import messagebox, ttk

from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService, OrderStatus


class SearchDialog(tk.Toplevel):
    """Dialog for searching orders."""

    def __init__(self, parent: tk.Widget, columns: List[str], search_callback: Callable):
        """Initialize the search dialog.

        Args:
            parent: Parent widget
            columns: List of column names to search in
            search_callback: Function to call with search parameters
        """
        super().__init__(parent)
        self.title("Search Orders")
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.columns = columns
        self.search_callback = search_callback

        # Create search field selection
        ttk.Label(self, text="Search in:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.field_var = tk.StringVar(value=columns[0] if columns else "")
        field_combo = ttk.Combobox(self, textvariable=self.field_var, values=columns)
        field_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Create search text entry
        ttk.Label(self, text="Search for:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(self, textvariable=self.search_var)
        search_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        search_entry.bind("<Return>", self._on_search)

        # Create exact match checkbox
        self.exact_match_var = tk.BooleanVar(value=False)
        exact_match_cb = ttk.Checkbutton(self, text="Exact match", variable=self.exact_match_var)
        exact_match_cb.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Create search button
        search_button = ttk.Button(self, text="Search", command=self._on_search)
        search_button.grid(row=3, column=1, padx=10, pady=10, sticky="e")

        # Create cancel button
        cancel_button = ttk.Button(self, text="Cancel", command=self.destroy)
        cancel_button.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        # Configure grid
        self.columnconfigure(1, weight=1)

    def _on_search(self, event=None):
        """Handle search button click or Enter key.

        Args:
            event: Event that triggered the search
        """
        field = self.field_var.get()
        search_text = self.search_var.get()
        exact_match = self.exact_match_var.get()

        if search_text:
            self.search_callback(field, search_text, exact_match)
            self.destroy()


class OrderView(BaseView):
    """View for managing orders."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Order View")

        self._order_service = None
        self.selected_order_id = None

        self._setup_ui()
        self._load_orders()

    def _setup_ui(self):
        """Set up the user interface components."""
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create toolbar
        toolbar = self._create_toolbar(main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Create status filter
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filter by status:").pack(side=tk.LEFT, padx=5)
        status_values = ["All"] + [status.name for status in OrderStatus]
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, values=status_values, width=15)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", self._on_status_filter)

        # Create content area with splitter
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create paned window for orders and details
        paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Create orders treeview on the left
        orders_frame = ttk.Frame(paned)
        paned.add(orders_frame, weight=2)

        columns = ("id", "customer", "date", "status", "payment_status", "total")
        self.orders_tree = ttk.Treeview(orders_frame, columns=columns, show="headings")
        self.orders_tree.heading("id", text="Order ID")
        self.orders_tree.heading("customer", text="Customer")
        self.orders_tree.heading("date", text="Date")
        self.orders_tree.heading("status", text="Status")
        self.orders_tree.heading("payment_status", text="Payment")
        self.orders_tree.heading("total", text="Total")

        self.orders_tree.column("id", width=80)
        self.orders_tree.column("customer", width=150)
        self.orders_tree.column("date", width=100)
        self.orders_tree.column("status", width=100)
        self.orders_tree.column("payment_status", width=100)
        self.orders_tree.column("total", width=100)

        scrollbar = ttk.Scrollbar(orders_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscroll=scrollbar.set)

        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)
        self.orders_tree.bind("<Double-1>", self._on_order_double_click)

        # Create order details frame on the right
        details_frame = ttk.LabelFrame(paned, text="Order Details")
        paned.add(details_frame, weight=3)

        # Create order details treeview
        self.details_tree = ttk.Treeview(details_frame, columns=("id", "product", "quantity", "price", "subtotal"),
                                         show="headings")
        self.details_tree.heading("id", text="Item ID")
        self.details_tree.heading("product", text="Product")
        self.details_tree.heading("quantity", text="Quantity")
        self.details_tree.heading("price", text="Price")
        self.details_tree.heading("subtotal", text="Subtotal")

        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_tree.yview)
        self.details_tree.configure(yscroll=details_scrollbar.set)

        self.details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    def _create_toolbar(self, parent):
        """Create toolbar with action buttons.

        Args:
            parent: Parent widget for the toolbar
        """
        toolbar = ttk.Frame(parent)

        new_btn = ttk.Button(toolbar, text="New Order", command=self._on_new_order)
        new_btn.pack(side=tk.LEFT, padx=2)

        edit_btn = ttk.Button(toolbar, text="Edit Order", command=self._on_edit_order)
        edit_btn.pack(side=tk.LEFT, padx=2)

        delete_btn = ttk.Button(toolbar, text="Delete Order", command=self._on_delete_order)
        delete_btn.pack(side=tk.LEFT, padx=2)

        search_btn = ttk.Button(toolbar, text="Search", command=self._on_search)
        search_btn.pack(side=tk.LEFT, padx=2)

        reset_btn = ttk.Button(toolbar, text="Reset Filters", command=self._on_reset)
        reset_btn.pack(side=tk.LEFT, padx=2)

        return toolbar

    def _load_orders(self):
        """Load orders from the database."""
        try:
            # Clear existing items
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)

            # Get orders from service
            orders = self.order_service.get_all_orders()

            # Populate treeview
            for order in orders:
                values = (
                    order.get('id', ''),
                    order.get('customer_name', ''),
                    order.get('order_date', '')[:10] if order.get('order_date') else '',
                    order.get('status', ''),
                    order.get('payment_status', ''),
                    f"${order.get('total', 0):.2f}"
                )
                self.orders_tree.insert('', tk.END, values=values, tags=(str(order.get('id')),))

            self.set_status(f"Loaded {len(orders)} orders")
        except Exception as e:
            self.logger.error(f"Error loading orders: {str(e)}")
            self.show_error("Load Error", f"Could not load orders: {str(e)}")

    def _load_order_details(self, order_id: int):
        """Load details for the selected order.

        Args:
            order_id: ID of the order to load details for
        """
        try:
            # Clear existing items
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            # Get order details
            order = self.order_service.get_order(order_id)
            if not order:
                return

            # Populate items treeview
            for item in order.get('items', []):
                values = (
                    item.get('id', ''),
                    item.get('product_name', ''),
                    item.get('quantity', 0),
                    f"${item.get('unit_price', 0):.2f}",
                    f"${item.get('subtotal', 0):.2f}"
                )
                self.details_tree.insert('', tk.END, values=values)

            self.set_status(f"Loaded details for order #{order_id}")
        except Exception as e:
            self.logger.error(f"Error loading order details: {str(e)}")
            self.show_error("Load Error", f"Could not load order details: {str(e)}")

    def _on_order_select(self, event=None):
        """Handle order selection in treeview."""
        selected_items = self.orders_tree.selection()
        if not selected_items:
            return

        # Get the order ID from the selected item
        item = selected_items[0]
        order_id = int(self.orders_tree.item(item, 'values')[0])
        self.selected_order_id = order_id

        # Load order details
        self._load_order_details(order_id)

    def _on_order_double_click(self, event=None):
        """Handle double-click on an order to edit it."""
        if self.selected_order_id:
            self._on_edit_order()

    def _on_new_order(self):
        """Handle new order button click."""
        # Placeholder for opening a new order dialog
        messagebox.showinfo("New Order", "New order functionality not implemented yet")

    def _on_edit_order(self):
        """Handle edit order button click."""
        if not self.selected_order_id:
            messagebox.showinfo("Edit Order", "Please select an order to edit")
            return

        # Placeholder for opening an edit order dialog
        messagebox.showinfo("Edit Order", f"Edit order #{self.selected_order_id} functionality not implemented yet")

    def _on_delete_order(self):
        """Handle delete order button click."""
        if not self.selected_order_id:
            messagebox.showinfo("Delete Order", "Please select an order to delete")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete order #{self.selected_order_id}?"):
            try:
                success = self.order_service.delete_order(self.selected_order_id)
                if success:
                    self._load_orders()
                    self.set_status(f"Deleted order #{self.selected_order_id}")
                else:
                    self.show_error("Delete Error", f"Could not delete order #{self.selected_order_id}")
            except Exception as e:
                self.logger.error(f"Error deleting order: {str(e)}")
                self.show_error("Delete Error", f"Error deleting order: {str(e)}")

    def _on_search(self):
        """Handle search button click."""
        # Get column names for search
        columns = [self.orders_tree.heading(col)["text"] for col in self.orders_tree["columns"]]

        # Open search dialog
        SearchDialog(self, columns, self._perform_search)

    def _perform_search(self, field: str, search_text: str, exact_match: bool):
        """Perform search based on criteria.

        Args:
            field: Field to search in
            search_text: Text to search for
            exact_match: Whether to perform exact matching
        """
        # Clear existing items
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        try:
            # Get all orders
            orders = self.order_service.get_all_orders()

            # Filter based on search criteria
            filtered_orders = []
            for order in orders:
                # Map the displayed field name back to the order dict key
                field_map = {
                    "Order ID": "id",
                    "Customer": "customer_name",
                    "Date": "order_date",
                    "Status": "status",
                    "Payment": "payment_status",
                    "Total": "total"
                }

                key = field_map.get(field)
                if not key:
                    continue

                value = str(order.get(key, ""))

                # Perform matching
                if exact_match:
                    if search_text.lower() == value.lower():
                        filtered_orders.append(order)
                else:
                    if search_text.lower() in value.lower():
                        filtered_orders.append(order)

            # Populate treeview with filtered orders
            for order in filtered_orders:
                values = (
                    order.get('id', ''),
                    order.get('customer_name', ''),
                    order.get('order_date', '')[:10] if order.get('order_date') else '',
                    order.get('status', ''),
                    order.get('payment_status', ''),
                    f"${order.get('total', 0):.2f}"
                )
                self.orders_tree.insert('', tk.END, values=values, tags=(str(order.get('id')),))

            self.set_status(f"Found {len(filtered_orders)} orders matching '{search_text}' in {field}")
        except Exception as e:
            self.logger.error(f"Error searching orders: {str(e)}")
            self.show_error("Search Error", f"Error searching orders: {str(e)}")

    def _on_filter(self):
        """Handle filter button click."""
        pass

    def _on_status_filter(self, event=None):
        """Handle status filter selection."""
        status_value = self.status_var.get()

        # Clear existing items
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        try:
            if status_value == "All":
                # Load all orders
                orders = self.order_service.get_all_orders()
            else:
                # Convert status string to enum
                status = OrderStatus[status_value]
                # Get filtered orders
                orders = self.order_service.get_orders(status)

            # Populate treeview
            for order in orders:
                values = (
                    order.get('id', ''),
                    order.get('customer_name', ''),
                    order.get('order_date', '')[:10] if order.get('order_date') else '',
                    order.get('status', ''),
                    order.get('payment_status', ''),
                    f"${order.get('total', 0):.2f}"
                )
                self.orders_tree.insert('', tk.END, values=values, tags=(str(order.get('id')),))

            self.set_status(f"Filtered to {len(orders)} orders with status {status_value}")
        except Exception as e:
            self.logger.error(f"Error filtering orders: {str(e)}")
            self.show_error("Filter Error", f"Error filtering orders: {str(e)}")

    def _on_reset(self):
        """Handle reset button click to clear all filters and reload orders."""
        # Reset status filter
        self.status_var.set("All")

        # Reload all orders
        self._load_orders()

    @property
    def order_service(self) -> IOrderService:
        """Get the order service.

        Returns:
            IOrderService: The order service instance
        """
        if self._order_service is None:
            self._order_service = self._get_service(IOrderService)
        return self._order_service

    @order_service.setter
    def order_service(self, service: IOrderService):
        """Set the order service.

        Args:
            service (IOrderService): The order service instance
        """
        self._order_service = service