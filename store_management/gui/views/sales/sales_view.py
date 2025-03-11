# gui/views/sales/sales_view.py
"""
Sales management view for the leatherworking ERP system.

This view provides a comprehensive interface for managing sales,
including a listing of all sales, dashboard metrics, and actions.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import SaleStatus, PaymentStatus
from gui.base.base_list_view import BaseListView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge


class SalesView(BaseListView):
    """
    Sales management view with dashboard, filtering, and actions.

    This view extends the BaseListView to provide a comprehensive interface
    for listing and managing sales, including metrics and quick actions.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the sales view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                filter_customer_id: ID of customer to filter sales by
                filter_status: Status to filter sales by
                filter_date_range: Date range to filter sales by
        """
        super().__init__(parent)
        self.title = "Sales Management"
        self.icon = "💰"
        self.logger = logging.getLogger(__name__)

        # Store filter parameters
        self.filter_customer_id = kwargs.get("filter_customer_id")
        self.filter_status = kwargs.get("filter_status")
        self.filter_date_range = kwargs.get("filter_date_range")

        # Initialize services
        self.sales_service = get_service("sales_service")
        self.customer_service = get_service("customer_service")

        # Set column definitions for the treeview
        self.columns = (
            "id", "date", "customer", "total", "items",
            "status", "payment_status", "fulfilled"
        )
        self.column_widths = {
            "id": 80,
            "date": 100,
            "customer": 200,
            "total": 100,
            "items": 60,
            "status": 120,
            "payment_status": 120,
            "fulfilled": 80
        }

        # Subscribe to events
        subscribe("sale_created", self.on_sale_updated)
        subscribe("sale_updated", self.on_sale_updated)
        subscribe("sale_status_changed", self.on_sale_updated)
        subscribe("payment_processed", self.on_sale_updated)

        # Build the view
        self.build()

        # Load initial data
        self.load_data()

    def build(self):
        """Build the sales view layout."""
        super().build()

        # Create sales dashboard at the top
        self.create_dashboard(self.content_frame)

        # Add advanced filters to search frame
        self.add_advanced_filters()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        actions_frame = ttk.Frame(self.header)
        actions_frame.pack(side=tk.RIGHT, padx=10)

        ttk.Button(
            actions_frame,
            text="Create Sale",
            command=self.on_add
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Reports",
            command=self.on_generate_reports
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Export",
            command=self.on_export
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Refresh",
            command=self.refresh
        ).pack(side=tk.RIGHT, padx=5)

    def create_dashboard(self, parent):
        """Create sales dashboard with key metrics.

        Args:
            parent: The parent widget
        """
        dashboard_frame = ttk.LabelFrame(parent, text="Sales Dashboard")
        dashboard_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Dashboard layout with metrics and charts
        dashboard_content = ttk.Frame(dashboard_frame)
        dashboard_content.pack(fill=tk.X, padx=10, pady=10)

        # Create metrics section
        metrics_frame = ttk.Frame(dashboard_content)
        metrics_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Sales metrics - first row
        ttk.Label(metrics_frame, text="Total Sales:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0,
                                                                                              sticky=tk.W, padx=5,
                                                                                              pady=2)
        self.total_sales_label = ttk.Label(metrics_frame, text="0")
        self.total_sales_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(metrics_frame, text="Total Revenue:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=2,
                                                                                                sticky=tk.W, padx=5,
                                                                                                pady=2)
        self.total_revenue_label = ttk.Label(metrics_frame, text="$0.00")
        self.total_revenue_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(metrics_frame, text="Avg. Order Value:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4,
                                                                                                   sticky=tk.W, padx=5,
                                                                                                   pady=2)
        self.avg_order_label = ttk.Label(metrics_frame, text="$0.00")
        self.avg_order_label.grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)

        # Sales metrics - second row
        ttk.Label(metrics_frame, text="Today's Sales:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=0,
                                                                                                sticky=tk.W, padx=5,
                                                                                                pady=2)
        self.today_sales_label = ttk.Label(metrics_frame, text="0")
        self.today_sales_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(metrics_frame, text="Monthly Sales:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=2,
                                                                                                sticky=tk.W, padx=5,
                                                                                                pady=2)
        self.monthly_sales_label = ttk.Label(metrics_frame, text="0")
        self.monthly_sales_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(metrics_frame, text="Pending Orders:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=4,
                                                                                                 sticky=tk.W, padx=5,
                                                                                                 pady=2)
        self.pending_orders_label = ttk.Label(metrics_frame, text="0")
        self.pending_orders_label.grid(row=1, column=5, sticky=tk.W, padx=5, pady=2)

        # Status overview section
        status_frame = ttk.LabelFrame(dashboard_content, text="Status Overview")
        status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))

        # Status badges grid
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(padx=10, pady=5)

        # Create status badges
        self.status_counts = {}

        # Row 1: Draft, Confirmed, In Progress
        self.status_counts["draft"] = self._create_status_badge(status_grid, "Draft", "draft", 0, 0)
        self.status_counts["confirmed"] = self._create_status_badge(status_grid, "Confirmed", "confirmed", 0, 1)
        self.status_counts["in_progress"] = self._create_status_badge(status_grid, "In Progress", "in_progress", 0, 2)

        # Row 2: Ready for Pickup, Shipped, Delivered
        self.status_counts["ready_for_pickup"] = self._create_status_badge(status_grid, "Ready", "ready_for_pickup", 1,
                                                                           0)
        self.status_counts["shipped"] = self._create_status_badge(status_grid, "Shipped", "shipped", 1, 1)
        self.status_counts["delivered"] = self._create_status_badge(status_grid, "Delivered", "delivered", 1, 2)

        # Row 3: Completed, Cancelled, Payment Pending
        self.status_counts["completed"] = self._create_status_badge(status_grid, "Completed", "completed", 2, 0)
        self.status_counts["cancelled"] = self._create_status_badge(status_grid, "Cancelled", "cancelled", 2, 1)
        self.status_counts["pending"] = self._create_status_badge(status_grid, "Payment Pending", "pending", 2, 2)

    def _create_status_badge(self, parent, label_text, status_value, row, col):
        """Create a status badge with counter.

        Args:
            parent: The parent widget
            label_text: The text to display on the badge
            status_value: The status value for styling
            row: Grid row
            col: Grid column

        Returns:
            Label widget for the count
        """
        # Create frame for badge and count
        badge_frame = ttk.Frame(parent)
        badge_frame.grid(row=row, column=col, padx=5, pady=5)

        # Create badge
        StatusBadge(badge_frame, label_text, status_value).pack(side=tk.LEFT)

        # Create count label
        count_label = ttk.Label(badge_frame, text="0")
        count_label.pack(side=tk.LEFT, padx=(5, 0))

        return count_label

    def create_treeview(self, parent):
        """Create the treeview for displaying sales data.

        Args:
            parent: The parent widget
        """
        # Create a frame for the treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create the treeview
        self.treeview = ttk.Treeview(
            tree_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse"
        )

        # Configure column headings and widths
        self.treeview.heading("id", text="Sale ID", command=lambda: self.on_sort("id", "asc"))
        self.treeview.heading("date", text="Date", command=lambda: self.on_sort("date", "desc"))
        self.treeview.heading("customer", text="Customer", command=lambda: self.on_sort("customer", "asc"))
        self.treeview.heading("total", text="Total", command=lambda: self.on_sort("total", "desc"))
        self.treeview.heading("items", text="Items", command=lambda: self.on_sort("items", "desc"))
        self.treeview.heading("status", text="Status", command=lambda: self.on_sort("status", "asc"))
        self.treeview.heading("payment_status", text="Payment", command=lambda: self.on_sort("payment_status", "asc"))
        self.treeview.heading("fulfilled", text="Fulfilled", command=lambda: self.on_sort("fulfilled", "asc"))

        for col, width in self.column_widths.items():
            self.treeview.column(col, width=width, minwidth=50)

        # Create vertical scrollbar
        yscrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.treeview.configure(yscrollcommand=yscrollbar.set)

        # Create horizontal scrollbar
        xscrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.treeview.configure(xscrollcommand=xscrollbar.set)

        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind double-click to view sale
        self.treeview.bind("<Double-1>", lambda e: self.on_view())

        # Bind selection to update action buttons
        self.treeview.bind("<<TreeviewSelect>>", self.on_select)

    def add_advanced_filters(self):
        """Add advanced search filters to the search frame."""
        # Get the search frame from the base class
        search_frame = self.search_frame

        # Add additional filters
        filters_frame = ttk.LabelFrame(search_frame, text="Advanced Filters")
        filters_frame.pack(fill=tk.X, padx=10, pady=5, after=search_frame.winfo_children()[0])

        # First row - Status and Payment Status
        row1_frame = ttk.Frame(filters_frame)
        row1_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(row1_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(row1_frame, textvariable=self.status_var, width=15, state="readonly")
        status_values = ["All"] + [s.value.replace("_", " ").title() for s in SaleStatus]
        status_combo["values"] = status_values
        status_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Payment Status:").pack(side=tk.LEFT, padx=(15, 5))
        self.payment_status_var = tk.StringVar(value="All")
        payment_status_combo = ttk.Combobox(row1_frame, textvariable=self.payment_status_var, width=15,
                                            state="readonly")
        payment_status_values = ["All"] + [p.value.replace("_", " ").title() for p in PaymentStatus]
        payment_status_combo["values"] = payment_status_values
        payment_status_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Customer:").pack(side=tk.LEFT, padx=(15, 5))
        self.customer_var = tk.StringVar()
        customer_entry = ttk.Entry(row1_frame, textvariable=self.customer_var, width=20)
        customer_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            row1_frame,
            text="...",
            width=2,
            command=self.select_customer
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Store customer ID separately from display name
        self.customer_id_var = tk.StringVar()
        if self.filter_customer_id:
            self.customer_id_var.set(str(self.filter_customer_id))
            # Load customer name
            try:
                customer = self.customer_service.get_customer(self.filter_customer_id)
                if customer:
                    name = ""
                    if hasattr(customer, 'first_name') and customer.first_name:
                        name += customer.first_name
                    if hasattr(customer, 'last_name') and customer.last_name:
                        if name:
                            name += " "
                        name += customer.last_name
                    self.customer_var.set(name)
            except Exception as e:
                self.logger.error(f"Error loading customer name: {e}")

        # Second row - Date ranges
        row2_frame = ttk.Frame(filters_frame)
        row2_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(row2_frame, text="Date From:").pack(side=tk.LEFT, padx=(0, 5))
        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(row2_frame, textvariable=self.date_from_var, width=12)
        date_from_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            row2_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.date_from_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(row2_frame, text="To:").pack(side=tk.LEFT, padx=(5, 5))
        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(row2_frame, textvariable=self.date_to_var, width=12)
        date_to_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            row2_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.date_to_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(row2_frame, text="Total Min:").pack(side=tk.LEFT, padx=(15, 5))
        self.total_min_var = tk.StringVar()
        total_min_entry = ttk.Entry(row2_frame, textvariable=self.total_min_var, width=10)
        total_min_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(row2_frame, text="Total Max:").pack(side=tk.LEFT, padx=(5, 5))
        self.total_max_var = tk.StringVar()
        total_max_entry = ttk.Entry(row2_frame, textvariable=self.total_max_var, width=10)
        total_max_entry.pack(side=tk.LEFT, padx=5)

        # Add apply filters button
        ttk.Button(
            filters_frame,
            text="Apply Filters",
            command=self.on_apply_filters
        ).pack(side=tk.RIGHT, padx=10, pady=5)

        ttk.Button(
            filters_frame,
            text="Clear Filters",
            command=self.on_clear_filters
        ).pack(side=tk.RIGHT, padx=5, pady=5)

    def create_item_actions(self, parent):
        """Create action buttons for selected sales.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.LabelFrame(parent, text="Sale Actions")
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            actions_frame,
            text="View Details",
            command=self.on_view,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.view_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Edit Sale",
            command=self.on_edit,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.edit_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Update Status",
            command=self.on_update_status,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.update_status_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Process Payment",
            command=self.on_process_payment,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.process_payment_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Generate Invoice",
            command=self.on_generate_invoice,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.generate_invoice_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Print Receipt",
            command=self.on_print_receipt,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.print_receipt_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Cancel Sale",
            command=self.on_cancel_sale,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.cancel_btn = actions_frame.winfo_children()[-1]

    def add_context_menu_items(self, menu):
        """Add sales-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_command(label="View Details", command=self.on_view)
        menu.add_command(label="Edit Sale", command=self.on_edit)
        menu.add_separator()
        menu.add_command(label="Update Status", command=self.on_update_status)
        menu.add_command(label="Process Payment", command=self.on_process_payment)
        menu.add_separator()
        menu.add_command(label="Generate Invoice", command=self.on_generate_invoice)
        menu.add_command(label="Print Receipt", command=self.on_print_receipt)
        menu.add_separator()
        menu.add_command(label="Cancel Sale", command=self.on_cancel_sale)

    def load_data(self):
        """Load sales data into the treeview based on current filters and pagination."""
        try:
            # Clear existing items
            for item in self.treeview.get_children():
                self.treeview.delete(item)

            # Get current page and search criteria
            offset = (self.current_page - 1) * self.page_size

            # Get search criteria
            search_text = self.search_var.get() if hasattr(self, 'search_var') else ""

            # Collect filter criteria
            filters = {}

            # Apply provided filter parameter
            if self.filter_customer_id:
                filters['customer_id'] = self.filter_customer_id
            elif hasattr(self, 'customer_id_var') and self.customer_id_var.get():
                filters['customer_id'] = int(self.customer_id_var.get())

            if self.filter_status:
                filters['status'] = self.filter_status
            elif hasattr(self, 'status_var') and self.status_var.get() != "All":
                filters['status'] = self.status_var.get().replace(" ", "_").lower()

            if hasattr(self, 'payment_status_var') and self.payment_status_var.get() != "All":
                filters['payment_status'] = self.payment_status_var.get().replace(" ", "_").lower()

            # Date ranges
            if hasattr(self, 'date_from_var') and self.date_from_var.get():
                try:
                    filters['date_from'] = datetime.datetime.strptime(self.date_from_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid date format for date_from: {self.date_from_var.get()}")

            if hasattr(self, 'date_to_var') and self.date_to_var.get():
                try:
                    filters['date_to'] = datetime.datetime.strptime(self.date_to_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid date format for date_to: {self.date_to_var.get()}")

            # Total amount range
            if hasattr(self, 'total_min_var') and self.total_min_var.get():
                try:
                    filters['total_min'] = float(self.total_min_var.get())
                except ValueError:
                    self.logger.warning(f"Invalid number format for total_min: {self.total_min_var.get()}")

            if hasattr(self, 'total_max_var') and self.total_max_var.get():
                try:
                    filters['total_max'] = float(self.total_max_var.get())
                except ValueError:
                    self.logger.warning(f"Invalid number format for total_max: {self.total_max_var.get()}")

            # Get the current sort field and direction
            sort_field = getattr(self, 'sort_field', 'date')
            sort_direction = getattr(self, 'sort_direction', 'desc')

            # Get total count
            total_count = self.sales_service.count_sales(
                search_text=search_text,
                filters=filters
            )

            # Calculate total pages
            total_pages = (total_count + self.page_size - 1) // self.page_size

            # Update pagination display
            self.update_pagination_display(total_pages)

            # Get sales for current page
            sales = self.sales_service.search_sales(
                search_text=search_text,
                filters=filters,
                sort_field=sort_field,
                sort_direction=sort_direction,
                offset=offset,
                limit=self.page_size
            )

            # Insert sales into treeview
            for sale in sales:
                values = self.extract_item_values(sale)
                item_id = str(sale.id) if hasattr(sale, 'id') else "0"

                self.treeview.insert('', 'end', iid=item_id, values=values)

                # Apply status styling
                if hasattr(sale, 'status') and sale.status:
                    status_style = get_status_style(sale.status.value)
                    tag_name = f"status_{sale.status.value}"

                    # Configure tag with status color if not already configured
                    if tag_name not in self.treeview.tag_configure():
                        self.treeview.tag_configure(tag_name, background=status_style.get('bg_light'))

                    # Apply tag to the row
                    self.treeview.item(item_id, tags=(tag_name,))

            # Update dashboard metrics
            self.update_dashboard_metrics()

        except Exception as e:
            self.logger.error(f"Error loading sales data: {e}")
            messagebox.showerror("Error", f"Failed to load sales data: {str(e)}")

    def extract_item_values(self, item):
        """Extract values from a sale item for display in the treeview.

        Args:
            item: The sale item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Extract sale values
        item_id = item.id if hasattr(item, 'id') else ""

        # Format date
        date = ""
        if hasattr(item, 'created_at') and item.created_at:
            date = item.created_at.strftime("%Y-%m-%d")

        # Format customer name
        customer = ""
        if hasattr(item, 'customer') and item.customer:
            customer_obj = item.customer
            name_parts = []
            if hasattr(customer_obj, 'first_name') and customer_obj.first_name:
                name_parts.append(customer_obj.first_name)
            if hasattr(customer_obj, 'last_name') and customer_obj.last_name:
                name_parts.append(customer_obj.last_name)
            customer = " ".join(name_parts)

        # Format total
        total = "$0.00"
        if hasattr(item, 'total_amount'):
            total = f"${item.total_amount:.2f}"

        # Format items count
        items_count = "0"
        if hasattr(item, 'items') and item.items:
            items_count = str(len(item.items))
        elif hasattr(item, 'item_count'):
            items_count = str(item.item_count)

        # Format status
        status = ""
        if hasattr(item, 'status') and item.status:
            status = item.status.value.replace("_", " ").title()

        # Format payment status
        payment_status = ""
        if hasattr(item, 'payment_status') and item.payment_status:
            payment_status = item.payment_status.value.replace("_", " ").title()

        # Format fulfilled flag
        fulfilled = "No"
        if hasattr(item, 'fulfilled') and item.fulfilled:
            fulfilled = "Yes"
        elif hasattr(item, 'status') and item.status:
            if item.status.value in ["completed", "delivered"]:
                fulfilled = "Yes"

        return (
            item_id, date, customer, total, items_count,
            status, payment_status, fulfilled
        )

    def update_dashboard_metrics(self):
        """Update sales dashboard metrics."""
        try:
            # Get sales metrics
            metrics = self.sales_service.get_sales_metrics()

            # Update total sales metrics
            if 'total_sales' in metrics:
                self.total_sales_label.configure(text=str(metrics['total_sales']))

            if 'total_revenue' in metrics:
                self.total_revenue_label.configure(text=f"${metrics['total_revenue']:.2f}")

            if 'avg_order_value' in metrics:
                self.avg_order_label.configure(text=f"${metrics['avg_order_value']:.2f}")

            # Update time-based metrics
            if 'today_sales' in metrics:
                self.today_sales_label.configure(text=str(metrics['today_sales']))

            if 'monthly_sales' in metrics:
                self.monthly_sales_label.configure(text=str(metrics['monthly_sales']))

            if 'pending_orders' in metrics:
                self.pending_orders_label.configure(text=str(metrics['pending_orders']))

            # Update status counts
            if 'status_counts' in metrics:
                status_counts = metrics['status_counts']
                for status, count in status_counts.items():
                    if status in self.status_counts:
                        self.status_counts[status].configure(text=str(count))

        except Exception as e:
            self.logger.error(f"Error updating sales metrics: {e}")

    def on_select(self, event=None):
        """Handle sale selection in the treeview."""
        selected_id = self.treeview.focus()

        # Enable/disable action buttons based on selection
        if selected_id:
            self.view_btn.configure(state=tk.NORMAL)
            self.edit_btn.configure(state=tk.NORMAL)
            self.update_status_btn.configure(state=tk.NORMAL)
            self.process_payment_btn.configure(state=tk.NORMAL)
            self.generate_invoice_btn.configure(state=tk.NORMAL)
            self.print_receipt_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.NORMAL)

            # Get sale status to determine if some actions should be disabled
            item = self.treeview.item(selected_id)
            status = ""
            payment_status = ""
            if item and "values" in item and len(item["values"]) > 5:
                status = item["values"][5].lower().replace(" ", "_")
                payment_status = item["values"][6].lower().replace(" ", "_")

            # Disable edit for completed sales
            if status in ["completed", "cancelled"]:
                self.edit_btn.configure(state=tk.DISABLED)

            # Disable cancel for completed or cancelled sales
            if status in ["completed", "cancelled"]:
                self.cancel_btn.configure(state=tk.DISABLED)

            # Disable payment processing for paid sales
            if payment_status in ["paid", "refunded"]:
                self.process_payment_btn.configure(state=tk.DISABLED)
        else:
            self.view_btn.configure(state=tk.DISABLED)
            self.edit_btn.configure(state=tk.DISABLED)
            self.update_status_btn.configure(state=tk.DISABLED)
            self.process_payment_btn.configure(state=tk.DISABLED)
            self.generate_invoice_btn.configure(state=tk.DISABLED)
            self.print_receipt_btn.configure(state=tk.DISABLED)
            self.cancel_btn.configure(state=tk.DISABLED)

    def on_apply_filters(self):
        """Handle apply filters button click."""
        # Reset to first page and reload data
        self.current_page = 1
        self.load_data()

    def on_clear_filters(self):
        """Handle clear filters button click."""
        # Reset filter values
        if hasattr(self, 'status_var'):
            self.status_var.set("All")

        if hasattr(self, 'payment_status_var'):
            self.payment_status_var.set("All")

        if hasattr(self, 'customer_var'):
            self.customer_var.set("")
            self.customer_id_var.set("")

        if hasattr(self, 'date_from_var'):
            self.date_from_var.set("")

        if hasattr(self, 'date_to_var'):
            self.date_to_var.set("")

        if hasattr(self, 'total_min_var'):
            self.total_min_var.set("")

        if hasattr(self, 'total_max_var'):
            self.total_max_var.set("")

        # Reset search
        if hasattr(self, 'search_var'):
            self.search_var.set("")

        # Reset filter parameters
        self.filter_customer_id = None
        self.filter_status = None
        self.filter_date_range = None

        # Reset to first page and reload data
        self.current_page = 1
        self.load_data()

    def on_add(self):
        """Handle add new sale action."""
        # Navigate to sale details view for new sale
        self.parent.master.show_view(
            "sales_details",
            view_data={"create_new": True}
        )

    def on_view(self):
        """Handle view sale action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to view.")
            return

        # Navigate to sale details view
        self.parent.master.show_view(
            "sales_details",
            view_data={"sale_id": int(selected_id), "readonly": True}
        )

    def on_edit(self):
        """Handle edit sale action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to edit.")
            return

        # Check if sale can be edited (status checks)
        item = self.treeview.item(selected_id)
        status = ""
        if item and "values" in item and len(item["values"]) > 5:
            status = item["values"][5].lower().replace(" ", "_")

        if status in ["completed", "cancelled"]:
            messagebox.showwarning("Cannot Edit", "Completed or cancelled sales cannot be edited.")
            return

        # Navigate to sale details view for editing
        self.parent.master.show_view(
            "sales_details",
            view_data={"sale_id": int(selected_id)}
        )

    def on_update_status(self):
        """Handle update status action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to update status.")
            return

        # Get current status
        item = self.treeview.item(selected_id)
        current_status = ""
        if item and "values" in item and len(item["values"]) > 5:
            current_status = item["values"][5]

        # Create status change dialog
        dialog = tk.Toplevel(self)
        dialog.title("Update Sale Status")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x200")

        # Status selection
        ttk.Label(dialog, text="Current Status:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        current_status_label = ttk.Label(dialog, text=current_status)
        current_status_label.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="New Status:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        new_status_var = tk.StringVar()
        status_combo = ttk.Combobox(dialog, textvariable=new_status_var, width=20, state="readonly")
        status_values = [s.name for s in SaleStatus]
        status_combo["values"] = status_values
        status_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Notes
        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        notes_var = tk.StringVar()
        notes_entry = ttk.Entry(dialog, textvariable=notes_var, width=30)
        notes_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        def on_status_change():
            # Validate input
            if not new_status_var.get():
                messagebox.showwarning("Input Error", "Please select a new status.", parent=dialog)
                return

            try:
                # Update sale status
                result = self.sales_service.update_sale_status(
                    int(selected_id),
                    new_status_var.get(),
                    notes=notes_var.get()
                )

                if result:
                    # Close dialog
                    dialog.destroy()

                    # Refresh data
                    self.load_data()

                    # Show success message
                    messagebox.showinfo("Success", "Sale status has been updated.")

                    # Publish event
                    publish("sale_status_changed", {
                        "sale_id": int(selected_id),
                        "new_status": new_status_var.get()
                    })

            except Exception as e:
                self.logger.error(f"Error updating sale status: {e}")
                messagebox.showerror("Update Error", f"Failed to update sale status: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Update",
            command=on_status_change
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_process_payment(self):
        """Handle process payment action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to process payment.")
            return

        # Check payment status
        item = self.treeview.item(selected_id)
        payment_status = ""
        if item and "values" in item and len(item["values"]) > 6:
            payment_status = item["values"][6].lower().replace(" ", "_")

        if payment_status == "paid":
            messagebox.showinfo("Already Paid", "This sale has already been paid in full.")
            return

        if payment_status == "refunded":
            messagebox.showwarning("Refunded", "This sale has been refunded and cannot accept payments.")
            return

        # Get sale total
        total = "0.00"
        if item and "values" in item and len(item["values"]) > 3:
            total = item["values"][3].replace("$", "")

        # Create payment dialog
        dialog = tk.Toplevel(self)
        dialog.title("Process Payment")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("500x350")

        # Payment details
        ttk.Label(dialog, text="Sale ID:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=selected_id).grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Total Amount:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=f"${total}").grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Payment Status:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=payment_status.replace("_", " ").title()).grid(row=2, column=1, padx=10, pady=5,
                                                                              sticky=tk.W)

        # Payment method
        ttk.Label(dialog, text="Payment Method:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        method_var = tk.StringVar(value="Credit Card")
        method_combo = ttk.Combobox(dialog, textvariable=method_var, width=20, state="readonly")
        method_combo["values"] = ["Credit Card", "Debit Card", "Cash", "Check", "Bank Transfer", "PayPal", "Other"]
        method_combo.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

        # Amount
        ttk.Label(dialog, text="Amount:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        amount_var = tk.StringVar(value=total)
        amount_entry = ttk.Entry(dialog, textvariable=amount_var, width=15)
        amount_entry.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)

        # Reference number
        ttk.Label(dialog, text="Reference #:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        reference_var = tk.StringVar()
        reference_entry = ttk.Entry(dialog, textvariable=reference_var, width=20)
        reference_entry.grid(row=5, column=1, padx=10, pady=5, sticky=tk.W)

        # Payment date
        ttk.Label(dialog, text="Payment Date:").grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
        date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        date_frame = ttk.Frame(dialog)
        date_frame.grid(row=6, column=1, padx=10, pady=5, sticky=tk.W)

        date_entry = ttk.Entry(date_frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT)

        ttk.Button(
            date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(date_var)
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Notes
        ttk.Label(dialog, text="Notes:").grid(row=7, column=0, padx=10, pady=5, sticky=tk.NW)
        notes_text = tk.Text(dialog, width=30, height=3)
        notes_text.grid(row=7, column=1, padx=10, pady=5, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)

        def on_process_payment():
            # Validate input
            if not amount_var.get():
                messagebox.showwarning("Input Error", "Please enter a payment amount.", parent=dialog)
                return

            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    messagebox.showwarning("Input Error", "Payment amount must be greater than zero.", parent=dialog)
                    return
            except ValueError:
                messagebox.showwarning("Input Error", "Payment amount must be a number.", parent=dialog)
                return

            try:
                # Gather payment data
                payment_data = {
                    "method": method_var.get(),
                    "amount": float(amount_var.get()),
                    "reference": reference_var.get(),
                    "notes": notes_text.get("1.0", tk.END).strip()
                }

                # Parse payment date
                if date_var.get():
                    try:
                        payment_data["date"] = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d")
                    except ValueError:
                        self.logger.warning(f"Invalid date format for payment date: {date_var.get()}")

                # Process payment
                result = self.sales_service.process_payment(
                    int(selected_id),
                    payment_data
                )

                if result:
                    # Close dialog
                    dialog.destroy()

                    # Refresh data
                    self.load_data()

                    # Show success message
                    messagebox.showinfo("Success", "Payment has been processed successfully.")

                    # Publish event
                    publish("payment_processed", {
                        "sale_id": int(selected_id),
                        "amount": float(amount_var.get())
                    })

            except Exception as e:
                self.logger.error(f"Error processing payment: {e}")
                messagebox.showerror("Payment Error", f"Failed to process payment: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Process Payment",
            command=on_process_payment
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_generate_invoice(self):
        """Handle generate invoice action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to generate invoice.")
            return

        try:
            # Generate invoice
            result = self.sales_service.generate_invoice(int(selected_id))

            if result:
                # Show success message
                messagebox.showinfo("Success", "Invoice has been generated successfully.")

                # Ask if user wants to view/print the invoice
                if messagebox.askyesno("View Invoice", "Do you want to view the generated invoice?"):
                    # This would open the invoice file
                    messagebox.showinfo("View Invoice", "Invoice viewer would open with the generated invoice.")

        except Exception as e:
            self.logger.error(f"Error generating invoice: {e}")
            messagebox.showerror("Invoice Error", f"Failed to generate invoice: {str(e)}")

    def on_print_receipt(self):
        """Handle print receipt action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to print receipt.")
            return

        try:
            # Print receipt
            result = self.sales_service.print_receipt(int(selected_id))

            if result:
                # Show success message
                messagebox.showinfo("Success", "Receipt has been sent to the printer.")

        except Exception as e:
            self.logger.error(f"Error printing receipt: {e}")
            messagebox.showerror("Print Error", f"Failed to print receipt: {str(e)}")

    def on_cancel_sale(self):
        """Handle cancel sale action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to cancel.")
            return

        # Check if sale can be cancelled
        item = self.treeview.item(selected_id)
        status = ""
        if item and "values" in item and len(item["values"]) > 5:
            status = item["values"][5].lower().replace(" ", "_")

        if status in ["completed", "cancelled"]:
            messagebox.showwarning("Cannot Cancel", "Completed or already cancelled sales cannot be cancelled.")
            return

        # Confirm cancellation
        if not messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel this sale?"):
            return

        # Create cancellation dialog
        dialog = tk.Toplevel(self)
        dialog.title("Cancel Sale")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x200")

        # Reason selection
        ttk.Label(dialog, text="Cancellation Reason:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        reason_var = tk.StringVar()
        reason_combo = ttk.Combobox(dialog, textvariable=reason_var, width=25, state="readonly")
        reason_values = [
            "Customer Request",
            "Payment Issue",
            "Inventory Issue",
            "Shipping Issue",
            "Pricing Error",
            "Duplicate Order",
            "Other"
        ]
        reason_combo["values"] = reason_values
        reason_combo.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # Notes
        ttk.Label(dialog, text="Notes:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        notes_text = tk.Text(dialog, width=30, height=4)
        notes_text.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        def on_confirm_cancel():
            # Validate input
            if not reason_var.get():
                messagebox.showwarning("Input Error", "Please select a cancellation reason.", parent=dialog)
                return

            try:
                # Cancel sale
                result = self.sales_service.cancel_sale(
                    int(selected_id),
                    reason=reason_var.get(),
                    notes=notes_text.get("1.0", tk.END).strip()
                )

                if result:
                    # Close dialog
                    dialog.destroy()

                    # Refresh data
                    self.load_data()

                    # Show success message
                    messagebox.showinfo("Success", "Sale has been cancelled.")

                    # Publish event
                    publish("sale_cancelled", {
                        "sale_id": int(selected_id)
                    })

            except Exception as e:
                self.logger.error(f"Error cancelling sale: {e}")
                messagebox.showerror("Cancel Error", f"Failed to cancel sale: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Confirm Cancel",
            command=on_confirm_cancel
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Back",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_generate_reports(self):
        """Handle generate reports button click."""
        # Create reports dialog
        dialog = tk.Toplevel(self)
        dialog.title("Sales Reports")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x350")

        # Report options frame
        options_frame = ttk.LabelFrame(dialog, text="Available Reports")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Report types
        report_var = tk.StringVar(value="sales_summary")
        ttk.Radiobutton(
            options_frame,
            text="Sales Summary Report",
            variable=report_var,
            value="sales_summary"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Sales by Customer Report",
            variable=report_var,
            value="sales_by_customer"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Sales by Product Report",
            variable=report_var,
            value="sales_by_product"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Sales Trend Analysis",
            variable=report_var,
            value="sales_trend"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Payment Status Report",
            variable=report_var,
            value="payment_status"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Tax Summary Report",
            variable=report_var,
            value="tax_summary"
        ).pack(anchor=tk.W, padx=10, pady=5)

        # Date range
        date_frame = ttk.LabelFrame(dialog, text="Date Range")
        date_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(date_frame, text="From:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        from_date_var = tk.StringVar()
        from_date_frame = ttk.Frame(date_frame)
        from_date_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        from_date_entry = ttk.Entry(from_date_frame, textvariable=from_date_var, width=12)
        from_date_entry.pack(side=tk.LEFT)

        ttk.Button(
            from_date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(from_date_var)
        ).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(date_frame, text="To:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        to_date_var = tk.StringVar()
        to_date_frame = ttk.Frame(date_frame)
        to_date_frame.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        to_date_entry = ttk.Entry(to_date_frame, textvariable=to_date_var, width=12)
        to_date_entry.pack(side=tk.LEFT)

        ttk.Button(
            to_date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(to_date_var)
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Format options
        format_frame = ttk.LabelFrame(dialog, text="Output Format")
        format_frame.pack(fill=tk.X, padx=10, pady=5)

        format_var = tk.StringVar(value="pdf")
        ttk.Radiobutton(
            format_frame,
            text="PDF",
            variable=format_var,
            value="pdf"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Radiobutton(
            format_frame,
            text="Excel",
            variable=format_var,
            value="excel"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Radiobutton(
            format_frame,
            text="CSV",
            variable=format_var,
            value="csv"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def generate_report():
            report_type = report_var.get()
            output_format = format_var.get()

            # Prepare date range
            date_range = {}
            if from_date_var.get():
                try:
                    date_range['from_date'] = datetime.datetime.strptime(from_date_var.get(), "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date", "From Date format is invalid.", parent=dialog)
                    return

            if to_date_var.get():
                try:
                    date_range['to_date'] = datetime.datetime.strptime(to_date_var.get(), "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date", "To Date format is invalid.", parent=dialog)
                    return

            # This would integrate with a reporting system
            # For this implementation, we'll just show a message
            messagebox.showinfo(
                "Generate Report",
                f"Report '{report_type}' would be generated in {output_format.upper()} format.",
                parent=dialog
            )
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="Generate",
            command=generate_report
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def on_export(self):
        """Handle export button click."""
        # Create file save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            # Export data
            result = self.sales_service.export_sales(file_path)

            if result:
                # Show success message
                messagebox.showinfo("Export Success", f"Sales data has been exported to {file_path}.")

        except Exception as e:
            self.logger.error(f"Error exporting sales data: {e}")
            messagebox.showerror("Export Error", f"Failed to export sales data: {str(e)}")

    def select_customer(self):
        """Open customer selection dialog."""
        # Create customer selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Customer")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("600x400")

        # Search frame
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            search_frame,
            text="Search",
            command=lambda: search_customers()
        ).pack(side=tk.LEFT, padx=5)

        # Customer list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview for customers
        columns = ("id", "name", "email", "phone", "status")
        customers_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)

        customers_tree.heading("id", text="ID")
        customers_tree.heading("name", text="Name")
        customers_tree.heading("email", text="Email")
        customers_tree.heading("phone", text="Phone")
        customers_tree.heading("status", text="Status")

        customers_tree.column("id", width=50)
        customers_tree.column("name", width=200)
        customers_tree.column("email", width=150)
        customers_tree.column("phone", width=100)
        customers_tree.column("status", width=80)

        # Add scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=customers_tree.yview)
        customers_tree.configure(yscrollcommand=tree_scroll.set)

        customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Select",
            command=lambda: select_customer()
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="New Customer",
            command=lambda: create_new_customer()
        ).pack(side=tk.LEFT, padx=5)

        def search_customers():
            """Search customers based on search text."""
            try:
                # Clear existing items
                for item in customers_tree.get_children():
                    customers_tree.delete(item)

                # Search customers
                customers = self.customer_service.search_customers(search_text=search_var.get())

                # Insert customers
                for customer in customers:
                    # Format name
                    name = ""
                    if hasattr(customer, 'first_name') and customer.first_name:
                        name += customer.first_name
                    if hasattr(customer, 'last_name') and customer.last_name:
                        if name:
                            name += " "
                        name += customer.last_name

                    # Format status
                    status = ""
                    if hasattr(customer, 'status') and customer.status:
                        status = customer.status.value.replace("_", " ").title()

                    customer_id = customer.id if hasattr(customer, 'id') else ""
                    email = customer.email if hasattr(customer, 'email') else ""
                    phone = customer.phone if hasattr(customer, 'phone') else ""

                    customers_tree.insert('', 'end', iid=str(customer_id), values=(
                        customer_id, name, email, phone, status
                    ))

            except Exception as e:
                self.logger.error(f"Error searching customers: {e}")
                messagebox.showerror("Search Error", f"Failed to search customers: {str(e)}", parent=dialog)

        def select_customer():
            """Select the highlighted customer."""
            selected_id = customers_tree.focus()
            if not selected_id:
                messagebox.showwarning("No Selection", "Please select a customer.", parent=dialog)
                return

            # Get customer name
            item = customers_tree.item(selected_id)
            customer_name = item["values"][1] if item and "values" in item and len(item["values"]) > 1 else ""

            # Update customer filter
            self.customer_id_var.set(selected_id)
            self.customer_var.set(customer_name)

            # Close dialog
            dialog.destroy()

        def create_new_customer():
            """Create a new customer."""
            # Close dialog and navigate to customer details view
            dialog.destroy()
            self.parent.master.show_view(
                "customer_details",
                view_data={"create_new": True}
            )

        # Perform initial search
        search_customers()

        # Set focus to search entry
        search_entry.focus_set()

    def on_sale_updated(self, data):
        """Handle sale updated event.

        Args:
            data: Event data including sale_id
        """
        # Refresh data to show the updated sale
        self.load_data()

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create a simple date picker dialog
        date_dialog = tk.Toplevel(self)
        date_dialog.title("Select Date")
        date_dialog.transient(self)
        date_dialog.grab_set()

        # Create a calendar (simplified version - production would use a better calendar)
        cal_frame = ttk.Frame(date_dialog, padding=10)
        cal_frame.pack(fill=tk.BOTH, expand=True)

        # Current year and month selection
        current_date = datetime.datetime.now()
        if date_var.get():
            try:
                current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d")
            except ValueError:
                pass

        year_var = tk.StringVar(value=str(current_date.year))
        month_var = tk.StringVar(value=str(current_date.month))

        header_frame = ttk.Frame(cal_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Year:").pack(side=tk.LEFT)
        ttk.Spinbox(
            header_frame,
            from_=2000,
            to=2050,
            textvariable=year_var,
            width=5
        ).pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(header_frame, text="Month:").pack(side=tk.LEFT)
        month_spin = ttk.Spinbox(
            header_frame,
            from_=1,
            to=12,
            textvariable=month_var,
            width=3
        )
        month_spin.pack(side=tk.LEFT, padx=5)

        # Simple calendar grid (would use a proper calendar widget in production)
        def select_date(day):
            year = int(year_var.get())
            month = int(month_var.get())
            date_var.set(f"{year:04d}-{month:02d}-{day:02d}")
            date_dialog.destroy()

        days_frame = ttk.Frame(cal_frame)
        days_frame.pack(fill=tk.BOTH, expand=True)

        # Button for each day (simplified)
        for day in range(1, 32):
            day_btn = ttk.Button(
                days_frame,
                text=str(day),
                width=3,
                command=lambda d=day: select_date(d)
            )
            row = (day - 1) // 7
            col = (day - 1) % 7
            day_btn.grid(row=row, column=col, padx=2, pady=2)

        # Cancel button
        ttk.Button(
            cal_frame,
            text="Cancel",
            command=date_dialog.destroy
        ).pack(pady=10)

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("sale_created", self.on_sale_updated)
        unsubscribe("sale_updated", self.on_sale_updated)
        unsubscribe("sale_status_changed", self.on_sale_updated)
        unsubscribe("payment_processed", self.on_sale_updated)

        # Call parent destroy
        super().destroy()