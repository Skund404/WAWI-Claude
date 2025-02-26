# gui/order/order_view.py
"""
Order view module for displaying and managing orders in the leatherworking store management application.
This view allows users to see, create, edit, and delete orders, as well as filter and search through them.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type, Union, Callable

from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService, OrderStatus

# Configure logger
logger = logging.getLogger(__name__)


class SearchDialog(tk.Toplevel):
    """Dialog for searching through orders."""

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

        # Create widgets
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Search field selection
        ttk.Label(main_frame, text="Search in:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.field_var = tk.StringVar(value=columns[0] if columns else "")
        field_combo = ttk.Combobox(main_frame, textvariable=self.field_var, values=columns)
        field_combo.grid(row=0, column=1, sticky=tk.EW, pady=5)

        # Search text
        ttk.Label(main_frame, text="Search text:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        search_entry.focus_set()
        search_entry.bind("<Return>", self._on_search)

        # Exact match option
        self.exact_match_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Exact match", variable=self.exact_match_var).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def _on_search(self, event=None):
        """Handle search button click or Enter key.

        Args:
            event: Event that triggered the search
        """
        field = self.field_var.get()
        search_text = self.search_var.get()
        exact_match = self.exact_match_var.get()

        if not search_text:
            messagebox.showwarning("Warning", "Please enter search text", parent=self)
            return

        self.destroy()
        self.search_callback(field, search_text, exact_match)


class OrderView(BaseView):
    """View for displaying and managing orders."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        logger.info("Initializing Order View")

        self.order_service = self._get_service(IOrderService)

        # Initialize variables
        self.current_orders = []
        self.selected_order_id = None

        # Set up the layout
        self._setup_ui()

        # Load initial data
        self._load_orders()

        logger.info("Order view initialized")

    def _setup_ui(self):
        """Set up the user interface components."""
        # Main layout - split into two frames
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Toolbar at the top
        self._create_toolbar()

        # Orders frame with treeview
        orders_frame = ttk.LabelFrame(self.main_frame, text="Orders")
        orders_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create orders treeview
        columns = ("order_id", "customer_name", "order_date", "status", "total_amount")
        self.orders_tree = ttk.Treeview(orders_frame, columns=columns, show="headings", selectmode="browse")

        # Configure columns
        self.orders_tree.heading("order_id", text="Order ID")
        self.orders_tree.heading("customer_name", text="Customer")
        self.orders_tree.heading("order_date", text="Date")
        self.orders_tree.heading("status", text="Status")
        self.orders_tree.heading("total_amount", text="Total Amount")

        self.orders_tree.column("order_id", width=80, anchor=tk.CENTER)
        self.orders_tree.column("customer_name", width=150)
        self.orders_tree.column("order_date", width=100, anchor=tk.CENTER)
        self.orders_tree.column("status", width=100, anchor=tk.CENTER)
        self.orders_tree.column("total_amount", width=100, anchor=tk.E)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(orders_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        self.orders_tree.configure(yscroll=scrollbar.set)

        # Pack the treeview and scrollbar
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)
        self.orders_tree.bind("<Double-1>", self._on_order_double_click)

        # Order details frame at the bottom
        self.details_frame = ttk.LabelFrame(self.main_frame, text="Order Details")
        self.details_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create order details treeview
        details_columns = ("item_id", "product_name", "quantity", "unit_price", "total_price")
        self.details_tree = ttk.Treeview(self.details_frame, columns=details_columns, show="headings",
                                         selectmode="browse")

        # Configure columns
        self.details_tree.heading("item_id", text="Item ID")
        self.details_tree.heading("product_name", text="Product")
        self.details_tree.heading("quantity", text="Quantity")
        self.details_tree.heading("unit_price", text="Unit Price")
        self.details_tree.heading("total_price", text="Total Price")

        self.details_tree.column("item_id", width=80, anchor=tk.CENTER)
        self.details_tree.column("product_name", width=200)
        self.details_tree.column("quantity", width=80, anchor=tk.CENTER)
        self.details_tree.column("unit_price", width=100, anchor=tk.E)
        self.details_tree.column("total_price", width=100, anchor=tk.E)

        # Add scrollbar for details
        details_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.details_tree.yview)
        self.details_tree.configure(yscroll=details_scrollbar.set)

        # Pack the details treeview and scrollbar
        self.details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_toolbar(self):
        """Create toolbar with action buttons."""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Create toolbar buttons
        ttk.Button(toolbar, text="New Order", command=self._on_new_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit Order", command=self._on_edit_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Order", command=self._on_delete_order).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        ttk.Button(toolbar, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter", command=self._on_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Reset", command=self._on_reset).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Create status filter dropdown
        ttk.Label(toolbar, text="Status:").pack(side=tk.LEFT, padx=2)
        self.status_var = tk.StringVar(value="All")
        statuses = ["All"] + [status.name for status in OrderStatus]
        status_combo = ttk.Combobox(toolbar, textvariable=self.status_var, values=statuses, width=12, state="readonly")
        status_combo.pack(side=tk.LEFT, padx=2)
        status_combo.bind("<<ComboboxSelected>>", self._on_status_filter)

    def _load_orders(self):
        """Load orders from the database."""
        try:
            # Clear existing items
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)

            # Fetch orders from service
            self.current_orders = self.order_service.get_all_orders()

            if not self.current_orders:
                logger.info("No orders found")
                return

            # Populate treeview
            for order in self.current_orders:
                # Format values for display
                order_id = order.get("id", "")
                customer_name = order.get("customer_name", "")
                order_date = order.get("order_date", "")
                status = order.get("status", "")
                total_amount = order.get("total_amount", 0.0)

                # Format currency
                formatted_total = f"${total_amount:.2f}" if total_amount else ""

                # Insert into treeview
                self.orders_tree.insert("", "end", values=(
                    order_id, customer_name, order_date, status, formatted_total
                ))

            logger.info(f"Loaded {len(self.current_orders)} orders")
        except Exception as e:
            logger.error(f"Error loading orders: {str(e)}", exc_info=True)
            self.show_error("Error", f"Failed to load orders: {str(e)}")

    def _load_order_details(self, order_id: int):
        """Load details for the selected order.

        Args:
            order_id: ID of the order to load details for
        """
        try:
            # Clear existing items
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            # Find order in current orders
            selected_order = next((o for o in self.current_orders if o.get("id") == order_id), None)

            if not selected_order:
                logger.warning(f"Order {order_id} not found in current orders")
                return

            # Get order items
            order_items = selected_order.get("items", [])

            if not order_items:
                logger.info(f"No items found for order {order_id}")
                return

            # Populate details treeview
            for item in order_items:
                item_id = item.get("id", "")
                product_name = item.get("product_name", "")
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0.0)
                total_price = quantity * unit_price

                # Format currency
                formatted_unit_price = f"${unit_price:.2f}" if unit_price else ""
                formatted_total_price = f"${total_price:.2f}" if total_price else ""

                # Insert into treeview
                self.details_tree.insert("", "end", values=(
                    item_id, product_name, quantity, formatted_unit_price, formatted_total_price
                ))

            logger.info(f"Loaded {len(order_items)} items for order {order_id}")
        except Exception as e:
            logger.error(f"Error loading order details: {str(e)}", exc_info=True)
            self.show_error("Error", f"Failed to load order details: {str(e)}")

    def _on_order_select(self, event=None):
        """Handle order selection in treeview."""
        selected_items = self.orders_tree.selection()
        if not selected_items:
            return

        # Get selected item
        item_id = selected_items[0]
        values = self.orders_tree.item(item_id, "values")

        if not values:
            return

        # Extract order ID from values
        try:
            order_id = int(values[0])
            self.selected_order_id = order_id
            self._load_order_details(order_id)
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing selected order: {str(e)}")

    def _on_order_double_click(self, event=None):
        """Handle double-click on an order to edit it."""
        if self.selected_order_id:
            self._on_edit_order()

    def _on_new_order(self):
        """Handle new order button click."""
        # This would open a dialog to create a new order
        # For now, show a placeholder message
        messagebox.showinfo("New Order", "Open new order dialog")
        logger.info("New order dialog requested")

    def _on_edit_order(self):
        """Handle edit order button click."""
        if not self.selected_order_id:
            messagebox.showwarning("Warning", "Please select an order to edit")
            return

        # This would open a dialog to edit the selected order
        # For now, show a placeholder message
        messagebox.showinfo("Edit Order", f"Edit order {self.selected_order_id}")
        logger.info(f"Edit order dialog requested for order {self.selected_order_id}")

    def _on_delete_order(self):
        """Handle delete order button click."""
        if not self.selected_order_id:
            messagebox.showwarning("Warning", "Please select an order to delete")
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete order {self.selected_order_id}?",
            icon="warning"
        )

        if confirm:
            try:
                # Delete the order
                self.order_service.delete_order(self.selected_order_id)

                # Reload orders
                self._load_orders()

                # Clear selection
                self.selected_order_id = None

                # Clear details
                for item in self.details_tree.get_children():
                    self.details_tree.delete(item)

                logger.info(f"Order {self.selected_order_id} deleted")
            except Exception as e:
                logger.error(f"Error deleting order: {str(e)}", exc_info=True)
                self.show_error("Error", f"Failed to delete order: {str(e)}")

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
        logger.info(f"Performing search: field={field}, text={search_text}, exact={exact_match}")

        # Get column index from heading text
        column_indexes = {self.orders_tree.heading(col)["text"]: i for i, col in enumerate(self.orders_tree["columns"])}
        column_index = column_indexes.get(field, 0)

        # Clear current selection
        self.orders_tree.selection_remove(self.orders_tree.selection())

        found_items = []

        # Search through the items
        for item_id in self.orders_tree.get_children():
            values = self.orders_tree.item(item_id, "values")
            value = str(values[column_index]) if values and len(values) > column_index else ""

            # Match according to search criteria
            if exact_match:
                if value == search_text:
                    found_items.append(item_id)
            else:
                if search_text.lower() in value.lower():
                    found_items.append(item_id)

        if found_items:
            # Select the first match and ensure it's visible
            self.orders_tree.selection_add(found_items[0])
            self.orders_tree.see(found_items[0])

            # Highlight all matches
            for item_id in found_items:
                self.orders_tree.item(item_id, tags=("match",))

            # Configure tag for highlighting
            self.orders_tree.tag_configure("match", background="#FFFFCC")

            logger.info(f"Found {len(found_items)} matching orders")
        else:
            messagebox.showinfo("Search Results", "No matching orders found")
            logger.info("No matching orders found")

    def _on_filter(self):
        """Handle filter button click."""
        # This would open a dialog to set up filtering criteria
        # For now, show a placeholder message
        messagebox.showinfo("Filter Orders", "Filter dialog would appear here")
        logger.info("Filter dialog requested")

    def _on_status_filter(self, event=None):
        """Handle status filter selection."""
        status = self.status_var.get()

        logger.info(f"Filtering orders by status: {status}")

        if status == "All":
            # Show all orders
            self._load_orders()
        else:
            try:
                # Filter orders by status
                filtered_orders = [
                    order for order in self.current_orders
                    if order.get("status", "") == status
                ]

                # Clear existing items
                for item in self.orders_tree.get_children():
                    self.orders_tree.delete(item)

                # Populate treeview with filtered orders
                for order in filtered_orders:
                    # Format values for display
                    order_id = order.get("id", "")
                    customer_name = order.get("customer_name", "")
                    order_date = order.get("order_date", "")
                    status = order.get("status", "")
                    total_amount = order.get("total_amount", 0.0)

                    # Format currency
                    formatted_total = f"${total_amount:.2f}" if total_amount else ""

                    # Insert into treeview
                    self.orders_tree.insert("", "end", values=(
                        order_id, customer_name, order_date, status, formatted_total
                    ))

                logger.info(f"Filtered to {len(filtered_orders)} orders with status {status}")
            except Exception as e:
                logger.error(f"Error filtering orders: {str(e)}", exc_info=True)
                self.show_error("Error", f"Failed to filter orders: {str(e)}")

    def _on_reset(self):
        """Handle reset button click to clear all filters and reload orders."""
        # Reset status filter
        self.status_var.set("All")

        # Clear any tags or highlights
        for item_id in self.orders_tree.get_children():
            self.orders_tree.item(item_id, tags=())

        # Reload all orders
        self._load_orders()

        logger.info("Reset filters and reloaded all orders")