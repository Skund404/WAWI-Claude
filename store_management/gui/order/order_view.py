# gui/order/order_view.py
"""
OrderView module for displaying and managing orders in the leatherworking store.
Provides a GUI interface for viewing, adding, updating, and deleting orders.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService, OrderStatus
from database.models.order import Order, OrderItem
from di.core import inject

# Configure logger
logger = logging.getLogger(__name__)


class SearchDialog(tk.Toplevel):
    """Dialog for searching orders based on various criteria."""

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
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.columns = columns
        self.search_callback = search_callback
        self._create_widgets()

        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Search field selection
        ttk.Label(self, text="Search in:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.field_var = tk.StringVar(value=self.columns[0] if self.columns else "")
        field_combo = ttk.Combobox(self, textvariable=self.field_var, values=self.columns)
        field_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        # Search term
        ttk.Label(self, text="Search for:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.search_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.search_var).grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        # Search options
        self.exact_match_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Exact match", variable=self.exact_match_var).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5
        )

        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Case sensitive", variable=self.case_sensitive_var).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5
        )

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Search", command=self._perform_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        self.columnconfigure(1, weight=1)

    def _perform_search(self) -> None:
        """Perform the search operation."""
        search_params = {
            "field": self.field_var.get(),
            "term": self.search_var.get(),
            "exact_match": self.exact_match_var.get(),
            "case_sensitive": self.case_sensitive_var.get()
        }

        self.search_callback(search_params)
        self.destroy()


class OrderView(BaseView):
    """View class for displaying and managing orders."""

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.title = "Orders"
        self.order_service = self.get_service(IOrderService)

        # Data storage
        self.orders: List[Dict[str, Any]] = []
        self.current_sort_column = ""
        self.sort_reverse = False
        self.selected_order_id = None

        # Set up UI components
        self.setup_ui()

        # Load initial data
        self.load_data()

        logger.info("OrderView initialized")

    def setup_ui(self) -> None:
        """Set up the user interface components."""
        # Create toolbar frame
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Toolbar buttons
        ttk.Button(toolbar_frame, text="New Order", command=self.create_new_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Edit", command=self.edit_selected_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Delete", command=self.delete_selected_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)

        # Status filter
        ttk.Label(toolbar_frame, text="Status:").pack(side=tk.LEFT, padx=(10, 2))
        self.status_var = tk.StringVar(value="All")
        status_values = ["All"] + [status.name for status in OrderStatus]
        self.status_combo = ttk.Combobox(toolbar_frame, textvariable=self.status_var, values=status_values, width=12)
        self.status_combo.pack(side=tk.LEFT)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_by_status())

        # Orders treeview
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = self._get_columns()
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")

        # Configure columns and headings
        self._setup_treeview()

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack scrollbars and treeview
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Status bar
        self.status_bar = ttk.Label(self, text="Ready", anchor=tk.W, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _get_columns(self) -> List[str]:
        """
        Get the column definitions for the treeview.

        Returns:
            List of column names
        """
        return ["id", "customer_name", "date", "status", "total_items", "total_amount", "payment_status"]

    def _setup_treeview(self) -> None:
        """Configure the treeview columns and headings."""
        columns = self._get_columns()
        column_widths = {
            "id": 50,
            "customer_name": 150,
            "date": 100,
            "status": 100,
            "total_items": 80,
            "total_amount": 100,
            "payment_status": 100
        }

        # Configure columns and headings
        for col in columns:
            width = column_widths.get(col, 100)
            self.tree.column(col, width=width, minwidth=50)
            self.tree.heading(col, text=col.replace('_', ' ').title(),
                              command=lambda _col=col: self._sort_column(_col))

    def load_data(self) -> None:
        """Load order data from the database."""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get orders from service
            orders = self.order_service.get_all_orders()
            self.orders = orders if orders else []

            # Format data for display
            formatted_orders = []
            for order in self.orders:
                formatted_order = {
                    "id": order.get("id", ""),
                    "customer_name": order.get("customer_name", ""),
                    "date": order.get("date", ""),
                    "status": order.get("status", ""),
                    "total_items": order.get("total_items", 0),
                    "total_amount": f"${order.get('total_amount', 0):.2f}",
                    "payment_status": order.get("payment_status", "")
                }
                formatted_orders.append(formatted_order)

            # Insert data into treeview
            for order in formatted_orders:
                self.tree.insert("", "end", values=[order.get(col, "") for col in self._get_columns()])

            # Update status bar
            self.status_bar.config(text=f"Loaded {len(self.orders)} orders")

            logger.info(f"Loaded {len(self.orders)} orders")
        except Exception as e:
            logger.error(f"Error loading orders: {str(e)}")
            messagebox.showerror("Load Error", f"Could not load orders: {str(e)}")
            self.status_bar.config(text="Error loading orders")

    def _sort_column(self, column: str) -> None:
        """
        Sort treeview data based on the selected column.

        Args:
            column: Column name to sort by
        """
        # If already sorting by this column, reverse the order
        if self.current_sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.current_sort_column = column
            self.sort_reverse = False

        # Get all data from treeview
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        # Sort the data
        items.sort(reverse=self.sort_reverse)

        # Rearrange items in the tree
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)

        # Update the heading to indicate sort direction
        for col in self._get_columns():
            if col == column:
                direction = " ↓" if self.sort_reverse else " ↑"
                self.tree.heading(col, text=f"{col.replace('_', ' ').title()}{direction}")
            else:
                self.tree.heading(col, text=col.replace('_', ' ').title())

    def _on_select(self, event: Any) -> None:
        """
        Handle treeview selection events.

        Args:
            event: Event data
        """
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            item_id = self.tree.item(selected_item, "values")[0]
            self.selected_order_id = item_id

    def _on_double_click(self, event: Any) -> None:
        """
        Handle double-click events on treeview items.

        Args:
            event: Event data
        """
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            self.edit_selected_order()

    def create_new_order(self) -> None:
        """Show dialog for creating a new order."""
        # This would typically open a dialog for creating a new order
        # For now, let's just show a message
        messagebox.showinfo("New Order", "Order creation dialog would open here")

    def edit_selected_order(self) -> None:
        """Show dialog for editing the selected order."""
        if not self.selected_order_id:
            messagebox.showinfo("No Selection", "Please select an order to edit")
            return

        # This would typically open a dialog for editing the selected order
        messagebox.showinfo("Edit Order", f"Editing order {self.selected_order_id}")

    def delete_selected_order(self) -> None:
        """Delete the selected order."""
        if not self.selected_order_id:
            messagebox.showinfo("No Selection", "Please select an order to delete")
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete order {self.selected_order_id}?",
            icon=messagebox.WARNING
        )

        if confirm:
            try:
                # Attempt to delete the order
                self.order_service.delete_order(self.selected_order_id)

                # Reload data to reflect changes
                self.load_data()

                # Update status
                self.status_bar.config(text=f"Order {self.selected_order_id} deleted")
                logger.info(f"Order {self.selected_order_id} deleted")
            except Exception as e:
                logger.error(f"Error deleting order: {str(e)}")
                messagebox.showerror("Delete Error", f"Could not delete order: {str(e)}")

    def filter_by_status(self) -> None:
        """Filter orders by the selected status."""
        selected_status = self.status_var.get()

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # If "All" is selected, show all orders
        if selected_status == "All":
            for order in self.orders:
                values = [order.get(col, "") for col in self._get_columns()]
                self.tree.insert("", "end", values=values)
        else:
            # Filter orders by status
            filtered_orders = [
                order for order in self.orders
                if str(order.get("status", "")) == selected_status
            ]

            # Insert filtered orders
            for order in filtered_orders:
                values = [order.get(col, "") for col in self._get_columns()]
                self.tree.insert("", "end", values=values)

        # Update status bar
        item_count = len(self.tree.get_children())
        status_text = f"Showing {item_count} orders"
        if selected_status != "All":
            status_text += f" with status '{selected_status}'"
        self.status_bar.config(text=status_text)

    def show_search_dialog(self) -> None:
        """Show dialog for searching orders."""
        columns = self._get_columns()
        SearchDialog(self, columns, self._perform_search)

    def _perform_search(self, search_params: Dict[str, Any]) -> None:
        """
        Perform search based on the provided parameters.

        Args:
            search_params: Dictionary containing search parameters
        """
        field = search_params.get("field")
        term = search_params.get("term")
        exact_match = search_params.get("exact_match", False)
        case_sensitive = search_params.get("case_sensitive", False)

        if not field or not term:
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter orders based on search criteria
        filtered_orders = []
        for order in self.orders:
            value = str(order.get(field, ""))

            # Apply case sensitivity
            if not case_sensitive:
                value = value.lower()
                term = term.lower()

            # Apply matching strategy
            if exact_match:
                if value == term:
                    filtered_orders.append(order)
            else:
                if term in value:
                    filtered_orders.append(order)

        # Insert filtered orders
        for order in filtered_orders:
            values = [order.get(col, "") for col in self._get_columns()]
            self.tree.insert("", "end", values=values)

        # Update status bar
        item_count = len(filtered_orders)
        self.status_bar.config(text=f"Found {item_count} orders matching '{term}' in '{field}'")