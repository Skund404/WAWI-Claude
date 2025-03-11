# gui/views/analytics/profitability_analytics_view.py
"""
Profitability analytics view for the leatherworking ERP system.

This module provides a detailed view of profitability analytics, including
margin analysis, cost breakdowns, and comparative metrics.
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
from services.dto.analytics_dto import ProfitabilityAnalyticsDTO, ProfitMarginDTO
from services.implementations.profitability_analytics_service import ProfitabilityAnalyticsService


class ProfitabilityAnalyticsView(BaseView):
    """Profitability analytics view displaying detailed financial metrics."""

    def __init__(self, parent):
        """
        Initialize the profitability analytics view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Profitability Analytics"
        self.description = "Detailed analysis of profitability and margins"

        # Initialize date range
        self.start_date = (datetime.now() - timedelta(days=365)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        self.end_date = datetime.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Initialize service
        self.analytics_service = resolve('IProfitabilityAnalyticsService')

        # Initialize data containers
        self.profitability_data = None
        self.product_margins = None
        self.project_margins = None
        self.cost_breakdown = None

        # Build the view
        self.build()

        # Load initial data
        self._load_data()

    def build(self):
        """Build the profitability analytics view."""
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
        self._create_margin_analysis_section()
        self._create_cost_breakdown_section()
        self._create_comparison_section()

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update the scrollable region."""
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

    def create_header(self):
        """Create a header for the profitability analytics view."""
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
        """Create profitability summary section."""
        summary_frame = ttk.LabelFrame(
            self.content_frame,
            text="Profitability Summary",
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

    def _create_margin_analysis_section(self):
        """Create margin analysis section."""
        margin_frame = ttk.LabelFrame(
            self.content_frame,
            text="Margin Analysis",
            padding=DEFAULT_PADDING
        )
        margin_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create tabs for different margin analyses
        tab_control = ttk.Notebook(margin_frame)
        tab_control.pack(fill=tk.BOTH, expand=True)

        # Product margins tab
        product_tab = ttk.Frame(tab_control)
        tab_control.add(product_tab, text="Product Margins")

        # Create placeholder for product margin chart
        self.product_margin_frame = ttk.Frame(product_tab)
        self.product_margin_frame.pack(fill=tk.BOTH, expand=True)

        # Project margins tab
        project_tab = ttk.Frame(tab_control)
        tab_control.add(project_tab, text="Project Margins")

        # Create placeholder for project margin chart
        self.project_margin_frame = ttk.Frame(project_tab)
        self.project_margin_frame.pack(fill=tk.BOTH, expand=True)

        # Margin trend tab
        trend_tab = ttk.Frame(tab_control)
        tab_control.add(trend_tab, text="Margin Trends")

        # Create placeholder for margin trend chart
        self.margin_trend_frame = ttk.Frame(trend_tab)
        self.margin_trend_frame.pack(fill=tk.BOTH, expand=True)

    def _create_cost_breakdown_section(self):
        """Create cost breakdown section."""
        cost_frame = ttk.LabelFrame(
            self.content_frame,
            text="Cost Breakdown",
            padding=DEFAULT_PADDING
        )
        cost_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Split into left (chart) and right (details)
        content_frame = ttk.Frame(cost_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create project type filter
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Project Type:").pack(side=tk.LEFT, padx=(0, 5))

        self.project_type_var = tk.StringVar(value="All Types")
        self.project_type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.project_type_var,
            state="readonly",
            width=20
        )
        self.project_type_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.project_type_combo.bind("<<ComboboxSelected>>", self._on_project_type_change)

        # Create placeholder for cost breakdown chart
        self.cost_chart_frame = ttk.Frame(left_frame, width=400, height=300)
        self.cost_chart_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create table for cost details
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Category", "Cost", "Percentage")
        self.cost_treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # Configure columns
        for col in columns:
            self.cost_treeview.heading(col, text=col)
            width = 100 if col != "Category" else 150
            self.cost_treeview.column(col, width=width, minwidth=50)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.cost_treeview.yview
        )
        self.cost_treeview.configure(yscrollcommand=scrollbar.set)

        self.cost_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_comparison_section(self):
        """Create comparative analysis section."""
        comparison_frame = ttk.LabelFrame(
            self.content_frame,
            text="Comparative Analysis",
            padding=DEFAULT_PADDING
        )
        comparison_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create layout for comparative charts
        left_frame = ttk.Frame(comparison_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_frame = ttk.Frame(comparison_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Create placeholders for comparison charts
        self.revenue_cost_frame = ttk.LabelFrame(
            left_frame,
            text="Revenue vs. Costs",
            padding=5
        )
        self.revenue_cost_frame.pack(fill=tk.BOTH, expand=True)

        self.margin_comparison_frame = ttk.LabelFrame(
            right_frame,
            text="Margin Comparison",
            padding=5
        )
        self.margin_comparison_frame.pack(fill=tk.BOTH, expand=True)

    def _load_data(self):
        """Load all profitability analytics data."""
        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Get profitability analytics data
            self.profitability_data = self.analytics_service.get_profitability_analytics(
                start_date=start_date,
                end_date=end_date
            )

            # Get product margins
            self.product_margins = self.analytics_service.get_profit_margins_by_product_type(
                start_date=start_date,
                end_date=end_date
            )

            # Get project margins
            self.project_margins = self.analytics_service.get_profit_margins_by_project_type(
                start_date=start_date,
                end_date=end_date
            )

            # Get cost breakdown
            project_type = None if self.project_type_var.get() == "All Types" else self.project_type_var.get()
            self.cost_breakdown = self.analytics_service.get_cost_breakdown(
                project_type=project_type
            )

            # Update project type dropdown options
            if self.profitability_data and hasattr(self.profitability_data, 'project_types'):
                project_types = ["All Types"] + self.profitability_data.project_types
                self.project_type_combo['values'] = project_types

            # Update UI with the loaded data
            self._update_ui()

        except Exception as e:
            logging.error(f"Error loading profitability analytics data: {e}")
            self.show_error(
                "Data Loading Error",
                f"Failed to load profitability analytics data: {str(e)}"
            )

    def _update_ui(self):
        """Update UI with loaded data."""
        if not self.profitability_data:
            return

        self._update_summary_section()
        self._update_margin_analysis_section()
        self._update_cost_breakdown_section()
        self._update_comparison_section()

    def _update_summary_section(self):
        """Update profitability summary section with loaded data."""
        # Clear existing widgets
        for widget in self.kpi_widgets.values():
            if widget.winfo_exists():
                widget.destroy()

        # Get the KPI frame
        kpi_frame = self.content_frame.winfo_children()[2].winfo_children()[0]

        # Create KPI widgets
        kpis = [
            {
                "title": "Total Revenue",
                "value": f"${self.profitability_data.total_revenue:.2f}",
                "subtitle": f"{self.profitability_data.order_count} orders",
                "key": "total_revenue"
            },
            {
                "title": "Total Costs",
                "value": f"${self.profitability_data.total_costs:.2f}",
                "subtitle": f"${self.profitability_data.cost_per_order:.2f} per order",
                "key": "total_costs"
            },
            {
                "title": "Gross Profit",
                "value": f"${self.profitability_data.gross_profit:.2f}",
                "subtitle": f"${self.profitability_data.profit_per_order:.2f} per order",
                "key": "gross_profit"
            },
            {
                "title": "Gross Margin",
                "value": f"{self.profitability_data.gross_margin:.1f}%",
                "subtitle": self._get_margin_trend_text(self.profitability_data.margin_trend),
                "key": "gross_margin"
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
                text=kpi["value"],
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

    def _get_margin_trend_text(self, trend_value):
        """
        Get descriptive text for margin trend.

        Args:
            trend_value: The trend value (positive or negative percentage)

        Returns:
            Formatted trend text
        """
        if trend_value > 0:
            return f"↑ {trend_value:.1f}% vs. previous"
        elif trend_value < 0:
            return f"↓ {abs(trend_value):.1f}% vs. previous"
        else:
            return "No change vs. previous"

    def _update_margin_analysis_section(self):
        """Update margin analysis section with loaded data."""
        self._update_product_margins()
        self._update_project_margins()
        self._update_margin_trends()

    def _update_product_margins(self):
        """Update product margins tab."""
        if not self.product_margins:
            return

        # Clear existing chart
        for widget in self.product_margin_frame.winfo_children():
            widget.destroy()

        # Prepare data for bar chart
        chart_data = [
            {
                "label": product_type,
                "value": margin,
                "color": self._get_margin_color(margin)
            }
            for product_type, margin in self.product_margins.items()
        ]

        # Sort by margin (descending)
        chart_data.sort(key=lambda x: x["value"], reverse=True)

        # Create bar chart
        bar_chart = create_bar_chart(
            self.product_margin_frame,
            chart_data,
            title="Profit Margins by Product Type",
            x_label="Product Type",
            y_label="Margin (%)",
            width=800,
            height=400
        )
        bar_chart.pack(fill=tk.BOTH, expand=True)

    def _update_project_margins(self):
        """Update project margins tab."""
        if not self.project_margins:
            return

        # Clear existing chart
        for widget in self.project_margin_frame.winfo_children():
            widget.destroy()

        # Prepare data for bar chart
        chart_data = [
            {
                "label": project_type,
                "value": margin,
                "color": self._get_margin_color(margin)
            }
            for project_type, margin in self.project_margins.items()
        ]

        # Sort by margin (descending)
        chart_data.sort(key=lambda x: x["value"], reverse=True)

        # Create bar chart
        bar_chart = create_bar_chart(
            self.project_margin_frame,
            chart_data,
            title="Profit Margins by Project Type",
            x_label="Project Type",
            y_label="Margin (%)",
            width=800,
            height=400
        )
        bar_chart.pack(fill=tk.BOTH, expand=True)

    def _update_margin_trends(self):
        """Update margin trends tab."""
        if not self.profitability_data or not hasattr(self.profitability_data, 'margin_by_period'):
            return

        # Clear existing chart
        for widget in self.margin_trend_frame.winfo_children():
            widget.destroy()

        # Prepare data for line chart
        margin_data = self.profitability_data.margin_by_period

        chart_data = [
            {
                "label": period,
                "value": margin,
                "color": COLORS["primary"]
            }
            for period, margin in margin_data.items()
        ]

        # Sort by period
        chart_data.sort(key=lambda x: x["label"])

        # Create line chart
        line_chart = create_line_chart(
            self.margin_trend_frame,
            chart_data,
            title="Gross Margin Trend",
            x_label="Period",
            y_label="Margin (%)",
            width=800,
            height=400,
            show_points=True,
            area_fill=True
        )
        line_chart.pack(fill=tk.BOTH, expand=True)

    def _update_cost_breakdown_section(self):
        """Update cost breakdown section with loaded data."""
        if not self.cost_breakdown:
            return

        # Clear existing chart
        for widget in self.cost_chart_frame.winfo_children():
            widget.destroy()

        # Clear existing treeview items
        for item in self.cost_treeview.get_children():
            self.cost_treeview.delete(item)

        # Prepare data for pie chart
        chart_data = [
            {
                "label": category,
                "value": percentage,
                "color": COLORS.get(f"cost_{i}", COLORS["accent"])
            }
            for i, (category, percentage) in enumerate(self.cost_breakdown.items())
        ]

        # Create pie chart
        pie_chart = create_pie_chart(
            self.cost_chart_frame,
            chart_data,
            title="Cost Breakdown",
            width=400,
            height=300,
            show_legend=True,
            show_percentage=True
        )
        pie_chart.pack(fill=tk.BOTH, expand=True)

        # Add cost categories to the treeview
        total_cost = self.profitability_data.total_costs if self.profitability_data else 0

        for category, percentage in self.cost_breakdown.items():
            cost_amount = total_cost * (percentage / 100) if total_cost > 0 else 0

            self.cost_treeview.insert(
                "",
                tk.END,
                values=(
                    category,
                    f"${cost_amount:.2f}",
                    f"{percentage:.1f}%"
                )
            )

        # Add total row
        self.cost_treeview.insert(
            "",
            tk.END,
            values=(
                "TOTAL",
                f"${total_cost:.2f}",
                "100.0%"
            ),
            tags=("total",)
        )

        # Configure tag for total row
        self.cost_treeview.tag_configure(
            "total",
            background=COLORS["light_accent"],
            font=("TkDefaultFont", 10, "bold")
        )

    def _update_comparison_section(self):
        """Update comparative analysis section with loaded data."""
        self._update_revenue_cost_chart()
        self._update_margin_comparison_chart()

    def _update_revenue_cost_chart(self):
        """Update revenue vs. costs chart."""
        if not self.profitability_data or not hasattr(self.profitability_data, 'revenue_by_period'):
            return

        # Clear existing chart
        for widget in self.revenue_cost_frame.winfo_children():
            widget.destroy()

        # Prepare data for line chart with multiple series
        revenue_data = self.profitability_data.revenue_by_period
        cost_data = self.profitability_data.costs_by_period

        # Ensure we have matching periods
        periods = sorted(set(revenue_data.keys()).intersection(cost_data.keys()))

        # Create formatted data
        chart_data = []
        for period in periods:
            if period in revenue_data:
                chart_data.append({
                    "label": period,
                    "value": revenue_data[period],
                    "series": "Revenue",
                    "color": COLORS["primary"]
                })

            if period in cost_data:
                chart_data.append({
                    "label": period,
                    "value": cost_data[period],
                    "series": "Costs",
                    "color": COLORS["secondary"]
                })

        # Create line chart with multiple series
        if chart_data:
            from gui.widgets.charts import create_multi_line_chart

            line_chart = create_multi_line_chart(
                self.revenue_cost_frame,
                chart_data,
                title="Revenue vs. Costs",
                x_label="Period",
                y_label="Amount ($)",
                width=400,
                height=300,
                show_points=True,
                show_legend=True
            )
            line_chart.pack(fill=tk.BOTH, expand=True)
        else:
            # Show a message if no data
            ttk.Label(
                self.revenue_cost_frame,
                text="No revenue/cost data available for the selected period",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _update_margin_comparison_chart(self):
        """Update margin comparison chart."""
        if not self.profitability_data or not hasattr(self.profitability_data, 'margin_comparison'):
            return

        # Clear existing chart
        for widget in self.margin_comparison_frame.winfo_children():
            widget.destroy()

        # Check if we have margin comparison data
        if not self.profitability_data.margin_comparison:
            ttk.Label(
                self.margin_comparison_frame,
                text="No margin comparison data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)
            return

        # Prepare data for bar chart
        chart_data = [
            {
                "label": category,
                "value": margin,
                "color": self._get_margin_color(margin)
            }
            for category, margin in self.profitability_data.margin_comparison.items()
        ]

        # Sort by margin (descending)
        chart_data.sort(key=lambda x: x["value"], reverse=True)

        # Create bar chart
        bar_chart = create_bar_chart(
            self.margin_comparison_frame,
            chart_data,
            title="Margin Comparison",
            x_label="Category",
            y_label="Margin (%)",
            width=400,
            height=300
        )
        bar_chart.pack(fill=tk.BOTH, expand=True)

    def _get_margin_color(self, margin_value):
        """
        Get color for margin visualization based on value.

        Args:
            margin_value: The margin percentage

        Returns:
            Color hex code
        """
        if margin_value >= 40:
            return COLORS["success"]
        elif margin_value >= 25:
            return COLORS["primary"]
        elif margin_value >= 15:
            return COLORS["secondary"]
        elif margin_value >= 0:
            return COLORS["warning"]
        else:
            return COLORS["danger"]

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

    def _on_project_type_change(self, event):
        """
        Handle project type change.

        Args:
            event: The combobox selection event
        """
        try:
            # Get cost breakdown with selected project type
            project_type = None if self.project_type_var.get() == "All Types" else self.project_type_var.get()
            self.cost_breakdown = self.analytics_service.get_cost_breakdown(
                project_type=project_type
            )

            # Update cost breakdown section
            self._update_cost_breakdown_section()

        except Exception as e:
            logging.error(f"Error updating cost breakdown: {e}")
            self.show_error(
                "Data Loading Error",
                f"Failed to update cost breakdown: {str(e)}"
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