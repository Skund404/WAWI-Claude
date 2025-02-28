# gui/order/order_view.py
"""
Order view implementation for managing orders.
"""
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

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

        # Create widgets
        self._create_widgets()

        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set focus to search entry
        self.search_entry.focus_set()

        # Bind Enter key to search
        self.bind("<Return>", self._on_search)

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Column selection
        ttk.Label(frame, text="Search in:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.column_var = tk.StringVar(value=self.columns[0] if self.columns else "")
        column_combo = ttk.Combobox(
            frame,
            textvariable=self.column_var,
            values=self.columns,
            state="readonly"
        )
        column_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Search text
        ttk.Label(frame, text="Search for:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.search_entry = ttk.Entry(frame, width=30)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Exact match checkbox
        self.exact_match_var = tk.BooleanVar(value=False)
        exact_match_check = ttk.Checkbutton(
            frame,
            text="Exact match",
            variable=self.exact_match_var
        )
        exact_match_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame,
            text="Search",
            command=self._on_search
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

    def _on_search(self, event=None):
        """Handle search button click or Enter key.

        Args:
            event: Event that triggered the search
        """
        column = self.column_var.get()
        search_text = self.search_entry.get()
        exact_match = self.exact_match_var.get()

        if not search_text:
            tk.messagebox.showwarning(
                "Empty Search",
                "Please enter search text."
            )
            return

        self.search_callback(column, search_text, exact_match)
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
        self.logger = logging.getLogger("gui.order.order_view")
        self.logger.info("Initializing Order View")

        self._selected_order_id = None

        self._setup_ui()
        self._load_orders()

    def _setup_ui(self):
        """Set up the user interface components."""
        # Create main layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Toolbar
        self.rowconfigure(1, weight=1)  # Content

        # Create toolbar
        toolbar = ttk.Frame(self, padding=(5, 5, 5, 5))
        toolbar.grid(row=0, column=0, sticky="ew")
        self._create_toolbar(toolbar)

        # Create content frame with split panes
        content = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Order list frame
        orders_frame = ttk.Frame(content, padding=5)
        content.add(orders_frame, weight=1)

        # Order details frame
        details_frame = ttk.Frame(content, padding=5)
        content.add(details_frame, weight=1)

        # Setup order list treeview
        orders_frame.columnconfigure(0, weight=1)
        orders_frame.rowconfigure(0, weight=0)  # Label
        orders_frame.rowconfigure(1, weight=1)  # Treeview

        ttk.Label(orders_frame, text="Orders", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )

        # Create orders treeview
        self.orders_tree = ttk.Treeview(
            orders_frame,
            columns=("id", "reference", "date", "status", "amount"),
            show="headings",
            selectmode="browse"
        )
        self.orders_tree.grid(row=1, column=0, sticky="nsew")

        # Configure treeview columns
        self.orders_tree.heading("id", text="ID")
        self.orders_tree.heading("reference", text="Reference")
        self.orders_tree.heading("date", text="Date")
        self.orders_tree.heading("status", text="Status")
        self.orders_tree.heading("amount", text="Amount")

        self.orders_tree.column("id", width=50, anchor="center")
        self.orders_tree.column("reference", width=100)
        self.orders_tree.column("date", width=100, anchor="center")
        self.orders_tree.column("status", width=100, anchor="center")
        self.orders_tree.column("amount", width=100, anchor="e")

        # Add scrollbar to treeview
        orders_scrollbar = ttk.Scrollbar(
            orders_frame,
            orient=tk.VERTICAL,
            command=self.orders_tree.yview
        )
        orders_scrollbar.grid(row=1, column=1, sticky="ns")
        self.orders_tree.configure(yscrollcommand=orders_scrollbar.set)

        # Bind selection event
        self.orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)
        self.orders_tree.bind("<Double-1>", self._on_order_double_click)

        # Setup filter combobox
        filter_frame = ttk.Frame(orders_frame)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        ttk.Label(filter_frame, text="Filter by status:").pack(side=tk.LEFT, padx=(0, 5))

        self.status_filter = ttk.Combobox(
            filter_frame,
            values=["All"] + [s.name for s in OrderStatus],
            state="readonly",
            width=15
        )
        self.status_filter.set("All")
        self.status_filter.pack(side=tk.LEFT)
        self.status_filter.bind("<<ComboboxSelected>>", self._on_status_filter)

        # Setup order details frame
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=0)  # Label
        details_frame.rowconfigure(1, weight=1)  # Notebook

        ttk.Label(details_frame, text="Order Details", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )

        # Create details notebook
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.grid(row=1, column=0, sticky="nsew")

        # General tab
        general_tab = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(general_tab, text="General")

        # Items tab
        items_tab = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(items_tab, text="Items")

        # Create form in general tab
        general_tab.columnconfigure(1, weight=1)

        row = 0
        for label_text in ["Order ID:", "Reference:", "Customer:", "Date:", "Status:", "Payment Status:",
                           "Total Amount:"]:
            ttk.Label(general_tab, text=label_text).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=5
            )
            value_label = ttk.Label(general_tab, text="")
            value_label.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            setattr(self, f"_{label_text.lower().replace(' ', '_').replace(':', '')}_label", value_label)
            row += 1

        # Notes field
        ttk.Label(general_tab, text="Notes:").grid(
            row=row, column=0, sticky="nw", padx=(0, 10), pady=5
        )

        self._notes_text = tk.Text(general_tab, height=5, width=30, wrap=tk.WORD)
        self._notes_text.grid(row=row, column=1, sticky="nsew", padx=5, pady=5)

        # Add scrollbar to notes
        notes_scrollbar = ttk.Scrollbar(
            general_tab,
            orient=tk.VERTICAL,
            command=self._notes_text.yview
        )
        notes_scrollbar.grid(row=row, column=2, sticky="ns")
        self._notes_text.configure(yscrollcommand=notes_scrollbar.set)

        row += 1
        general_tab.rowconfigure(row, weight=1)  # Push everything up

        # Create items treeview in items tab
        items_tab.columnconfigure(0, weight=1)
        items_tab.rowconfigure(0, weight=1)

        self.items_tree = ttk.Treeview(
            items_tab,
            columns=("id", "product", "quantity", "price", "total"),
            show="headings",
            selectmode="browse"
        )
        self.items_tree.grid(row=0, column=0, sticky="nsew")

        # Configure treeview columns
        self.items_tree.heading("id", text="ID")
        self.items_tree.heading("product", text="Product")
        self.items_tree.heading("quantity", text="Quantity")
        self.items_tree.heading("price", text="Unit Price")
        self.items_tree.heading("total", text="Total")

        self.items_tree.column("id", width=50, anchor="center")
        self.items_tree.column("product", width=200)
        self.items_tree.column("quantity", width=100, anchor="center")
        self.items_tree.column("price", width=100, anchor="e")
        self.items_tree.column("total", width=100, anchor="e")

        # Add scrollbar to treeview
        items_scrollbar = ttk.Scrollbar(
            items_tab,
            orient=tk.VERTICAL,
            command=self.items_tree.yview
        )
        items_scrollbar.grid(row=0, column=1, sticky="ns")
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)

        # Toolbar for items
        items_toolbar = ttk.Frame(items_tab)
        items_toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        ttk.Button(
            items_toolbar,
            text="Add Item",
            command=self._on_add_item
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            items_toolbar,
            text="Edit Item",
            command=self._on_edit_item
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            items_toolbar,
            text="Remove Item",
            command=self._on_remove_item
        ).pack(side=tk.LEFT, padx=5)

    def _create_toolbar(self, parent):
        """Create toolbar with action buttons.

        Args:
            parent: Parent widget for the toolbar
        """
        # New order button
        new_button = ttk.Button(
            parent,
            text="New Order",
            command=self._on_new_order
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))

        # Edit order button
        edit_button = ttk.Button(
            parent,
            text="Edit Order",
            command=self._on_edit_order
        )
        edit_button.pack(side=tk.LEFT, padx=5)

        # Delete order button
        delete_button = ttk.Button(
            parent,
            text="Delete Order",
            command=self._on_delete_order
        )
        delete_button.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(parent, orient=tk.VERTICAL).pack(
            side=tk.LEFT, padx=10, fill=tk.Y
        )

        # Search button
        search_button = ttk.Button(
            parent,
            text="Search",
            command=self._on_search
        )
        search_button.pack(side=tk.LEFT, padx=5)

        # Reset button
        reset_button = ttk.Button(
            parent,
            text="Reset",
            command=self._on_reset
        )
        reset_button.pack(side=tk.LEFT, padx=5)

    def _load_orders(self):
        """Load orders from the database."""
        try:
            order_service = self.get_service(IOrderService)
            orders = order_service.get_all_orders()

            # Clear treeview
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)

            # Populate treeview
            for order in orders:
                self.orders_tree.insert(
                    "",
                    "end",
                    values=(
                        order.get("id", ""),
                        order.get("reference_number", ""),
                        order.get("order_date", ""),
                        order.get("status", ""),
                        f"${order.get('total_amount', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error loading orders: {str(e)}")
            self.show_error("Load Error", f"Failed to load orders: {str(e)}")

    def _load_order_details(self, order_id: int):
        """Load details for the selected order.

        Args:
            order_id: ID of the order to load details for
        """
        try:
            order_service = self.get_service(IOrderService)
            order = order_service.get_order_by_id(order_id)

            if not order:
                return

            # Update general tab labels
            self._order_id_label.config(text=str(order.get("id", "")))
            self._reference_label.config(text=order.get("reference_number", ""))
            self._customer_label.config(text=order.get("customer_name", ""))
            self._date_label.config(text=order.get("order_date", ""))
            self._status_label.config(text=order.get("status", ""))
            self._payment_status_label.config(text=order.get("payment_status", ""))
            self._total_amount_label.config(text=f"${order.get('total_amount', 0):.2f}")

            # Update notes
            self._notes_text.delete(1.0, tk.END)
            self._notes_text.insert(tk.END, order.get("notes", ""))

            # Load order items
            self._load_order_items(order_id)
        except Exception as e:
            self.logger.error(f"Error loading order details: {str(e)}")
            self.show_error("Load Error", f"Failed to load order details: {str(e)}")

    def _load_order_items(self, order_id: int):
        """Load items for the selected order.

        Args:
            order_id: ID of the order to load items for
        """
        try:
            order_service = self.get_service(IOrderService)
            items = order_service.get_order_items(order_id)

            # Clear treeview
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)

            # Populate treeview
            for item in items:
                self.items_tree.insert(
                    "",
                    "end",
                    values=(
                        item.get("id", ""),
                        item.get("product_name", ""),
                        item.get("quantity", 0),
                        f"${item.get('unit_price', 0):.2f}",
                        f"${item.get('total_price', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error loading order items: {str(e)}")
            self.show_error("Load Error", f"Failed to load order items: {str(e)}")

    def _on_order_select(self, event=None):
        """Handle order selection in treeview."""
        selection = self.orders_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.orders_tree.item(item, "values")
        if not values:
            return

        order_id = int(values[0])
        self._selected_order_id = order_id
        self._load_order_details(order_id)

    def _on_order_double_click(self, event=None):
        """Handle double-click on an order to edit it."""
        self._on_edit_order()

    def _on_new_order(self):
        """Handle new order button click."""
        # Open new order dialog
        pass

    def _on_edit_order(self):
        """Handle edit order button click."""
        if not self._selected_order_id:
            self.show_info("No Selection", "Please select an order to edit.")
            return

        # Open edit order dialog
        pass

    def _on_delete_order(self):
        """Handle delete order button click."""
        if not self._selected_order_id:
            self.show_info("No Selection", "Please select an order to delete.")
            return

        if not self.confirm("Confirm Delete", "Are you sure you want to delete this order?"):
            return

        try:
            order_service = self.get_service(IOrderService)
            success = order_service.delete_order(self._selected_order_id)

            if success:
                self.show_info("Success", "Order deleted successfully.")
                self._selected_order_id = None
                self._load_orders()
            else:
                self.show_error("Delete Error", "Failed to delete order.")
        except Exception as e:
            self.logger.error(f"Error deleting order: {str(e)}")
            self.show_error("Delete Error", f"Failed to delete order: {str(e)}")

    def _on_search(self):
        """Handle search button click."""
        columns = ["id", "reference", "customer", "status"]
        SearchDialog(self, columns, self._perform_search)

    def _perform_search(self, field: str, search_text: str, exact_match: bool):
        """Perform search based on criteria.

        Args:
            field: Field to search in
            search_text: Text to search for
            exact_match: Whether to perform exact matching
        """
        try:
            order_service = self.get_service(IOrderService)
            orders = order_service.search_orders(field, search_text, exact_match)

            # Clear treeview
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)

            # Populate treeview
            for order in orders:
                self.orders_tree.insert(
                    "",
                    "end",
                    values=(
                        order.get("id", ""),
                        order.get("reference_number", ""),
                        order.get("order_date", ""),
                        order.get("status", ""),
                        f"${order.get('total_amount', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error searching orders: {str(e)}")
            self.show_error("Search Error", f"Failed to search orders: {str(e)}")

    def _on_status_filter(self, event=None):
        """Handle status filter selection."""
        status = self.status_filter.get()

        try:
            order_service = self.get_service(IOrderService)

            if status == "All":
                orders = order_service.get_all_orders()
            else:
                orders = order_service.get_orders_by_status(status)

            # Clear treeview
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)

            # Populate treeview
            for order in orders:
                self.orders_tree.insert(
                    "",
                    "end",
                    values=(
                        order.get("id", ""),
                        order.get("reference_number", ""),
                        order.get("order_date", ""),
                        order.get("status", ""),
                        f"${order.get('total_amount', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error filtering orders: {str(e)}")
            self.show_error("Filter Error", f"Failed to filter orders: {str(e)}")

    def _on_reset(self):
        """Handle reset button click to clear all filters and reload orders."""
        self.status_filter.set("All")
        self._load_orders()

    def _on_add_item(self):
        """Handle add item button click."""
        if not self._selected_order_id:
            self.show_info("No Order Selected", "Please select an order first.")
            return

        # Open add item dialog
        pass

    def _on_edit_item(self):
        """Handle edit item button click."""
        selection = self.items_tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select an item to edit.")
            return

        # Open edit item dialog
        pass

    def _on_remove_item(self):
        """Handle remove item button click."""
        selection = self.items_tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select an item to remove.")
            return

        item = selection[0]
        values = self.items_tree.item(item, "values")
        if not values:
            return

        item_id = int(values[0])

        if not self.confirm("Confirm Remove", "Are you sure you want to remove this item?"):
            return

        try:
            order_service = self.get_service(IOrderService)
            success = order_service.remove_order_item(self._selected_order_id, item_id)

            if success:
                self.show_info("Success", "Item removed successfully.")
                self._load_order_items(self._selected_order_id)
                # Reload order to update totals
                self._load_order_details(self._selected_order_id)
            else:
                self.show_error("Remove Error", "Failed to remove item.")
        except Exception as e:
            self.logger.error(f"Error removing item: {str(e)}")
            self.show_error("Remove Error", f"Failed to remove item: {str(e)}")

    def order_service(self, service: IOrderService):
        """Set the order service.

        Args:
            service (IOrderService): The order service instance
        """
        self._order_service = service
