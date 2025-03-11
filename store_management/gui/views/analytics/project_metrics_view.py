# gui/views/analytics/project_metrics_view.py
"""
Project metrics analytics view for the leatherworking ERP system.

This module provides a detailed view of project metrics analytics, including
efficiency metrics, resource utilization, and bottleneck analysis.
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
from services.dto.analytics_dto import ProjectMetricsDTO, ProjectPhaseMetricsDTO
from services.implementations.project_metrics_service import ProjectMetricsService


class ProjectMetricsView(BaseView):
    """Project metrics view displaying detailed project efficiency analytics."""

    def __init__(self, parent):
        """
        Initialize the project metrics view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Project Metrics Analytics"
        self.description = "Detailed analysis of project efficiency and bottlenecks"

        # Initialize date range
        self.start_date = (datetime.now() - timedelta(days=365)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        self.end_date = datetime.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Initialize service
        self.analytics_service = resolve('IProjectMetricsService')

        # Initialize data containers
        self.project_metrics_data = None
        self.project_completion_time = None
        self.project_phase_metrics = None
        self.bottleneck_analysis = None

        # Project type filter
        self.project_type = "All"

        # Build the view
        self.build()

        # Load initial data
        self._load_data()

    def build(self):
        """Build the project metrics view."""
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
        self._create_completion_time_section()
        self._create_phase_analysis_section()
        self._create_resource_utilization_section()
        self._create_bottleneck_section()

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update the scrollable region."""
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

    def create_header(self):
        """Create a header for the project metrics view."""
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
        """Create filter section for date range and project type."""
        filter_frame = ttk.LabelFrame(
            self.content_frame,
            text="Filters",
            padding=DEFAULT_PADDING
        )
        filter_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create two rows for filters
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))

        project_frame = ttk.Frame(filter_frame)
        project_frame.pack(fill=tk.X)

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

        # Project filter row
        # Project type
        ttk.Label(project_frame, text="Project Type:").grid(row=0, column=0, padx=(0, 10))

        self.project_type_var = tk.StringVar(value="All")
        self.project_type_combo = ttk.Combobox(
            project_frame,
            textvariable=self.project_type_var,
            state="readonly",
            width=15
        )
        self.project_type_combo.grid(row=0, column=1, padx=(0, 20))
        self.project_type_combo.bind("<<ComboboxSelected>>", self._on_project_type_change)

        # Apply button
        ttk.Button(
            project_frame,
            text="Apply Filters",
            command=self._apply_filters
        ).grid(row=0, column=2, padx=(0, 5))

        # Reset button
        ttk.Button(
            project_frame,
            text="Reset Filters",
            command=self._reset_filters
        ).grid(row=0, column=3, padx=(0, 5))

        # Configure grid
        date_frame.columnconfigure(8, weight=1)
        project_frame.columnconfigure(4, weight=1)

    def _create_summary_section(self):
        """Create project metrics summary section."""
        summary_frame = ttk.LabelFrame(
            self.content_frame,
            text="Project Metrics Summary",
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

    def _create_completion_time_section(self):
        """Create project completion time section."""
        completion_frame = ttk.LabelFrame(
            self.content_frame,
            text="Project Completion Time",
            padding=DEFAULT_PADDING
        )
        completion_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Split into left (chart) and right (details)
        content_frame = ttk.Frame(completion_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create placeholder for completion time chart
        self.completion_chart_frame = ttk.Frame(left_frame, width=400, height=300)
        self.completion_chart_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create table for completion time details
        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Project Type", "Avg. Time (days)", "Min Time", "Max Time", "On-Time %")
        self.completion_treeview = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # Configure columns
        for col in columns:
            self.completion_treeview.heading(col, text=col)
            width = 100 if col != "Project Type" else 150
            self.completion_treeview.column(col, width=width, minwidth=50)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self.completion_treeview.yview
        )
        self.completion_treeview.configure(yscrollcommand=scrollbar.set)

        self.completion_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_phase_analysis_section(self):
        """Create project phase analysis section."""
        phase_frame = ttk.LabelFrame(
            self.content_frame,
            text="Project Phase Analysis",
            padding=DEFAULT_PADDING
        )
        phase_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create placeholder for phase heatmap
        self.phase_chart_frame = ttk.Frame(phase_frame, height=400)
        self.phase_chart_frame.pack(fill=tk.BOTH, expand=True)

    def _create_resource_utilization_section(self):
        """Create resource utilization section."""
        resource_frame = ttk.LabelFrame(
            self.content_frame,
            text="Resource Utilization",
            padding=DEFAULT_PADDING
        )
        resource_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Create tabs for different resource views
        tab_control = ttk.Notebook(resource_frame)
        tab_control.pack(fill=tk.BOTH, expand=True)

        # Material usage tab
        material_tab = ttk.Frame(tab_control)
        tab_control.add(material_tab, text="Material Usage")

        # Create placeholder for material usage chart
        self.material_usage_frame = ttk.Frame(material_tab, height=300)
        self.material_usage_frame.pack(fill=tk.BOTH, expand=True)

        # Tool usage tab
        tool_tab = ttk.Frame(tab_control)
        tab_control.add(tool_tab, text="Tool Usage")

        # Create placeholder for tool usage chart
        self.tool_usage_frame = ttk.Frame(tool_tab, height=300)
        self.tool_usage_frame.pack(fill=tk.BOTH, expand=True)

        # Time allocation tab
        time_tab = ttk.Frame(tab_control)
        tab_control.add(time_tab, text="Time Allocation")

        # Create placeholder for time allocation chart
        self.time_allocation_frame = ttk.Frame(time_tab, height=300)
        self.time_allocation_frame.pack(fill=tk.BOTH, expand=True)

    def _create_bottleneck_section(self):
        """Create bottleneck analysis section."""
        bottleneck_frame = ttk.LabelFrame(
            self.content_frame,
            text="Bottleneck Analysis",
            padding=DEFAULT_PADDING
        )
        bottleneck_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Split into left (chart) and right (recommendations)
        content_frame = ttk.Frame(bottleneck_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create placeholder for bottleneck chart
        self.bottleneck_chart_frame = ttk.Frame(left_frame, width=400, height=300)
        self.bottleneck_chart_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 10))

        # Create recommendations section
        recommendations_frame = ttk.LabelFrame(
            right_frame,
            text="Improvement Recommendations",
            padding=5
        )
        recommendations_frame.pack(fill=tk.BOTH, expand=True)

        # Create a text widget for recommendations
        self.recommendations_text = tk.Text(
            recommendations_frame,
            wrap=tk.WORD,
            height=10,
            width=40,
            borderwidth=0,
            highlightthickness=0
        )
        self.recommendations_text.pack(fill=tk.BOTH, expand=True)
        self.recommendations_text.config(state=tk.DISABLED)

    def _load_data(self):
        """Load all project metrics analytics data."""
        try:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Get project metrics data
            self.project_metrics_data = self.analytics_service.get_project_metrics(
                start_date=start_date,
                end_date=end_date
            )

            # Get project completion time
            project_type = None if self.project_type_var.get() == "All" else self.project_type_var.get()
            self.project_completion_time = self.analytics_service.get_project_completion_time(
                project_type=project_type
            )

            # Get project phase metrics
            self.project_phase_metrics = self.analytics_service.get_project_phase_metrics(
                project_type=project_type
            )

            # Get bottleneck analysis
            self.bottleneck_analysis = self.analytics_service.get_bottleneck_analysis()

            # Update project type dropdown options
            if self.project_metrics_data and hasattr(self.project_metrics_data, 'project_types'):
                project_types = ["All"] + self.project_metrics_data.project_types
                self.project_type_combo['values'] = project_types

            # Update UI with the loaded data
            self._update_ui()

        except Exception as e:
            logging.error(f"Error loading project metrics data: {e}")
            self.show_error(
                "Data Loading Error",
                f"Failed to load project metrics data: {str(e)}"
            )

    def _update_ui(self):
        """Update UI with loaded data."""
        if not self.project_metrics_data:
            return

        self._update_summary_section()
        self._update_completion_time_section()
        self._update_phase_analysis_section()
        self._update_resource_utilization_section()
        self._update_bottleneck_section()

    def _update_summary_section(self):
        """Update project metrics summary section with loaded data."""
        # Clear existing widgets
        for widget in self.kpi_widgets.values():
            if widget.winfo_exists():
                widget.destroy()

        # Get the KPI frame
        kpi_frame = self.content_frame.winfo_children()[2].winfo_children()[0]

        # Create KPI widgets
        kpis = [
            {
                "title": "Total Projects",
                "value": self.project_metrics_data.total_projects,
                "subtitle": f"{self.project_metrics_data.completed_projects} completed",
                "key": "total_projects"
            },
            {
                "title": "Avg. Completion Time",
                "value": f"{self.project_metrics_data.avg_completion_time:.1f} days",
                "subtitle": self._get_time_trend_text(self.project_metrics_data.completion_time_trend),
                "key": "avg_completion_time"
            },
            {
                "title": "On-Time Completion",
                "value": f"{self.project_metrics_data.on_time_percentage:.1f}%",
                "subtitle": f"{self.project_metrics_data.on_time_projects} of {self.project_metrics_data.completed_projects}",
                "key": "on_time_percentage"
            },
            {
                "title": "Resource Efficiency",
                "value": f"{self.project_metrics_data.resource_efficiency:.1f}%",
                "subtitle": self._get_efficiency_text(self.project_metrics_data.resource_efficiency),
                "key": "resource_efficiency"
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

    def _update_completion_time_section(self):
        """Update completion time section with loaded data."""
        if not self.project_completion_time:
            return

        # Clear existing chart
        for widget in self.completion_chart_frame.winfo_children():
            widget.destroy()

        # Clear existing treeview items
        for item in self.completion_treeview.get_children():
            self.completion_treeview.delete(item)

        # Check if we have detailed completion time data or just summary
        if isinstance(self.project_completion_time, dict) and "by_type" in self.project_completion_time:
            # We have detailed completion time data
            completion_by_type = self.project_completion_time.get("by_type", {})

            # Prepare data for bar chart
            chart_data = [
                {
                    "label": project_type,
                    "value": data.get("avg_days", 0),
                    "color": COLORS.get(f"project_{i}", COLORS["accent"])
                }
                for i, (project_type, data) in enumerate(completion_by_type.items())
            ]

            # Sort by completion time (ascending)
            chart_data.sort(key=lambda x: x["value"])

            # Create bar chart
            bar_chart = create_bar_chart(
                self.completion_chart_frame,
                chart_data,
                title="Average Completion Time by Project Type",
                x_label="Project Type",
                y_label="Days",
                width=400,
                height=300
            )
            bar_chart.pack(fill=tk.BOTH, expand=True)

            # Add completion time data to the treeview
            for project_type, data in completion_by_type.items():
                self.completion_treeview.insert(
                    "",
                    tk.END,
                    values=(
                        project_type,
                        f"{data.get('avg_days', 0):.1f}",
                        f"{data.get('min_days', 0):.1f}",
                        f"{data.get('max_days', 0):.1f}",
                        f"{data.get('on_time_percentage', 0):.1f}%"
                    )
                )

        else:
            # We have simple completion time data
            # Create a simple bar chart with summary data
            chart_data = []
            for project_type, days in self.project_completion_time.items():
                if isinstance(days, (int, float)):
                    chart_data.append({
                        "label": project_type,
                        "value": days,
                        "color": COLORS["primary"]
                    })

            # Sort by completion time (ascending)
            chart_data.sort(key=lambda x: x["value"])

            # Create bar chart
            if chart_data:
                bar_chart = create_bar_chart(
                    self.completion_chart_frame,
                    chart_data,
                    title="Average Completion Time by Project Type",
                    x_label="Project Type",
                    y_label="Days",
                    width=400,
                    height=300
                )
                bar_chart.pack(fill=tk.BOTH, expand=True)

                # Add completion time data to the treeview
                for item in chart_data:
                    self.completion_treeview.insert(
                        "",
                        tk.END,
                        values=(
                            item["label"],
                            f"{item['value']:.1f}",
                            "-",
                            "-",
                            "-"
                        )
                    )
            else:
                # Show a message if no data
                ttk.Label(
                    self.completion_chart_frame,
                    text="No completion time data available",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)

    def _update_phase_analysis_section(self):
        """Update phase analysis section with loaded data."""
        if not self.project_phase_metrics:
            return

        # Clear existing chart
        for widget in self.phase_chart_frame.winfo_children():
            widget.destroy()

        # Check if we have phase metrics data
        if isinstance(self.project_phase_metrics, dict) and self.project_phase_metrics:
            # Create tabs for different phase views
            tab_control = ttk.Notebook(self.phase_chart_frame)
            tab_control.pack(fill=tk.BOTH, expand=True)

            # Duration tab
            duration_tab = ttk.Frame(tab_control)
            tab_control.add(duration_tab, text="Phase Duration")

            # Bottleneck tab
            bottleneck_tab = ttk.Frame(tab_control)
            tab_control.add(bottleneck_tab, text="Phase Bottlenecks")

            # Variability tab
            variability_tab = ttk.Frame(tab_control)
            tab_control.add(variability_tab, text="Phase Variability")

            # Check if we have data in a suitable format for heatmap
            if any(isinstance(metrics, dict) for metrics in self.project_phase_metrics.values()):
                # Prepare data for duration heatmap
                heatmap_data = []
                project_types = set()
                phases = set()

                # Collect all project types and phases
                for project_type, phase_dict in self.project_phase_metrics.items():
                    if isinstance(phase_dict, dict):
                        project_types.add(project_type)
                        for phase, metrics in phase_dict.items():
                            if isinstance(metrics, dict):
                                phases.add(phase)

                # Sort project types and phases
                project_types = sorted(project_types)
                phases = sorted(phases)

                # Create heatmap data
                for project_type in project_types:
                    phase_dict = self.project_phase_metrics.get(project_type, {})
                    if isinstance(phase_dict, dict):
                        for phase in phases:
                            metrics = phase_dict.get(phase, {})
                            if isinstance(metrics, dict):
                                avg_days = metrics.get("avg_duration", 0)
                                heatmap_data.append({
                                    "x": phase,
                                    "y": project_type,
                                    "value": avg_days
                                })

                # Create duration heatmap
                if heatmap_data:
                    heatmap = HeatmapChart(
                        duration_tab,
                        data=heatmap_data,
                        title="Phase Duration by Project Type",
                        x_label="Phase",
                        y_label="Project Type",
                        x_key="x",
                        y_key="y",
                        value_key="value",
                        width=800,
                        height=400,
                        color_min=COLORS["light_success"],
                        color_max=COLORS["danger"]
                    )
                    heatmap.pack(fill=tk.BOTH, expand=True)
                else:
                    ttk.Label(
                        duration_tab,
                        text="No phase duration data available",
                        anchor=tk.CENTER
                    ).pack(fill=tk.BOTH, expand=True)

                # Prepare data for bottleneck heatmap
                bottleneck_data = []

                # Create bottleneck heatmap data
                for project_type in project_types:
                    phase_dict = self.project_phase_metrics.get(project_type, {})
                    if isinstance(phase_dict, dict):
                        for phase in phases:
                            metrics = phase_dict.get(phase, {})
                            if isinstance(metrics, dict):
                                bottleneck_score = metrics.get("bottleneck_score", 0)
                                bottleneck_data.append({
                                    "x": phase,
                                    "y": project_type,
                                    "value": bottleneck_score
                                })

                # Create bottleneck heatmap
                if bottleneck_data:
                    heatmap = HeatmapChart(
                        bottleneck_tab,
                        data=bottleneck_data,
                        title="Phase Bottleneck Score by Project Type",
                        x_label="Phase",
                        y_label="Project Type",
                        x_key="x",
                        y_key="y",
                        value_key="value",
                        width=800,
                        height=400,
                        color_min=COLORS["light_success"],
                        color_max=COLORS["danger"]
                    )
                    heatmap.pack(fill=tk.BOTH, expand=True)
                else:
                    ttk.Label(
                        bottleneck_tab,
                        text="No phase bottleneck data available",
                        anchor=tk.CENTER
                    ).pack(fill=tk.BOTH, expand=True)

                # Prepare data for variability heatmap
                variability_data = []

                # Create variability heatmap data
                for project_type in project_types:
                    phase_dict = self.project_phase_metrics.get(project_type, {})
                    if isinstance(phase_dict, dict):
                        for phase in phases:
                            metrics = phase_dict.get(phase, {})
                            if isinstance(metrics, dict):
                                variability = metrics.get("variability", 0)
                                variability_data.append({
                                    "x": phase,
                                    "y": project_type,
                                    "value": variability
                                })

                # Create variability heatmap
                if variability_data:
                    heatmap = HeatmapChart(
                        variability_tab,
                        data=variability_data,
                        title="Phase Duration Variability by Project Type",
                        x_label="Phase",
                        y_label="Project Type",
                        x_key="x",
                        y_key="y",
                        value_key="value",
                        width=800,
                        height=400,
                        color_min=COLORS["light_success"],
                        color_max=COLORS["danger"]
                    )
                    heatmap.pack(fill=tk.BOTH, expand=True)
                else:
                    ttk.Label(
                        variability_tab,
                        text="No phase variability data available",
                        anchor=tk.CENTER
                    ).pack(fill=tk.BOTH, expand=True)
            else:
                # Show a message if no suitable data
                ttk.Label(
                    tab_control,
                    text="No phase metrics data available in the required format",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)
        else:
            # Show a message if no data
            ttk.Label(
                self.phase_chart_frame,
                text="No phase metrics data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _update_resource_utilization_section(self):
        """Update resource utilization section with loaded data."""
        if not self.project_metrics_data:
            return

        self._update_material_usage()
        self._update_tool_usage()
        self._update_time_allocation()

    def _update_material_usage(self):
        """Update material usage chart."""
        # Clear existing chart
        for widget in self.material_usage_frame.winfo_children():
            widget.destroy()

        # Check if we have material usage data
        if hasattr(self.project_metrics_data, 'material_usage'):
            material_usage = self.project_metrics_data.material_usage

            if isinstance(material_usage, dict) and material_usage:
                # Prepare data for pie chart
                chart_data = [
                    {
                        "label": material_type,
                        "value": usage,
                        "color": COLORS.get(f"material_{i}", COLORS["accent"])
                    }
                    for i, (material_type, usage) in enumerate(material_usage.items())
                ]

                # Create pie chart
                pie_chart = create_pie_chart(
                    self.material_usage_frame,
                    chart_data,
                    title="Material Usage by Type",
                    width=800,
                    height=300,
                    show_legend=True,
                    show_percentage=True
                )
                pie_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(
                    self.material_usage_frame,
                    text="No material usage data available",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(
                self.material_usage_frame,
                text="No material usage data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _update_tool_usage(self):
        """Update tool usage chart."""
        # Clear existing chart
        for widget in self.tool_usage_frame.winfo_children():
            widget.destroy()

        # Check if we have tool usage data
        if hasattr(self.project_metrics_data, 'tool_usage'):
            tool_usage = self.project_metrics_data.tool_usage

            if isinstance(tool_usage, dict) and tool_usage:
                # Prepare data for bar chart
                chart_data = [
                    {
                        "label": tool_type,
                        "value": usage,
                        "color": COLORS.get(f"tool_{i}", COLORS["primary"])
                    }
                    for i, (tool_type, usage) in enumerate(tool_usage.items())
                ]

                # Sort by usage (descending)
                chart_data.sort(key=lambda x: x["value"], reverse=True)

                # Create bar chart
                bar_chart = create_bar_chart(
                    self.tool_usage_frame,
                    chart_data,
                    title="Tool Usage by Type",
                    x_label="Tool Type",
                    y_label="Usage Hours",
                    width=800,
                    height=300
                )
                bar_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(
                    self.tool_usage_frame,
                    text="No tool usage data available",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(
                self.tool_usage_frame,
                text="No tool usage data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _update_time_allocation(self):
        """Update time allocation chart."""
        # Clear existing chart
        for widget in self.time_allocation_frame.winfo_children():
            widget.destroy()

        # Check if we have time allocation data
        if hasattr(self.project_metrics_data, 'time_allocation'):
            time_allocation = self.project_metrics_data.time_allocation

            if isinstance(time_allocation, dict) and time_allocation:
                # Prepare data for pie chart
                chart_data = [
                    {
                        "label": activity,
                        "value": percentage,
                        "color": COLORS.get(f"activity_{i}", COLORS["accent"])
                    }
                    for i, (activity, percentage) in enumerate(time_allocation.items())
                ]

                # Create pie chart
                pie_chart = create_pie_chart(
                    self.time_allocation_frame,
                    chart_data,
                    title="Project Time Allocation",
                    width=800,
                    height=300,
                    show_legend=True,
                    show_percentage=True
                )
                pie_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(
                    self.time_allocation_frame,
                    text="No time allocation data available",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(
                self.time_allocation_frame,
                text="No time allocation data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

    def _update_bottleneck_section(self):
        """Update bottleneck analysis section with loaded data."""
        if not self.bottleneck_analysis:
            return

        # Clear existing chart
        for widget in self.bottleneck_chart_frame.winfo_children():
            widget.destroy()

        # Clear existing recommendations
        self.recommendations_text.config(state=tk.NORMAL)
        self.recommendations_text.delete(1.0, tk.END)

        # Check if we have bottleneck data
        if isinstance(self.bottleneck_analysis, dict) and self.bottleneck_analysis:
            # Extract bottleneck scores
            bottleneck_scores = {}
            recommendations = []

            # Extract bottleneck scores and recommendations
            for key, value in self.bottleneck_analysis.items():
                if key == "recommendations":
                    if isinstance(value, list):
                        recommendations = value
                    elif isinstance(value, str):
                        recommendations = [value]
                elif isinstance(value, (int, float)):
                    bottleneck_scores[key] = value
                elif isinstance(value, dict) and "score" in value:
                    bottleneck_scores[key] = value["score"]
                    if "recommendation" in value:
                        recommendations.append(f"{key}: {value['recommendation']}")

            # Prepare data for bar chart
            chart_data = [
                {
                    "label": bottleneck,
                    "value": score,
                    "color": self._get_bottleneck_color(score)
                }
                for bottleneck, score in bottleneck_scores.items()
            ]

            # Sort by bottleneck score (descending)
            chart_data.sort(key=lambda x: x["value"], reverse=True)

            # Create bar chart
            if chart_data:
                bar_chart = create_bar_chart(
                    self.bottleneck_chart_frame,
                    chart_data,
                    title="Bottleneck Analysis",
                    x_label="Factor",
                    y_label="Impact Score",
                    width=400,
                    height=300
                )
                bar_chart.pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(
                    self.bottleneck_chart_frame,
                    text="No bottleneck analysis data available",
                    anchor=tk.CENTER
                ).pack(fill=tk.BOTH, expand=True)

            # Update recommendations
            if recommendations:
                for i, recommendation in enumerate(recommendations):
                    self.recommendations_text.insert(tk.END, f"{i + 1}. {recommendation}\n\n")
            else:
                self.recommendations_text.insert(tk.END, "No specific recommendations available.")

            self.recommendations_text.config(state=tk.DISABLED)
        else:
            # Show a message if no data
            ttk.Label(
                self.bottleneck_chart_frame,
                text="No bottleneck analysis data available",
                anchor=tk.CENTER
            ).pack(fill=tk.BOTH, expand=True)

            self.recommendations_text.insert(tk.END, "No bottleneck analysis data available.")
            self.recommendations_text.config(state=tk.DISABLED)

    def _get_time_trend_text(self, trend_value):
        """
        Get descriptive text for time trend.

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

    def _get_efficiency_text(self, efficiency):
        """
        Get descriptive text for efficiency rating.

        Args:
            efficiency: The efficiency percentage

        Returns:
            Efficiency rating text
        """
        if efficiency >= 90:
            return "Excellent"
        elif efficiency >= 80:
            return "Good"
        elif efficiency >= 70:
            return "Satisfactory"
        elif efficiency >= 60:
            return "Needs Improvement"
        else:
            return "Poor"

    def _get_bottleneck_color(self, score):
        """
        Get color for bottleneck visualization based on score.

        Args:
            score: The bottleneck score

        Returns:
            Color hex code
        """
        if score >= 8:
            return COLORS["danger"]
        elif score >= 5:
            return COLORS["warning"]
        elif score >= 3:
            return COLORS["secondary"]
        else:
            return COLORS["success"]

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

    def _on_project_type_change(self, event):
        """
        Handle project type change.

        Args:
            event: The combobox selection event
        """
        self.project_type = self.project_type_var.get()

    def _apply_filters(self):
        """Apply filters and reload data."""
        self._load_data()

    def _reset_filters(self):
        """Reset filters to default values."""
        self.period_var.set("Last 12 Months")
        self._set_default_date_range("Last 12 Months")
        self.project_type_var.set("All")
        self.project_type = "All"
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