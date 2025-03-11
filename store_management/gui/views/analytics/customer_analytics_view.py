# gui/views/analytics/customer_analytics_view.py
"""
Customer analytics view for the leatherworking ERP system.

This module provides a detailed view of customer analytics, including
segmentation, retention, and lifetime value metrics.
"""

import datetime
from datetime import datetime, timedelta
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple

from di.resolve import resolve
from gui.base.base_view import BaseView
from gui.config import DEFAULT_PADDING
from gui.theme import COLORS
from gui.widgets.charts import create_bar_chart, create_line_chart, create_pie_chart
from gui.widgets.charts.heatmap import HeatmapChart
from gui.widgets.enum_combobox import EnumCombobox
from services.dto.analytics_dto import CustomerAnalyticsDTO, CustomerSegmentDTO
from services.implementations.customer_analytics_service import CustomerAnalyticsService


class CustomerAnalyticsView(BaseView):
    """Customer analytics view displaying detailed customer metrics."""

    def __init__(self, parent):
        """
        Initialize the customer analytics view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Customer Analytics"
        self.description = "Detailed metrics and insights about customer behavior"

        # Initialize date range
        self.start_date = (datetime.now() - timedelta(days=365)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        self.end_date = datetime.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Initialize service
        self.analytics_service = resolve('ICustomerAnalyticsService')

        # Initialize data containers
        self.customer_analytics = None
        self.customer_segments = None
        self.retention_data = None
        self.lifetime_value = None

        # Build the view
        self.build()

        # Load initial data
        self._load_data()

    def build(self):
        """Build the customer analytics view."""
        # Create the main container frame with scrolling
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Create the header with title and filter controls
        self.create_header()

        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self.main_container, bg=self.main_container.cget("background"))
        self.scrollbar = ttk.Scrollbar(self.main_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a frame inside the canvas for all content
        self.content_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)

        # Configure canvas scrolling
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Create the content sections
        self._create_date_filter_section()
        self._create_summary_section()
        self._create_segmentation_section()
        self._create_retention_section()
        self._create_lifetime_value_section()

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update the scrollable region."""
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

    def create_header(self):
        """Create a header for the customer analytics view."""
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(
            title_frame,
            text=self.title,
            font=("TkDefaultFont", 16, "bold")
        ).pack(side=tk.TOP, anchor=tk.W)

        ttk.Label(
            title_frame,
            text=self.description,
            font=("TkDefaultFont", 10)
        ).pack(side=tk.TOP, anchor=tk.W)

        # Action buttons
        action_frame = ttk.Frame(header_frame)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self._add_default_action_buttons(action_frame)

        ttk.Button(
            action_frame,
            text="Export PDF",
            command=self._export_pdf
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            action_frame,
            text="Export Excel",
            command=self._export_excel
        ).pack(side=tk.LEFT)

    def _create_date_filter_section(self):
        """Create date filter section."""
        filter_frame = ttk.LabelFrame(
            self.content_frame,
            text="Date Range",
            padding=DEFAULT_PADDING
        )
        filter_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Period combobox
        ttk.Label(filter_frame, text="Period:").grid(row=0, column=0, padx=(0, 10))

        self.period_var = tk.StringVar(value="Last 12 Months")
        period_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.period_var,
            values=[
                "Last 30 Days",
                "Last 90 Days",
                "Last 6 Months",
                "Last 12 Months",
                "Year to Date",
                "Custom Range"
            ],
            state="readonly",
            width=15
        )
        period_combo.grid(row=0, column=1, padx=(0, 20))
        period_combo.bind("<<ComboboxSelected>>", self._on_period_change)

        # Start date
        ttk.Label(filter_frame, text="Start Date:").grid(row=0, column=2, padx=(0, 10))

        self.start_date_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        start_date_entry = ttk.Entry(
            filter_frame,
            textvariable=self.start_date_var,
            width=12
        )
        start_date_entry.grid(row=0, column=3, padx=(0, 5))

        ttk.Button(
            filter_frame,
            text="📅",
            width=3,
            command=lambda: self._show_date_picker(self.start_date_var)
        ).grid(row=0, column=4, padx=(0, 20))

        # End date
        ttk.Label(filter_frame, text="End Date:").grid(row=0, column=5, padx=(0, 10))

        self.end_date_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        end_date_entry = ttk.Entry(
            filter_frame,
            textvariable=self.end_date_var,
            width=12
        )
        end_date_entry.grid(row=0, column=6, padx=(0, 5))

        ttk.Button(
            filter_frame,
            text="📅",
            width=3,
            command=lambda: self._show_date_picker(self.end_date_var)
        ).grid(row=0, column=7, padx=(0, 20))

        # Apply button
        ttk.Button(
            filter_frame,
            text="Apply",
            command=self._apply_date_filter
        ).grid(row=0, column=8, padx=(0, 5))

        # Configure grid
        filter_frame.columnconfigure(9, weight=1)

    def _create_summary_section(self):
        """Create customer summary section."""
        summary_frame = ttk.LabelFrame(
            self.content_frame,
            text="Customer Summary",
            padding=DEFAULT_PADDING
        )
        summary_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create a frame for the KPI widgets
        kpi_frame = ttk.Frame(summary_frame)
        kpi_frame.pack(fill=tk.X, expand=True)

        # Configure the grid
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1, uniform="kpi")

        # KPI widgets will be created/updated when data is loaded
        self.kpi_widgets = {}

    def _create_segmentation_section(self):
        """Create customer segmentation section."""
        segment_frame = ttk.LabelFrame(
            self.content_frame,
            text="Customer Segmentation",
            padding=DEFAULT_PADDING
        )
        segment_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create a frame for the segment visualization and table
        content_frame = ttk.Frame(segment_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Split into left (chart) and right (table)
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a placeholder for the pie chart
        self.segment_chart_frame = ttk.Frame(left_frame, width=400, height=300)
        self.segment_chart_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create a table for segment details
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Segment", "Customers", "Orders", "Avg. Order", "Last Purchase")
        self.segment_treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=5
        )

        # Configure columns
        for col in columns:
            self.segment_treeview.heading(col, text=col)
            width = 100 if col != "Segment" else 120
            self.segment_treeview.column(col, width=width, minwidth=50)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.segment_treeview.yview
        )
        self.segment_treeview.configure(yscrollcommand=scrollbar.set)

        self.segment_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_retention_section(self):
        """Create customer retention section."""
        retention_frame = ttk.LabelFrame(
            self.content_frame,
            text="Customer Retention",
            padding=DEFAULT_PADDING
        )
        retention_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Controls frame
        controls_frame = ttk.Frame(retention_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(controls_frame, text="Cohort Period:").pack(side=tk.LEFT, padx=(0, 5))

        self.cohort_period_var = tk.StringVar(value="Month")
        cohort_period_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.cohort_period_var,
            values=["Day", "Week", "Month", "Quarter", "Year"],
            state="readonly",
            width=10
        )
        cohort_period_combo.pack(side=tk.LEFT, padx=(0, 15))
        cohort_period_combo.bind("<<ComboboxSelected>>", self._on_cohort_period_change)

        ttk.Label(controls_frame, text="Number of Periods:").pack(side=tk.LEFT, padx=(0, 5))

        self.period_count_var = tk.StringVar(value="6")
        period_count_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.period_count_var,
            values=["3", "6", "12", "18", "24"],
            state="readonly",
            width=5
        )
        period_count_combo.pack(side=tk.LEFT, padx=(0, 15))
        period_count_combo.bind("<<ComboboxSelected>>", self._on_period_count_change)

        ttk.Button(
            controls_frame,
            text="Update",
            command=self._update_retention_data
        ).pack(side=tk.LEFT)

        # Create a frame for the retention heatmap
        self.retention_chart_frame = ttk.Frame(retention_frame, height=300)
        self.retention_chart_frame.pack(fill=tk.BOTH, expand=True)

    def _create_lifetime_value_section(self):
        """Create customer lifetime value section."""
        ltv_frame = ttk.LabelFrame(
            self.content_frame,
            text="Customer Lifetime Value",
            padding=DEFAULT_PADDING
        )
        ltv_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Split into left (metrics) and right (chart)
        content_frame = ttk.Frame(ltv_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create metrics section
        metrics_frame = ttk.Frame(left_frame)
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create metrics placeholders
        self.ltv_metrics = {}
        metrics = [
            ("Average Customer LTV", "avg_ltv"),
            ("Average Purchase Value", "avg_purchase"),
            ("Average Purchase Frequency", "avg_frequency"),
            ("Average Customer Lifespan", "avg_lifespan"),
            ("Customer Acquisition Cost", "acquisition_cost"),
            ("LTV:CAC Ratio", "ltv_cac_ratio")
        ]

        for i, (label, key) in enumerate(metrics):
            label_widget = ttk.Label(
                metrics_frame,
                text=f"{label}:",
                font=("TkDefaultFont", 10, "bold")
            )
            label_widget.grid(row=i, column=0, sticky=tk.W, pady=5)

            value_widget = ttk.Label(
                metrics_frame,
                text="-",
                font=("TkDefaultFont", 10)
            )
            value_widget.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=5)

            self.ltv_metrics[key] = value_widget

        # Configure grid
        metrics_frame.columnconfigure(1, weight=1)

        # Create a placeholder for the chart
        self.ltv_chart_frame = ttk.Frame(right_frame, width=400, height=300)
        self.ltv_chart_frame.pack(fill=tk.BOTH, expand=True)

    def _load_data(self):
        """Load all customer analytics data."""
        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Get customer analytics data
            self.customer_analytics = self.analytics_service.get_customer_analytics(
                start_date=start_date,
                end_date=end_date
            )

            # Get customer segments
            self.customer_segments = self.analytics_service.get_customer_segments(
                segment_count=3,
                min_orders=1
            )

            # Get retention data
            period_unit = self.cohort_period_var.get().lower()
            period_count = int(self.period_count_var.get())
            self.retention_data = self.analytics_service.get_retention_data(
                period_count=period_count,
                period_unit=period_unit
            )

            # Get customer lifetime value data
            self.lifetime_value = self.analytics_service.get_customer_lifetime_value()

            # Update UI with the loaded data
            self._update_ui()

        except Exception as e:
            logging.error(f"Error loading customer analytics data: {e}")
            self.show_error(
                "Data Loading Error",
                f"Failed to load customer analytics data: {str(e)}"
            )

    def _update_ui(self):
        """Update UI with loaded data."""
        if not self.customer_analytics:
            return

        self._update_summary_section()
        self._update_segmentation_section()
        self._update_retention_section()
        self._update_lifetime_value_section()

    def _update_summary_section(self):
        """Update customer summary section with loaded data."""
        # Clear existing widgets
        for widget in self.kpi_widgets.values():
            if widget.winfo_exists():
                widget.destroy()

        # Get the KPI frame
        kpi_frame = self.content_frame.winfo_children()[2].winfo_children()[0]

        # Create KPI widgets
        kpis = [
            {
                "title": "Total Customers",
                "value": self.customer_analytics.total_customers,
                "subtitle": f"{self.customer_analytics.new_customers} new in period",
                "key": "total_customers"
            },
            {
                "title": "Active Customers",
                "value": self.customer_analytics.active_customers,
                "subtitle": f"{self.customer_analytics.active_percentage:.1f}% active rate",
                "key": "active_customers"
            },
            {
                "title": "Orders per Customer",
                "value": f"{self.customer_analytics.avg_orders_per_customer:.2f}",
                "subtitle": f"{self.customer_analytics.total_orders} total orders",
                "key": "orders_per_customer"
            },
            {
                "title": "Avg. Order Value",
                "value": f"${self.customer_analytics.avg_order_value:.2f}",
                "subtitle": f"${self.customer_analytics.total_revenue:.2f} total revenue",
                "key": "avg_order_value"
            }
        ]

        # Create KPI widgets
        for i, kpi in enumerate(kpis):
            frame = ttk.Frame(kpi_frame, style="Card.TFrame")
            frame.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)

            title_label = ttk.Label(
                frame,
                text=kpi["title"],
                font=("TkDefaultFont", 12, "bold")
            )
            title_label.pack(anchor=tk.CENTER, pady=(10, 5))

            value_label = ttk.Label(
                frame,
                text=str(kpi["value"]),
                font=("TkDefaultFont", 18)
            )
            value_label.pack(anchor=tk.CENTER, pady=5)

            subtitle_label = ttk.Label(
                frame,
                text=kpi["subtitle"],
                font=("TkDefaultFont", 10),
                foreground=COLORS["secondary_text"]
            )
            subtitle_label.pack(anchor=tk.CENTER, pady=(5, 10))

            self.kpi_widgets[kpi["key"]] = frame

    def _update_segmentation_section(self):
        """Update customer segmentation section with loaded data."""
        if not self.customer_segments:
            return

        # Clear existing chart
        for widget in self.segment_chart_frame.winfo_children():
            widget.destroy()

        # Clear existing treeview items
        for item in self.segment_treeview.get_children():
            self.segment_treeview.delete(item)

        # Prepare data for pie chart
        chart_data = [
            {
                "label": segment.name,
                "value": segment.customer_count,
                "color": COLORS.get(f"segment_{i}", COLORS["accent"])
            }
            for i, segment in enumerate(self.customer_segments)
        ]

        # Create pie chart
        pie_chart = create_pie_chart(
            self.segment_chart_frame,
            chart_data,
            title="Customer Segments",
            width=400,
            height=300,
            show_legend=True
        )
        pie_chart.pack(fill=tk.BOTH, expand=True)

        # Add segments to the treeview
        for segment in self.customer_segments:
            self.segment_treeview.insert(
                "",
                tk.END,
                values=(
                    segment.name,
                    segment.customer_count,
                    segment.order_count,
                    f"${segment.avg_order_value:.2f}",
                    segment.recency_days
                )
            )

    def _update_retention_section(self):
        """Update customer retention section with loaded data."""
        if not self.retention_data:
            return

        # Clear existing chart
        for widget in self.retention_chart_frame.winfo_children():
            widget.destroy()

        # Prepare data for heatmap
        cohorts = self.retention_data.get("cohorts", [])
        periods = self.retention_data.get("periods", [])
        values = self.retention_data.get("values", [])

        heatmap_data = []
        for i, cohort in enumerate(cohorts):
            for j, period in enumerate(periods):
                if i < len(values) and j < len(values[i]):
                    heatmap_data.append({
                        "x": period,
                        "y": cohort,
                        "value": values[i][j]
                    })

        # Create heatmap
        heatmap = HeatmapChart(
            self.retention_chart_frame,
            data=heatmap_data,
            title="Customer Retention by Cohort",
            x_label="Period",
            y_label="Cohort",
            x_key="x",
            y_key="y",
            value_key="value",
            width=800,
            height=400,
            color_min=COLORS["light_blue"],
            color_max=COLORS["dark_blue"]
        )
        heatmap.pack(fill=tk.BOTH, expand=True)

    def _update_lifetime_value_section(self):
        """Update customer lifetime value section with loaded data."""
        if not self.lifetime_value:
            return

        # Update metrics
        metrics_mapping = {
            "avg_ltv": "avg_ltv",
            "avg_purchase": "avg_purchase_value",
            "avg_frequency": "purchase_frequency",
            "avg_lifespan": "customer_lifespan",
            "acquisition_cost": "acquisition_cost",
            "ltv_cac_ratio": "ltv_cac_ratio"
        }

        for ui_key, data_key in metrics_mapping.items():
            if ui_key in self.ltv_metrics and data_key in self.lifetime_value:
                value = self.lifetime_value[data_key]

                # Format value appropriately
                if isinstance(value, (int, float)):
                    if ui_key in ["avg_ltv", "avg_purchase", "acquisition_cost"]:
                        formatted_value = f"${value:.2f}"
                    elif ui_key == "avg_frequency":
                        formatted_value = f"{value:.2f} orders/year"
                    elif ui_key == "avg_lifespan":
                        formatted_value = f"{value:.1f} years"
                    elif ui_key == "ltv_cac_ratio":
                        formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)

                self.ltv_metrics[ui_key].configure(text=formatted_value)

        # Clear existing chart
        for widget in self.ltv_chart_frame.winfo_children():
            widget.destroy()

        # Prepare data for bar chart - LTV by segment
        if "segment_ltv" in self.lifetime_value:
            chart_data = [
                {
                    "label": segment,
                    "value": ltv,
                    "color": COLORS.get(f"segment_{i}", COLORS["accent"])
                }
                for i, (segment, ltv) in enumerate(self.lifetime_value["segment_ltv"].items())
            ]

            # Create bar chart
            bar_chart = create_bar_chart(
                self.ltv_chart_frame,
                chart_data,
                title="Customer Lifetime Value by Segment",
                x_label="Segment",
                y_label="Lifetime Value ($)",
                width=400,
                height=300
            )
            bar_chart.pack(fill=tk.BOTH, expand=True)

    def _show_date_picker(self, date_var):
        """
        Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        from tkcalendar import DateEntry

        top = tk.Toplevel(self)
        top.title("Select Date")
        top.geometry("300x250")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()

        # Create calendar
        cal = DateEntry(
            top,
            width=12,
            background=COLORS["primary"],
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd",
            firstweekday="sunday"
        )
        cal.pack(pady=20)

        # Try to set initial date from the variable
        try:
            initial_date = datetime.strptime(date_var.get(), "%Y-%m-%d")
            cal.set_date(initial_date)
        except:
            pass

        def set_date():
            date_var.set(cal.get_date().strftime("%Y-%m-%d"))
            top.destroy()

        # Add buttons
        ttk.Button(top, text="Select", command=set_date).pack(pady=10)
        ttk.Button(top, text="Cancel", command=top.destroy).pack()

    def _set_default_date_range(self, period):
        """
        Set default date range based on time period.

        Args:
            period: The time period to set
        """
        today = datetime.now()
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        if period == "Last 30 Days":
            start_date = today - timedelta(days=30)
        elif period == "Last 90 Days":
            start_date = today - timedelta(days=90)
        elif period == "Last 6 Months":
            start_date = today - timedelta(days=180)
        elif period == "Last 12 Months":
            start_date = today - timedelta(days=365)
        elif period == "Year to Date":
            start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Custom - keep current dates
            return

        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        self.start_date_var.set(start_date.strftime("%Y-%m-%d"))
        self.end_date_var.set(end_date.strftime("%Y-%m-%d"))

    def _on_period_change(self, event):
        """
        Handle time period change.

        Args:
            event: The combobox selection event
        """
        period = self.period_var.get()
        self._set_default_date_range(period)

    def _apply_date_filter(self):
        """Apply date filter and reload data."""
        self._load_data()

    def _on_cohort_period_change(self, event):
        """
        Handle cohort period change.

        Args:
            event: The combobox selection event
        """
        pass  # We'll apply this when the Update button is clicked

    def _on_period_count_change(self, event):
        """
        Handle period count change.

        Args:
            event: The combobox selection event
        """
        pass  # We'll apply this when the Update button is clicked

    def _update_retention_data(self):
        """Update retention data with current settings."""
        try:
            # Get retention data with current settings
            period_unit = self.cohort_period_var.get().lower()
            period_count = int(self.period_count_var.get())
            self.retention_data = self.analytics_service.get_retention_data(
                period_count=period_count,
                period_unit=period_unit
            )

            # Update UI
            self._update_retention_section()

        except Exception as e:
            logging.error(f"Error updating retention data: {e}")
            self.show_error(
                "Data Loading Error",
                f"Failed to update retention data: {str(e)}"
            )

    def _export_pdf(self):
        """Export analytics to PDF."""
        # Placeholder for PDF export functionality
        self.show_info(
            "Export to PDF",
            "PDF export functionality is not yet implemented."
        )

    def _export_excel(self):
        """Export analytics to Excel."""
        # Placeholder for Excel export functionality
        self.show_info(
            "Export to Excel",
            "Excel export functionality is not yet implemented."
        )

    def refresh(self):
        """Refresh the view by reloading data."""
        self._load_data()