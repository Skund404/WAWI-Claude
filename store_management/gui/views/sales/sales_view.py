# gui/views/sales/sales_view.py
"""
Sales list view and dashboard for the leatherworking application.

This view provides a comprehensive interface for managing sales records,
including filtering, detailed metrics, and various sales-related actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from typing import Any, Dict, List, Optional, Tuple
import logging

# Import GUI components
from gui.base.base_list_view import BaseListView
from gui.theme import COLORS, get_status_style
from gui.widgets.status_badge import StatusBadge

# Import services and utilities
from gui.utils.service_access import get_service
from gui.utils.event_bus import publish, subscribe, unsubscribe

# Import model enums
from database.models.enums import SaleStatus, PaymentStatus


class SalesView(BaseListView):
    """
    Sales view for displaying and managing sales records.

    This view extends BaseListView to provide a comprehensive interface
    for sales management, including a dashboard, filtering options,
    and various sales-related actions.
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize the sales view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                filter_customer_id: ID of customer to filter sales by
                filter_status: Status to filter sales by
                filter_date_range: Date range to filter sales by
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing SalesView")

        # Extract filter parameters
        self.filter_customer_id = kwargs.pop('filter_customer_id', None)
        self.filter_status = kwargs.pop('filter_status', None)
        self.filter_date_range = kwargs.pop('filter_date_range', None)

        # Initialize base class
        super().__init__(parent)

        # Initialize services
        self.sales_service = get_service("sales_service")
        self.customer_service = get_service("customer_service")

        # Set up event subscriptions
        subscribe("sale_updated", self.on_sale_updated)
        subscribe("sale_status_changed", self.on_sale_updated)

        # Initialize additional instance variables
        self.status_labels = {}
        self.dashboard_metrics = {}
        self.chart_canvas = None

        # Set view title
        self.title = "Sales Management"

    def build(self):
        """Build the sales view layout."""
        self.logger.debug("Building SalesView layout")

        # Create the header with title and action buttons
        self.create_header()

        # Create a frame for the main content
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create dashboard at the top
        self.create_dashboard(content_frame)

        # Create treeview in the middle
        self.create_treeview(content_frame)

        # Add advanced filters to search frame
        self.add_advanced_filters()

        # Create action buttons at the bottom
        self.create_item_actions(content_frame)

        # Create pagination controls
        self.create_pagination(content_frame)

        # Load initial data
        self.load_data()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Add button for generating reports
        self.add_header_button("Generate Reports", self.on_generate_reports, icon="chart-bar")

        # Add button for exporting sales data
        self.add_header_button("Export Data", self.on_export, icon="download")

        # Add separator
        ttk.Separator(self.header_actions_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Add button for creating a new sale
        self.add_header_button("Add Sale", self.on_add, icon="plus", primary=True)

    def create_dashboard(self, parent):
        """
        Create sales dashboard with key metrics.

        Args:
            parent: The parent widget
        """
        # Create dashboard frame
        dashboard_frame = ttk.Frame(parent, style="Card.TFrame")
        dashboard_frame.pack(fill=tk.X, pady=10, padx=5)

        # Create title for dashboard
        ttk.Label(
            dashboard_frame,
            text="Sales Dashboard",
            style="CardTitle.TLabel"
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Create metrics section
        metrics_frame = ttk.Frame(dashboard_frame)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)

        # Configure grid columns
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)
        metrics_frame.columnconfigure(3, weight=1)

        # Create KPI metrics - first row
        self.dashboard_metrics["today_sales"] = self._create_metric_widget(
            metrics_frame, "Today's Sales", "$0.00", row=0, column=0
        )

        self.dashboard_metrics["week_sales"] = self._create_metric_widget(
            metrics_frame, "This Week", "$0.00", row=0, column=1
        )

        self.dashboard_metrics["month_sales"] = self._create_metric_widget(
            metrics_frame, "This Month", "$0.00", row=0, column=2
        )

        self.dashboard_metrics["year_sales"] = self._create_metric_widget(
            metrics_frame, "This Year", "$0.00", row=0, column=3
        )

        # Create status counts - second row
        status_frame = ttk.Frame(dashboard_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create status badges
        status_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.status_labels["quote"] = self._create_status_badge(
            status_frame, "Quote Requests", SaleStatus.QUOTE_REQUEST.value, 0
        )

        self.status_labels["design"] = self._create_status_badge(
            status_frame, "Design Phase", SaleStatus.DESIGN_APPROVAL.value, 1
        )

        self.status_labels["production"] = self._create_status_badge(
            status_frame, "In Production", SaleStatus.IN_PRODUCTION.value, 2
        )

        self.status_labels["ready"] = self._create_status_badge(
            status_frame, "Ready", SaleStatus.READY_FOR_PICKUP.value, 3
        )

        self.status_labels["completed"] = self._create_status_badge(
            status_frame, "Completed", SaleStatus.COMPLETED.value, 4
        )

        # Create charts section
        chart_frame = ttk.Frame(dashboard_frame)
        chart_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        # Create chart canvas
        self.chart_canvas = tk.Canvas(chart_frame, height=150, bg=COLORS["bg_color"])
        self.chart_canvas.pack(fill=tk.X, pady=5)

        # Label for chart
        ttk.Label(
            chart_frame,
            text="Sales Trend (Last 30 Days)",
            style="Small.TLabel"
        ).pack(anchor=tk.W)

    def _create_metric_widget(self, parent, title, value, row, column):
        """
        Create a metric widget with title and value.

        Args:
            parent: The parent widget
            title: The title for the metric
            value: The initial value for the metric
            row: Grid row
            column: Grid column

        Returns:
            Dictionary with references to the widget labels
        """
        frame = ttk.Frame(parent, style="MetricCard.TFrame")
        frame.grid(row=row, column=column, padx=5, pady=5, sticky=tk.NSEW)

        # Create title label
        title_label = ttk.Label(frame, text=title, style="MetricTitle.TLabel")
        title_label.pack(anchor=tk.W, padx=10, pady=(10, 0))

        # Create value label
        value_label = ttk.Label(frame, text=value, style="MetricValue.TLabel")
        value_label.pack(anchor=tk.W, padx=10, pady=(0, 10))

        return {
            "frame": frame,
            "title": title_label,
            "value": value_label
        }

    def _create_status_badge(self, parent, label_text, status_value, col):
        """
        Create a status badge with counter.

        Args:
            parent: The parent widget
            label_text: The text to display on the badge
            status_value: The status value for styling
            col: Grid column

        Returns:
            Label widget for the count
        """
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=col, padx=5, pady=5, sticky=tk.NSEW)

        # Create the status badge
        status_style = get_status_style(status_value)
        badge = StatusBadge(
            frame,
            text=label_text,
            bg_color=status_style.get("bg", COLORS["accent_light"]),
            fg_color=status_style.get("fg", COLORS["text_dark"])
        )
        badge.pack(anchor=tk.CENTER, pady=(0, 5))

        # Create count label
        count_label = ttk.Label(frame, text="0", style="LargeValue.TLabel")
        count_label.pack(anchor=tk.CENTER)

        return count_label

    def create_treeview(self, parent):
        """
        Create the treeview for displaying sales data.

        Args:
            parent: The parent widget
        """
        # Call the base class method to create the treeview
        super().create_treeview(parent)

        # Configure columns
        self.treeview.configure(columns=(
            "id", "date", "customer", "amount", "status", "payment_status", "items", "notes"
        ))

        # Set column headings
        self.treeview.heading("id", text="Sale ID")
        self.treeview.heading("date", text="Date")
        self.treeview.heading("customer", text="Customer")
        self.treeview.heading("amount", text="Amount")
        self.treeview.heading("status", text="Status")
        self.treeview.heading("payment_status", text="Payment")
        self.treeview.heading("items", text="Items")
        self.treeview.heading("notes", text="Notes")

        # Set column widths
        self.treeview.column("id", width=80)
        self.treeview.column("date", width=120)
        self.treeview.column("customer", width=200)
        self.treeview.column("amount", width=100)
        self.treeview.column("status", width=150)
        self.treeview.column("payment_status", width=100)
        self.treeview.column("items", width=80)
        self.treeview.column("notes", width=200)

    def add_advanced_filters(self):
        """Add advanced search filters to the search frame."""
        if not hasattr(self, 'search_frame'):
            self.logger.warning("Search frame not available for adding filters")
            return

        # Add status filter
        status_frame = ttk.Frame(self.search_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=["All"] + [s.value for s in SaleStatus]
        )
        status_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Add payment status filter
        payment_frame = ttk.Frame(self.search_frame)
        payment_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(payment_frame, text="Payment:").pack(side=tk.LEFT, padx=5)

        self.payment_var = tk.StringVar(value="All")
        payment_combo = ttk.Combobox(
            payment_frame,
            textvariable=self.payment_var,
            values=["All"] + [s.value for s in PaymentStatus]
        )
        payment_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Add date range filter
        date_frame = ttk.Frame(self.search_frame)
        date_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(date_frame, text="Date Range:").pack(side=tk.LEFT, padx=5)

        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(date_frame, textvariable=self.date_from_var, width=12)
        date_from_entry.pack(side=tk.LEFT, padx=5)

        date_from_btn = ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(self.date_from_var)
        )
        date_from_btn.pack(side=tk.LEFT)

        ttk.Label(date_frame, text="to").pack(side=tk.LEFT, padx=5)

        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(date_frame, textvariable=self.date_to_var, width=12)
        date_to_entry.pack(side=tk.LEFT, padx=5)

        date_to_btn = ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(self.date_to_var)
        )
        date_to_btn.pack(side=tk.LEFT)

        # Add customer filter
        customer_frame = ttk.Frame(self.search_frame)
        customer_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(customer_frame, text="Customer:").pack(side=tk.LEFT, padx=5)

        self.customer_id_var = tk.StringVar()
        self.customer_name_var = tk.StringVar()

        customer_entry = ttk.Entry(
            customer_frame,
            textvariable=self.customer_name_var,
            state="readonly"
        )
        customer_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        customer_btn = ttk.Button(
            customer_frame,
            text="Select",
            command=self.select_customer
        )
        customer_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(
            customer_frame,
            text="Clear",
            command=lambda: [
                self.customer_id_var.set(""),
                self.customer_name_var.set("")
            ]
        )
        clear_btn.pack(side=tk.LEFT)

        # Add amount range filter
        amount_frame = ttk.Frame(self.search_frame)
        amount_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(amount_frame, text="Amount Range:").pack(side=tk.LEFT, padx=5)

        self.amount_min_var = tk.StringVar()
        amount_min_entry = ttk.Entry(amount_frame, textvariable=self.amount_min_var, width=10)
        amount_min_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(amount_frame, text="to").pack(side=tk.LEFT, padx=5)

        self.amount_max_var = tk.StringVar()
        amount_max_entry = ttk.Entry(amount_frame, textvariable=self.amount_max_var, width=10)
        amount_max_entry.pack(side=tk.LEFT, padx=5)

        # Set initial filter values if provided
        if self.filter_customer_id:
            self.customer_id_var.set(str(self.filter_customer_id))
            try:
                customer = self.customer_service.get_customer(self.filter_customer_id)
                self.customer_name_var.set(f"{customer.first_name} {customer.last_name}")
            except Exception as e:
                self.logger.error(f"Error loading customer for filter: {e}")

        if self.filter_status:
            self.status_var.set(self.filter_status)

        if self.filter_date_range:
            if isinstance(self.filter_date_range, tuple) and len(self.filter_date_range) == 2:
                start_date, end_date = self.filter_date_range
                if start_date:
                    self.date_from_var.set(start_date.strftime("%Y-%m-%d"))
                if end_date:
                    self.date_to_var.set(end_date.strftime("%Y-%m-%d"))

    def create_item_actions(self, parent):
        """
        Create action buttons for selected sales.

        Args:
            parent: The parent widget
        """
        # Call the base class method to create the item actions frame
        super().create_item_actions(parent)

        # Add additional sales-specific action buttons
        self.add_item_action_buttons(self.item_actions_frame)

    def add_context_menu_items(self, menu):
        """
        Add sales-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        # Call the base class method to add standard context menu items
        super().add_context_menu_items(menu)

        # Add separator
        menu.add_separator()

        # Add sales-specific context menu items
        menu.add_command(label="Update Status", command=self.on_update_status)
        menu.add_command(label="Process Payment", command=self.on_process_payment)
        menu.add_command(label="Generate Invoice", command=self.on_generate_invoice)
        menu.add_command(label="Print Receipt", command=self.on_print_receipt)

        # Add cancel sale option
        menu.add_separator()
        menu.add_command(label="Cancel Sale", command=self.on_cancel_sale)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons for sales.

        Args:
            parent: The parent widget for the buttons
        """
        # Add update status button
        self.update_status_btn = ttk.Button(
            parent,
            text="Update Status",
            command=self.on_update_status,
            state=tk.DISABLED
        )
        self.update_status_btn.pack(side=tk.LEFT, padx=5)

        # Add process payment button
        self.process_payment_btn = ttk.Button(
            parent,
            text="Process Payment",
            command=self.on_process_payment,
            state=tk.DISABLED
        )
        self.process_payment_btn.pack(side=tk.LEFT, padx=5)

        # Add generate invoice button
        self.generate_invoice_btn = ttk.Button(
            parent,
            text="Generate Invoice",
            command=self.on_generate_invoice,
            state=tk.DISABLED
        )
        self.generate_invoice_btn.pack(side=tk.LEFT, padx=5)

        # Add print receipt button
        self.print_receipt_btn = ttk.Button(
            parent,
            text="Print Receipt",
            command=self.on_print_receipt,
            state=tk.DISABLED
        )
        self.print_receipt_btn.pack(side=tk.LEFT, padx=5)

    def extract_item_values(self, item):
        """
        Extract values from a sale item for display in the treeview.

        Args:
            item: The sale item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Extract sale date
        sale_date = ""
        if hasattr(item, "created_at") and item.created_at:
            sale_date = item.created_at.strftime("%Y-%m-%d %H:%M")

        # Extract customer name
        customer_name = ""
        if hasattr(item, "customer") and item.customer:
            customer_name = f"{item.customer.first_name} {item.customer.last_name}"

        # Extract sale amount
        amount = "$0.00"
        if hasattr(item, "total_amount") and item.total_amount is not None:
            amount = f"${item.total_amount:.2f}"

        # Extract status
        status = ""
        if hasattr(item, "status") and item.status:
            status = item.status

        # Extract payment status
        payment_status = ""
        if hasattr(item, "payment_status") and item.payment_status:
            payment_status = item.payment_status

        # Extract item count
        item_count = 0
        if hasattr(item, "items") and item.items:
            item_count = len(item.items)

        # Extract notes
        notes = ""
        if hasattr(item, "notes") and item.notes:
            notes = item.notes

        return [
            getattr(item, "id", ""),
            sale_date,
            customer_name,
            amount,
            status,
            payment_status,
            item_count,
            notes
        ]

    def load_data(self):
        """Load sales data into the treeview based on current filters and pagination."""
        try:
            # Clear existing items
            self.treeview.delete(*self.treeview.get_children())

            # Get current page and search criteria
            offset = (self.current_page - 1) * self.page_size

            # Build filter criteria
            filters = {}

            # Add search text
            search_text = self.search_var.get() if hasattr(self, 'search_var') else ""

            # Add status filter
            if hasattr(self, 'status_var') and self.status_var.get() != "All":
                filters['status'] = self.status_var.get()

            # Add payment status filter
            if hasattr(self, 'payment_var') and self.payment_var.get() != "All":
                filters['payment_status'] = self.payment_var.get()

            # Add customer filter
            if hasattr(self, 'customer_id_var') and self.customer_id_var.get():
                filters['customer_id'] = int(self.customer_id_var.get())

            # Add date range filter
            date_from = None
            date_to = None

            if hasattr(self, 'date_from_var') and self.date_from_var.get():
                try:
                    date_from = datetime.datetime.strptime(self.date_from_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid from date format: {self.date_from_var.get()}")

            if hasattr(self, 'date_to_var') and self.date_to_var.get():
                try:
                    # Set time to end of day for inclusive filtering
                    date_to = datetime.datetime.strptime(self.date_to_var.get(), "%Y-%m-%d")
                    date_to = date_to.replace(hour=23, minute=59, second=59)
                except ValueError:
                    self.logger.warning(f"Invalid to date format: {self.date_to_var.get()}")

            if date_from or date_to:
                filters['date_range'] = (date_from, date_to)

            # Add amount range filter
            amount_min = None
            amount_max = None

            if hasattr(self, 'amount_min_var') and self.amount_min_var.get():
                try:
                    amount_min = float(self.amount_min_var.get())
                except ValueError:
                    self.logger.warning(f"Invalid minimum amount: {self.amount_min_var.get()}")

            if hasattr(self, 'amount_max_var') and self.amount_max_var.get():
                try:
                    amount_max = float(self.amount_max_var.get())
                except ValueError:
                    self.logger.warning(f"Invalid maximum amount: {self.amount_max_var.get()}")

            if amount_min is not None or amount_max is not None:
                filters['amount_range'] = (amount_min, amount_max)

            # Get total count for pagination
            total_count = self.sales_service.count_sales(
                search_text=search_text,
                filters=filters
            )

            # Update pagination display
            total_pages = (total_count + self.page_size - 1) // self.page_size
            self.update_pagination_display(total_pages)

            # Get sales for current page
            sales = self.sales_service.search_sales(
                search_text=search_text,
                filters=filters,
                offset=offset,
                limit=self.page_size,
                include_customer=True,
                include_items=True
            )

            # Insert sales into treeview
            for sale in sales:
                values = self.extract_item_values(sale)
                item_id = str(getattr(sale, "id", 0))
                self.treeview.insert('', 'end', iid=item_id, values=values)

            # Update dashboard metrics
            self.update_dashboard_metrics()

        except Exception as e:
            self.logger.error(f"Error loading sales data: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load sales data: {str(e)}")

    def update_dashboard_metrics(self):
        """Update sales dashboard metrics."""
        try:
            # Get current date for time-based metrics
            now = datetime.datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Get week start (Monday)
            week_start = today - datetime.timedelta(days=today.weekday())

            # Get month start
            month_start = today.replace(day=1)

            # Get year start
            year_start = today.replace(month=1, day=1)

            # Get sales metrics
            metrics = self.sales_service.get_sales_metrics()

            # Update dashboard widgets
            if "today_sales" in self.dashboard_metrics:
                today_value = metrics.get("today_sales", 0)
                self.dashboard_metrics["today_sales"]["value"].config(
                    text=f"${today_value:.2f}"
                )

            if "week_sales" in self.dashboard_metrics:
                week_value = metrics.get("week_sales", 0)
                self.dashboard_metrics["week_sales"]["value"].config(
                    text=f"${week_value:.2f}"
                )

            if "month_sales" in self.dashboard_metrics:
                month_value = metrics.get("month_sales", 0)
                self.dashboard_metrics["month_sales"]["value"].config(
                    text=f"${month_value:.2f}"
                )

            if "year_sales" in self.dashboard_metrics:
                year_value = metrics.get("year_sales", 0)
                self.dashboard_metrics["year_sales"]["value"].config(
                    text=f"${year_value:.2f}"
                )

            # Update status counts
            status_counts = metrics.get("status_counts", {})

            for status_key, label in self.status_labels.items():
                count = 0

                if status_key == "quote":
                    count = status_counts.get(SaleStatus.QUOTE_REQUEST.value, 0)
                elif status_key == "design":
                    count = status_counts.get(SaleStatus.DESIGN_APPROVAL.value, 0)
                elif status_key == "production":
                    count = status_counts.get(SaleStatus.IN_PRODUCTION.value, 0)
                elif status_key == "ready":
                    count = status_counts.get(SaleStatus.READY_FOR_PICKUP.value, 0)
                elif status_key == "completed":
                    count = status_counts.get(SaleStatus.COMPLETED.value, 0)

                label.config(text=str(count))

            # Update chart if available
            if self.chart_canvas:
                self._draw_sales_trend_chart(metrics.get("daily_sales", []))

        except Exception as e:
            self.logger.error(f"Error updating dashboard metrics: {e}", exc_info=True)

    def _draw_sales_trend_chart(self, daily_sales):
        """
        Draw sales trend chart on the canvas.

        Args:
            daily_sales: List of (date, amount) tuples for the last 30 days
        """
        # Clear the canvas
        self.chart_canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.chart_canvas.winfo_width()
        canvas_height = self.chart_canvas.winfo_height()

        # If the canvas isn't fully rendered yet, use default dimensions
        if canvas_width < 10:
            canvas_width = 600

        # Skip if no data
        if not daily_sales:
            self.chart_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="No sales data available",
                fill=COLORS["text_secondary"]
            )
            return

        # Sort by date
        daily_sales.sort(key=lambda x: x[0])

        # Extract dates and amounts
        dates = [d[0] for d in daily_sales]
        amounts = [d[1] for d in daily_sales]

        # Find min and max values
        max_amount = max(amounts) if amounts else 0
        min_amount = min(amounts) if amounts else 0

        # Add 10% padding to max for visibility
        max_amount = max_amount * 1.1 if max_amount > 0 else 10

        # Calculate scaling factors
        x_scale = canvas_width / (len(dates) + 1)
        y_scale = (canvas_height - 40) / max_amount  # Leave room for labels

        # Draw axes
        self.chart_canvas.create_line(
            30, canvas_height - 30,  # x-axis start
                canvas_width - 10, canvas_height - 30,  # x-axis end
            fill=COLORS["text_secondary"]
        )

        self.chart_canvas.create_line(
            30, 10,  # y-axis start
            30, canvas_height - 30,  # y-axis end
            fill=COLORS["text_secondary"]
        )

        # Draw data points and connect with lines
        points = []
        for i, (date, amount) in enumerate(daily_sales):
            # Calculate x,y coordinates
            x = 30 + (i + 1) * x_scale
            y = canvas_height - 30 - (amount * y_scale)

            # Store point
            points.append((x, y))

            # Draw point
            self.chart_canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=COLORS["accent"],
                outline=""
            )

            # Draw date label (every 5th day)
            if i % 5 == 0:
                self.chart_canvas.create_text(
                    x, canvas_height - 15,
                    text=date.strftime("%d"),
                    fill=COLORS["text_secondary"],
                    font=("Arial", 8)
                )

        # Connect points with lines
        if len(points) > 1:
            for i in range(len(points) - 1):
                self.chart_canvas.create_line(
                    points[i][0], points[i][1],
                    points[i + 1][0], points[i + 1][1],
                    fill=COLORS["accent"],
                    width=2
                )

    def on_search(self, criteria):
        """
        Handle search.

        Args:
            criteria: Dictionary of search criteria
        """
        self.logger.debug(f"Search criteria: {criteria}")

        # Reset to first page when searching
        self.current_page = 1

        # Apply search by reloading data
        self.load_data()

    def on_apply_filters(self):
        """Handle apply filters button click."""
        # Reset to first page when filtering
        self.current_page = 1

        # Apply filters by reloading data
        self.load_data()

    def on_clear_filters(self):
        """Handle clear filters button click."""
        # Reset all filter variables
        if hasattr(self, 'status_var'):
            self.status_var.set("All")

        if hasattr(self, 'payment_var'):
            self.payment_var.set("All")

        if hasattr(self, 'date_from_var'):
            self.date_from_var.set("")

        if hasattr(self, 'date_to_var'):
            self.date_to_var.set("")

        if hasattr(self, 'customer_id_var'):
            self.customer_id_var.set("")

        if hasattr(self, 'customer_name_var'):
            self.customer_name_var.set("")

        if hasattr(self, 'amount_min_var'):
            self.amount_min_var.set("")

        if hasattr(self, 'amount_max_var'):
            self.amount_max_var.set("")

        # Reset to first page
        self.current_page = 1

        # Reload data with cleared filters
        self.load_data()

    def on_select(self):
        """Handle item selection."""
        # Call base class handler
        super().on_select()

        # Get selected item ID
        selected_id = self.get_selected_id()

        # Enable/disable action buttons based on selection
        state = tk.NORMAL if selected_id else tk.DISABLED

        if hasattr(self, 'update_status_btn'):
            self.update_status_btn.config(state=state)

        if hasattr(self, 'process_payment_btn'):
            self.process_payment_btn.config(state=state)

        if hasattr(self, 'generate_invoice_btn'):
            self.generate_invoice_btn.config(state=state)

        if hasattr(self, 'print_receipt_btn'):
            self.print_receipt_btn.config(state=state)

    def on_add(self):
        """Handle add new sale action."""
        self.logger.info("Adding new sale")

        # Open order creation wizard
        # The actual implementation will need to be added
        # when order_creation_wizard.py is implemented
        messagebox.showinfo(
            "Feature Not Implemented",
            "The order creation wizard will be implemented in the next phase."
        )

    def on_view(self):
        """Handle view sale action."""
        self.logger.info("Viewing sale details")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to view.")
            return

        # Navigate to sales details view
        # This will be implemented when sales_details_view.py is created
        messagebox.showinfo(
            "Feature Not Implemented",
            "The sales details view will be implemented in the next phase."
        )

    def on_edit(self):
        """Handle edit sale action."""
        self.logger.info("Editing sale")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to edit.")
            return

        # Navigate to sales details view in edit mode
        # This will be implemented when sales_details_view.py is created
        messagebox.showinfo(
            "Feature Not Implemented",
            "The sales details edit view will be implemented in the next phase."
        )

    def on_update_status(self):
        """Handle update status action."""
        self.logger.info("Updating sale status")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to update.")
            return

        try:
            # Get the sale
            sale = self.sales_service.get_sale(selected_id, include_items=False)

            # Create status update dialog
            dialog = tk.Toplevel(self)
            dialog.title("Update Sale Status")
            dialog.transient(self)
            dialog.grab_set()

            # Center dialog
            dialog.geometry("400x300")
            dialog.resizable(False, False)

            # Status selection
            ttk.Label(dialog, text="Current Status:").pack(anchor=tk.W, padx=20, pady=(20, 5))
            ttk.Label(dialog, text=sale.status, style="Value.TLabel").pack(anchor=tk.W, padx=20)

            ttk.Label(dialog, text="New Status:").pack(anchor=tk.W, padx=20, pady=(20, 5))

            status_var = tk.StringVar(value=sale.status)
            status_combo = ttk.Combobox(
                dialog,
                textvariable=status_var,
                values=[s.value for s in SaleStatus]
            )
            status_combo.pack(fill=tk.X, padx=20, pady=5)

            # Notes entry
            ttk.Label(dialog, text="Notes:").pack(anchor=tk.W, padx=20, pady=(10, 5))

            notes_var = tk.StringVar()
            notes_entry = ttk.Entry(dialog, textvariable=notes_var, width=50)
            notes_entry.pack(fill=tk.X, padx=20, pady=5)

            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=20, pady=20)

            ttk.Button(
                button_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                button_frame,
                text="Update",
                style="Accent.TButton",
                command=lambda: self.on_status_change(
                    selected_id,
                    status_var.get(),
                    notes_var.get(),
                    dialog
                )
            ).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            self.logger.error(f"Error preparing status update: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to prepare status update: {str(e)}")

    def on_status_change(self, sale_id, new_status, notes, dialog):
        """
        Handle status change confirmation.

        Args:
            sale_id: ID of the sale to update
            new_status: New status value
            notes: Status change notes
            dialog: Dialog to close on success
        """
        try:
            # Validate new status
            if not new_status:
                messagebox.showwarning("Input Error", "Please select a new status.")
                return

            # Update the sale status
            self.sales_service.update_sale_status(
                sale_id=sale_id,
                new_status=new_status,
                notes=notes
            )

            # Close the dialog
            dialog.destroy()

            # Refresh the view
            self.refresh()

            # Show success message
            messagebox.showinfo("Success", "Sale status updated successfully.")

        except Exception as e:
            self.logger.error(f"Error updating sale status: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to update sale status: {str(e)}")

    def on_process_payment(self):
        """Handle process payment action."""
        self.logger.info("Processing payment")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to process payment.")
            return

        # Open payment dialog
        # This will be implemented when payment_dialog.py is created
        messagebox.showinfo(
            "Feature Not Implemented",
            "The payment processing dialog will be implemented in the next phase."
        )

    def on_generate_invoice(self):
        """Handle generate invoice action."""
        self.logger.info("Generating invoice")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to generate an invoice.")
            return

        # Open invoice generator
        # This will be implemented when invoice_generator.py is created
        messagebox.showinfo(
            "Feature Not Implemented",
            "The invoice generator will be implemented in the next phase."
        )

    def on_print_receipt(self):
        """Handle print receipt action."""
        self.logger.info("Printing receipt")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to print receipt.")
            return

        # Generate and print receipt
        # This will be implemented as part of the invoice generator
        messagebox.showinfo(
            "Feature Not Implemented",
            "The receipt printing feature will be implemented in the next phase."
        )

    def on_cancel_sale(self):
        """Handle cancel sale action."""
        self.logger.info("Cancelling sale")

        # Get selected sale ID
        selected_id = self.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to cancel.")
            return

        # Confirm cancellation
        if not messagebox.askyesno(
                "Confirm Cancellation",
                "Are you sure you want to cancel this sale? This action cannot be undone."
        ):
            return

        try:
            # Cancel the sale
            self.sales_service.cancel_sale(selected_id)

            # Refresh the view
            self.refresh()

            # Show success message
            messagebox.showinfo("Success", "Sale has been cancelled.")

        except Exception as e:
            self.logger.error(f"Error cancelling sale: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to cancel sale: {str(e)}")

    def on_generate_reports(self):
        """Handle generate reports button click."""
        self.logger.info("Opening report generator")

        # Create report options dialog
        dialog = tk.Toplevel(self)
        dialog.title("Generate Sales Report")
        dialog.transient(self)
        dialog.grab_set()

        # Center dialog
        dialog.geometry("400x400")
        dialog.resizable(False, False)

        # Report type selection
        ttk.Label(dialog, text="Report Type:", style="Heading.TLabel").pack(anchor=tk.W, padx=20, pady=(20, 10))

        report_type_var = tk.StringVar(value="sales_summary")

        report_types = [
            ("Sales Summary", "sales_summary"),
            ("Sales by Customer", "sales_by_customer"),
            ("Sales by Product", "sales_by_product"),
            ("Sales by Status", "sales_by_status"),
            ("Sales Trend", "sales_trend"),
        ]

        for text, value in report_types:
            ttk.Radiobutton(
                dialog,
                text=text,
                variable=report_type_var,
                value=value
            ).pack(anchor=tk.W, padx=30, pady=2)

        # Date range
        ttk.Label(dialog, text="Date Range:", style="Heading.TLabel").pack(anchor=tk.W, padx=20, pady=(20, 10))

        date_frame = ttk.Frame(dialog)
        date_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT)

        date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(date_frame, textvariable=date_from_var, width=12)
        date_from_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(date_from_var)
        ).pack(side=tk.LEFT)

        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(10, 0))

        date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(date_frame, textvariable=date_to_var, width=12)
        date_to_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(date_to_var)
        ).pack(side=tk.LEFT)

        # Output format
        ttk.Label(dialog, text="Output Format:", style="Heading.TLabel").pack(anchor=tk.W, padx=20, pady=(20, 10))

        format_var = tk.StringVar(value="pdf")

        ttk.Radiobutton(
            dialog,
            text="PDF",
            variable=format_var,
            value="pdf"
        ).pack(anchor=tk.W, padx=30, pady=2)

        ttk.Radiobutton(
            dialog,
            text="Excel",
            variable=format_var,
            value="excel"
        ).pack(anchor=tk.W, padx=30, pady=2)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Generate",
            style="Accent.TButton",
            command=lambda: self.generate_report(
                report_type_var.get(),
                date_from_var.get(),
                date_to_var.get(),
                format_var.get(),
                dialog
            )
        ).pack(side=tk.RIGHT, padx=5)

    def generate_report(self, report_type, date_from, date_to, output_format, dialog):
        """
        Generate sales report.

        Args:
            report_type: Type of report to generate
            date_from: Start date for report data
            date_to: End date for report data
            output_format: Output format (pdf, excel)
            dialog: Dialog to close on success
        """
        try:
            # Parse dates
            from_date = None
            to_date = None

            if date_from:
                try:
                    from_date = datetime.datetime.strptime(date_from, "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date", "Please enter valid From date (YYYY-MM-DD).")
                    return

            if date_to:
                try:
                    to_date = datetime.datetime.strptime(date_to, "%Y-%m-%d")
                    # Set to end of day
                    to_date = to_date.replace(hour=23, minute=59, second=59)
                except ValueError:
                    messagebox.showwarning("Invalid Date", "Please enter valid To date (YYYY-MM-DD).")
                    return

            # Choose save location
            file_extension = ".pdf" if output_format == "pdf" else ".xlsx"
            filename = f"sales_report_{report_type}{file_extension}"

            save_path = filedialog.asksaveasfilename(
                defaultextension=file_extension,
                filetypes=[
                    ("PDF files", "*.pdf") if output_format == "pdf" else ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                initialfile=filename
            )

            if not save_path:
                return  # User cancelled

            # Generate report
            self.sales_service.generate_report(
                report_type=report_type,
                date_range=(from_date, to_date),
                output_format=output_format,
                output_path=save_path
            )

            # Close dialog
            dialog.destroy()

            # Show success message
            messagebox.showinfo(
                "Report Generated",
                f"Sales report has been generated and saved to:\n{save_path}"
            )

        except Exception as e:
            self.logger.error(f"Error generating report: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def on_export(self):
        """Handle export button click."""
        self.logger.info("Exporting sales data")

        try:
            # Choose save location
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                initialfile="sales_export.csv"
            )

            if not save_path:
                return  # User cancelled

            # Build filter criteria for export
            filters = {}

            # Add search text
            search_text = self.search_var.get() if hasattr(self, 'search_var') else ""

            # Add status filter
            if hasattr(self, 'status_var') and self.status_var.get() != "All":
                filters['status'] = self.status_var.get()

            # Add payment status filter
            if hasattr(self, 'payment_var') and self.payment_var.get() != "All":
                filters['payment_status'] = self.payment_var.get()

            # Add customer filter
            if hasattr(self, 'customer_id_var') and self.customer_id_var.get():
                filters['customer_id'] = int(self.customer_id_var.get())

            # Add date range filter
            date_from = None
            date_to = None

            if hasattr(self, 'date_from_var') and self.date_from_var.get():
                try:
                    date_from = datetime.datetime.strptime(self.date_from_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid from date format: {self.date_from_var.get()}")

            if hasattr(self, 'date_to_var') and self.date_to_var.get():
                try:
                    # Set time to end of day for inclusive filtering
                    date_to = datetime.datetime.strptime(self.date_to_var.get(), "%Y-%m-%d")
                    date_to = date_to.replace(hour=23, minute=59, second=59)
                except ValueError:
                    self.logger.warning(f"Invalid to date format: {self.date_to_var.get()}")

            if date_from or date_to:
                filters['date_range'] = (date_from, date_to)

            # Add amount range filter
            amount_min = None
            amount_max = None

            if hasattr(self, 'amount_min_var') and self.amount_min_var.get():
                try:
                    amount_min = float(self.amount_min_var.get())
                except ValueError:
                    self.logger.warning(f"Invalid minimum amount: {self.amount_min_var.get()}")

            if hasattr(self, 'amount_max_var') and self.amount_max_var.get():
                try:
                    amount_max = float(self.amount_max_var.get())
                except ValueError:
                    self.logger.warning(f"Invalid maximum amount: {self.amount_max_var.get()}")

            if amount_min is not None or amount_max is not None:
                filters['amount_range'] = (amount_min, amount_max)

            # Export data
            result = self.sales_service.export_sales(
                output_path=save_path,
                search_text=search_text,
                filters=filters,
                include_customer=True,
                include_items=True
            )

            # Show success message
            messagebox.showinfo(
                "Export Complete",
                f"Sales data has been exported to:\n{save_path}\n\n{result['count']} records exported."
            )

        except Exception as e:
            self.logger.error(f"Error exporting sales data: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to export sales data: {str(e)}")

    def select_customer(self):
        """Open customer selection dialog."""
        self.logger.debug("Opening customer selection dialog")

        # Create customer selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Customer")
        dialog.transient(self)
        dialog.grab_set()

        # Set dialog size and position
        dialog.geometry("600x500")
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
            command=lambda: self.search_customers(search_var.get(), customer_tree)
        )
        search_btn.pack(side=tk.LEFT, padx=5)

        # Create customers treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "email", "phone", "status")
        customer_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        customer_tree.heading("id", text="ID")
        customer_tree.heading("name", text="Name")
        customer_tree.heading("email", text="Email")
        customer_tree.heading("phone", text="Phone")
        customer_tree.heading("status", text="Status")

        # Define columns
        customer_tree.column("id", width=50)
        customer_tree.column("name", width=150)
        customer_tree.column("email", width=150)
        customer_tree.column("phone", width=100)
        customer_tree.column("status", width=100)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=customer_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=customer_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        customer_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        customer_tree.pack(fill=tk.BOTH, expand=True)

        # Create buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="New Customer",
            command=lambda: self.create_new_customer(dialog)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Select",
            style="Accent.TButton",
            command=lambda: self.select_customer_from_tree(customer_tree, dialog)
        ).pack(side=tk.RIGHT, padx=5)

        # Load initial customer data
        self.search_customers("", customer_tree)

        # Set focus to search entry
        search_entry.focus_set()

        # Bind double-click to select
        customer_tree.bind("<Double-1>", lambda e: self.select_customer_from_tree(customer_tree, dialog))

        # Bind Enter key in search entry
        search_entry.bind("<Return>", lambda e: self.search_customers(search_var.get(), customer_tree))

        # Wait for dialog to close
        dialog.wait_window()

    def search_customers(self, search_text, tree):
        """
        Search customers based on search text.

        Args:
            search_text: Text to search for
            tree: Treeview to display results
        """
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)

            # Search customers
            customers = self.customer_service.search_customers(
                search_text=search_text,
                limit=100
            )

            # Display results
            for customer in customers:
                tree.insert(
                    "",
                    "end",
                    iid=str(customer.id),
                    values=(
                        customer.id,
                        f"{customer.first_name} {customer.last_name}",
                        customer.email,
                        customer.phone,
                        customer.status
                    )
                )

        except Exception as e:
            self.logger.error(f"Error searching customers: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to search customers: {str(e)}")

    def select_customer_from_tree(self, tree, dialog):
        """
        Select the highlighted customer.

        Args:
            tree: Treeview with customer data
            dialog: Dialog to close after selection
        """
        # Get selected item
        selected_id = tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer.")
            return

        # Get selected item data
        item_data = tree.item(selected_id)
        values = item_data["values"]

        if not values or len(values) < 2:
            messagebox.showwarning("Selection Error", "Invalid customer data.")
            return

        # Set customer ID and name
        self.customer_id_var.set(str(values[0]))
        self.customer_name_var.set(values[1])

        # Close dialog
        dialog.destroy()

    def create_new_customer(self, parent_dialog):
        """
        Create a new customer.

        Args:
            parent_dialog: Parent dialog to close after creation
        """
        # Close the customer selection dialog
        parent_dialog.destroy()

        # TODO: Open customer details dialog in create mode
        # This will be implemented when the detailed customer creation UI is available
        messagebox.showinfo(
            "Feature Not Implemented",
            "The new customer creation feature will be implemented in the next phase."
        )

    def on_sale_updated(self, data):
        """
        Handle sale updated event.

        Args:
            data: Event data including sale_id
        """
        self.logger.debug(f"Sale updated event received: {data}")

        # Refresh the view
        self.refresh()

    def show_date_picker(self, date_var):
        """
        Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create date picker dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Date")
        dialog.transient(self)
        dialog.grab_set()

        # Set dialog size and position
        dialog.geometry("300x350")
        dialog.resizable(False, False)

        # Current date
        now = datetime.datetime.now()

        # Set current month and year
        self.calendar_year = tk.IntVar(value=now.year)
        self.calendar_month = tk.IntVar(value=now.month)

        # Month and year selection
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            header_frame,
            text="<",
            width=2,
            command=lambda: self.prev_month(month_year_label, calendar_frame)
        ).pack(side=tk.LEFT)

        month_year_label = ttk.Label(
            header_frame,
            text=f"{now.strftime('%B')} {now.year}",
            style="Heading.TLabel"
        )
        month_year_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        ttk.Button(
            header_frame,
            text=">",
            width=2,
            command=lambda: self.next_month(month_year_label, calendar_frame)
        ).pack(side=tk.RIGHT)

        # Create calendar frame
        calendar_frame = ttk.Frame(dialog)
        calendar_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(
                calendar_frame,
                text=day,
                anchor=tk.CENTER,
                style="Bold.TLabel"
            ).grid(row=0, column=i, sticky=tk.NSEW)

        # Initialize calendar
        self.update_calendar(
            calendar_frame,
            month_year_label,
            self.calendar_year.get(),
            self.calendar_month.get(),
            date_var,
            dialog
        )

        # Today button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Today",
            command=lambda: [
                date_var.set(now.strftime("%Y-%m-%d")),
                dialog.destroy()
            ]
        ).pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Clear",
            command=lambda: [
                date_var.set(""),
                dialog.destroy()
            ]
        ).pack(side=tk.RIGHT, padx=5)

    def update_calendar(self, frame, label, year, month, date_var, dialog):
        """
        Update the calendar display based on selected month and year.

        Args:
            frame: Calendar frame
            label: Month/year label
            year: Year to display
            month: Month to display
            date_var: Variable to update with selected date
            dialog: Dialog to close on selection
        """
        # Update month/year label
        month_name = datetime.date(year, month, 1).strftime("%B")
        label.config(text=f"{month_name} {year}")

        # Clear previous calendar
        for widget in frame.winfo_children():
            if widget.grid_info().get("row", 0) > 0:  # Keep headers
                widget.destroy()

        # Get first day of month and number of days
        first_day = datetime.date(year, month, 1)
        last_day = (datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1,
                                                                                       1)) - datetime.timedelta(days=1)

        # Calculate where to start (Monday = 0)
        start_weekday = (first_day.weekday() + 0) % 7

        # Create calendar buttons
        day = 1
        for row in range(1, 7):  # 6 weeks max
            for col in range(7):  # 7 days per week
                if (row == 1 and col < start_weekday) or day > last_day.day:
                    # Empty cell
                    ttk.Label(
                        frame,
                        text="",
                        width=4,
                        anchor=tk.CENTER
                    ).grid(row=row, column=col, padx=2, pady=2, sticky=tk.NSEW)
                else:
                    # Date button
                    day_btn = ttk.Button(
                        frame,
                        text=str(day),
                        width=4,
                        command=lambda d=day: [
                            date_var.set(f"{year:04d}-{month:02d}-{d:02d}"),
                            dialog.destroy()
                        ]
                    )
                    day_btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.NSEW)
                    day += 1

    def prev_month(self, label, frame):
        """
        Go to previous month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month and year
        if self.calendar_month.get() == 1:
            self.calendar_month.set(12)
            self.calendar_year.set(self.calendar_year.get() - 1)
        else:
            self.calendar_month.set(self.calendar_month.get() - 1)

        # Update calendar
        self.update_calendar(
            frame,
            label,
            self.calendar_year.get(),
            self.calendar_month.get(),
            getattr(self, "date_var", tk.StringVar()),
            frame.winfo_toplevel()
        )

    def next_month(self, label, frame):
        """
        Go to next month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month and year
        if self.calendar_month.get() == 12:
            self.calendar_month.set(1)
            self.calendar_year.set(self.calendar_year.get() + 1)
        else:
            self.calendar_month.set(self.calendar_month.get() + 1)

        # Update calendar
        self.update_calendar(
            frame,
            label,
            self.calendar_year.get(),
            self.calendar_month.get(),
            getattr(self, "date_var", tk.StringVar()),
            frame.winfo_toplevel()
        )

    def refresh(self):
        """Refresh the view."""
        # Update dashboard metrics
        self.update_dashboard_metrics()

        # Reload data
        self.load_data()

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("sale_updated", self.on_sale_updated)
        unsubscribe("sale_status_changed", self.on_sale_updated)

        # Call base class destroy
        super().destroy()