# gui/views/analytics/material_usage_view.py
"""
Material usage analytics view for the leatherworking ERP system.

This module provides a detailed view of material usage analytics, including
consumption patterns, waste analysis, and material cost trends.
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
from services.dto.analytics_dto import MaterialUsageAnalyticsDTO, MaterialUsageItemDTO
from services.implementations.material_usage_analytics_service import MaterialUsageAnalyticsService


class MaterialUsageView(BaseView):
    """Material usage analytics view displaying detailed material consumption metrics."""

    def __init__(self, parent):
        """
        Initialize the material usage analytics view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Material Usage Analytics"
        self.description = "Detailed analysis of material consumption and costs"

        # Initialize date range
        self.start_date = (datetime.now() - timedelta(days=365)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        self.end_date = datetime.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Initialize service
        self.analytics_service = resolve('IMaterialUsageAnalyticsService')

        # Initialize data containers
        self.material_usage_data = None
        self.consumption_by_type = None
        self.waste_analysis = None
        self.inventory_turnover = None

        # Material type filter
        self.material_type = "All"

        # Build the view
        self.build()

        # Load initial data
        self._load_data()

    def build(self):
        """Build the material usage analytics view."""
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
        self._create_filter_section()
        self._create_summary_section()
        self._create_consumption_section()
        self._create_waste_section()
        self._create_turnover_section()
        self._create_cost_trend_section()

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update the scrollable region."""
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

    def create_header(self):
        """Create a header for the material usage analytics view."""
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

    def _create_filter_section(self):
        """Create filter section for date range and material type."""
        filter_frame = ttk.LabelFrame(
            self.content_frame,
            text="Filters",
            padding=DEFAULT_PADDING
        )
        filter_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create two rows for filters
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))

        material_frame = ttk.Frame(filter_frame)
        material_frame.pack(fill=tk.X)

        # Date filter row
        # Period combobox
        ttk.Label(date_frame, text="Period:").grid(row=0, column=0, padx=(0, 10))

        self.period_var = tk.StringVar(value="Last 12 Months")
        period_combo = ttk.Combobox(
            date_frame,
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
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=2, padx=(0, 10))

        self.start_date_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        start_date_entry = ttk.Entry(
            date_frame,
            textvariable=self.start_date_var,
            width=12
        )
        start_date_entry.grid(row=0, column=3, padx=(0, 5))

        ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=lambda: self._show_date_picker(self.start_date_var)
        ).grid(row=0, column=4, padx=(0, 20))

        # End date
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=5, padx=(0, 10))

        self.end_date_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        end_date_entry = ttk.Entry(
            date_frame,
            textvariable=self.end_date_var,
            width=12
        )
        end_date_entry.grid(row=0, column=6, padx=(0, 5))

        ttk.Button(
            date_frame,
            text="📅",
            width=3,
            command=lambda: self._show_date_picker(self.end_date_var)
        ).grid(row=0, column=7, padx=(0, 20))

        # Material filter row
        # Material type
        ttk.Label(material_frame, text="Material Type:").grid(row=0, column=0, padx=(0, 10))

        self.material_type_var = tk.StringVar(value="All")
        self.material_type_combo = ttk.Combobox(
            material_frame,
            textvariable=self.material_type_var,
            state="readonly",
            width=15
        )
        self.material_type_combo.grid(row=0, column=1, padx=(0, 20))
        self.material_type_combo.bind("<<ComboboxSelected>>", self._on_material_type_change)

        # Apply button
        ttk.Button(
            material_frame,
            text="Apply Filters",
            command=self._apply_filters
        ).grid(row=0, column=2, padx=(0, 5))

        # Reset button
        ttk.Button(
            material_frame,
            text="Reset Filters",
            command=self._reset_filters
        ).grid(row=0, column=3, padx=(0, 5))

        # Configure grid
        date_frame.columnconfigure(8, weight=1)
        material_frame.columnconfigure(4, weight=1)

    def _create_summary_section(self):
        """Create material usage summary section."""
        summary_frame = ttk.LabelFrame(
            self.content_frame,
            text="Material Usage Summary",
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

    def _create_consumption_section(self):
        """Create material consumption section."""
        consumption_frame = ttk.LabelFrame(
            self.content_frame,
            text="Material Consumption",
            padding=DEFAULT_PADDING
        )
        consumption_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Split into left (chart) and right (table)
        content_frame = ttk.Frame(consumption_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create placeholder for consumption chart
        self.consumption_chart_frame = ttk.Frame(left_frame, width=400, height=300)
        self.consumption_chart_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create table for consumption details
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Material Type", "Quantity Used", "Cost", "% of Total")
        self.consumption_treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # Configure columns
        for col in columns:
            self.consumption_treeview.heading(col, text=col)
            width = 100 if col != "Material Type" else 150
            self.consumption_treeview.column(col, width=width, minwidth=50)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.consumption_treeview.yview
        )
        self.consumption_treeview.configure(yscrollcommand=scrollbar.set)

        self.consumption_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_waste_section(self):
        """Create material waste analysis section."""
        waste_frame = ttk.LabelFrame(
            self.content_frame,
            text="Waste Analysis",
            padding=DEFAULT_PADDING
        )
        waste_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Split into left (chart) and right (details)
        content_frame = ttk.Frame(waste_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create placeholder for waste chart
        self.waste_chart_frame = ttk.Frame(left_frame, width=400, height=300)
        self.waste_chart_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create table for waste details
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Material Type", "Waste %", "Cost Impact", "Trend")
        self.waste_treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # Configure columns
        for col in columns:
            self.waste_treeview.heading(col, text=col)
            width = 100
            self.waste_treeview.column(col, width=width, minwidth=50)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.waste_treeview.yview
        )
        self.waste_treeview.configure(yscrollcommand=scrollbar.set)

        self.waste_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_turnover_section(self):
        """Create inventory turnover section."""
        turnover_frame = ttk.LabelFrame(
            self.content_frame,
            text="Inventory Turnover",
            padding=DEFAULT_PADDING
        )
        turnover_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create placeholder for turnover chart
        self.turnover_chart_frame = ttk.Frame(turnover_frame, height=300)
        self.turnover_chart_frame.pack(fill=tk.BOTH, expand=True)

    def _create_cost_trend_section(self):
        """Create material cost trend section."""
        cost_frame = ttk.LabelFrame(
            self.content_frame,
            text="Material Cost Trends",
            padding=DEFAULT_PADDING
        )
        cost_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create placeholder for cost trend chart
        self.cost_trend_frame = ttk.Frame(cost_frame, height=300)
        self.cost_trend_frame.pack(fill=tk.BOTH, expand=True)

    def _load_data(self):
        """Load all material usage analytics data."""
        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Get material usage analytics data
            self.material_usage_data = self.analytics_service.get_material_usage_analytics(
                start_date=start_date,
                end_date=end_date
            )

            # Get material consumption by type
            self.consumption_by_type = self.analytics_service.get_material_consumption_by_type(
                start_date=start_date,
                end_date=end_date
            )

            # Get waste analysis
            material_type = None if self.material_type_var.get() == "All" else self.material_type_var.get()
            self.waste_analysis = self.analytics_service.get_waste_analysis(
                material_type=material_type
            )

            # Get inventory turnover
            self.inventory_turnover = self.analytics_service.get_inventory_turnover(
                start_date=start_date,
                end_date=end_date
            )

            # Update material type dropdown options
            if self.material_usage_data and hasattr(self.material_usage_data, 'material_types'):
                material_types = ["All"] + self.material_usage_data.material_types
                self.material_type_combo['values'] = material_types

            # Update UI with the loaded data
            self._update_ui()

        except Exception as e:
            logging.error(f"Error loading material usage analytics data: {e}")
            self.show_error(
                "Data Loading Error",
                f"Failed to load material usage analytics data: {str(e)}"
            )

    def _update_ui(self):
        """Update UI with loaded data."""
        if not self.material_usage_data:
            return

        self._update_summary_section()
        self._update_consumption_section()
        self._update_waste_section()
        self._update_turnover_section()
        self._update_cost_trend_section()

    def _update_summary_section(self):
        """Update material usage summary section with loaded data."""
        # Clear existing widgets
        for widget in self.kpi_widgets.values():
            if widget.winfo_exists():
                widget.destroy()

        # Get the KPI frame
        kpi_frame = self.content_frame.winfo_children()[2].winfo_children()[0]

        # Create KPI widgets
        kpis = [
            {
                "title": "Total Material Cost",
                "value": f"${self.material_usage_data.total_material_cost:.2f}",
                "subtitle": f"{self.material_usage_data.total_items_used} items used",
                "key": "total_cost"
            },
            {
                "title": "Average Cost per Project",
                "value": f"${self.material_usage_data.avg_cost_per_project:.2f}",
                "subtitle": f"{self.material_usage_data.project_count} projects",
                "key": "avg_cost"
            },
            {
                "title": "Waste Percentage",
                "value": f"{self.material_usage_data.overall_waste_percentage:.1f}%",
                "subtitle": f"${self.material_usage_data.waste_cost_impact:.2f} impact",
                "key": "waste_percentage"
            },
            {
                "title": "Inventory Turnover",
                "value": f"{self.material_usage_data.overall_turnover_rate:.2f}",
                "subtitle": f"{self.material_usage_data.avg_days_in_inventory:.1f} days avg. in inventory",
                "key": "turnover_rate"
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

    def _update_consumption_section(self):
        """Update consumption section with loaded data."""
        if not self.consumption_by_type:
            return

        # Clear existing chart
        for widget in self.consumption_chart_frame.winfo_children():
            widget.destroy()

        # Clear existing treeview items
        for item in self.consumption_treeview.get_children():
            self.consumption_treeview.delete(item)

        # Prepare data for pie chart
        chart_data = [
            {
                "label": material_type,
                "value": consumption,
                "color": COLORS.get(f"material_{i}", COLORS["accent"])
            }
            for i, (material_type, consumption) in enumerate(self.consumption_by_type.items())
        ]

        # Create pie chart
        pie_chart = create_pie_chart(
            self.consumption_chart_frame,
            chart_data,
            title="Material Consumption by Type",
            width=400,
            height=300,
            show_legend=True,
            show_percentage=True
        )
        pie_chart.pack(fill=tk.BOTH, expand=True)

        # Add consumption data to the treeview
        total_consumption = sum(self.consumption_by_type.values())
        total_cost = self.material_usage_data.total_material_cost if self.material_usage_data else 0

        # Add detailed material usage data if available
        if hasattr(self.material_usage_data, 'material_items'):
            for item in self.material_usage_data.material_items:
                percentage = (item.quantity / total_consumption * 100) if total_consumption > 0 else 0

                self.consumption_treeview.insert(
                    "",
                    tk.END,
                    values=(
                        item.material_type,
                        f"{item.quantity:.2f} {item.unit}",
                        f"${item.cost:.2f}",
                        f"{percentage:.1f}%"
                    )
                )
        else:
            # Fall back to summary data
            for material_type, consumption in self.consumption_by_type.items():
                percentage = (consumption / total_consumption * 100) if total_consumption > 0 else 0
                cost_estimate = (consumption / total_consumption * total_cost) if total_consumption > 0 else 0

                self.consumption_treeview.insert(
                    "",
                    tk.END,
                    values=(
                        material_type,
                        f"{consumption:.2f}",
                        f"${cost_estimate:.2f}",
                        f"{percentage:.1f}%"
                    )
                )

        # Add total row
        self.consumption_treeview.insert(
            "",
            tk.END,
            values=(
                "TOTAL",
                f"{total_consumption:.2f}",
                f"${total_cost:.2f}",
                "100.0%"
            ),
            tags=("total",)
        )

        # Configure tag for total row
        self.consumption_treeview.tag_configure(
            "total",
            background=COLORS["light_accent"],
            font=("TkDefaultFont", 10, "bold")
        )

    def _update_waste_section(self):
        """Update waste analysis section with loaded data."""
        if not self.waste_analysis:
            return

        # Clear existing chart
        for widget in self.waste_chart_frame.winfo_children():
            widget.destroy()

        # Clear existing treeview items
        for item in self.waste_treeview.get_children():
            self.waste_treeview.delete(item)

        # Prepare data for bar chart
        chart_data = [
            {
                "label": material_type,
                "value": waste_percentage,
                "color": self._get_waste_color(waste_percentage)
            }
            for material_type, waste_percentage in self.waste_analysis.items()
            if isinstance(waste_percentage, (int, float))
        ]

        # Sort by waste percentage (descending)
        chart_data.sort(key=lambda x: x["value"], reverse=True)

        # Create bar chart
        bar_chart = create_bar_chart(
            self.waste_chart_frame,
            chart_data,
            title="Waste Percentage by Material Type",
            x_label="Material Type",
            y_label="Waste (%)",
            width=400,
            height=300
        )
        bar_chart.pack(fill=tk.BOTH, expand=True)

        # Add waste data to the treeview
        for material_type, waste_data in self.waste_analysis.items():
            if isinstance(waste_data, dict):
                waste_percentage = waste_data.get("percentage", 0)
                cost_impact = waste_data.get("cost_impact", 0)
                trend = waste_data.get("trend", 0)

                trend_text = self._get_trend_text(trend)

                self.waste_treeview.insert(
                    "",
                    tk.END,
                    values=(
                        material_type,
                        f"{waste_percentage:.1f}%",
                        f"${cost_impact:.2f}",
                        trend_text
                    ),
                    tags=(self._get_waste_tag(waste_percentage),)
                )
            elif isinstance(waste_data, (int, float)):
                # Simple format with just percentages
                self.waste_treeview.insert(
                    "",
                    tk.END,
                    values=(
                        material_type,
                        f"{waste_data:.1f}%",
                        "-",
                        "-"
                    ),
                    tags=(self._get_waste_tag(waste_data),)
                )

        # Configure tags for waste levels
        self.waste_treeview.tag_configure(
            "low_waste",
            background=COLORS["light_success"],
            foreground=COLORS["text"]
        )
        self.waste_treeview.tag_configure(
            "medium_waste",
            background=COLORS["light_warning"],
            foreground=COLORS["text"]
        )
        self.waste_treeview.tag_configure(
            "high_waste",
            background=COLORS["light_danger"],
            foreground=COLORS["text"]
        )

    def _update_turnover_section(self):
        """Update inventory turnover section with loaded data."""
        if not self.inventory_turnover:
            return

        # Clear existing chart
        for widget in self.turnover_chart_frame.winfo_children():
            widget.destroy()

        # Check if we have turnover by category or by material
        has_by_category = False
        has_by_material = False

        if isinstance(self.inventory_turnover, dict):
            # Check if this is category-level data
            first_value = next(iter(self.inventory_turnover.values()), None)
            has_by_category = isinstance(first_value, (int, float))

            # Check if this is material-level data
            if not has_by_category and isinstance(first_value, dict):
                has_by_material = any(isinstance(v, dict) for v in self.inventory_turnover.values())

        # Create tabs for different turnover views
        tab_control = ttk.Notebook(self.turnover_chart_frame)
        tab_control.pack(fill=tk.BOTH, expand=True)

        # Overall turnover tab
        overall_tab = ttk.Frame(tab_control)
        tab_control.add(overall_tab, text="Overall Turnover")

        # By category tab
        if has_by_category:
            category_tab = ttk.Frame(tab_control)
            tab_control.add(category_tab, text="By Category")

            # Create bar chart for turnover by category
            chart_data = [
                {
                    "label": category,
                    "value": turnover,
                    "color": self._get_turnover_color(turnover)
                }
                for category, turnover in self.inventory_turnover.items()
                if isinstance(turnover, (int, float))
            ]

            # Sort by turnover rate (descending)
            chart_data.sort(key=lambda x: x["value"], reverse=True)

            # Create bar chart
            bar_chart = create_bar_chart(
                category_tab,
                chart_data,
                title="Inventory Turnover by Category",
                x_label="Category",
                y_label="Turnover Rate",
                width=800,
                height=300
            )
            bar_chart.pack(fill=tk.BOTH, expand=True)

        # By material tab
        if has_by_material:
            material_tab = ttk.Frame(tab_control)
            tab_control.add(material_tab, text="By Material")

            # Create table for material turnover details
            columns = ("Material", "Turnover Rate", "Days in Inventory", "Efficiency")
            material_treeview = ttk.Treeview(
                material_tab,
                columns=columns,
                show="headings",
                height=10
            )

            # Configure columns
            for col in columns:
                material_treeview.heading(col, text=col)
                width = 150
                material_treeview.column(col, width=width, minwidth=50)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(
                material_tab,
                orient=tk.VERTICAL,
                command=material_treeview.yview
            )
            material_treeview.configure(yscrollcommand=scrollbar.set)

            material_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Add turnover data to the treeview
            for category, materials in self.inventory_turnover.items():
                if isinstance(materials, dict):
                    for material, details in materials.items():
                        if isinstance(details, dict):
                            turnover = details.get("turnover_rate", 0)
                            days = details.get("days_in_inventory", 0)

                            material_treeview.insert(
                                "",
                                tk.END,
                                values=(
                                    f"{material} ({category})",
                                    f"{turnover:.2f}",
                                    f"{days:.1f} days",
                                    self._get_efficiency_rating(turnover)
                                ),
                                tags=(self._get_turnover_tag(turnover),)
                            )

            # Configure tags for turnover rates
            material_treeview.tag_configure(
                "low_turnover",
                background=COLORS["light_danger"],
                foreground=COLORS["text"]
            )
            material_treeview.tag_configure(
                "medium_turnover",
                background=COLORS["light_warning"],
                foreground=COLORS["text"]
            )
            material_treeview.tag_configure(
                "high_turnover",
                background=COLORS["light_success"],
                foreground=COLORS["text"]
            )

        # Create overall turnover gauge chart
        if hasattr(self.material_usage_data, 'overall_turnover_rate'):
            from gui.widgets.charts import create_gauge_chart

            overall_turnover = self.material_usage_data.overall_turnover_rate

            gauge_chart = create_gauge_chart(
                overall_tab,
                value=overall_turnover,
                min_value=0,
                max_value=12,
                title="Overall Inventory Turnover Rate",
                width=400,
                height=300
            )
            gauge_chart.pack(fill=tk.BOTH, expand=True)
        else:
            # Fallback to text display
            ttk.Label(
                overall_tab,
                text="Overall inventory turnover data not available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _update_cost_trend_section(self):
        """Update material cost trend section with loaded data."""
        if not hasattr(self.material_usage_data, 'cost_trends'):
            return

        # Clear existing chart
        for widget in self.cost_trend_frame.winfo_children():
            widget.destroy()

        # Check if we have cost trend data
        cost_trends = getattr(self.material_usage_data, 'cost_trends', None)
        if not cost_trends:
            ttk.Label(
                self.cost_trend_frame,
                text="No cost trend data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)
            return

        # Create tabs for different cost views
        tab_control = ttk.Notebook(self.cost_trend_frame)
        tab_control.pack(fill=tk.BOTH, expand=True)

        # Overall cost tab
        overall_tab = ttk.Frame(tab_control)
        tab_control.add(overall_tab, text="Overall Cost")

        # By material type tab
        by_type_tab = ttk.Frame(tab_control)
        tab_control.add(by_type_tab, text="By Material Type")

        # Check if we have overall cost trend
        if "overall" in cost_trends:
            # Prepare data for line chart
            overall_data = cost_trends["overall"]

            chart_data = [
                {
                    "label": period,
                    "value": cost,
                    "color": COLORS["primary"]
                }
                for period, cost in overall_data.items()
            ]

            # Sort by period
            chart_data.sort(key=lambda x: x["label"])

            # Create line chart
            line_chart = create_line_chart(
                overall_tab,
                chart_data,
                title="Overall Material Cost Trend",
                x_label="Period",
                y_label="Cost ($)",
                width=800,
                height=300,
                show_points=True,
                area_fill=True
            )
            line_chart.pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(
                overall_tab,
                text="No overall cost trend data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

        # Check if we have cost trend by material type
        if "by_type" in cost_trends:
            from gui.widgets.charts import create_multi_line_chart

            # Prepare data for multi-line chart
            by_type_data = cost_trends["by_type"]

            # Create formatted data
            chart_data = []

            # Get all periods from all material types
            all_periods = set()
            for material_type, data in by_type_data.items():
                all_periods.update(data.keys())

            # Sort periods
            sorted_periods = sorted(all_periods)

            # Colors for different material types
            colors = {
                "LEATHER": COLORS["primary"],
                "HARDWARE": COLORS["secondary"],
                "SUPPLIES": COLORS["accent"],
                "THREAD": COLORS["warning"],
                "ADHESIVE": COLORS["danger"],
                "DYE": COLORS["success"],
                "LINING": COLORS["info"]
            }

            # Add data for each material type and period
            for material_type, data in by_type_data.items():
                color = colors.get(material_type, COLORS["primary"])

                for period in sorted_periods:
                    if period in data:
                        chart_data.append({
                            "label": period,
                            "value": data[period],
                            "series": material_type,
                            "color": color
                        })

            # Create multi-line chart
            if chart_data:
                multi_line_chart = create_multi_line_chart(
                    by_type_tab,
                    chart_data,
                    title="Material Cost Trend by Type",
                    x_label="Period",
                    y_label="Cost ($)",
                    width=800,
                    height=300,
                    show_points=True,
                    show_legend=True
                )
                multi_line_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(
                    by_type_tab,
                    text="No material type cost trend data available",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(
                by_type_tab,
                text="No material type cost trend data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _get_waste_color(self, waste_percentage):
        """
        Get color for waste visualization based on percentage.

        Args:
            waste_percentage: The waste percentage

        Returns:
            Color hex code
        """
        if waste_percentage <= 5:
            return COLORS["success"]
        elif waste_percentage <= 15:
            return COLORS["warning"]
        else:
            return COLORS["danger"]

    def _get_waste_tag(self, waste_percentage):
        """
        Get tag for waste level based on percentage.

        Args:
            waste_percentage: The waste percentage

        Returns:
            Tag name for styling
        """
        if waste_percentage <= 5:
            return "low_waste"
        elif waste_percentage <= 15:
            return "medium_waste"
        else:
            return "high_waste"

    def _get_turnover_color(self, turnover_rate):
        """
        Get color for turnover visualization based on rate.

        Args:
            turnover_rate: The turnover rate

        Returns:
            Color hex code
        """
        if turnover_rate >= 6:
            return COLORS["success"]
        elif turnover_rate >= 3:
            return COLORS["primary"]
        else:
            return COLORS["warning"]

    def _get_turnover_tag(self, turnover_rate):
        """
        Get tag for turnover level based on rate.

        Args:
            turnover_rate: The turnover rate

        Returns:
            Tag name for styling
        """
        if turnover_rate >= 6:
            return "high_turnover"
        elif turnover_rate >= 3:
            return "medium_turnover"
        else:
            return "low_turnover"

    def _get_efficiency_rating(self, turnover_rate):
        """
        Get efficiency rating text based on turnover rate.

        Args:
            turnover_rate: The turnover rate

        Returns:
            Efficiency rating text
        """
        if turnover_rate >= 6:
            return "Excellent"
        elif turnover_rate >= 4:
            return "Good"
        elif turnover_rate >= 2:
            return "Average"
        else:
            return "Poor"

    def _get_trend_text(self, trend_value):
        """
        Get descriptive text for trend value.

        Args:
            trend_value: The trend value (positive or negative percentage)

        Returns:
            Formatted trend text
        """
        if trend_value > 0:
            return f"↑ {trend_value:.1f}%"
        elif trend_value < 0:
            return f"↓ {abs(trend_value):.1f}%"
        else:
            return "No change"

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

    def _on_material_type_change(self, event):
        """
        Handle material type change.

        Args:
            event: The combobox selection event
        """
        self.material_type = self.material_type_var.get()

    def _apply_filters(self):
        """Apply filters and reload data."""
        self._load_data()

    def _reset_filters(self):
        """Reset filters to default values."""
        self.period_var.set("Last 12 Months")
        self._set_default_date_range("Last 12 Months")
        self.material_type_var.set("All")
        self.material_type = "All"
        self._load_data()

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