# gui/views/analytics/analytics_dashboard.py
"""
Analytics dashboard view.

This module provides a comprehensive dashboard view for analytics data,
integrating metrics from various analytics services.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.widgets.charts import (
    BarChart, LineChart, PieChart, create_dashboard_kpi_chart, prepare_chart_data
)

from di.resolve import resolve
from services.implementations.analytics_dashboard_service import AnalyticsDashboardService
from services.dto.analytics_dto import AnalyticsSummaryDTO


class AnalyticsDashboardView(BaseView):
    """View for displaying the integrated analytics dashboard."""

    def __init__(self, parent):
        """
        Initialize the analytics dashboard view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)

        # Services
        self.analytics_service = resolve('AnalyticsDashboardService')

        # State variables
        self.time_period = tk.StringVar(value="yearly")
        self.time_periods = ["monthly", "quarterly", "yearly"]

        self.start_date = None
        self.end_date = None

        # UI elements
        self.controls_frame = None
        self.content_frame = None
        self.status_bar = None

        # Chart widgets
        self.revenue_chart = None
        self.profit_chart = None
        self.margin_chart = None
        self.customer_chart = None
        self.material_chart = None
        self.project_chart = None

        # Default date range
        self._set_default_date_range()

        # Load data and build UI
        self.build()

    def build(self):
        """Build the analytics dashboard view."""
        # Create main layout
        self.create_header()

        # Controls section
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Time period selection
        ttk.Label(self.controls_frame, text="Time Period:").pack(side=tk.LEFT, padx=(0, 5))
        period_combo = ttk.Combobox(
            self.controls_frame,
            textvariable=self.time_period,
            values=self.time_periods,
            width=10,
            state="readonly"
        )
        period_combo.pack(side=tk.LEFT, padx=(0, 10))
        period_combo.bind("<<ComboboxSelected>>", self._on_period_change)

        # Date range display
        date_format = "%b %d, %Y"
        date_range_text = f"Date Range: {self.start_date.strftime(date_format)} - {self.end_date.strftime(date_format)}"
        self.date_range_label = ttk.Label(self.controls_frame, text=date_range_text)
        self.date_range_label.pack(side=tk.LEFT, padx=(0, 10))

        # Refresh button
        refresh_btn = ttk.Button(
            self.controls_frame,
            text="Refresh",
            command=self.refresh
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # Create scrollable content frame
        canvas = tk.Canvas(self, bg=COLORS["background"])
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.content_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Configure scrolling
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"), width=event.width)
            canvas.itemconfig(canvas_window, width=event.width)

        self.content_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # Status bar
        self.status_bar = ttk.Label(self, text="Loading data...", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # Load data
        self.after(100, self._load_data)

    def _load_data(self):
        """Load analytics data."""
        try:
            # Update status
            self.status_bar.config(text="Loading analytics data...")

            # Get analytics summary data
            summary = self.analytics_service.get_analytics_summary(
                time_period=self.time_period.get(),
                start_date=self.start_date,
                end_date=self.end_date
            )

            # Get KPI data
            kpis = self.analytics_service.get_key_performance_indicators(
                time_period=self.time_period.get(),
                start_date=self.start_date,
                end_date=self.end_date
            )

            # Create dashboard sections
            self._create_kpi_section(summary, kpis)
            self._create_revenue_section(summary, kpis)
            self._create_customer_section(summary, kpis)
            self._create_operations_section(summary, kpis)

            # Update status
            self.status_bar.config(text=f"Data loaded successfully. Last update: {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            # Handle error
            self.status_bar.config(text=f"Error loading data: {str(e)}")
            self.show_error("Data Load Error", f"Error loading analytics data: {str(e)}")

    def _create_kpi_section(self, summary: AnalyticsSummaryDTO, kpis: Dict[str, Any]):
        """
        Create KPI summary section.

        Args:
            summary: Analytics summary data
            kpis: Key performance indicators data
        """
        # Create section frame
        section_frame = ttk.LabelFrame(self.content_frame, text="Key Performance Indicators")
        section_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)

        # Create grid for KPIs
        kpi_frame = ttk.Frame(section_frame)
        kpi_frame.pack(fill=tk.X, padx=10, pady=5)

        # Helper function for KPI formatting
        def format_change(value, change_type="percentage"):
            """Format change value with appropriate symbol and style."""
            if value is None:
                return "N/A", "neutral"

            if change_type == "percentage":
                formatted = f"{value:+.1f}%" if value != 0 else "0.0%"
            else:  # absolute
                formatted = f"{value:+.1f}" if value != 0 else "0.0"

            style = "success" if value > 0 else ("danger" if value < 0 else "neutral")
            return formatted, style

        # Create KPI cards for financial metrics
        financial_kpis = kpis.get("financial_kpis", {})

        # Revenue KPI
        revenue_data = financial_kpis.get("revenue", {})
        revenue_value = revenue_data.get("value", 0)
        revenue_change = revenue_data.get("change")
        revenue_change_str, revenue_style = format_change(revenue_change)

        revenue_frame = ttk.Frame(kpi_frame, padding=10)
        revenue_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ttk.Label(
            revenue_frame,
            text="Revenue",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w")

        ttk.Label(
            revenue_frame,
            text=f"${revenue_value:,.2f}",
            font=("Helvetica", 16)
        ).pack(anchor="w")

        change_label = ttk.Label(
            revenue_frame,
            text=f"Change: {revenue_change_str}",
            foreground=COLORS[revenue_style]
        )
        change_label.pack(anchor="w")

        # Profit KPI
        profit_data = financial_kpis.get("profit", {})
        profit_value = profit_data.get("value", 0)
        profit_change = profit_data.get("change")
        profit_change_str, profit_style = format_change(profit_change)

        profit_frame = ttk.Frame(kpi_frame, padding=10)
        profit_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ttk.Label(
            profit_frame,
            text="Profit",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w")

        ttk.Label(
            profit_frame,
            text=f"${profit_value:,.2f}",
            font=("Helvetica", 16)
        ).pack(anchor="w")

        change_label = ttk.Label(
            profit_frame,
            text=f"Change: {profit_change_str}",
            foreground=COLORS[profit_style]
        )
        change_label.pack(anchor="w")

        # Margin KPI
        margin_data = financial_kpis.get("margin", {})
        margin_value = margin_data.get("value", 0)
        margin_change = margin_data.get("change")
        margin_change_str, margin_style = format_change(margin_change, "absolute")

        margin_frame = ttk.Frame(kpi_frame, padding=10)
        margin_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        ttk.Label(
            margin_frame,
            text="Profit Margin",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w")

        ttk.Label(
            margin_frame,
            text=f"{margin_value:.1f}%",
            font=("Helvetica", 16)
        ).pack(anchor="w")

        change_label = ttk.Label(
            margin_frame,
            text=f"Change: {margin_change_str}%",
            foreground=COLORS[margin_style]
        )
        change_label.pack(anchor="w")

        # Customer Retention KPI
        customer_kpis = kpis.get("customer_kpis", {})
        retention_data = customer_kpis.get("retention_rate", {})
        retention_value = retention_data.get("value", 0)
        retention_change = retention_data.get("change")
        retention_change_str, retention_style = format_change(retention_change, "absolute")

        retention_frame = ttk.Frame(kpi_frame, padding=10)
        retention_frame.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        ttk.Label(
            retention_frame,
            text="Customer Retention",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w")

        ttk.Label(
            retention_frame,
            text=f"{retention_value:.1f}%",
            font=("Helvetica", 16)
        ).pack(anchor="w")

        change_label = ttk.Label(
            retention_frame,
            text=f"Change: {retention_change_str}%",
            foreground=COLORS[retention_style]
        )
        change_label.pack(anchor="w")

        # Configure grid
        kpi_frame.columnconfigure(0, weight=1)
        kpi_frame.columnconfigure(1, weight=1)
        kpi_frame.columnconfigure(2, weight=1)
        kpi_frame.columnconfigure(3, weight=1)

    def _create_revenue_section(self, summary: AnalyticsSummaryDTO, kpis: Dict[str, Any]):
        """
        Create revenue and profitability section.

        Args:
            summary: Analytics summary data
            kpis: Key performance indicators data
        """
        # Create section frame
        section_frame = ttk.LabelFrame(self.content_frame, text="Revenue & Profitability")
        section_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)

        # Create grid for charts
        charts_frame = ttk.Frame(section_frame)
        charts_frame.pack(fill=tk.X, padx=10, pady=5)

        # Revenue trend chart
        revenue_frame = ttk.Frame(charts_frame)
        revenue_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Get revenue trend data
        try:
            revenue_data = self.analytics_service.get_trend_data(
                metric_type="revenue",
                time_period=self.time_period.get(),
                months=12 if self.time_period.get() == "monthly" else
                (4 if self.time_period.get() == "quarterly" else 3)
            )

            # Create revenue chart
            self.revenue_chart = LineChart(
                revenue_frame,
                data=revenue_data,
                title="Revenue Trend",
                width=400,
                height=300,
                x_key="period",
                y_key="value",
                x_label="Period",
                y_label="Revenue ($)",
                line_color=COLORS["primary"],
                show_area=True,
                show_grid=True
            )
            self.revenue_chart.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            ttk.Label(revenue_frame, text=f"Error loading revenue chart: {str(e)}").pack(pady=20)

        # Profit margin chart
        margin_frame = ttk.Frame(charts_frame)
        margin_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Get margin trend data
        try:
            margin_data = self.analytics_service.get_trend_data(
                metric_type="margin",
                time_period=self.time_period.get(),
                months=12 if self.time_period.get() == "monthly" else
                (4 if self.time_period.get() == "quarterly" else 3)
            )

            # Create margin chart
            self.margin_chart = LineChart(
                margin_frame,
                data=margin_data,
                title="Profit Margin Trend",
                width=400,
                height=300,
                x_key="period",
                y_key="value",
                x_label="Period",
                y_label="Margin (%)",
                line_color=COLORS["success"],
                show_area=True,
                show_grid=True
            )
            self.margin_chart.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            ttk.Label(margin_frame, text=f"Error loading margin chart: {str(e)}").pack(pady=20)

        # Top products chart
        products_frame = ttk.Frame(charts_frame)
        products_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Get top products
        try:
            top_products = summary.top_products

            if top_products:
                # Prepare data for chart
                products_data = []
                for product in top_products:
                    products_data.append({
                        "label": product.get("name", "Unknown"),
                        "value": product.get("profit", 0)
                    })

                # Create products chart
                product_chart = BarChart(
                    products_frame,
                    data=products_data,
                    title="Top Products by Profit",
                    width=800,
                    height=300,
                    x_key="label",
                    y_key="value",
                    x_label="Product",
                    y_label="Profit ($)",
                    color=COLORS["success"]
                )
                product_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(products_frame, text="No product data available").pack(pady=20)
        except Exception as e:
            ttk.Label(products_frame, text=f"Error loading products chart: {str(e)}").pack(pady=20)

        # Configure grid
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

    def _create_customer_section(self, summary: AnalyticsSummaryDTO, kpis: Dict[str, Any]):
        """
        Create customer analytics section.

        Args:
            summary: Analytics summary data
            kpis: Key performance indicators data
        """
        # Create section frame
        section_frame = ttk.LabelFrame(self.content_frame, text="Customer Analytics")
        section_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)

        # Create grid for charts
        charts_frame = ttk.Frame(section_frame)
        charts_frame.pack(fill=tk.X, padx=10, pady=5)

        # Customer retention trend chart
        retention_frame = ttk.Frame(charts_frame)
        retention_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Get retention trend data
        try:
            retention_data = self.analytics_service.get_trend_data(
                metric_type="customer_retention",
                time_period=self.time_period.get(),
                months=12 if self.time_period.get() == "monthly" else
                (4 if self.time_period.get() == "quarterly" else 3)
            )

            # Create retention chart
            self.customer_chart = LineChart(
                retention_frame,
                data=retention_data,
                title="Customer Retention Trend",
                width=400,
                height=300,
                x_key="period",
                y_key="value",
                x_label="Period",
                y_label="Retention Rate (%)",
                line_color=COLORS["info"],
                show_area=True,
                show_grid=True
            )
            self.customer_chart.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            ttk.Label(retention_frame, text=f"Error loading retention chart: {str(e)}").pack(pady=20)

        # Top customers list
        customers_frame = ttk.Frame(charts_frame)
        customers_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Create customer list
        ttk.Label(
            customers_frame,
            text="Top Customers by Spend",
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Create customer list
        top_customers = summary.top_customers

        if top_customers:
            # Create table header
            header_frame = ttk.Frame(customers_frame)
            header_frame.pack(fill=tk.X, anchor="w")

            ttk.Label(header_frame, text="Customer", width=20, anchor="w", font=("Helvetica", 10, "bold")).pack(
                side=tk.LEFT)
            ttk.Label(header_frame, text="Total Spent", width=15, anchor="e", font=("Helvetica", 10, "bold")).pack(
                side=tk.LEFT)
            ttk.Label(header_frame, text="Orders", width=10, anchor="e", font=("Helvetica", 10, "bold")).pack(
                side=tk.LEFT)
            ttk.Label(header_frame, text="Avg Order", width=15, anchor="e", font=("Helvetica", 10, "bold")).pack(
                side=tk.LEFT)

            # Create customer rows
            for customer in top_customers:
                customer_id = customer.get("customer_id", "Unknown")
                total_spent = customer.get("total_spent", 0)
                total_orders = customer.get("total_orders", 0)
                avg_order_value = customer.get("avg_order_value", 0)

                # Create row
                row_frame = ttk.Frame(customers_frame)
                row_frame.pack(fill=tk.X, anchor="w", pady=2)

                ttk.Label(row_frame, text=f"Customer {customer_id}", width=20, anchor="w").pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"${total_spent:,.2f}", width=15, anchor="e").pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"{total_orders}", width=10, anchor="e").pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"${avg_order_value:,.2f}", width=15, anchor="e").pack(side=tk.LEFT)
        else:
            ttk.Label(customers_frame, text="No customer data available").pack(pady=20)

        # Configure grid
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

    def _create_operations_section(self, summary: AnalyticsSummaryDTO, kpis: Dict[str, Any]):
        """
        Create operations analytics section.

        Args:
            summary: Analytics summary data
            kpis: Key performance indicators data
        """
        # Create section frame
        section_frame = ttk.LabelFrame(self.content_frame, text="Operations Analytics")
        section_frame.pack(fill=tk.X, padx=10, pady=10, ipady=5)

        # Create grid for charts
        charts_frame = ttk.Frame(section_frame)
        charts_frame.pack(fill=tk.X, padx=10, pady=5)

        # Material cost trend chart
        material_frame = ttk.Frame(charts_frame)
        material_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Get material cost trend data
        try:
            if summary.material_cost_trend:
                # Create material cost chart
                self.material_chart = LineChart(
                    material_frame,
                    data=summary.material_cost_trend,
                    title="Material Cost Trend",
                    width=400,
                    height=300,
                    x_key="period",
                    y_key="cost",
                    x_label="Period",
                    y_label="Cost ($)",
                    line_color=COLORS["warning"],
                    show_area=True,
                    show_grid=True
                )
                self.material_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(material_frame, text="No material cost data available").pack(pady=20)
        except Exception as e:
            ttk.Label(material_frame, text=f"Error loading material cost chart: {str(e)}").pack(pady=20)

        # Project efficiency chart
        project_frame = ttk.Frame(charts_frame)
        project_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Get project efficiency data
        try:
            project_data = self.analytics_service.get_trend_data(
                metric_type="project_efficiency",
                time_period=self.time_period.get(),
                months=12 if self.time_period.get() == "monthly" else
                (4 if self.time_period.get() == "quarterly" else 3)
            )

            # Create project efficiency chart
            self.project_chart = LineChart(
                project_frame,
                data=project_data,
                title="Project Efficiency Trend",
                width=400,
                height=300,
                x_key="period",
                y_key="value",
                x_label="Period",
                y_label="Efficiency Score",
                line_color=COLORS["secondary"],
                show_area=True,
                show_grid=True
            )
            self.project_chart.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            ttk.Label(project_frame, text=f"Error loading project efficiency chart: {str(e)}").pack(pady=20)

        # Project completion rate
        completion_frame = ttk.Frame(charts_frame)
        completion_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Get project completion rate
        project_completion = summary.project_completion_rate

        # Create project completion gauge
        ttk.Label(
            completion_frame,
            text="Project Completion Rate",
            font=("Helvetica", 12, "bold")
        ).pack(pady=(10, 5))

        ttk.Label(
            completion_frame,
            text=f"{project_completion:.1f}%",
            font=("Helvetica", 16)
        ).pack(pady=5)

        # Create gauge visualization
        gauge_canvas = tk.Canvas(
            completion_frame,
            width=400,
            height=50,
            bg=COLORS["background"],
            highlightthickness=0
        )
        gauge_canvas.pack(pady=10)

        # Draw gauge background
        gauge_canvas.create_rectangle(
            50, 20, 350, 40,
            fill=COLORS["border"],
            outline=""
        )

        # Draw gauge fill
        fill_width = int(300 * (project_completion / 100))
        gauge_canvas.create_rectangle(
            50, 20, 50 + fill_width, 40,
            fill=COLORS["success"],
            outline=""
        )

        # Draw gauge markers
        for i in range(0, 101, 25):
            x_pos = 50 + (i * 3)
            gauge_canvas.create_line(
                x_pos, 10, x_pos, 50,
                fill=COLORS["text"],
                width=1
            )
            gauge_canvas.create_text(
                x_pos, 5,
                text=f"{i}%",
                fill=COLORS["text"],
                font=("Helvetica", 8),
                anchor="n"
            )

        # Configure grid
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

    def _set_default_date_range(self):
        """Set default date range based on time period."""
        today = datetime.now()

        if self.time_period.get() == "monthly":
            self.start_date = today - timedelta(days=30)
        elif self.time_period.get() == "quarterly":
            self.start_date = today - timedelta(days=90)
        else:  # yearly
            self.start_date = today - timedelta(days=365)

        self.end_date = today

    def _on_period_change(self, event):
        """
        Handle time period change.

        Args:
            event: The combobox selection event
        """
        # Update date range
        self._set_default_date_range()

        # Update date range label
        date_format = "%b %d, %Y"
        date_range_text = f"Date Range: {self.start_date.strftime(date_format)} - {self.end_date.strftime(date_format)}"
        self.date_range_label.config(text=date_range_text)

        # Refresh data
        self.refresh()

    def refresh(self):
        """Refresh analytics data."""
        # Clear existing charts
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Load new data
        self._load_data()