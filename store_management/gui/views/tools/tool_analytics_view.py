# gui/views/tools/tool_analytics_view.py
"""
Tool analytics view for the leatherworking ERP system.

This view provides detailed analytics and reports about tool usage,
maintenance history, and other metrics.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import calendar
import math

from gui.base.base_view import BaseView
from gui.theme import COLORS
from gui.config import Config
from utils.service_access import with_service


class ToolAnalyticsView(BaseView):
    """Tool analytics view for visualizing tool usage and maintenance data."""

    def __init__(self, parent):
        """Initialize the tool analytics view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Tool Analytics"
        self.icon = "📊"  # Analytics icon
        self.logger = logging.getLogger(__name__)

        # Track the currently selected timeframe and chart
        self.current_timeframe = "month"
        self.current_chart = "usage"

        self.build()

    def build(self):
        """Build the analytics view layout."""
        super().build()

        # Update header subtitle
        self.header_subtitle.config(text="Analyze tool usage, maintenance, and costs")

        # Create main content frame
        content_frame = ttk.Frame(self.content_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create controls frame
        controls_frame = ttk.Frame(content_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        # Create chart selection
        chart_frame = ttk.LabelFrame(controls_frame, text="Chart Type")
        chart_frame.pack(side=tk.LEFT, padx=10, pady=5)

        self.chart_var = tk.StringVar(value="usage")
        ttk.Radiobutton(chart_frame, text="Usage", value="usage",
                        variable=self.chart_var, command=self.on_chart_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(chart_frame, text="Maintenance", value="maintenance",
                        variable=self.chart_var, command=self.on_chart_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(chart_frame, text="Costs", value="costs",
                        variable=self.chart_var, command=self.on_chart_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(chart_frame, text="Status", value="status",
                        variable=self.chart_var, command=self.on_chart_change).pack(side=tk.LEFT, padx=5)

        # Create timeframe selection
        timeframe_frame = ttk.LabelFrame(controls_frame, text="Timeframe")
        timeframe_frame.pack(side=tk.LEFT, padx=10, pady=5)

        self.timeframe_var = tk.StringVar(value="month")
        ttk.Radiobutton(timeframe_frame, text="Month", value="month",
                        variable=self.timeframe_var, command=self.on_timeframe_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(timeframe_frame, text="Quarter", value="quarter",
                        variable=self.timeframe_var, command=self.on_timeframe_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(timeframe_frame, text="Year", value="year",
                        variable=self.timeframe_var, command=self.on_timeframe_change).pack(side=tk.LEFT, padx=5)

        # Create date selection
        date_frame = ttk.Frame(controls_frame)
        date_frame.pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT, padx=5)

        # Month and year spinners
        date_spinners_frame = ttk.Frame(date_frame)
        date_spinners_frame.pack(side=tk.LEFT)

        # Month selection
        self.month_var = tk.IntVar(value=datetime.now().month)
        month_spinner = ttk.Spinbox(date_spinners_frame, from_=1, to=12, width=3,
                                    textvariable=self.month_var, command=self.on_date_change)
        month_spinner.grid(row=0, column=0)

        ttk.Label(date_spinners_frame, text="/").grid(row=0, column=1)

        # Year selection
        current_year = datetime.now().year
        self.year_var = tk.IntVar(value=current_year)
        year_spinner = ttk.Spinbox(date_spinners_frame, from_=current_year - 10, to=current_year + 1, width=5,
                                   textvariable=self.year_var, command=self.on_date_change)
        year_spinner.grid(row=0, column=2)

        # Create chart area
        self.chart_frame = ttk.Frame(content_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create stats area
        self.stats_frame = ttk.LabelFrame(content_frame, text="Statistics")
        self.stats_frame.pack(fill=tk.X, pady=5)

        # Create report options
        report_frame = ttk.Frame(content_frame)
        report_frame.pack(fill=tk.X, pady=10)

        ttk.Button(report_frame, text="Generate Report",
                   command=self.on_generate_report).pack(side=tk.LEFT, padx=5)

        # Export options dropdown
        ttk.Button(report_frame, text="Export Data",
                   command=self.on_export_data).pack(side=tk.LEFT, padx=5)

        # Load initial chart
        self.load_chart()

    def on_chart_change(self):
        """Handle chart type change."""
        self.current_chart = self.chart_var.get()
        self.load_chart()

    def on_timeframe_change(self):
        """Handle timeframe change."""
        self.current_timeframe = self.timeframe_var.get()
        self.load_chart()

    def on_date_change(self):
        """Handle date change."""
        self.load_chart()

    def get_date_range(self):
        """Get the start and end dates based on the current timeframe.

        Returns:
            Tuple of (start_date, end_date)
        """
        year = self.year_var.get()
        month = self.month_var.get()

        if self.current_timeframe == "month":
            # Get days in the selected month
            last_day = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, last_day, 23, 59, 59)
        elif self.current_timeframe == "quarter":
            # Calculate the quarter
            quarter = (month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3

            start_date = datetime(year, start_month, 1)
            last_day = calendar.monthrange(year, end_month)[1]
            end_date = datetime(year, end_month, last_day, 23, 59, 59)
        else:  # year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)

        return start_date, end_date

    def load_chart(self):
        """Load the appropriate chart based on current selections."""
        # Clear existing chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        # Clear existing stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        # Get date range
        start_date, end_date = self.get_date_range()

        # Load the appropriate chart
        if self.current_chart == "usage":
            self.load_usage_chart(start_date, end_date)
        elif self.current_chart == "maintenance":
            self.load_maintenance_chart(start_date, end_date)
        elif self.current_chart == "costs":
            self.load_cost_chart(start_date, end_date)
        elif self.current_chart == "status":
            self.load_status_chart()

    @with_service("tool_checkout_service")
    def load_usage_chart(self, start_date, end_date, service=None):
        """Load the tool usage chart.

        Args:
            start_date: The start date for the chart
            end_date: The end date for the chart
            service: The tool checkout service injected by the decorator
        """
        try:
            # Get checkout data for the date range
            checkouts = service.get_checkouts(
                criteria={
                    "checked_out_date__gte": start_date,
                    "checked_out_date__lte": end_date
                },
                limit=1000,
                include_tool=True
            )

            # Count checkouts by date
            checkout_counts = {}

            # Create time buckets based on timeframe
            if self.current_timeframe == "month":
                # Daily buckets for the month
                days_in_month = (end_date - start_date).days + 1
                for day in range(days_in_month):
                    date = start_date + timedelta(days=day)
                    checkout_counts[date.strftime("%d")] = 0

                # Count checkouts by day
                for checkout in checkouts:
                    if checkout.checked_out_date:
                        day = checkout.checked_out_date.strftime("%d")
                        checkout_counts[day] = checkout_counts.get(day, 0) + 1

                x_label = "Day of Month"

            elif self.current_timeframe == "quarter":
                # Weekly buckets for the quarter
                weeks_in_quarter = math.ceil((end_date - start_date).days / 7)
                for week in range(weeks_in_quarter):
                    week_start = start_date + timedelta(weeks=week)
                    week_label = f"{week_start.strftime('%m/%d')}"
                    checkout_counts[week_label] = 0

                # Count checkouts by week
                for checkout in checkouts:
                    if checkout.checked_out_date:
                        week_num = (checkout.checked_out_date - start_date).days // 7
                        week_start = start_date + timedelta(weeks=week_num)
                        week_label = f"{week_start.strftime('%m/%d')}"
                        checkout_counts[week_label] = checkout_counts.get(week_label, 0) + 1

                x_label = "Week Starting"

            else:  # year
                # Monthly buckets for the year
                for month in range(1, 13):
                    month_name = datetime(year=start_date.year, month=month, day=1).strftime("%b")
                    checkout_counts[month_name] = 0

                # Count checkouts by month
                for checkout in checkouts:
                    if checkout.checked_out_date:
                        month_name = checkout.checked_out_date.strftime("%b")
                        checkout_counts[month_name] = checkout_counts.get(month_name, 0) + 1

                x_label = "Month"

            # Create the chart
            self.create_bar_chart(
                self.chart_frame,
                "Tool Checkouts",
                x_label,
                "Number of Checkouts",
                checkout_counts
            )

            # Calculate statistics
            total_checkouts = len(checkouts)

            # Count unique tools
            unique_tools = set()
            for checkout in checkouts:
                if checkout.tool_id:
                    unique_tools.add(checkout.tool_id)

            # Count by user
            user_counts = {}
            for checkout in checkouts:
                if checkout.checked_out_by:
                    user_counts[checkout.checked_out_by] = user_counts.get(checkout.checked_out_by, 0) + 1

            # Find most frequent user
            most_frequent_user = ""
            most_frequent_count = 0
            for user, count in user_counts.items():
                if count > most_frequent_count:
                    most_frequent_user = user
                    most_frequent_count = count

            # Add statistics to the stats frame
            ttk.Label(self.stats_frame, text=f"Total Checkouts: {total_checkouts}").pack(side=tk.LEFT, padx=20, pady=5)
            ttk.Label(self.stats_frame, text=f"Unique Tools Used: {len(unique_tools)}").pack(side=tk.LEFT, padx=20,
                                                                                             pady=5)
            if most_frequent_user:
                ttk.Label(self.stats_frame,
                          text=f"Most Active User: {most_frequent_user} ({most_frequent_count} checkouts)").pack(
                    side=tk.LEFT, padx=20, pady=5)

        except Exception as e:
            self.logger.error(f"Error loading usage chart: {e}")
            self.show_chart_error("Error loading usage data")

    @with_service("tool_maintenance_service")
    def load_maintenance_chart(self, start_date, end_date, service=None):
        """Load the tool maintenance chart.

        Args:
            start_date: The start date for the chart
            end_date: The end date for the chart
            service: The tool maintenance service injected by the decorator
        """
        try:
            # Get maintenance data for the date range
            maintenance_records = service.get_maintenance_records(
                criteria={
                    "maintenance_date__gte": start_date,
                    "maintenance_date__lte": end_date
                },
                limit=1000,
                include_tool=True
            )

            # Count maintenance by type
            type_counts = {}

            for record in maintenance_records:
                if record.maintenance_type:
                    type_counts[record.maintenance_type] = type_counts.get(record.maintenance_type, 0) + 1

            # Create the chart
            self.create_pie_chart(
                self.chart_frame,
                "Maintenance by Type",
                type_counts
            )

            # Count maintenance by date
            date_counts = {}

            # Create time buckets based on timeframe
            if self.current_timeframe == "month":
                # Daily buckets for the month
                days_in_month = (end_date - start_date).days + 1
                for day in range(days_in_month):
                    date = start_date + timedelta(days=day)
                    date_counts[date.strftime("%d")] = 0

                # Count maintenance by day
                for record in maintenance_records:
                    if record.maintenance_date:
                        day = record.maintenance_date.strftime("%d")
                        date_counts[day] = date_counts.get(day, 0) + 1

                x_label = "Day of Month"

            elif self.current_timeframe == "quarter":
                # Weekly buckets for the quarter
                weeks_in_quarter = math.ceil((end_date - start_date).days / 7)
                for week in range(weeks_in_quarter):
                    week_start = start_date + timedelta(weeks=week)
                    week_label = f"{week_start.strftime('%m/%d')}"
                    date_counts[week_label] = 0

                # Count maintenance by week
                for record in maintenance_records:
                    if record.maintenance_date:
                        week_num = (record.maintenance_date - start_date).days // 7
                        if week_num >= 0 and week_num < weeks_in_quarter:
                            week_start = start_date + timedelta(weeks=week_num)
                            week_label = f"{week_start.strftime('%m/%d')}"
                            date_counts[week_label] = date_counts.get(week_label, 0) + 1

                x_label = "Week Starting"

            else:  # year
                # Monthly buckets for the year
                for month in range(1, 13):
                    month_name = datetime(year=start_date.year, month=month, day=1).strftime("%b")
                    date_counts[month_name] = 0

                # Count maintenance by month
                for record in maintenance_records:
                    if record.maintenance_date:
                        month_name = record.maintenance_date.strftime("%b")
                        date_counts[month_name] = date_counts.get(month_name, 0) + 1

                x_label = "Month"

            # Create the timeline chart
            timeline_frame = ttk.Frame(self.chart_frame)
            timeline_frame.pack(fill=tk.X, expand=True, pady=10)

            self.create_bar_chart(
                timeline_frame,
                "Maintenance Timeline",
                x_label,
                "Number of Maintenance Activities",
                date_counts
            )

            # Calculate statistics
            total_maintenance = len(maintenance_records)

            # Count unique tools
            unique_tools = set()
            for record in maintenance_records:
                if record.tool_id:
                    unique_tools.add(record.tool_id)

            # Calculate total cost
            total_cost = sum(record.cost or 0 for record in maintenance_records)

            # Add statistics to the stats frame
            ttk.Label(self.stats_frame, text=f"Total Maintenance Activities: {total_maintenance}").pack(side=tk.LEFT,
                                                                                                        padx=20, pady=5)
            ttk.Label(self.stats_frame, text=f"Unique Tools Maintained: {len(unique_tools)}").pack(side=tk.LEFT,
                                                                                                   padx=20, pady=5)
            ttk.Label(self.stats_frame, text=f"Total Cost: ${total_cost:.2f}").pack(side=tk.LEFT, padx=20, pady=5)

        except Exception as e:
            self.logger.error(f"Error loading maintenance chart: {e}")
            self.show_chart_error("Error loading maintenance data")

    @with_service("tool_maintenance_service")
    @with_service("tool_checkout_service")
    def load_cost_chart(self, start_date, end_date, tool_maintenance_service=None, tool_checkout_service=None):
        """Load the tool cost chart.

        Args:
            start_date: The start date for the chart
            end_date: The end date for the chart
            tool_maintenance_service: The tool maintenance service injected by the decorator
            tool_checkout_service: The tool checkout service injected by the decorator
        """
        try:
            # Get maintenance data for the date range
            maintenance_records = tool_maintenance_service.get_maintenance_records(
                criteria={
                    "maintenance_date__gte": start_date,
                    "maintenance_date__lte": end_date
                },
                limit=1000,
                include_tool=True
            )

            # Group costs by tool category
            category_costs = {}

            for record in maintenance_records:
                if record.tool and hasattr(record.tool, "tool_category") and record.cost:
                    category = record.tool["tool_category"]
                    if category:
                        category_costs[category] = category_costs.get(category, 0) + record.cost

            # Create the chart
            self.create_pie_chart(
                self.chart_frame,
                "Maintenance Costs by Tool Category",
                category_costs
            )

            # Create cost timeline
            cost_timeline = {}

            # Create time buckets based on timeframe
            if self.current_timeframe == "month":
                # Weekly buckets for the month
                weeks_in_month = math.ceil((end_date - start_date).days / 7)
                for week in range(weeks_in_month):
                    week_start = start_date + timedelta(weeks=week)
                    week_label = f"Week {week + 1}"
                    cost_timeline[week_label] = 0

                # Sum costs by week
                for record in maintenance_records:
                    if record.maintenance_date and record.cost:
                        week_num = (record.maintenance_date - start_date).days // 7
                        if week_num >= 0 and week_num < weeks_in_month:
                            week_label = f"Week {week_num + 1}"
                            cost_timeline[week_label] = cost_timeline.get(week_label, 0) + record.cost

                x_label = "Week"

            elif self.current_timeframe == "quarter":
                # Monthly buckets for the quarter
                months = set()
                current = start_date
                while current <= end_date:
                    month_name = current.strftime("%b")
                    months.add(month_name)
                    # Move to next month
                    if current.month == 12:
                        current = datetime(current.year + 1, 1, 1)
                    else:
                        current = datetime(current.year, current.month + 1, 1)

                for month in sorted(months, key=lambda m: datetime.strptime(m, "%b").month):
                    cost_timeline[month] = 0

                # Sum costs by month
                for record in maintenance_records:
                    if record.maintenance_date and record.cost:
                        month_name = record.maintenance_date.strftime("%b")
                        cost_timeline[month_name] = cost_timeline.get(month_name, 0) + record.cost

                x_label = "Month"

            else:  # year
                # Quarterly buckets for the year
                for quarter in range(1, 5):
                    cost_timeline[f"Q{quarter}"] = 0

                # Sum costs by quarter
                for record in maintenance_records:
                    if record.maintenance_date and record.cost:
                        quarter = (record.maintenance_date.month - 1) // 3 + 1
                        cost_timeline[f"Q{quarter}"] = cost_timeline.get(f"Q{quarter}", 0) + record.cost

                x_label = "Quarter"

            # Create the timeline chart
            timeline_frame = ttk.Frame(self.chart_frame)
            timeline_frame.pack(fill=tk.X, expand=True, pady=10)

            self.create_bar_chart(
                timeline_frame,
                "Maintenance Cost Timeline",
                x_label,
                "Maintenance Cost ($)",
                cost_timeline
            )

            # Calculate statistics
            total_cost = sum(record.cost or 0 for record in maintenance_records)
            avg_cost_per_record = total_cost / len(maintenance_records) if maintenance_records else 0

            # Count unique tools
            unique_tools = set()
            tool_costs = {}
            for record in maintenance_records:
                if record.tool_id:
                    unique_tools.add(record.tool_id)
                    if record.cost:
                        tool_costs[record.tool_id] = tool_costs.get(record.tool_id, 0) + record.cost

            avg_cost_per_tool = total_cost / len(unique_tools) if unique_tools else 0

            # Find most expensive tool
            most_expensive_tool = None
            highest_cost = 0
            for tool_id, cost in tool_costs.items():
                if cost > highest_cost:
                    most_expensive_tool = tool_id
                    highest_cost = cost

            # Get tool name for most expensive tool
            most_expensive_name = "Unknown"
            if most_expensive_tool:
                for record in maintenance_records:
                    if record.tool_id == most_expensive_tool and record.tool:
                        most_expensive_name = record.tool["name"]
                        break

            # Add statistics to the stats frame
            ttk.Label(self.stats_frame, text=f"Total Maintenance Cost: ${total_cost:.2f}").pack(side=tk.LEFT, padx=20,
                                                                                                pady=5)
            ttk.Label(self.stats_frame, text=f"Avg Cost per Maintenance: ${avg_cost_per_record:.2f}").pack(side=tk.LEFT,
                                                                                                           padx=20,
                                                                                                           pady=5)
            ttk.Label(self.stats_frame, text=f"Avg Cost per Tool: ${avg_cost_per_tool:.2f}").pack(side=tk.LEFT, padx=20,
                                                                                                  pady=5)
            if most_expensive_tool:
                ttk.Label(self.stats_frame,
                          text=f"Most Expensive Tool: {most_expensive_name} (${highest_cost:.2f})").pack(
                    side=tk.LEFT, padx=20, pady=5)

        except Exception as e:
            self.logger.error(f"Error loading cost chart: {e}")
            self.show_chart_error("Error loading cost data")

    @with_service("tool_service")
    def load_status_chart(self, service=None):
        """Load the tool status chart.

        Args:
            service: The tool service injected by the decorator
        """
        try:
            # Get tool status counts
            status_counts = {}

            # Get counts by status
            in_stock = service.count_tools(criteria={"status": "IN_STOCK"})
            checked_out = service.count_tools(criteria={"status": "CHECKED_OUT"})
            maintenance = service.count_tools(criteria={"status": "MAINTENANCE"})
            damaged = service.count_tools(criteria={"status": "DAMAGED"})
            lost = service.count_tools(criteria={"status": "LOST"})

            # Add to counts dictionary
            status_counts["In Stock"] = in_stock
            status_counts["Checked Out"] = checked_out
            status_counts["In Maintenance"] = maintenance
            status_counts["Damaged"] = damaged
            status_counts["Lost"] = lost

            # Create the chart
            self.create_pie_chart(
                self.chart_frame,
                "Tool Status Distribution",
                status_counts
            )

            # Get tool category distribution
            categories = service.get_tool_categories()

            category_counts = {}
            for category in categories:
                count = service.count_tools(criteria={"tool_category": category})
                if count > 0:
                    category_counts[category] = count

            # Create category chart
            category_frame = ttk.Frame(self.chart_frame)
            category_frame.pack(fill=tk.X, expand=True, pady=10)

            self.create_bar_chart(
                category_frame,
                "Tools by Category",
                "Category",
                "Number of Tools",
                category_counts
            )

            # Calculate statistics
            total_tools = sum(status_counts.values())
            active_tools = in_stock + checked_out
            inactive_tools = maintenance + damaged + lost

            # Calculate percentages
            in_stock_pct = in_stock / total_tools * 100 if total_tools else 0
            active_pct = active_tools / total_tools * 100 if total_tools else 0

            # Add statistics to the stats frame
            ttk.Label(self.stats_frame, text=f"Total Tools: {total_tools}").pack(side=tk.LEFT, padx=20, pady=5)
            ttk.Label(self.stats_frame, text=f"Active Tools: {active_tools} ({active_pct:.1f}%)").pack(side=tk.LEFT,
                                                                                                       padx=20, pady=5)
            ttk.Label(self.stats_frame, text=f"In Stock: {in_stock} ({in_stock_pct:.1f}%)").pack(side=tk.LEFT, padx=20,
                                                                                                 pady=5)
            ttk.Label(self.stats_frame, text=f"Inactive/Unavailable: {inactive_tools}").pack(side=tk.LEFT, padx=20,
                                                                                             pady=5)

        except Exception as e:
            self.logger.error(f"Error loading status chart: {e}")
            self.show_chart_error("Error loading status data")

    def create_bar_chart(self, parent, title, x_label, y_label, data):
        """Create a simple bar chart.

        Args:
            parent: The parent widget
            title: The chart title
            x_label: The x-axis label
            y_label: The y-axis label
            data: Dictionary of label -> value
        """
        # Create a frame for the chart
        chart_frame = ttk.LabelFrame(parent, text=title)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add a canvas for drawing
        canvas = tk.Canvas(chart_frame, bg="white", height=300)
        canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Check if we have data
        if not data:
            self.show_chart_error("No data available for the selected period", canvas)
            return

        # Get the max value for scaling
        max_value = max(data.values()) if data.values() else 0

        if max_value == 0:
            self.show_chart_error("No data available for the selected period", canvas)
            return

        # Calculate chart dimensions
        chart_width = canvas.winfo_width() - 60
        chart_height = canvas.winfo_height() - 60

        # Make sure we have reasonable dimensions
        if chart_width < 100:
            chart_width = 300
        if chart_height < 100:
            chart_height = 250

        # Set margins
        left_margin = 50
        bottom_margin = 50
        top_margin = 20
        right_margin = 10

        # Calculate bar dimensions
        bar_count = len(data)
        if bar_count > 0:
            bar_width = (chart_width - left_margin - right_margin) / bar_count
            bar_spacing = bar_width * 0.2
            bar_width = bar_width - bar_spacing
        else:
            bar_width = 20
            bar_spacing = 5

        # Draw axes
        canvas.create_line(left_margin, top_margin, left_margin, chart_height + top_margin, width=2)
        canvas.create_line(left_margin, chart_height + top_margin, chart_width + left_margin, chart_height + top_margin,
                           width=2)

        # Draw labels
        canvas.create_text(chart_width / 2 + left_margin, chart_height + bottom_margin - 10,
                           text=x_label, font=("Arial", 10))
        canvas.create_text(10, top_margin + chart_height / 2, text=y_label, angle=90, font=("Arial", 10))

        # Draw y-axis ticks
        num_ticks = 5
        for i in range(num_ticks + 1):
            y = top_margin + chart_height - (i / num_ticks) * chart_height
            value = (i / num_ticks) * max_value
            canvas.create_line(left_margin - 5, y, left_margin, y, width=1)
            canvas.create_text(left_margin - 10, y, text=f"{value:.1f}", anchor=tk.E, font=("Arial", 8))

        # Draw bars
        x = left_margin + bar_spacing
        for label, value in data.items():
            bar_height = (value / max_value) * chart_height if max_value > 0 else 0

            # Draw the bar
            canvas.create_rectangle(
                x,
                top_margin + chart_height - bar_height,
                x + bar_width,
                top_margin + chart_height,
                fill=COLORS["primary"],
                outline=""
            )

            # Draw the label
            canvas.create_text(
                x + bar_width / 2,
                top_margin + chart_height + 5,
                text=label,
                anchor=tk.N,
                font=("Arial", 8)
            )

            # Draw the value
            if bar_height > 20:  # Only draw value if bar is tall enough
                canvas.create_text(
                    x + bar_width / 2,
                    top_margin + chart_height - bar_height - 5,
                    text=f"{value:.1f}",
                    anchor=tk.S,
                    font=("Arial", 8)
                )

            # Move to next bar
            x += bar_width + bar_spacing

    def create_pie_chart(self, parent, title, data):
        """Create a simple pie chart.

        Args:
            parent: The parent widget
            title: The chart title
            data: Dictionary of label -> value
        """
        # Create a frame for the chart
        chart_frame = ttk.LabelFrame(parent, text=title)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create layout with canvas on left and legend on right
        chart_layout = ttk.Frame(chart_frame)
        chart_layout.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add a canvas for drawing
        canvas = tk.Canvas(chart_layout, bg="white", width=300, height=300)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add a frame for the legend
        legend_frame = ttk.Frame(chart_layout)
        legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Check if we have data
        if not data:
            self.show_chart_error("No data available for the selected period", canvas)
            return

        # Calculate total
        total = sum(data.values())

        if total == 0:
            self.show_chart_error("No data available for the selected period", canvas)
            return

        # Calculate chart dimensions
        chart_width = canvas.winfo_width()
        chart_height = canvas.winfo_height()

        # Make sure we have reasonable dimensions
        if chart_width < 100:
            chart_width = 300
        if chart_height < 100:
            chart_height = 300

        # Calculate center and radius
        center_x = chart_width / 2
        center_y = chart_height / 2
        radius = min(center_x, center_y) * 0.8

        # Colors for pie slices
        colors = [
            "#4285F4", "#EA4335", "#FBBC05", "#34A853", "#FF6D01",
            "#46BDC6", "#7B0099", "#B31412", "#0F9D58", "#8430CE"
        ]

        # Draw pie slices
        start_angle = 0
        legend_items = []

        for i, (label, value) in enumerate(data.items()):
            # Calculate angles
            angle = (value / total) * 360
            end_angle = start_angle + angle

            # Draw slice
            color = colors[i % len(colors)]

            # Angles in degrees for start_angle & end_angle
            canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=angle,
                fill=color, outline="white", width=2
            )

            # Add to legend items
            legend_items.append((label, value, color))

            # Update start angle for next slice
            start_angle = end_angle

        # Create legend
        for i, (label, value, color) in enumerate(legend_items):
            # Create frame for legend item
            item_frame = ttk.Frame(legend_frame)
            item_frame.pack(fill=tk.X, pady=2)

            # Color box
            color_box = tk.Canvas(item_frame, width=15, height=15, bg=color, highlightthickness=1,
                                  highlightbackground="black")
            color_box.pack(side=tk.LEFT, padx=2)

            # Label and value
            percentage = (value / total) * 100
            ttk.Label(item_frame, text=f"{label}: {value:.1f} ({percentage:.1f}%)").pack(side=tk.LEFT, padx=2)

    def show_chart_error(self, message, canvas=None):
        """Show an error message in the chart area.

        Args:
            message: The error message to display
            canvas: Optional canvas to display the message on
        """
        if canvas:
            # Display error on the provided canvas
            canvas.create_text(
                canvas.winfo_width() / 2,
                canvas.winfo_height() / 2,
                text=message,
                font=("Arial", 12),
                fill="red"
            )
        else:
            # Create a new label in the chart frame
            error_label = ttk.Label(
                self.chart_frame,
                text=message,
                foreground="red",
                font=("Arial", 12)
            )
            error_label.pack(expand=True, pady=50)

    def on_generate_report(self):
        """Generate a comprehensive report."""
        messagebox.showinfo("Coming Soon", "Report generation will be available in a future update")

    def on_export_data(self):
        """Export the current chart data."""
        messagebox.showinfo("Coming Soon", "Data export will be available in a future update")