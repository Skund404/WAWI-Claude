# gui/views/reports/sales_reports.py
"""
Sales reports module for the leatherworking ERP system.

This module provides various sales-related reports, including
revenue analysis, product performance, and customer analytics.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import math
import calendar

from gui.views.reports.base_report_view import BaseReportView
from gui.views.reports.export_utils import ReportExporter, get_default_report_filename
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.widgets.enum_combobox import EnumCombobox
from gui.theme import COLORS
from gui.config import DEFAULT_PADDING

from database.models.enums import (
    SaleStatus, PaymentStatus, CustomerTier, ProjectType
)

from di import resolve
from utils.service_access import with_service

logger = logging.getLogger(__name__)


class SalesPerformanceReport(BaseReportView):
    """
    Sales Performance Report.

    Shows sales performance metrics including revenue, profit margins,
    and sales trends over time.
    """

    REPORT_TITLE = "Sales Performance Report"
    REPORT_DESCRIPTION = "Analysis of sales performance metrics over time"

    def __init__(self, parent):
        """
        Initialize the sales performance report view.

        Args:
            parent: The parent widget
        """
        # Initialize filter variables
        self.time_grouping = tk.StringVar()
        self.payment_status_filter = tk.StringVar()
        self.sale_status_filter = tk.StringVar()
        self.include_cancelled = tk.BooleanVar(value=False)

        # Initialize report columns
        self.columns = [
            {"name": "Period", "key": "period", "width": 100},
            {"name": "Number of Sales", "key": "sales_count", "width": 120},
            {"name": "Revenue", "key": "revenue", "width": 120},
            {"name": "Cost", "key": "cost", "width": 120},
            {"name": "Profit", "key": "profit", "width": 120},
            {"name": "Margin %", "key": "margin_percentage", "width": 100},
            {"name": "Avg Sale Value", "key": "avg_sale", "width": 120},
            {"name": "Completed Sales", "key": "completed_count", "width": 130},
            {"name": "Status", "key": "status", "width": 100}
        ]

        # Initialize the visualization data
        self.chart_data = {}

        # Call parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the sales performance report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the filter controls
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Time Grouping filter
        group_frame = ttk.Frame(filter_container)
        group_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(group_frame, text="Group By:").pack(side=tk.LEFT, padx=(0, 5))

        group_options = ["Day", "Week", "Month", "Quarter", "Year"]
        group_combo = ttk.Combobox(group_frame, textvariable=self.time_grouping,
                                   values=group_options, state="readonly", width=10)
        group_combo.pack(side=tk.LEFT)
        self.time_grouping.set("Month")  # Default value

        # Payment Status filter
        payment_frame = ttk.Frame(filter_container)
        payment_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(payment_frame, text="Payment Status:").pack(side=tk.LEFT, padx=(0, 5))

        payment_statuses = ["All"] + [s.value for s in PaymentStatus]
        payment_combo = ttk.Combobox(payment_frame, textvariable=self.payment_status_filter,
                                     values=payment_statuses, state="readonly", width=15)
        payment_combo.pack(side=tk.LEFT)
        self.payment_status_filter.set("All")  # Default value

        # Sale Status filter
        status_frame = ttk.Frame(filter_container)
        status_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(status_frame, text="Sale Status:").pack(side=tk.LEFT, padx=(0, 5))

        # We'll use a subset of sale statuses that make sense for reporting
        sale_statuses = ["All", "completed", "in_production", "in_progress", "cancelled"]
        status_combo = ttk.Combobox(status_frame, textvariable=self.sale_status_filter,
                                    values=sale_statuses, state="readonly", width=15)
        status_combo.pack(side=tk.LEFT)
        self.sale_status_filter.set("All")  # Default value

        # Include Cancelled Checkbox
        cancelled_frame = ttk.Frame(filter_container)
        cancelled_frame.pack(side=tk.LEFT)

        ttk.Checkbutton(cancelled_frame, text="Include Cancelled",
                        variable=self.include_cancelled).pack(side=tk.LEFT)

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.time_grouping.set("Month")
        self.payment_status_filter.set("All")
        self.sale_status_filter.set("All")
        self.include_cancelled.set(False)

    def create_report_content(self, parent):
        """
        Create the main content area for the sales performance report.

        Args:
            parent: The parent widget
        """
        # Create notebook for tabbed views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create data view tab
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="Data View")

        # Create trend view tab
        self.trend_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trend_frame, text="Trend View")

        # Create comparison view tab
        self.comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comparison_frame, text="Year Comparison")

        # Set up the data view
        self._create_data_view(self.data_frame)

        # Set up the trend view
        self._create_trend_view(self.trend_frame)

        # Set up the comparison view
        self._create_comparison_view(self.comparison_frame)

        # Create summary section
        self._create_summary_section(parent)

    def _create_data_view(self, parent):
        """
        Create the data view tab with the treeview.

        Args:
            parent: The parent widget
        """
        # Create column configuration
        columns = [col["name"] for col in self.columns]

        # Create the treeview
        self.tree = EnhancedTreeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        for i, col in enumerate(self.columns):
            self.tree.heading(i, text=col["name"])
            self.tree.column(i, width=col["width"], stretch=tk.NO)

        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

    def _create_trend_view(self, parent):
        """
        Create the trend view tab with visualizations.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simulated chart with canvas or frame elements

        # Create a frame for the chart
        chart_frame = ttk.Frame(parent)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for drawing the chart
        self.chart_canvas = tk.Canvas(
            chart_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.chart_canvas.pack(fill=tk.BOTH, expand=True)

        # Add a placeholder text
        self.chart_canvas.create_text(
            200, 100,
            text="Sales Trend Chart\n\n" +
                 "In a real implementation, this would display a line chart\n" +
                 "showing sales performance trends over time.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def _create_comparison_view(self, parent):
        """
        Create the comparison view tab for comparing periods.

        Args:
            parent: The parent widget
        """
        # Create a frame for the comparison chart
        comparison_frame = ttk.Frame(parent)
        comparison_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for drawing the comparison chart
        self.comparison_canvas = tk.Canvas(
            comparison_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.comparison_canvas.pack(fill=tk.BOTH, expand=True)

        # Add a placeholder text
        self.comparison_canvas.create_text(
            200, 100,
            text="Year-over-Year Comparison Chart\n\n" +
                 "In a real implementation, this would display a bar chart\n" +
                 "comparing sales performance for same periods across years.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def _create_summary_section(self, parent):
        """
        Create the summary section below the tabs.

        Args:
            parent: The parent widget
        """
        # Create a summary frame
        summary_frame = ttk.LabelFrame(parent, text="Performance Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create a grid for the summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Revenue:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_revenue_label = ttk.Label(summary_grid, text="$0.00")
        self.total_revenue_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Profit:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.total_profit_label = ttk.Label(summary_grid, text="$0.00")
        self.total_profit_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Avg Profit Margin:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.avg_margin_label = ttk.Label(summary_grid, text="0.0%")
        self.avg_margin_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="Total Sales:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.total_sales_label = ttk.Label(summary_grid, text="0")
        self.total_sales_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Average Sale:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.avg_sale_label = ttk.Label(summary_grid, text="$0.00")
        self.avg_sale_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="Best Period:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.best_period_label = ttk.Label(summary_grid, text="None")
        self.best_period_label.grid(row=1, column=5, sticky=tk.W)

    def load_report_data(self):
        """Load sales performance data for the report."""
        self.update_status("Loading sales performance data...")
        self.is_loading = True

        try:
            # Get date range
            start_date, end_date = self.date_selector.get_date_range()

            # Get filter values
            time_grouping = self.time_grouping.get()
            payment_status = self.payment_status_filter.get()
            sale_status = self.sale_status_filter.get()
            include_cancelled = self.include_cancelled.get()

            # Build filter criteria
            criteria = {
                "start_date": start_date,
                "end_date": end_date,
                "time_grouping": time_grouping.lower()
            }

            if payment_status != "All":
                criteria["payment_status"] = payment_status

            if sale_status != "All":
                criteria["sale_status"] = sale_status

            if not include_cancelled:
                criteria["exclude_cancelled"] = True

            # Generate sample data for demonstration
            self.report_data = self._get_sample_sales_data(criteria)

            # Update the display
            self.update_report_display()

            # Update status
            self.update_status(f"Loaded sales data for {len(self.report_data)} periods")

        except Exception as e:
            logger.error(f"Error loading sales data: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def update_report_display(self):
        """Update the report display with current data."""
        # Update the data view
        self._update_data_view()

        # Update the summary section
        self._update_summary_section()

        # Update the trend view
        self._update_trend_view()

        # Update the comparison view
        self._update_comparison_view()

    def _update_data_view(self):
        """Update the data view with the current report data."""
        # Clear existing data
        self.tree.clear()

        if not self.report_data:
            return

        # Add data to treeview
        for item in self.report_data:
            values = [item.get(col["key"], "") for col in self.columns]

            # Format currency values
            currency_indices = [i for i, col in enumerate(self.columns)
                                if col["key"] in ["revenue", "cost", "profit", "avg_sale"]]

            for idx in currency_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"${values[idx]:.2f}"

            # Format percentage values
            percent_indices = [i for i, col in enumerate(self.columns)
                               if col["key"] in ["margin_percentage"]]

            for idx in percent_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"{values[idx]:.1f}%"

            # Add tag based on profit margin
            if "margin_percentage" in item:
                margin = item["margin_percentage"]
                if margin < 0:
                    tag = "negative_margin"
                elif margin < 10:
                    tag = "low_margin"
                elif margin > 40:
                    tag = "high_margin"
                else:
                    tag = "normal_margin"
            else:
                tag = "normal_margin"

            self.tree.insert("", tk.END, values=values, tags=(tag,))

        # Configure tag colors
        self.tree.tag_configure("negative_margin", background="#FFCDD2")  # Light red
        self.tree.tag_configure("low_margin", background="#FFF9C4")  # Light yellow
        self.tree.tag_configure("high_margin", background="#C8E6C9")  # Light green

    def _update_summary_section(self):
        """Update the summary section with aggregated metrics."""
        if not self.report_data:
            return

        # Calculate summary metrics
        total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
        total_profit = sum(item.get("profit", 0) for item in self.report_data)
        total_sales = sum(item.get("sales_count", 0) for item in self.report_data)

        # Calculate average profit margin (weighted by revenue)
        weighted_margin = sum(
            item.get("margin_percentage", 0) * item.get("revenue", 0)
            for item in self.report_data if item.get("revenue", 0) > 0
        )
        avg_margin = weighted_margin / total_revenue if total_revenue > 0 else 0

        # Calculate average sale value
        avg_sale = total_revenue / total_sales if total_sales > 0 else 0

        # Find the best period (highest profit)
        best_period = max(self.report_data, key=lambda x: x.get("profit", 0), default=None)
        best_period_name = best_period.get("period", "None") if best_period else "None"

        # Update the summary labels
        self.total_revenue_label.config(text=f"${total_revenue:.2f}")
        self.total_profit_label.config(text=f"${total_profit:.2f}")
        self.avg_margin_label.config(text=f"{avg_margin:.1f}%")
        self.total_sales_label.config(text=str(total_sales))
        self.avg_sale_label.config(text=f"${avg_sale:.2f}")
        self.best_period_label.config(text=best_period_name)

    def _update_trend_view(self):
        """Update the trend view with visualization."""
        # In a real implementation, this would use a proper charting library
        # For now, we'll just create a simple visual representation with canvas

        # Clear the canvas
        self.chart_canvas.delete("all")

        if not self.report_data or len(self.report_data) < 2:
            self.chart_canvas.create_text(
                200, 100,
                text="Insufficient data for trend visualization.\n" +
                     "Please select a date range with more data points.",
                fill="#666666",
                font=("TkDefaultFont", 10)
            )
            return

        # Get canvas dimensions
        canvas_width = self.chart_canvas.winfo_width() or 400
        canvas_height = self.chart_canvas.winfo_height() or 300

        # Set chart margins
        margin_left = 60
        margin_right = 30
        margin_top = 30
        margin_bottom = 60

        # Calculate chart area
        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        # Sort data by period (assuming periods are sortable strings)
        sorted_data = sorted(self.report_data, key=lambda x: x.get("period", ""))

        # Get revenue and profit data
        periods = [item.get("period", "") for item in sorted_data]
        revenues = [item.get("revenue", 0) for item in sorted_data]
        profits = [item.get("profit", 0) for item in sorted_data]

        # Find max value for scaling
        max_value = max(max(revenues, default=0), max(profits, default=0)) * 1.1  # Add 10% margin
        if max_value == 0:
            max_value = 1  # Avoid division by zero

        # Draw axes
        # X-axis
        self.chart_canvas.create_line(
            margin_left, canvas_height - margin_bottom,
                         canvas_width - margin_right, canvas_height - margin_bottom,
            width=2
        )

        # Y-axis
        self.chart_canvas.create_line(
            margin_left, margin_top,
            margin_left, canvas_height - margin_bottom,
            width=2
        )

        # Draw grid lines and labels for Y-axis
        num_y_ticks = 5
        for i in range(num_y_ticks + 1):
            y_value = max_value * i / num_y_ticks
            y_pos = canvas_height - margin_bottom - (i * chart_height / num_y_ticks)

            # Grid line
            self.chart_canvas.create_line(
                margin_left, y_pos,
                canvas_width - margin_right, y_pos,
                dash=(2, 4),
                fill="#CCCCCC"
            )

            # Label
            self.chart_canvas.create_text(
                margin_left - 10, y_pos,
                text=f"${y_value:.0f}",
                anchor="e",
                font=("TkDefaultFont", 8)
            )

        # Draw X-axis labels and tick marks
        num_periods = len(periods)
        if num_periods > 0:
            step = max(1, num_periods // 8)  # Show at most ~8 labels to avoid crowding
            for i in range(0, num_periods, step):
                x_pos = margin_left + (i * chart_width / (num_periods - 1 if num_periods > 1 else 1))

                # Tick mark
                self.chart_canvas.create_line(
                    x_pos, canvas_height - margin_bottom,
                    x_pos, canvas_height - margin_bottom + 5,
                    width=1
                )

                # Label
                self.chart_canvas.create_text(
                    x_pos, canvas_height - margin_bottom + 20,
                    text=periods[i],
                    anchor="center",
                    font=("TkDefaultFont", 8)
                )

        # Plot revenue line
        if num_periods > 1 and max(revenues) > 0:
            for i in range(num_periods - 1):
                x1 = margin_left + (i * chart_width / (num_periods - 1))
                y1 = canvas_height - margin_bottom - (revenues[i] * chart_height / max_value)
                x2 = margin_left + ((i + 1) * chart_width / (num_periods - 1))
                y2 = canvas_height - margin_bottom - (revenues[i + 1] * chart_height / max_value)

                self.chart_canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#2196F3",  # Blue
                    width=2
                )

        # Plot profit line
        if num_periods > 1 and max(profits) > 0:
            for i in range(num_periods - 1):
                x1 = margin_left + (i * chart_width / (num_periods - 1))
                y1 = canvas_height - margin_bottom - (profits[i] * chart_height / max_value)
                x2 = margin_left + ((i + 1) * chart_width / (num_periods - 1))
                y2 = canvas_height - margin_bottom - (profits[i + 1] * chart_height / max_value)

                self.chart_canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#4CAF50",  # Green
                    width=2
                )

        # Add legend
        legend_x = canvas_width - margin_right - 100
        legend_y = margin_top + 20

        # Revenue legend
        self.chart_canvas.create_line(
            legend_x, legend_y,
            legend_x + 30, legend_y,
            fill="#2196F3",
            width=2
        )
        self.chart_canvas.create_text(
            legend_x + 40, legend_y,
            text="Revenue",
            anchor="w",
            font=("TkDefaultFont", 9)
        )

        # Profit legend
        self.chart_canvas.create_line(
            legend_x, legend_y + 20,
                      legend_x + 30, legend_y + 20,
            fill="#4CAF50",
            width=2
        )
        self.chart_canvas.create_text(
            legend_x + 40, legend_y + 20,
            text="Profit",
            anchor="w",
            font=("TkDefaultFont", 9)
        )

        # Add chart title
        self.chart_canvas.create_text(
            canvas_width // 2, margin_top // 2,
            text="Sales Performance Trend",
            font=("TkDefaultFont", 12, "bold")
        )

    def _update_comparison_view(self):
        """Update the comparison view with year-over-year data."""
        # In a real implementation, this would use a proper charting library
        # For now, we'll just create a simple visual representation with canvas

        # Clear the canvas
        self.comparison_canvas.delete("all")

        # This is a placeholder. In a real implementation, we would need to:
        # 1. Group data by month/quarter for each year
        # 2. Align periods across years
        # 3. Draw bars side by side for comparison

        self.comparison_canvas.create_text(
            200, 100,
            text="Year-over-Year Comparison\n\n" +
                 "In a real implementation, this would display a bar chart\n" +
                 "comparing sales performance across different years.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")

        try:
            # Create summary data for the report
            total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
            total_profit = sum(item.get("profit", 0) for item in self.report_data)
            total_sales = sum(item.get("sales_count", 0) for item in self.report_data)

            summary_data = {
                "Total Revenue": f"${total_revenue:.2f}",
                "Total Profit": f"${total_profit:.2f}",
                "Total Sales": str(total_sales),
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to create the PDF
            success = ReportExporter.export_to_pdf(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None,  # Let the user choose the filename
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report exported to PDF successfully")
            else:
                self.update_status("PDF export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def export_excel(self):
        """Export the report to Excel."""
        self.update_status("Exporting to Excel...")

        try:
            # Create summary data for the report
            total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
            total_profit = sum(item.get("profit", 0) for item in self.report_data)
            total_sales = sum(item.get("sales_count", 0) for item in self.report_data)

            summary_data = {
                "Total Revenue": f"${total_revenue:.2f}",
                "Total Profit": f"${total_profit:.2f}",
                "Total Sales": str(total_sales),
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to create the Excel file
            success = ReportExporter.export_to_excel(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None,  # Let the user choose the filename
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report exported to Excel successfully")
            else:
                self.update_status("Excel export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def print_report(self):
        """Print the report."""
        self.update_status("Preparing to print...")

        try:
            # Create summary data for the report
            total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
            total_profit = sum(item.get("profit", 0) for item in self.report_data)
            total_sales = sum(item.get("sales_count", 0) for item in self.report_data)

            summary_data = {
                "Total Revenue": f"${total_revenue:.2f}",
                "Total Profit": f"${total_profit:.2f}",
                "Total Sales": str(total_sales),
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to print
            success = ReportExporter.print_report(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report sent to printer")
            else:
                self.update_status("Print cancelled")

        except Exception as e:
            logger.error(f"Error printing report: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def _get_sample_sales_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample sales performance data for demonstration purposes.

        In a real implementation, this would fetch data from the sales service.

        Args:
            criteria: Filter criteria

        Returns:
            List of sales performance records by period
        """
        # Get date range
        start_date = criteria.get("start_date", datetime.now() - timedelta(days=365))
        end_date = criteria.get("end_date", datetime.now())

        # Get grouping option
        grouping = criteria.get("time_grouping", "month")

        # Generate periods based on date range and grouping
        periods = []

        if grouping == "day":
            # Daily grouping
            current_date = start_date
            while current_date <= end_date:
                periods.append({
                    "period": current_date.strftime("%Y-%m-%d"),
                    "start": current_date,
                    "end": current_date + timedelta(days=1) - timedelta(seconds=1)
                })
                current_date += timedelta(days=1)

        elif grouping == "week":
            # Weekly grouping
            current_date = start_date
            while current_date <= end_date:
                # Find the start of the week (Monday)
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=7) - timedelta(seconds=1)

                periods.append({
                    "period": f"Week {week_start.strftime('%Y-%m-%d')}",
                    "start": week_start,
                    "end": week_end
                })

                current_date = week_start + timedelta(days=7)

        elif grouping == "month":
            # Monthly grouping
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                # Get the last day of the month
                if current_date.month == 12:
                    month_end = current_date.replace(year=current_date.year + 1, month=1) - timedelta(days=1)
                else:
                    month_end = current_date.replace(month=current_date.month + 1) - timedelta(days=1)

                month_end = month_end.replace(hour=23, minute=59, second=59)

                periods.append({
                    "period": current_date.strftime("%Y-%m"),
                    "start": current_date,
                    "end": month_end
                })

                # Move to the next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        elif grouping == "quarter":
            # Quarterly grouping
            current_date = start_date.replace(month=((start_date.month - 1) // 3) * 3 + 1, day=1)
            while current_date <= end_date:
                quarter = (current_date.month - 1) // 3 + 1

                # Calculate quarter end date
                if quarter == 4:
                    quarter_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    quarter_end = current_date.replace(month=quarter * 3 + 1, day=1) - timedelta(days=1)

                quarter_end = quarter_end.replace(hour=23, minute=59, second=59)

                periods.append({
                    "period": f"{current_date.year}-Q{quarter}",
                    "start": current_date,
                    "end": quarter_end
                })

                # Move to the next quarter
                if quarter == 4:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=quarter * 3 + 1)

        elif grouping == "year":
            # Yearly grouping
            current_date = start_date.replace(month=1, day=1)
            while current_date <= end_date:
                year_end = current_date.replace(year=current_date.year + 1) - timedelta(days=1)
                year_end = year_end.replace(hour=23, minute=59, second=59)

                periods.append({
                    "period": str(current_date.year),
                    "start": current_date,
                    "end": year_end
                })

                current_date = current_date.replace(year=current_date.year + 1)

        # Generate sales data for each period
        sales_data = []

        for i, period in enumerate(periods):
            # Generate random but somewhat realistic sales data
            period_factor = 1.0 + 0.2 * math.sin(i / 4.0)  # Cyclic variation
            trend_factor = 1.0 + (i / len(periods)) * 0.5  # Upward trend
            seasonal_factor = 1.0 + 0.3 * math.sin(i / (len(periods) / 4.0) * 2 * math.pi)  # Seasonal variation

            sales_count = int(10 * period_factor * trend_factor * seasonal_factor) + 5
            avg_sale = 150.0 * (1.0 + 0.1 * math.sin(i / 3.0))
            revenue = sales_count * avg_sale

            # Cost is typically 40-70% of revenue for a leatherworking business
            cost_percentage = 40.0 + 30.0 * (0.5 + 0.5 * math.sin(i / 2.0))
            cost = revenue * (cost_percentage / 100.0)

            profit = revenue - cost
            margin_percentage = (profit / revenue) * 100 if revenue > 0 else 0

            completed_count = int(sales_count * (0.7 + 0.2 * math.sin(i / 3.0)))

            # Status based on profit margin
            if margin_percentage < 10:
                status = "Concern"
            elif margin_percentage < 20:
                status = "Average"
            elif margin_percentage < 35:
                status = "Good"
            else:
                status = "Excellent"

            period_data = {
                "period": period["period"],
                "start_date": period["start"],
                "end_date": period["end"],
                "sales_count": sales_count,
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "margin_percentage": margin_percentage,
                "avg_sale": avg_sale,
                "completed_count": completed_count,
                "status": status
            }

            sales_data.append(period_data)

        return sales_data


class CustomerAnalyticsReport(BaseReportView):
    """
    Customer Analytics Report.

    Analyzes customer purchase behavior, segmentation, and value metrics.
    """

    REPORT_TITLE = "Customer Analytics Report"
    REPORT_DESCRIPTION = "Analysis of customer purchasing patterns and segmentation"

    def __init__(self, parent):
        """
        Initialize the customer analytics report view.

        Args:
            parent: The parent widget
        """
        # Initialize filter variables
        self.customer_tier_filter = tk.StringVar()
        self.min_purchases_filter = tk.StringVar()
        self.sort_by = tk.StringVar()

        # Initialize report columns
        self.columns = [
            {"name": "Customer ID", "key": "id", "width": 90},
            {"name": "Customer Name", "key": "name", "width": 180},
            {"name": "Tier", "key": "tier", "width": 90},
            {"name": "Source", "key": "source", "width": 120},
            {"name": "Total Spent", "key": "total_spent", "width": 110},
            {"name": "Orders", "key": "order_count", "width": 70},
            {"name": "Avg Order", "key": "avg_order", "width": 100},
            {"name": "First Purchase", "key": "first_purchase", "width": 120},
            {"name": "Last Purchase", "key": "last_purchase", "width": 120},
            {"name": "Days Since Last", "key": "days_since", "width": 120},
            {"name": "Lifetime Value", "key": "customer_value", "width": 120}
        ]

        # Call parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the customer analytics report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the filter controls
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Customer Tier filter
        tier_frame = ttk.Frame(filter_container)
        tier_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(tier_frame, text="Customer Tier:").pack(side=tk.LEFT, padx=(0, 5))

        tiers = ["All"] + [t.value for t in CustomerTier]
        tier_combo = ttk.Combobox(tier_frame, textvariable=self.customer_tier_filter,
                                  values=tiers, state="readonly", width=12)
        tier_combo.pack(side=tk.LEFT)
        self.customer_tier_filter.set("All")  # Default value

        # Minimum Purchases filter
        min_purchases_frame = ttk.Frame(filter_container)
        min_purchases_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(min_purchases_frame, text="Min Purchases:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(min_purchases_frame, textvariable=self.min_purchases_filter, width=5).pack(side=tk.LEFT)

        # Sort options
        sort_frame = ttk.Frame(filter_container)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sort By:").pack(side=tk.LEFT, padx=(0, 5))

        sort_options = ["Total Spent", "Order Count", "Last Purchase", "Lifetime Value"]
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by,
                                  values=sort_options, state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT)
        self.sort_by.set("Total Spent")  # Default value

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.customer_tier_filter.set("All")
        self.min_purchases_filter.set("")
        self.sort_by.set("Total Spent")

    def create_report_content(self, parent):
        """
        Create the main content area for the customer analytics report.

        Args:
            parent: The parent widget
        """
        # Create notebook for tabbed views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create customer list tab
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="Customer List")

        # Create segmentation tab
        self.segment_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.segment_frame, text="Segmentation")

        # Create retention tab
        self.retention_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.retention_frame, text="Retention Analysis")

        # Set up the list view
        self._create_list_view(self.list_frame)

        # Set up the segmentation view
        self._create_segmentation_view(self.segment_frame)

        # Set up the retention view
        self._create_retention_view(self.retention_frame)

        # Create summary section
        self._create_summary_section(parent)

    def _create_list_view(self, parent):
        """
        Create the customer list view tab.

        Args:
            parent: The parent widget
        """
        # Create column configuration
        columns = [col["name"] for col in self.columns[1:]]  # Skip ID column

        # Create the treeview
        self.tree = EnhancedTreeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        for i, col in enumerate(self.columns[1:], 0):
            self.tree.heading(i, text=col["name"])
            self.tree.column(i, width=col["width"], stretch=tk.NO)

        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

    def _create_segmentation_view(self, parent):
        """
        Create the customer segmentation view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a placeholder

        segmentation_frame = ttk.Frame(parent)
        segmentation_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the segmentation visualization
        self.segmentation_canvas = tk.Canvas(
            segmentation_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.segmentation_canvas.pack(fill=tk.BOTH, expand=True)

        # Add placeholder text
        self.segmentation_canvas.create_text(
            200, 100,
            text="Customer Segmentation Analysis\n\n" +
                 "In a real implementation, this would show charts\n" +
                 "visualizing customer segments by tier, value, and behavior.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def _create_retention_view(self, parent):
        """
        Create the customer retention analysis view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a placeholder

        retention_frame = ttk.Frame(parent)
        retention_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the retention visualization
        self.retention_canvas = tk.Canvas(
            retention_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.retention_canvas.pack(fill=tk.BOTH, expand=True)

        # Add placeholder text
        self.retention_canvas.create_text(
            200, 100,
            text="Customer Retention Analysis\n\n" +
                 "In a real implementation, this would show charts\n" +
                 "tracking customer retention rates and purchase frequency.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def _create_summary_section(self, parent):
        """
        Create the summary section below the tabs.

        Args:
            parent: The parent widget
        """
        # Create a summary frame
        summary_frame = ttk.LabelFrame(parent, text="Customer Analytics Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create a grid for the summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Customers:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_customers_label = ttk.Label(summary_grid, text="0")
        self.total_customers_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Revenue:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.total_revenue_label = ttk.Label(summary_grid, text="$0.00")
        self.total_revenue_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Avg Lifetime Value:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.avg_value_label = ttk.Label(summary_grid, text="$0.00")
        self.avg_value_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="New Customers:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.new_customers_label = ttk.Label(summary_grid, text="0")
        self.new_customers_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Avg Order Size:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.avg_order_label = ttk.Label(summary_grid, text="$0.00")
        self.avg_order_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="Top Customer:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.top_customer_label = ttk.Label(summary_grid, text="None")
        self.top_customer_label.grid(row=1, column=5, sticky=tk.W)

    def load_report_data(self):
        """Load customer analytics data for the report."""
        self.update_status("Loading customer analytics data...")
        self.is_loading = True

        try:
            # Get date range
            start_date, end_date = self.date_selector.get_date_range()

            # Get filter values
            tier = self.customer_tier_filter.get()
            min_purchases = self.min_purchases_filter.get()
            sort_by = self.sort_by.get()

            # Build filter criteria
            criteria = {
                "start_date": start_date,
                "end_date": end_date
            }

            if tier != "All":
                criteria["tier"] = tier

            if min_purchases:
                try:
                    criteria["min_purchases"] = int(min_purchases)
                except ValueError:
                    messagebox.showwarning("Invalid Filter", "Min Purchases must be a number")

            # Translate sort_by to data field
            sort_field_map = {
                "Total Spent": "total_spent",
                "Order Count": "order_count",
                "Last Purchase": "last_purchase",
                "Lifetime Value": "customer_value"
            }

            sort_field = sort_field_map.get(sort_by, "total_spent")
            criteria["sort_by"] = sort_field

            # Generate sample data for demonstration
            self.report_data = self._get_sample_customer_data(criteria)

            # Update the display
            self.update_report_display()

            # Update status
            self.update_status(f"Loaded data for {len(self.report_data)} customers")

        except Exception as e:
            logger.error(f"Error loading customer data: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def update_report_display(self):
        """Update the report display with current data."""
        # Update the list view
        self._update_list_view()

        # Update the summary section
        self._update_summary_section()

        # In a real implementation, we would also update:
        # - Segmentation view
        # - Retention view

    def _update_list_view(self):
        """Update the customer list view with the current report data."""
        # Clear existing data
        self.tree.clear()

        if not self.report_data:
            return

        # Add data to treeview
        for item in self.report_data:
            values = [item.get(col["key"], "") for col in self.columns[1:]]

            # Format currency values
            currency_indices = [i for i, col in enumerate(self.columns[1:])
                                if col["key"] in ["total_spent", "avg_order", "customer_value"]]

            for idx in currency_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"${values[idx]:.2f}"

            # Format date values
            date_indices = [i for i, col in enumerate(self.columns[1:])
                            if col["key"] in ["first_purchase", "last_purchase"]]

            for idx in date_indices:
                date_value = item.get(self.columns[idx + 1]["key"])
                if isinstance(date_value, datetime):
                    values[idx] = date_value.strftime("%Y-%m-%d")

            # Add tag based on customer tier
            tier = item.get("tier", "").lower()

            if tier == "vip":
                tag = "vip_tier"
            elif tier == "premium":
                tag = "premium_tier"
            else:
                tag = "standard_tier"

            self.tree.insert("", tk.END, values=values, tags=(tag,))

        # Configure tag colors
        self.tree.tag_configure("vip_tier", background="#E1F5FE")  # Light blue
        self.tree.tag_configure("premium_tier", background="#F1F8E9")  # Light green

    def _update_summary_section(self):
        """Update the summary section with aggregated metrics."""
        if not self.report_data:
            return

        # Calculate summary metrics
        total_customers = len(self.report_data)
        total_revenue = sum(item.get("total_spent", 0) for item in self.report_data)

        # Average customer lifetime value
        total_value = sum(item.get("customer_value", 0) for item in self.report_data)
        avg_value = total_value / total_customers if total_customers > 0 else 0

        # Count new customers (first purchase within date range)
        today = datetime.now()
        new_customers = sum(1 for item in self.report_data
                            if item.get("days_since_first", 0) <= 90)  # New = last 90 days

        # Average order size
        total_orders = sum(item.get("order_count", 0) for item in self.report_data)
        avg_order = total_revenue / total_orders if total_orders > 0 else 0

        # Find top customer by total spent
        top_customer = max(self.report_data, key=lambda x: x.get("total_spent", 0), default=None)
        top_customer_name = top_customer.get("name", "None") if top_customer else "None"

        # Update the summary labels
        self.total_customers_label.config(text=str(total_customers))
        self.total_revenue_label.config(text=f"${total_revenue:.2f}")
        self.avg_value_label.config(text=f"${avg_value:.2f}")
        self.new_customers_label.config(text=str(new_customers))
        self.avg_order_label.config(text=f"${avg_order:.2f}")
        self.top_customer_label.config(text=top_customer_name)

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")

        try:
            # Create summary data for the report
            total_customers = len(self.report_data)
            total_revenue = sum(item.get("total_spent", 0) for item in self.report_data)

            summary_data = {
                "Total Customers": str(total_customers),
                "Total Revenue": f"${total_revenue:.2f}",
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to create the PDF
            success = ReportExporter.export_to_pdf(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None,  # Let the user choose the filename
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report exported to PDF successfully")
            else:
                self.update_status("PDF export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def export_excel(self):
        """Export the report to Excel."""
        self.update_status("Exporting to Excel...")

        try:
            # Create summary data for the report
            total_customers = len(self.report_data)
            total_revenue = sum(item.get("total_spent", 0) for item in self.report_data)

            summary_data = {
                "Total Customers": str(total_customers),
                "Total Revenue": f"${total_revenue:.2f}",
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to create the Excel file
            success = ReportExporter.export_to_excel(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None,  # Let the user choose the filename
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report exported to Excel successfully")
            else:
                self.update_status("Excel export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def _get_sample_customer_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample customer data for demonstration purposes.

        In a real implementation, this would fetch data from the customer service.

        Args:
            criteria: Filter criteria

        Returns:
            List of customer records with analytics data
        """
        sample_data = []

        # Get date range
        start_date = criteria.get("start_date", datetime.now() - timedelta(days=365))
        end_date = criteria.get("end_date", datetime.now())

        # Sample customer names
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa",
                       "James", "Jennifer", "Matthew", "Elizabeth", "Daniel", "Mary", "Alex", "Laura"]

        last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
                      "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"]

        # Customer tiers from enums
        tiers = [t.value for t in CustomerTier]

        # Customer sources
        sources = ["Website", "Retail Store", "Referral", "Trade Show", "Social Media"]

        # Generate a set of customer records
        for i in range(1, 51):  # 50 sample customers
            # Randomize customer attributes
            first_name = first_names[i % len(first_names)]
            last_name = last_names[(i * 3) % len(last_names)]
            full_name = f"{first_name} {last_name}"

            # Determine tier based on various factors
            tier_idx = min(i % 4, len(tiers) - 1)  # 0-3, mapped to tiers
            tier = tiers[tier_idx]

            # Determine customer source
            source = sources[i % len(sources)]

            # Generate order history data
            # Higher value customers (lower tier_idx) have more orders
            base_orders = 8 - tier_idx * 2  # VIP: 8, standard: 2
            variation = i % 5  # 0-4
            order_count = max(1, base_orders + variation)

            # Generate total spent (higher for VIP customers)
            base_amount = 200.0 * (4 - tier_idx)  # VIP: 800, standard: 200
            per_order = base_amount / (base_orders if base_orders > 0 else 1)
            total_spent = order_count * per_order * (0.8 + 0.4 * (i % 5) / 4.0)

            # Average order value
            avg_order = total_spent / order_count if order_count > 0 else 0

            # Generate purchase dates
            date_range = (end_date - start_date).days
            first_offset = (10 + i * 7) % max(1, date_range)
            first_purchase = start_date + timedelta(days=first_offset)

            # Last purchase - more recent for higher value customers
            recency_factor = 0.7 - (tier_idx * 0.15)  # VIP: more recent
            last_offset = int(date_range * (1.0 - recency_factor)) + (i % 30)
            last_offset = min(date_range - 1, max(0, last_offset))

            last_purchase = end_date - timedelta(days=last_offset)

            # Ensure first purchase is before or same as last purchase
            if first_purchase > last_purchase:
                first_purchase, last_purchase = last_purchase, first_purchase

            # Days since last purchase
            days_since = (datetime.now() - last_purchase).days

            # Days since first purchase
            days_since_first = (datetime.now() - first_purchase).days

            # Customer lifetime value estimation
            time_factor = max(1, min(4, days_since_first / 365.0))  # Years as customer (capped at 4)
            future_value = total_spent * (1.0 + (0.5 / time_factor)) * (1.0 - (days_since / 500.0))
            customer_value = max(total_spent, future_value)

            # Filter based on criteria
            if criteria.get("tier") and criteria["tier"] != tier:
                continue

            if criteria.get("min_purchases") and order_count < criteria["min_purchases"]:
                continue

            # Create the customer record
            customer = {
                "id": 1000 + i,
                "name": full_name,
                "tier": tier,
                "source": source,
                "total_spent": total_spent,
                "order_count": order_count,
                "avg_order": avg_order,
                "first_purchase": first_purchase,
                "last_purchase": last_purchase,
                "days_since": days_since,
                "days_since_first": days_since_first,
                "customer_value": customer_value
            }

            sample_data.append(customer)

        # Sort the data if requested
        sort_field = criteria.get("sort_by", "total_spent")
        reverse = True  # Descending order for most fields

        if sort_field == "last_purchase":
            # Most recent first (largest date)
            sample_data.sort(key=lambda x: x.get(sort_field, datetime.min), reverse=True)
        else:
            # Highest value first
            sample_data.sort(key=lambda x: x.get(sort_field, 0), reverse=True)

        return sample_data


class ProductPerformanceReport(BaseReportView):
    """
    Product Performance Report.

    Analyzes sales and profitability metrics for products.
    """

    REPORT_TITLE = "Product Performance Report"
    REPORT_DESCRIPTION = "Analysis of product sales, margins, and profitability"

    def __init__(self, parent):
        """
        Initialize the product performance report view.

        Args:
            parent: The parent widget
        """
        # Initialize filter variables
        self.product_type_filter = tk.StringVar()
        self.min_sales_filter = tk.StringVar()
        self.sort_by = tk.StringVar()

        # Initialize report columns
        self.columns = [
            {"name": "Product ID", "key": "id", "width": 80},
            {"name": "Product Name", "key": "name", "width": 200},
            {"name": "Type", "key": "type", "width": 120},
            {"name": "Units Sold", "key": "units_sold", "width": 80},
            {"name": "Revenue", "key": "revenue", "width": 100},
            {"name": "Cost", "key": "cost", "width": 100},
            {"name": "Profit", "key": "profit", "width": 100},
            {"name": "Margin %", "key": "margin_percentage", "width": 80},
            {"name": "Avg Price", "key": "avg_price", "width": 90},
            {"name": "Stock Level", "key": "stock_level", "width": 90},
            {"name": "Status", "key": "status", "width": 90}
        ]

        # Call parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the product performance report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the filter controls
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Product Type filter
        type_frame = ttk.Frame(filter_container)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(type_frame, text="Product Type:").pack(side=tk.LEFT, padx=(0, 5))

        # Use project types as product types for this report
        product_types = ["All"] + [t.value for t in ProjectType if t.value not in ["prototype", "repair", "sample"]]
        type_combo = ttk.Combobox(type_frame, textvariable=self.product_type_filter,
                                  values=product_types, state="readonly", width=15)
        type_combo.pack(side=tk.LEFT)
        self.product_type_filter.set("All")  # Default value

        # Minimum Sales filter
        min_sales_frame = ttk.Frame(filter_container)
        min_sales_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(min_sales_frame, text="Min Sales:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(min_sales_frame, textvariable=self.min_sales_filter, width=5).pack(side=tk.LEFT)

        # Sort options
        sort_frame = ttk.Frame(filter_container)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sort By:").pack(side=tk.LEFT, padx=(0, 5))

        sort_options = ["Revenue", "Units Sold", "Profit", "Margin %"]
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by,
                                  values=sort_options, state="readonly", width=10)
        sort_combo.pack(side=tk.LEFT)
        self.sort_by.set("Revenue")  # Default value

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.product_type_filter.set("All")
        self.min_sales_filter.set("")
        self.sort_by.set("Revenue")

    def create_report_content(self, parent):
        """
        Create the main content area for the product performance report.

        Args:
            parent: The parent widget
        """
        # Create notebook for tabbed views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create product list tab
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="Product List")

        # Create category analysis tab
        self.category_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.category_frame, text="Category Analysis")

        # Create performance matrix tab
        self.matrix_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.matrix_frame, text="Performance Matrix")

        # Set up the list view
        self._create_list_view(self.list_frame)

        # Set up the category analysis view
        self._create_category_view(self.category_frame)

        # Set up the performance matrix view
        self._create_matrix_view(self.matrix_frame)

        # Create summary section
        self._create_summary_section(parent)

    def _create_list_view(self, parent):
        """
        Create the product list view tab.

        Args:
            parent: The parent widget
        """
        # Create column configuration
        columns = [col["name"] for col in self.columns[1:]]  # Skip ID column

        # Create the treeview
        self.tree = EnhancedTreeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        for i, col in enumerate(self.columns[1:], 0):
            self.tree.heading(i, text=col["name"])
            self.tree.column(i, width=col["width"], stretch=tk.NO)

        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

    def _create_category_view(self, parent):
        """
        Create the category analysis view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a placeholder

        category_frame = ttk.Frame(parent)
        category_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the category visualization
        self.category_canvas = tk.Canvas(
            category_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.category_canvas.pack(fill=tk.BOTH, expand=True)

        # Add placeholder text
        self.category_canvas.create_text(
            200, 100,
            text="Product Category Analysis\n\n" +
                 "In a real implementation, this would show charts\n" +
                 "comparing performance across product categories.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def _create_matrix_view(self, parent):
        """
        Create the performance matrix view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a placeholder

        matrix_frame = ttk.Frame(parent)
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the matrix visualization
        self.matrix_canvas = tk.Canvas(
            matrix_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.matrix_canvas.pack(fill=tk.BOTH, expand=True)

        # Add placeholder text
        self.matrix_canvas.create_text(
            200, 100,
            text="Product Performance Matrix\n\n" +
                 "In a real implementation, this would show a scatter plot\n" +
                 "visualization of products by sales volume and profit margin.",
            fill="#666666",
            font=("TkDefaultFont", 10)
        )

    def _create_summary_section(self, parent):
        """
        Create the summary section below the tabs.

        Args:
            parent: The parent widget
        """
        # Create a summary frame
        summary_frame = ttk.LabelFrame(parent, text="Product Performance Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create a grid for the summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Products:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_products_label = ttk.Label(summary_grid, text="0")
        self.total_products_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Revenue:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.total_revenue_label = ttk.Label(summary_grid, text="$0.00")
        self.total_revenue_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Profit:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.total_profit_label = ttk.Label(summary_grid, text="$0.00")
        self.total_profit_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="Avg Margin:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.avg_margin_label = ttk.Label(summary_grid, text="0.0%")
        self.avg_margin_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Best Product:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.best_product_label = ttk.Label(summary_grid, text="None")
        self.best_product_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="Best Category:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.best_category_label = ttk.Label(summary_grid, text="None")
        self.best_category_label.grid(row=1, column=5, sticky=tk.W)

    def load_report_data(self):
        """Load product performance data for the report."""
        self.update_status("Loading product performance data...")
        self.is_loading = True

        try:
            # Get date range
            start_date, end_date = self.date_selector.get_date_range()

            # Get filter values
            product_type = self.product_type_filter.get()
            min_sales = self.min_sales_filter.get()
            sort_by = self.sort_by.get()

            # Build filter criteria
            criteria = {
                "start_date": start_date,
                "end_date": end_date
            }

            if product_type != "All":
                criteria["product_type"] = product_type

            if min_sales:
                try:
                    criteria["min_sales"] = int(min_sales)
                except ValueError:
                    messagebox.showwarning("Invalid Filter", "Min Sales must be a number")

            # Translate sort_by to data field
            sort_field_map = {
                "Revenue": "revenue",
                "Units Sold": "units_sold",
                "Profit": "profit",
                "Margin %": "margin_percentage"
            }

            sort_field = sort_field_map.get(sort_by, "revenue")
            criteria["sort_by"] = sort_field

            # Generate sample data for demonstration
            self.report_data = self._get_sample_product_data(criteria)

            # Update the display
            self.update_report_display()

            # Update status
            self.update_status(f"Loaded data for {len(self.report_data)} products")

        except Exception as e:
            logger.error(f"Error loading product performance data: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def update_report_display(self):
        """Update the report display with current data."""
        # Update the list view
        self._update_list_view()

        # Update the summary section
        self._update_summary_section()

        # In a real implementation, we would also update:
        # - Category analysis view
        # - Performance matrix view

    def _update_list_view(self):
        """Update the product list view with the current report data."""
        # Clear existing data
        self.tree.clear()

        if not self.report_data:
            return

        # Add data to treeview
        for item in self.report_data:
            values = [item.get(col["key"], "") for col in self.columns[1:]]

            # Format currency values
            currency_indices = [i for i, col in enumerate(self.columns[1:])
                                if col["key"] in ["revenue", "cost", "profit", "avg_price"]]

            for idx in currency_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"${values[idx]:.2f}"

            # Format percentage values
            percent_indices = [i for i, col in enumerate(self.columns[1:])
                               if col["key"] in ["margin_percentage"]]

            for idx in percent_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"{values[idx]:.1f}%"

            # Add tag based on product performance
            if "margin_percentage" in item:
                margin = item["margin_percentage"]
                if margin < 0:
                    tag = "negative_margin"
                elif margin < 15:
                    tag = "low_margin"
                elif margin > 40:
                    tag = "high_margin"
                else:
                    tag = "normal_margin"
            else:
                tag = "normal_margin"

            self.tree.insert("", tk.END, values=values, tags=(tag,))

        # Configure tag colors
        self.tree.tag_configure("negative_margin", background="#FFCDD2")  # Light red
        self.tree.tag_configure("low_margin", background="#FFF9C4")  # Light yellow
        self.tree.tag_configure("high_margin", background="#C8E6C9")  # Light green

    def _update_summary_section(self):
        """Update the summary section with aggregated metrics."""
        if not self.report_data:
            return

        # Calculate summary metrics
        total_products = len(self.report_data)
        total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
        total_profit = sum(item.get("profit", 0) for item in self.report_data)

        # Calculate average margin (weighted by revenue)
        weighted_margin = sum(
            item.get("margin_percentage", 0) * item.get("revenue", 0)
            for item in self.report_data if item.get("revenue", 0) > 0
        )
        avg_margin = weighted_margin / total_revenue if total_revenue > 0 else 0

        # Find best product by profit
        best_product = max(self.report_data, key=lambda x: x.get("profit", 0), default=None)
        best_product_name = best_product.get("name", "None") if best_product else "None"

        # Find best category by total profit
        category_profits = {}
        for item in self.report_data:
            category = item.get("type", "Unknown")
            profit = item.get("profit", 0)
            if category not in category_profits:
                category_profits[category] = 0
            category_profits[category] += profit

        best_category = max(category_profits.items(), key=lambda x: x[1], default=(None, 0))[0]

        # Update the summary labels
        self.total_products_label.config(text=str(total_products))
        self.total_revenue_label.config(text=f"${total_revenue:.2f}")
        self.total_profit_label.config(text=f"${total_profit:.2f}")
        self.avg_margin_label.config(text=f"{avg_margin:.1f}%")
        self.best_product_label.config(text=best_product_name)
        self.best_category_label.config(text=str(best_category))

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")

        try:
            # Create summary data for the report
            total_products = len(self.report_data)
            total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
            total_profit = sum(item.get("profit", 0) for item in self.report_data)

            summary_data = {
                "Total Products": str(total_products),
                "Total Revenue": f"${total_revenue:.2f}",
                "Total Profit": f"${total_profit:.2f}",
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to create the PDF
            success = ReportExporter.export_to_pdf(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None,  # Let the user choose the filename
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report exported to PDF successfully")
            else:
                self.update_status("PDF export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def export_excel(self):
        """Export the report to Excel."""
        self.update_status("Exporting to Excel...")

        try:
            # Create summary data for the report
            total_products = len(self.report_data)
            total_revenue = sum(item.get("revenue", 0) for item in self.report_data)
            total_profit = sum(item.get("profit", 0) for item in self.report_data)

            summary_data = {
                "Total Products": str(total_products),
                "Total Revenue": f"${total_revenue:.2f}",
                "Total Profit": f"${total_profit:.2f}",
                "Date Range": f"{self.date_selector.start_date.get()} to {self.date_selector.end_date.get()}",
                "Report Date": datetime.now().strftime("%Y-%m-%d")
            }

            # Use the ReportExporter to create the Excel file
            success = ReportExporter.export_to_excel(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None,  # Let the user choose the filename
                include_summary=True,
                summary_data=summary_data
            )

            if success:
                self.update_status("Report exported to Excel successfully")
            else:
                self.update_status("Excel export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def _get_sample_product_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample product performance data for demonstration purposes.

        In a real implementation, this would fetch data from the product and sales services.

        Args:
            criteria: Filter criteria

        Returns:
            List of product records with performance data
        """
        sample_data = []

        # Use project types as product types
        product_types = [t.value for t in ProjectType if t.value not in ["prototype", "repair", "sample"]]

        # Filter by product type if specified
        if criteria.get("product_type") and criteria["product_type"] != "All":
            product_types = [t for t in product_types if t == criteria["product_type"]]

        # Sample product names for each type
        type_products = {
            "wallet": ["Bifold Wallet", "Trifold Wallet", "Minimalist Card Holder", "Money Clip Wallet",
                       "Passport Wallet"],
            "briefcase": ["Executive Briefcase", "Laptop Briefcase", "Document Case", "Portfolio Case"],
            "messenger_bag": ["Classic Messenger", "Laptop Messenger", "Commuter Bag", "Crossbody Satchel"],
            "tote_bag": ["Shopping Tote", "Beach Tote", "Market Tote", "Daily Carry Tote"],
            "backpack": ["Daypack", "Laptop Backpack", "Roll-Top Backpack", "Commuter Pack"],
            "belt": ["Dress Belt", "Casual Belt", "Work Belt", "Braided Belt"],
            "watch_strap": ["Classic Watch Band", "NATO Style Band", "Rally Band", "Double-Wrap Band"],
            "notebook_cover": ["A5 Journal Cover", "Pocket Notebook Wrap", "Refillable Planner", "Sketchbook Cover"],
            "phone_case": ["iPhone Sleeve", "Android Case", "Snap-On Case", "Folio Cover"],
            "key_case": ["Key Holder", "Keychain", "Key Organizer", "Keyfob"],
            "custom": ["Custom Order", "Bespoke Design", "Custom Commission"]
        }

        # Generate a set of product records
        product_id = 1000

        for product_type in product_types:
            # Get product names for this type
            product_names = type_products.get(product_type, ["Unknown Product"])

            for product_name in product_names:
                # Generate performance metrics with some variation
                base_price = 0

                # Set base price based on product type
                if product_type == "wallet":
                    base_price = 60
                elif product_type == "briefcase":
                    base_price = 350
                elif product_type == "messenger_bag":
                    base_price = 250
                elif product_type == "tote_bag":
                    base_price = 180
                elif product_type == "backpack":
                    base_price = 200
                elif product_type == "belt":
                    base_price = 80
                elif product_type == "watch_strap":
                    base_price = 70
                elif product_type == "notebook_cover":
                    base_price = 50
                elif product_type == "phone_case":
                    base_price = 40
                elif product_type == "key_case":
                    base_price = 30
                elif product_type == "custom":
                    base_price = 300

                # Adjust price with some variation
                price_variation = 0.8 + (product_id % 5) * 0.1  # 0.8-1.2
                avg_price = base_price * price_variation

                # Generate units sold with variation by product type
                # Higher priced items tend to sell in lower quantities
                base_quantity = int(100 * (1.0 - (base_price / 400) * 0.7))  # Higher price = lower quantity
                quantity_variation = 0.5 + (product_id % 10) * 0.1  # 0.5-1.4
                units_sold = int(base_quantity * quantity_variation)

                # Calculate revenue
                revenue = units_sold * avg_price

                # Calculate cost and profit
                # Cost percentage varies by product type and complexity
                base_cost_pct = 35 + (product_id % 20)  # 35-54% cost
                cost = revenue * (base_cost_pct / 100.0)
                profit = revenue - cost

                # Calculate margin percentage
                margin_percentage = (profit / revenue) * 100 if revenue > 0 else 0

                # Determine stock level and status
                stock_level = int(units_sold * (0.1 + (product_id % 5) * 0.05))  # 10-30% of sales

                if stock_level == 0:
                    status = "Out of Stock"
                elif stock_level < units_sold * 0.1:
                    status = "Low Stock"
                elif stock_level > units_sold:
                    status = "Overstocked"
                else:
                    status = "In Stock"

                # Filter based on criteria
                if criteria.get("min_sales") and units_sold < criteria["min_sales"]:
                    continue

                # Create the product record
                product = {
                    "id": product_id,
                    "name": product_name,
                    "type": product_type,
                    "units_sold": units_sold,
                    "revenue": revenue,
                    "cost": cost,
                    "profit": profit,
                    "margin_percentage": margin_percentage,
                    "avg_price": avg_price,
                    "stock_level": stock_level,
                    "status": status
                }

                sample_data.append(product)
                product_id += 1

        # Sort the data if requested
        sort_field = criteria.get("sort_by", "revenue")
        sample_data.sort(key=lambda x: x.get(sort_field, 0), reverse=True)

        return sample_data