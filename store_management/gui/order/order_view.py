# gui/order/order_view.py
"""
View for managing orders in a leatherworking store management system.
Provides functionality to view, add, edit, and delete orders.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService, OrderStatus

# Configure logger
logger = logging.getLogger(__name__)


class SearchDialog(tk.Toplevel):
    """Dialog window for searching orders."""

    def __init__(self, parent: tk.Widget, columns: List[str], search_callback: Callable):
        """
        Initialize the search dialog.

        Args:
            parent: Parent widget
            columns: List of column names to search in
            search_callback: Function to call with search parameters
        """
        super().__init__(parent)
        self.title("Search Orders")
        self.transient(parent)
        self.resizable(False, False)

        self.search_callback = search_callback
        self.result = None

        # Variables
        self.search_field = tk.StringVar(value=columns[0] if columns else "")
        self.search_text = tk.StringVar()

        # Create UI
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Search field selector
        ttk.Label(frame, text="Search in:").grid(row=0, column=0, sticky=tk.W, pady=5)
        field_combo = ttk.Combobox(frame, textvariable=self.search_field, values=columns)
        field_combo.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        field_combo.state(['readonly'])

        # Search text
        ttk.Label(frame, text="Search for:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.search_text, width=30).grid(
            row=1, column=1, sticky="ew", pady=5, padx=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

        # Set focus
        self.search_text.set("")
        self.bind("<Return>", self._on_search)
        self.bind("<Escape>", lambda e: self.destroy())

        # Center dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (parent.winfo_width() - width) // 2 + parent.winfo_x()
        y = (parent.winfo_height() - height) // 2 + parent.winfo_y()
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.grab_set()
        self.wait_window()

    def _on_search(self, event=None):
        """
        Handle search button click or Enter key.

        Args:
            event: Event that triggered the search
        """
        if not self.search_text.get().strip():
            messagebox.showwarning("Warning", "Please enter search text.", parent=self)
            return

        search_params = {
            "field": self.search_field.get(),
            "text": self.search_text.get().strip()
        }

        self.destroy()
        self.search_callback(search_params)


class OrderView(BaseView):
    """
    View for displaying and managing orders.

    Provides a tabular interface for viewing orders, with functionality
    to add, edit, and delete entries. Includes search and filter capabilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)

        self._order_service = None
        self._selected_order_id = None

        # Initialize UI components
        self._create_ui()
        self._load_data()

        logger.info("Order view initialized")

    def get_service(self, service_type: Type) -> Any:
        """
        Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            return self._app.get_service(service_type)
        except Exception as e:
            logger.error(f"Failed to get service {service_type.__name__}: {str(e)}")
            raise

    @property
    def order_service(self) -> IOrderService:
        """
        Lazy-loaded order service property.

        Returns:
            IOrderService: Order service instance
        """
        if self._order_service is None:
            self._order_service = self.get_service(IOrderService)
        return self._order_service

    def _create_ui(self) -> None:
        """Create and configure UI components."""
        # Configure frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Create toolbar
        toolbar_frame = ttk.Frame(self, padding=5)
        toolbar_frame.grid(row=0, column=0, sticky="ew")

        # Add toolbar buttons
        ttk.Button(toolbar_frame, text="Add Order", command=self._add_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="View Details", command=self._view_details).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Refresh", command=self._load_data).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar_frame, text="Search", command=self._show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Filter", command=self._show_filter_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Reset View", command=self._reset_view).pack(side=tk.LEFT, padx=2)

        # Create status filter dropdown
        ttk.Label(toolbar_frame, text="Status:").pack(side=tk.LEFT, padx=(10, 2))
        self.status_filter = ttk.Combobox(toolbar_frame, width=12, state="readonly")
        self.status_filter.pack(side=tk.LEFT, padx=2)

        # Populate status dropdown options
        status_options = ["All"] + [status.name for status in OrderStatus]
        self.status_filter.configure(values=status_options)
        self.status_filter.current(0)  # Default to "All"
        self.status_filter.bind("<<ComboboxSelected>>", self._on_status_filter_change)

        # Create treeview
        columns = (
            "id", "order_number", "customer_name", "order_date",
            "total_amount", "status", "payment_status", "items_count"
        )
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        # Define column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("order_number", text="Order #")
        self.tree.heading("customer_name", text="Customer")
        self.tree.heading("order_date", text="Date")
        self.tree.heading("total_amount", text="Total")
        self.tree.heading("status", text="Status")
        self.tree.heading("payment_status", text="Payment")
        self.tree.heading("items_count", text="Items")

        # Configure column widths
        self.tree.column("id", width=60, stretch=False)
        self.tree.column("order_number", width=100)
        self.tree.column("customer_name", width=180)
        self.tree.column("order_date", width=100)
        self.tree.column("total_amount", width=90, anchor=tk.E)
        self.tree.column("status", width=100)
        self.tree.column("payment_status", width=100)
        self.tree.column("items_count", width=60, anchor=tk.CENTER)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)

        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scrollbar.grid(row=1, column=1, sticky="ns")
        x_scrollbar.grid(row=2, column=0, sticky="ew")

        # Add status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Set initial status
        self.status_var.set("Ready")

    def _load_data(self) -> None:
        """
        Load orders from the order service and populate the treeview.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get orders from service
            orders = self.order_service.get_orders()

            if not orders:
                self.status_var.set("No orders found")
                logger.info("No orders found")
                return

            # Apply status filter if selected
            status_filter = self.status_filter.get()
            if status_filter != "All":
                orders = [order for order in orders if order.get("status") == status_filter]

            # Populate treeview
            for order in orders:
                # Format data for display
                total_amount = order.get("total_amount", 0)
                formatted_total = f"${total_amount:.2f}" if total_amount else "N/A"

                items_count = len(order.get("items", []))

                self.tree.insert("", tk.END, values=(
                    order.get("id", ""),
                    order.get("order_number", ""),
                    order.get("customer_name", ""),
                    order.get("order_date", ""),
                    formatted_total,
                    order.get("status", ""),
                    order.get("payment_status", ""),
                    items_count
                ))

            # Update status
            self.status_var.set(f"Loaded {len(orders)} orders")
            logger.info(f"Loaded {len(orders)} orders")

        except Exception as e:
            error_message = f"Error loading orders: {str(e)}"
            self.show_error("Data Loading Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error loading data")

    def _on_select(self, event=None) -> None:
        """
        Handle selection of an item in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self._selected_order_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            self._selected_order_id = values[0]  # ID is the first column

    def _on_double_click(self, event=None) -> None:
        """
        Handle double-click on a treeview item.

        Args:
            event: Double-click event
        """
        self._view_details()

    def _on_status_filter_change(self, event=None) -> None:
        """
        Handle status filter selection change.

        Args:
            event: ComboboxSelected event
        """
        self._load_data()

    def _add_order(self) -> None:
        """
        Show dialog to add a new order.
        """
        # This would typically open an order entry dialog
        # For now, display a placeholder message
        self.show_info("Add Order", "Order entry dialog would open here.")
        logger.info("Add order functionality called")

    def _edit_selected(self) -> None:
        """
        Show dialog to edit the selected order.
        """
        if not self._selected_order_id:
            self.show_warning("Warning", "Please select an order to edit.")
            return

        # This would typically open an order edit dialog
        # For now, display a placeholder message
        self.show_info("Edit Order", f"Edit dialog for order ID {self._selected_order_id} would open here.")
        logger.info(f"Edit order called for ID: {self._selected_order_id}")

    def _delete_selected(self) -> None:
        """
        Delete the selected order after confirmation.
        """
        if not self._selected_order_id:
            self.show_warning("Warning", "Please select an order to delete.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete this order?\n"
                                   "This action cannot be undone."):
            return

        try:
            # Delete order through service
            result = self.order_service.delete_order(self._selected_order_id)

            if result:
                self.show_info("Success", "Order deleted successfully!")
                self._selected_order_id = None
                self._load_data()  # Refresh the view
            else:
                self.show_error("Error", "Failed to delete order.")

        except Exception as e:
            error_message = f"Error deleting order: {str(e)}"
            self.show_error("Delete Error", error_message)
            logger.error(error_message, exc_info=True)

    def _view_details(self) -> None:
        """
        Show detailed view of the selected order.
        """
        if not self._selected_order_id:
            self.show_warning("Warning", "Please select an order to view details.")
            return

        try:
            # Get order details from service
            order = self.order_service.get_order_by_id(self._selected_order_id)

            if not order:
                self.show_error("Error", "Selected order not found.")
                self._load_data()  # Refresh to ensure view is up-to-date
                return

            # This would typically open an order details dialog
            # For now, display a placeholder message
            details = f"Order #{order.get('order_number', '')}\n" \
                      f"Customer: {order.get('customer_name', '')}\n" \
                      f"Status: {order.get('status', '')}\n" \
                      f"Total: ${order.get('total_amount', 0):.2f}"

            self.show_info("Order Details", details)
            logger.info(f"View details called for order ID: {self._selected_order_id}")

        except Exception as e:
            error_message = f"Error viewing order details: {str(e)}"
            self.show_error("View Error", error_message)
            logger.error(error_message, exc_info=True)

    def _show_search_dialog(self) -> None:
        """
        Show search dialog for orders.
        """
        columns = ["order_number", "customer_name", "status", "payment_status"]
        SearchDialog(self, columns, self._perform_search)

    def _perform_search(self, search_params: Dict[str, str]) -> None:
        """
        Perform search based on parameters from search dialog.

        Args:
            search_params: Dictionary with search field and text
        """
        field = search_params.get("field", "")
        text = search_params.get("text", "").lower()

        if not field or not text:
            return

        try:
            # Clear current items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get all orders and filter locally
            all_orders = self.order_service.get_all_orders()
            filtered_orders = []

            for order in all_orders:
                # Get field value and compare
                value = str(order.get(field, "")).lower()
                if text in value:
                    filtered_orders.append(order)

            # Populate treeview with filtered orders
            for order in filtered_orders:
                total_amount = order.get("total_amount", 0)
                formatted_total = f"${total_amount:.2f}" if total_amount else "N/A"

                items_count = len(order.get("items", []))

                self.tree.insert("", tk.END, values=(
                    order.get("id", ""),
                    order.get("order_number", ""),
                    order.get("customer_name", ""),
                    order.get("order_date", ""),
                    formatted_total,
                    order.get("status", ""),
                    order.get("payment_status", ""),
                    items_count
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_orders)} orders matching '{text}' in {field}")
            logger.info(f"Search performed: {len(filtered_orders)} orders found matching '{text}' in {field}")

        except Exception as e:
            error_message = f"Error searching orders: {str(e)}"
            self.show_error("Search Error", error_message)
            logger.error(error_message, exc_info=True)

    def _show_filter_dialog(self) -> None:
        """
        Show filter dialog for orders.
        """
        # This would typically open a filter dialog
        # For now, display a placeholder message
        self.show_info("Filter Orders", "Filter dialog would open here.")
        logger.info("Filter dialog requested")

    def _reset_view(self) -> None:
        """
        Reset all filters and reload data.
        """
        self.status_filter.current(0)  # Reset to "All"
        self._load_data()
        self.status_var.set("View reset")
        logger.info("View reset")