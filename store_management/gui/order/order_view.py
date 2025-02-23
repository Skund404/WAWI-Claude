# gui\\order\\order_view.py
import tkinter
import tkinter.ttk
import logging
from typing import Optional, List, Dict, Any
from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService
from database.models.enums import OrderStatus, PaymentStatus
from gui.dialogs.search_dialog import SearchDialog  # Import SearchDialog


class OrderView(BaseView):
    """View for managing orders in the application.

    Provides functionality for:
    - Viewing order list
    - Creating new orders
    - Updating existing orders
    - Deleting orders
    - Filtering and searching orders
    """

    def __init__(self, parent, app):
        """Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface components."""
        self._setup_treeview()
        self.load_data()
        # Example: Bind double click, but no need to call create sample data because is handled above.
        self.tree.bind("<Double-1>", self.on_double_click)

    def _get_columns(self):
        """Get the column definitions for the treeview."""
        return ("Order Number", "Customer Name", "Status", "Payment Status", "Total Amount", "Notes")

    def _setup_treeview(self):
        """Configure the treeview columns and headings."""
        columns = self._get_columns()
        self.tree = tkinter.ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self._sort_column(_col))
            self.tree.column(col, minwidth=100)
        self.tree.pack(expand=True, fill=tkinter.BOTH)

    def load_data(self):
        """Load and display order data in the treeview."""
        try:
            order_service = self.get_service(IOrderService)
            orders = order_service.get_all_orders()
            self.tree.delete(*self.tree.get_children())  # Clear existing data
            for order in orders:
                self.tree.insert("", tkinter.END, values=(
                    order.order_number,
                    order.customer_name,
                    order.status,
                    order.payment_status,
                    order.total_amount,
                    order.notes
                ))
        except Exception as e:
            self.show_error("Error loading order data", str(e))

    def show_add_dialog(self):
        """Show dialog for adding a new order."""
        pass  # Implement add dialog here

    def delete_selected(self, event):
        """Delete the selected order."""
        pass  # Implement delete logic here

    def on_double_click(self, event):
        """Handle double-click on an order to edit it."""
        pass  # Implement edit order logic here

    def _sort_column(self, col):
        """Sort treeview by the specified column."""
        pass  # Implement sort column logic here

    def _get_dialog_fields(self):
        """Get field definitions for the order dialog."""
        pass  # Implement field definitions here

    def show_search_dialog(self):
        """Show dialog for searching orders."""
        columns = self._get_columns()
        search_callback = self._search_orders  # Defining the search callback
        dialog = SearchDialog(self, columns, search_callback)

    def _search_orders(self, search_term: str, columns: List[str]):
        """
        Search for orders based on the provided search term and columns.

        Args:
            search_term (str): The term to search for.
            columns (List[str]): A list of column names to search within.
        """
        try:
            order_service = self.get_service(IOrderService)
            orders = order_service.search_orders(search_term, columns)

            # Clear existing data in the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert the new data in the treeview
            for order in orders:
                self.tree.insert("", END, values=(
                order.order_number, order.customer_name, order.status, order.payment_status, order.total_amount,
                order.notes))
        except Exception as e:
            self.show_error("Error searching orders", str(e))