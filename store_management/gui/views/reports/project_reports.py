# gui/views/reports/project_reports.py
"""
Project reports module for the leatherworking ERP system.

This module provides various project-related reports, including
project status tracking, efficiency metrics, and cost analysis.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import math

from gui.views.reports.base_report_view import BaseReportView
from gui.views.reports.export_utils import ReportExporter, get_default_report_filename
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.widgets.enum_combobox import EnumCombobox
from gui.theme import COLORS
from gui.config import DEFAULT_PADDING

from database.models.enums import (
    ProjectType, ProjectStatus, PickingListStatus, ToolListStatus
)

from di import resolve
from utils.service_access import with_service

logger = logging.getLogger(__name__)


class ProjectStatusReport(BaseReportView):
    """
    Project Status Report.

    Provides an overview of project statuses, timelines, and completion metrics.
    """

    REPORT_TITLE = "Project Status Report"
    REPORT_DESCRIPTION = "Overview of project statuses, timelines, and completion metrics"

    def __init__(self, parent):
        """
        Initialize the project status report view.

        Args:
            parent: The parent widget
        """
        # Initialize filter variables
        self.project_type_filter = tk.StringVar()
        self.status_filter = tk.StringVar()
        self.sort_by = tk.StringVar()

        # Initialize report columns
        self.columns = [
            {"name": "Project ID", "key": "id", "width": 80},
            {"name": "Project Name", "key": "name", "width": 200},
            {"name": "Type", "key": "type", "width": 120},
            {"name": "Status", "key": "status", "width": 120},
            {"name": "Start Date", "key": "start_date", "width": 100},
            {"name": "End Date", "key": "end_date", "width": 100},
            {"name": "Duration (Days)", "key": "duration_days", "width": 120},
            {"name": "Completion %", "key": "completion_percentage", "width": 100},
            {"name": "Days Left", "key": "days_left", "width": 80},
            {"name": "Customer", "key": "customer_name", "width": 150}
        ]

        # Call parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the project status report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the filter controls
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Project Type Filter
        type_frame = ttk.Frame(filter_container)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(type_frame, text="Project Type:").pack(side=tk.LEFT, padx=(0, 5))

        # Get project types from enum
        project_types = ["All"] + [t.value for t in ProjectType]
        type_combo = ttk.Combobox(type_frame, textvariable=self.project_type_filter,
                                  values=project_types, state="readonly", width=15)
        type_combo.pack(side=tk.LEFT)
        self.project_type_filter.set("All")  # Default value

        # Status Filter
        status_frame = ttk.Frame(filter_container)
        status_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        # Simplified status list for filtering
        statuses = ["All", "Not Started", "In Progress", "Completed", "On Hold", "Cancelled"]
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_filter,
                                    values=statuses, state="readonly", width=15)
        status_combo.pack(side=tk.LEFT)
        self.status_filter.set("All")  # Default value

        # Sort options
        sort_frame = ttk.Frame(filter_container)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sort By:").pack(side=tk.LEFT, padx=(0, 5))

        sort_options = ["Start Date", "End Date", "Project Name", "Completion %", "Days Left"]
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by,
                                  values=sort_options, state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT)
        self.sort_by.set("Start Date")  # Default value

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.project_type_filter.set("All")
        self.status_filter.set("All")
        self.sort_by.set("Start Date")

    def create_report_content(self, parent):
        """
        Create the main content area for the project status report.

        Args:
            parent: The parent widget
        """
        # Create notebook for tabbed views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create project list tab
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="Project List")

        # Create gantt view tab
        self.gantt_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gantt_frame, text="Timeline View")

        # Create status distribution tab
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="Status Distribution")

        # Set up the list view
        self._create_list_view(self.list_frame)

        # Set up the gantt view
        self._create_gantt_view(self.gantt_frame)

        # Set up the status distribution view
        self._create_status_view(self.status_frame)

        # Create summary section
        self._create_summary_section(parent)

    def _create_list_view(self, parent):
        """
        Create the project list view tab.

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

    def _create_gantt_view(self, parent):
        """
        Create the gantt/timeline view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper gantt chart library
        # For now, we'll create a simple visual representation with canvas

        # Create a frame for the gantt chart
        gantt_frame = ttk.Frame(parent)
        gantt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the gantt chart
        self.gantt_canvas = tk.Canvas(
            gantt_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.gantt_canvas.pack(fill=tk.BOTH, expand=True)

    def _create_status_view(self, parent):
        """
        Create the status distribution view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Create a frame for the status distribution chart
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the status distribution chart
        self.status_canvas = tk.Canvas(
            status_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.status_canvas.pack(fill=tk.BOTH, expand=True)

    def _create_summary_section(self, parent):
        """
        Create the summary section below the tabs.

        Args:
            parent: The parent widget
        """
        # Create a summary frame
        summary_frame = ttk.LabelFrame(parent, text="Project Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create a grid for the summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Projects:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_projects_label = ttk.Label(summary_grid, text="0")
        self.total_projects_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="In Progress:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.in_progress_label = ttk.Label(summary_grid, text="0")
        self.in_progress_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Completed:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.completed_label = ttk.Label(summary_grid, text="0")
        self.completed_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="Avg Duration:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.avg_duration_label = ttk.Label(summary_grid, text="0 days")
        self.avg_duration_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Delayed:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.delayed_label = ttk.Label(summary_grid, text="0")
        self.delayed_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="On Hold:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.on_hold_label = ttk.Label(summary_grid, text="0")
        self.on_hold_label.grid(row=1, column=5, sticky=tk.W)

    def load_report_data(self):
        """Load project status data for the report."""
        self.update_status("Loading project status data...")
        self.is_loading = True

        try:
            # Get date range
            start_date, end_date = self.date_selector.get_date_range()

            # Get filter values
            project_type = self.project_type_filter.get()
            status = self.status_filter.get()
            sort_by = self.sort_by.get()

            # Build filter criteria
            criteria = {
                "start_date": start_date,
                "end_date": end_date
            }

            if project_type != "All":
                criteria["project_type"] = project_type

            if status != "All":
                criteria["status"] = status

            # Translate sort_by to data field
            sort_field_map = {
                "Start Date": "start_date",
                "End Date": "end_date",
                "Project Name": "name",
                "Completion %": "completion_percentage",
                "Days Left": "days_left"
            }

            sort_field = sort_field_map.get(sort_by, "start_date")
            criteria["sort_by"] = sort_field

            # Generate sample data for demonstration
            self.report_data = self._get_sample_project_data(criteria)

            # Update the display
            self.update_report_display()

            # Update status
            self.update_status(f"Loaded data for {len(self.report_data)} projects")

        except Exception as e:
            logger.error(f"Error loading project status data: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def update_report_display(self):
        """Update the report display with current data."""
        # Update the list view
        self._update_list_view()

        # Update the gantt view
        self._update_gantt_view()

        # Update the status distribution view
        self._update_status_view()

        # Update the summary section
        self._update_summary_section()

    def _update_list_view(self):
        """Update the project list view with the current report data."""
        # Clear existing data
        self.tree.clear()

        if not self.report_data:
            return

        # Add data to treeview
        for item in self.report_data:
            values = [item.get(col["key"], "") for col in self.columns[1:]]

            # Format date values
            date_indices = [i for i, col in enumerate(self.columns[1:])
                            if col["key"] in ["start_date", "end_date"]]

            for idx in date_indices:
                date_value = item.get(self.columns[idx + 1]["key"])
                if isinstance(date_value, datetime):
                    values[idx] = date_value.strftime("%Y-%m-%d")

            # Format percentage values
            percent_indices = [i for i, col in enumerate(self.columns[1:])
                               if col["key"] in ["completion_percentage"]]

            for idx in percent_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"{values[idx]:.1f}%"

            # Add tag based on status
            status = item.get("status", "").lower()

            if "complete" in status:
                tag = "completed"
            elif "hold" in status:
                tag = "on_hold"
            elif "cancel" in status:
                tag = "cancelled"
            elif item.get("days_left", 0) < 0:
                tag = "overdue"
            else:
                tag = "normal"

            self.tree.insert("", tk.END, values=values, tags=(tag,))

        # Configure tag colors
        self.tree.tag_configure("completed", background="#C8E6C9")  # Light green
        self.tree.tag_configure("on_hold", background="#FFF9C4")  # Light yellow
        self.tree.tag_configure("cancelled", background="#E0E0E0")  # Light gray
        self.tree.tag_configure("overdue", background="#FFCDD2")  # Light red

    def _update_gantt_view(self):
        """Update the gantt view with timeline visualization."""
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Clear the canvas
        self.gantt_canvas.delete("all")

        if not self.report_data or len(self.report_data) == 0:
            self.gantt_canvas.create_text(
                200, 100,
                text="No project data available for timeline visualization.",
                fill="#666666",
                font=("TkDefaultFont", 10)
            )
            return

        # Get canvas dimensions
        canvas_width = self.gantt_canvas.winfo_width() or 600
        canvas_height = self.gantt_canvas.winfo_height() or 400

        # Set chart margins
        margin_left = 200  # For project names
        margin_right = 20
        margin_top = 40
        margin_bottom = 30

        # Calculate chart area
        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        # Find date range for all projects
        all_dates = []
        for project in self.report_data:
            if project.get("start_date"):
                all_dates.append(project["start_date"])
            if project.get("end_date"):
                all_dates.append(project["end_date"])

        if not all_dates:
            # No valid dates found
            self.gantt_canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text="No valid date range found for projects.",
                fill="#666666",
                font=("TkDefaultFont", 10)
            )
            return

        # Calculate date range with padding
        min_date = min(all_dates)
        max_date = max(all_dates)

        # Add some padding to the date range (10% on each side)
        date_range_days = (max_date - min_date).days
        if date_range_days <= 0:
            date_range_days = 30  # Default to 30 days if range is zero or negative

        padding_days = max(5, date_range_days // 10)
        chart_start = min_date - timedelta(days=padding_days)
        chart_end = max_date + timedelta(days=padding_days)

        chart_days = (chart_end - chart_start).days

        # Draw the timeline header
        self.gantt_canvas.create_text(
            canvas_width // 2, margin_top // 2,
            text="Project Timeline",
            font=("TkDefaultFont", 12, "bold")
        )

        # Draw time axis
        # X-axis
        self.gantt_canvas.create_line(
            margin_left, canvas_height - margin_bottom,
                         canvas_width - margin_right, canvas_height - margin_bottom,
            width=2
        )

        # Date markers
        num_markers = min(chart_days // 7 + 1, 12)  # Show dates roughly every week, but no more than 12
        if num_markers < 2:
            num_markers = 2  # Ensure at least start and end dates

        date_step = chart_days / (num_markers - 1)

        for i in range(num_markers):
            marker_date = chart_start + timedelta(days=i * date_step)
            x_pos = margin_left + (i * date_step * chart_width / chart_days)

            # Date marker line
            self.gantt_canvas.create_line(
                x_pos, canvas_height - margin_bottom,
                x_pos, canvas_height - margin_bottom + 5,
                width=1
            )

            # Date label
            self.gantt_canvas.create_text(
                x_pos, canvas_height - margin_bottom + 15,
                text=marker_date.strftime("%Y-%m-%d"),
                font=("TkDefaultFont", 8),
                angle=45,
                anchor=tk.NE
            )

        # Draw today marker if within chart range
        today = datetime.now()
        if chart_start <= today <= chart_end:
            days_from_start = (today - chart_start).days
            today_x = margin_left + (days_from_start * chart_width / chart_days)

            self.gantt_canvas.create_line(
                today_x, margin_top,
                today_x, canvas_height - margin_bottom,
                width=1, dash=(5, 3), fill="#FF0000"
            )

            self.gantt_canvas.create_text(
                today_x, margin_top - 10,
                text="Today",
                fill="#FF0000",
                font=("TkDefaultFont", 8)
            )

        # Draw project bars
        bar_height = min(20, (chart_height) / (len(self.report_data) + 1))
        spacing = (chart_height - bar_height * len(self.report_data)) / (len(self.report_data) + 1)

        for i, project in enumerate(sorted(self.report_data, key=lambda p: p.get("start_date", datetime.min))):
            # Get project dates
            start_date = project.get("start_date", chart_start)
            end_date = project.get("end_date", chart_end)

            # Ensure dates are within chart range
            if start_date < chart_start:
                start_date = chart_start
            if end_date > chart_end:
                end_date = chart_end

            # Convert dates to x positions
            start_days = (start_date - chart_start).days
            end_days = (end_date - chart_start).days

            start_x = margin_left + (start_days * chart_width / chart_days)
            end_x = margin_left + (end_days * chart_width / chart_days)

            # Y position for this project
            y_pos = margin_top + spacing * (i + 1) + bar_height * i

            # Determine color based on status
            status = project.get("status", "").lower()
            if "complete" in status:
                fill_color = "#4CAF50"  # Green
            elif "hold" in status:
                fill_color = "#FFC107"  # Amber
            elif "cancel" in status:
                fill_color = "#9E9E9E"  # Gray
            elif project.get("days_left", 0) < 0:
                fill_color = "#F44336"  # Red
            else:
                fill_color = "#2196F3"  # Blue

            # Draw the project bar
            self.gantt_canvas.create_rectangle(
                start_x, y_pos,
                end_x, y_pos + bar_height,
                fill=fill_color, outline="#000000"
            )

            # Add progress indicator if available
            completion = project.get("completion_percentage", 0)
            if completion > 0:
                progress_width = (end_x - start_x) * (completion / 100)
                self.gantt_canvas.create_rectangle(
                    start_x, y_pos,
                    start_x + progress_width, y_pos + bar_height,
                    fill="#1565C0",  # Darker blue
                    outline=""
                )

            # Add project name label
            project_name = project.get("name", f"Project {i + 1}")
            truncated_name = project_name[:20] + "..." if len(project_name) > 20 else project_name

            self.gantt_canvas.create_text(
                margin_left - 10, y_pos + bar_height // 2,
                text=truncated_name,
                anchor=tk.E,
                font=("TkDefaultFont", 9)
            )

    def _update_status_view(self):
        """Update the status distribution view."""
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Clear the canvas
        self.status_canvas.delete("all")

        if not self.report_data:
            self.status_canvas.create_text(
                200, 100,
                text="No project data available for status visualization.",
                fill="#666666",
                font=("TkDefaultFont", 10)
            )
            return

        # Get canvas dimensions
        canvas_width = self.status_canvas.winfo_width() or 600
        canvas_height = self.status_canvas.winfo_height() or 400

        # Set chart margins
        margin_left = 60
        margin_right = 30
        margin_top = 40
        margin_bottom = 60

        # Calculate chart area
        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        # Count projects by status
        status_counts = {}
        for project in self.report_data:
            status = project.get("status", "Unknown")
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        # Sort statuses by order in workflow
        status_order = [
            "not_started", "initial_consultation", "design_phase", "pattern_development",
            "client_approval", "material_selection", "material_purchased",
            "cutting", "skiving", "preparation", "assembly", "stitching",
            "edge_finishing", "hardware_installation", "conditioning",
            "quality_check", "final_touches", "photography", "packaging",
            "completed", "on_hold", "cancelled"
        ]

        # Group statuses into major categories for clearer visualization
        status_categories = {
            "Not Started": ["not_started", "initial_consultation"],
            "Design": ["design_phase", "pattern_development", "client_approval"],
            "Materials": ["material_selection", "material_purchased"],
            "Production": ["cutting", "skiving", "preparation", "assembly", "stitching",
                           "edge_finishing", "hardware_installation", "conditioning"],
            "Finishing": ["quality_check", "final_touches", "photography", "packaging"],
            "Completed": ["completed"],
            "On Hold": ["on_hold"],
            "Cancelled": ["cancelled"]
        }

        # Count by category
        category_counts = {}
        for project in self.report_data:
            status = project.get("status", "").lower()

            # Find which category this status belongs to
            category = "Other"
            for cat, statuses in status_categories.items():
                if any(s in status for s in statuses):
                    category = cat
                    break

            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1

        # Colors for categories
        category_colors = {
            "Not Started": "#E3F2FD",  # Light blue
            "Design": "#BBDEFB",  # Blue 100
            "Materials": "#90CAF9",  # Blue 200
            "Production": "#64B5F6",  # Blue 300
            "Finishing": "#42A5F5",  # Blue 400
            "Completed": "#4CAF50",  # Green
            "On Hold": "#FFC107",  # Amber
            "Cancelled": "#9E9E9E",  # Gray
            "Other": "#E0E0E0"  # Light gray
        }

        # Draw title
        self.status_canvas.create_text(
            canvas_width // 2, margin_top // 2,
            text="Project Status Distribution",
            font=("TkDefaultFont", 12, "bold")
        )

        # Calculate total for percentage
        total_projects = len(self.report_data)

        # Draw the bar chart
        bar_width = min(50, chart_width / (len(category_counts) + 1))
        spacing = (chart_width - bar_width * len(category_counts)) / (len(category_counts) + 1)

        # Sort categories by workflow order
        ordered_categories = [
            "Not Started", "Design", "Materials", "Production", "Finishing",
            "Completed", "On Hold", "Cancelled", "Other"
        ]
        categories = [c for c in ordered_categories if c in category_counts]

        max_count = max(category_counts.values()) if category_counts else 0

        for i, category in enumerate(categories):
            count = category_counts.get(category, 0)
            percentage = (count / total_projects) * 100 if total_projects > 0 else 0

            # Calculate bar height
            bar_height = (count / max_count) * chart_height if max_count > 0 else 0

            # Calculate bar position
            x_pos = margin_left + spacing * (i + 1) + bar_width * i
            y_pos = canvas_height - margin_bottom - bar_height

            # Draw the bar
            self.status_canvas.create_rectangle(
                x_pos, y_pos,
                x_pos + bar_width, canvas_height - margin_bottom,
                fill=category_colors.get(category, "#E0E0E0"),
                outline="#000000"
            )

            # Add category label
            self.status_canvas.create_text(
                x_pos + bar_width // 2, canvas_height - margin_bottom + 15,
                text=category,
                font=("TkDefaultFont", 8),
                angle=45,
                anchor=tk.NW
            )

            # Add count and percentage
            self.status_canvas.create_text(
                x_pos + bar_width // 2, y_pos - 10,
                text=f"{count} ({percentage:.1f}%)",
                font=("TkDefaultFont", 8)
            )

        # Y-axis
        self.status_canvas.create_line(
            margin_left, margin_top,
            margin_left, canvas_height - margin_bottom,
            width=1
        )

        # X-axis
        self.status_canvas.create_line(
            margin_left, canvas_height - margin_bottom,
                         canvas_width - margin_right, canvas_height - margin_bottom,
            width=1
        )

        # Y-axis labels
        for i in range(6):
            y_value = max_count * i / 5
            y_pos = canvas_height - margin_bottom - (i * chart_height / 5)

            self.status_canvas.create_line(
                margin_left - 5, y_pos,
                margin_left, y_pos,
                width=1
            )

            self.status_canvas.create_text(
                margin_left - 10, y_pos,
                text=str(int(y_value)),
                anchor=tk.E,
                font=("TkDefaultFont", 8)
            )

    def _update_summary_section(self):
        """Update the summary section with aggregated metrics."""
        if not self.report_data:
            return

        # Calculate summary metrics
        total_projects = len(self.report_data)

        # Count by status categories
        in_progress_count = 0
        completed_count = 0
        on_hold_count = 0
        delayed_count = 0

        for project in self.report_data:
            status = project.get("status", "").lower()

            if "complete" in status:
                completed_count += 1
            elif "hold" in status:
                on_hold_count += 1
            elif "cancel" not in status:  # Not counting cancelled as in progress
                in_progress_count += 1

            # Count delayed projects (negative days left and not completed)
            if project.get("days_left", 0) < 0 and "complete" not in status and "cancel" not in status:
                delayed_count += 1

        # Calculate average duration for completed projects
        completed_projects = [p for p in self.report_data
                              if "complete" in p.get("status", "").lower()]

        total_duration = sum(p.get("duration_days", 0) for p in completed_projects)
        avg_duration = total_duration / len(completed_projects) if completed_projects else 0

        # Update summary labels
        self.total_projects_label.config(text=str(total_projects))
        self.in_progress_label.config(text=str(in_progress_count))
        self.completed_label.config(text=str(completed_count))
        self.avg_duration_label.config(text=f"{int(avg_duration)} days")
        self.delayed_label.config(text=str(delayed_count))
        self.on_hold_label.config(text=str(on_hold_count))

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")

        try:
            # Create summary data for the report
            total_projects = len(self.report_data)
            in_progress = sum(1 for p in self.report_data
                              if "complete" not in p.get("status", "").lower()
                              and "cancel" not in p.get("status", "").lower())
            completed = sum(1 for p in self.report_data
                            if "complete" in p.get("status", "").lower())

            summary_data = {
                "Total Projects": str(total_projects),
                "In Progress": str(in_progress),
                "Completed": str(completed),
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
            total_projects = len(self.report_data)
            in_progress = sum(1 for p in self.report_data
                              if "complete" not in p.get("status", "").lower()
                              and "cancel" not in p.get("status", "").lower())
            completed = sum(1 for p in self.report_data
                            if "complete" in p.get("status", "").lower())

            summary_data = {
                "Total Projects": str(total_projects),
                "In Progress": str(in_progress),
                "Completed": str(completed),
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

    def _get_sample_project_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample project data for demonstration purposes.

        In a real implementation, this would fetch data from the project service.

        Args:
            criteria: Filter criteria

        Returns:
            List of project records with status data
        """
        sample_data = []

        # Get date range from criteria
        start_date = criteria.get("start_date", datetime.now() - timedelta(days=180))
        end_date = criteria.get("end_date", datetime.now())

        # Project types from enum
        project_types = [t.value for t in ProjectType
                         if t.value not in ["sample", "prototype"]]  # Filter out non-client types

        # Filter by project type if specified
        if criteria.get("project_type") and criteria["project_type"] != "All":
            project_types = [t for t in project_types if t == criteria["project_type"]]

        # Project statuses - simplified for better visualization
        status_groups = {
            "Not Started": ["not_started", "initial_consultation"],
            "Design": ["design_phase", "pattern_development", "client_approval"],
            "Materials": ["material_selection", "material_purchased"],
            "Production": ["cutting", "skiving", "preparation", "assembly", "stitching"],
            "Finishing": ["edge_finishing", "hardware_installation", "conditioning",
                          "quality_check", "final_touches", "photography", "packaging"],
            "Completed": ["completed"],
            "On Hold": ["on_hold"],
            "Cancelled": ["cancelled"]
        }

        # Filter by status if specified
        active_status_groups = list(status_groups.keys())
        if criteria.get("status") and criteria["status"] != "All":
            if criteria["status"] in status_groups:
                active_status_groups = [criteria["status"]]
            else:
                # Try to find a match
                for group, statuses in status_groups.items():
                    if criteria["status"].lower() in [s.lower() for s in statuses]:
                        active_status_groups = [group]
                        break

        # Sample customer names
        customer_names = [
            "John Smith", "Jane Johnson", "Michael Williams", "Emily Jones",
            "David Brown", "Sarah Davis", "Robert Miller", "Lisa Wilson",
            "James Moore", "Jennifer Taylor", "Daniel Anderson", "Elizabeth Thomas"
        ]

        # Generate projects
        today = datetime.now()
        project_id = 1000

        for i in range(30):  # Generate 30 sample projects
            # Pick a project type
            project_type = project_types[i % len(project_types)]

            # Generate project name based on type
            project_name = f"{project_type.title()} Project {project_id}"

            # Determine status group - create a reasonable distribution
            status_idx = i % len(active_status_groups)
            status_group = active_status_groups[status_idx]

            # Pick a specific status from the group
            possible_statuses = status_groups[status_group]
            status = possible_statuses[i % len(possible_statuses)]

            # Determine project dates based on status
            if status_group in ["Not Started", "Design"]:
                # New projects - start dates near today
                days_ago = i % 10
                start_date = today - timedelta(days=days_ago)

                # End date is in the future
                duration = 14 + (i % 30)  # 14-43 days
                end_date = start_date + timedelta(days=duration)

                # Completion percentage
                if status_group == "Not Started":
                    completion = 0
                else:
                    completion = 10 + (i % 3) * 10  # 10-30%

            elif status_group in ["Materials", "Production"]:
                # In-progress projects
                days_ago = 10 + (i % 20)
                start_date = today - timedelta(days=days_ago)

                duration = 21 + (i % 21)  # 21-41 days
                end_date = start_date + timedelta(days=duration)

                # Completion based on time elapsed
                days_elapsed = (today - start_date).days
                total_days = (end_date - start_date).days
                completion = min(95, (days_elapsed / total_days) * 100) if total_days > 0 else 0

                # Add some variation
                completion_variation = -10 + (i % 20)  # -10 to +9
                completion = max(0, min(95, completion + completion_variation))

            elif status_group == "Finishing":
                # Late-stage projects
                days_ago = 15 + (i % 25)
                start_date = today - timedelta(days=days_ago)

                duration = 28 + (i % 14)  # 28-41 days
                end_date = start_date + timedelta(days=duration)

                # High completion for finishing
                completion = 70 + (i % 25)  # 70-94%

            elif status_group == "Completed":
                # Completed projects - in the past
                days_ago = 30 + (i % 90)
                end_date = today - timedelta(days=i % 30)

                duration = 14 + (i % 28)  # 14-41 days
                start_date = end_date - timedelta(days=duration)

                completion = 100

            elif status_group == "On Hold":
                # On hold projects - started but paused
                days_ago = 20 + (i % 40)
                start_date = today - timedelta(days=days_ago)

                duration = 30 + (i % 30)  # 30-59 days
                end_date = start_date + timedelta(days=duration)

                # Partial completion before being put on hold
                completion = 20 + (i % 40)  # 20-59%

            else:  # Cancelled
                # Cancelled projects
                days_ago = 10 + (i % 50)
                start_date = today - timedelta(days=days_ago)

                # Short duration before cancellation
                duration = 5 + (i % 10)  # 5-14 days
                end_date = start_date + timedelta(days=duration)

                # Low completion before cancellation
                completion = 5 + (i % 15)  # 5-19%

            # Calculate days left
            days_left = (end_date - today).days

            # Calculate duration in days
            duration_days = (end_date - start_date).days

            # Assign a customer
            customer_name = customer_names[i % len(customer_names)]

            # Create the project record
            project = {
                "id": project_id,
                "name": project_name,
                "type": project_type,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
                "duration_days": duration_days,
                "completion_percentage": completion,
                "days_left": days_left,
                "customer_name": customer_name
            }

            sample_data.append(project)
            project_id += 1

        # Sort the data if requested
        sort_field = criteria.get("sort_by", "start_date")
        reverse = True if sort_field in ["completion_percentage"] else False

        if sort_field in ["start_date", "end_date"]:
            sample_data.sort(key=lambda x: x.get(sort_field, datetime.min), reverse=reverse)
        elif sort_field == "days_left":
            # Sort with overdue projects first (negative days)
            sample_data.sort(key=lambda x: x.get(sort_field, 0))
        else:
            sample_data.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)

        return sample_data


class ProjectEfficiencyReport(BaseReportView):
    """
    Project Efficiency Report.

    Analyzes project efficiency metrics, including time management,
    resource utilization, and productivity.
    """

    REPORT_TITLE = "Project Efficiency Report"
    REPORT_DESCRIPTION = "Analysis of project efficiency and productivity metrics"

    def __init__(self, parent):
        """
        Initialize the project efficiency report view.

        Args:
            parent: The parent widget
        """
        # Initialize filter variables
        self.project_type_filter = tk.StringVar()
        self.min_completion_filter = tk.StringVar()
        self.sort_by = tk.StringVar()
        self.completed_only = tk.BooleanVar(value=False)

        # Initialize report columns
        self.columns = [
            {"name": "Project ID", "key": "id", "width": 80},
            {"name": "Project Name", "key": "name", "width": 180},
            {"name": "Type", "key": "type", "width": 100},
            {"name": "Status", "key": "status", "width": 100},
            {"name": "Planned Days", "key": "planned_days", "width": 100},
            {"name": "Actual Days", "key": "actual_days", "width": 100},
            {"name": "Time Variance", "key": "time_variance", "width": 100},
            {"name": "Material Efficiency", "key": "material_efficiency", "width": 120},
            {"name": "Labor Hours", "key": "labor_hours", "width": 90},
            {"name": "Productivity", "key": "productivity", "width": 100},
            {"name": "Overall Score", "key": "efficiency_score", "width": 100}
        ]

        # Call parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the project efficiency report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the filter controls
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Project Type Filter
        type_frame = ttk.Frame(filter_container)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(type_frame, text="Project Type:").pack(side=tk.LEFT, padx=(0, 5))

        # Get project types from enum
        project_types = ["All"] + [t.value for t in ProjectType]
        type_combo = ttk.Combobox(type_frame, textvariable=self.project_type_filter,
                                  values=project_types, state="readonly", width=15)
        type_combo.pack(side=tk.LEFT)
        self.project_type_filter.set("All")  # Default value

        # Minimum Completion Filter
        min_completion_frame = ttk.Frame(filter_container)
        min_completion_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(min_completion_frame, text="Min Completion %:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(min_completion_frame, textvariable=self.min_completion_filter, width=5).pack(side=tk.LEFT)

        # Completed Only Checkbox
        completed_frame = ttk.Frame(filter_container)
        completed_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Checkbutton(completed_frame, text="Completed Only",
                        variable=self.completed_only).pack(side=tk.LEFT)

        # Sort options
        sort_frame = ttk.Frame(filter_container)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sort By:").pack(side=tk.LEFT, padx=(0, 5))

        sort_options = ["Efficiency Score", "Time Variance", "Material Efficiency", "Productivity"]
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by,
                                  values=sort_options, state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT)
        self.sort_by.set("Efficiency Score")  # Default value

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.project_type_filter.set("All")
        self.min_completion_filter.set("")
        self.sort_by.set("Efficiency Score")
        self.completed_only.set(False)

    def create_report_content(self, parent):
        """
        Create the main content area for the project efficiency report.

        Args:
            parent: The parent widget
        """
        # Create notebook for tabbed views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create efficiency metrics tab
        self.metrics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.metrics_frame, text="Efficiency Metrics")

        # Create time variance tab
        self.time_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.time_frame, text="Time Variance")

        # Create productivity analysis tab
        self.productivity_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.productivity_frame, text="Productivity Analysis")

        # Set up the metrics view (main grid view)
        self._create_metrics_view(self.metrics_frame)

        # Set up the time variance view
        self._create_time_variance_view(self.time_frame)

        # Set up the productivity analysis view
        self._create_productivity_view(self.productivity_frame)

        # Create summary section
        self._create_summary_section(parent)

    def _create_metrics_view(self, parent):
        """
        Create the efficiency metrics view tab.

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

    def _create_time_variance_view(self, parent):
        """
        Create the time variance view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Create a frame for the time variance chart
        time_frame = ttk.Frame(parent)
        time_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the time variance chart
        self.time_canvas = tk.Canvas(
            time_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.time_canvas.pack(fill=tk.BOTH, expand=True)

    def _create_productivity_view(self, parent):
        """
        Create the productivity analysis view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Create a frame for the productivity chart
        productivity_frame = ttk.Frame(parent)
        productivity_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the productivity chart
        self.productivity_canvas = tk.Canvas(
            productivity_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.productivity_canvas.pack(fill=tk.BOTH, expand=True)

    def _create_summary_section(self, parent):
        """
        Create the summary section below the tabs.

        Args:
            parent: The parent widget
        """
        # Create a summary frame
        summary_frame = ttk.LabelFrame(parent, text="Efficiency Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create a grid for the summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Projects:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_projects_label = ttk.Label(summary_grid, text="0")
        self.total_projects_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Avg Efficiency:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.avg_efficiency_label = ttk.Label(summary_grid, text="0.0%")
        self.avg_efficiency_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="On-Time Projects:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.on_time_label = ttk.Label(summary_grid, text="0 (0.0%)")
        self.on_time_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="Avg Time Variance:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.avg_variance_label = ttk.Label(summary_grid, text="0.0%")
        self.avg_variance_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Avg Material Usage:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.avg_material_label = ttk.Label(summary_grid, text="0.0%")
        self.avg_material_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="Most Efficient:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.most_efficient_label = ttk.Label(summary_grid, text="None")
        self.most_efficient_label.grid(row=1, column=5, sticky=tk.W)

    def load_report_data(self):
        """Load project efficiency data for the report."""
        self.update_status("Loading project efficiency data...")
        self.is_loading = True

        try:
            # Get date range
            start_date, end_date = self.date_selector.get_date_range()

            # Get filter values
            project_type = self.project_type_filter.get()
            min_completion = self.min_completion_filter.get()
            sort_by = self.sort_by.get()
            completed_only = self.completed_only.get()

            # Build filter criteria
            criteria = {
                "start_date": start_date,
                "end_date": end_date
            }

            if project_type != "All":
                criteria["project_type"] = project_type

            if min_completion:
                try:
                    criteria["min_completion"] = float(min_completion)
                except ValueError:
                    messagebox.showwarning("Invalid Filter", "Min Completion must be a number")

            if completed_only:
                criteria["completed_only"] = True

            # Translate sort_by to data field
            sort_field_map = {
                "Efficiency Score": "efficiency_score",
                "Time Variance": "time_variance",
                "Material Efficiency": "material_efficiency",
                "Productivity": "productivity"
            }

            sort_field = sort_field_map.get(sort_by, "efficiency_score")
            criteria["sort_by"] = sort_field

            # Generate sample data for demonstration
            self.report_data = self._get_sample_efficiency_data(criteria)

            # Update the display
            self.update_report_display()

            # Update status
            self.update_status(f"Loaded efficiency data for {len(self.report_data)} projects")

        except Exception as e:
            logger.error(f"Error loading project efficiency data: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def update_report_display(self):
        """Update the report display with current data."""
        # Update the metrics view
        self._update_metrics_view()

        # Update the time variance view
        self._update_time_variance_view()

        # Update the productivity view
        self._update_productivity_view()

        # Update the summary section
        self._update_summary_section()

    def _update_metrics_view(self):
        """Update the efficiency metrics view with the current report data."""
        # Clear existing data
        self.tree.clear()

        if not self.report_data:
            return

        # Add data to treeview
        for item in self.report_data:
            values = [item.get(col["key"], "") for col in self.columns[1:]]

            # Format percentage values
            percent_indices = [i for i, col in enumerate(self.columns[1:])
                               if col["key"] in ["time_variance", "material_efficiency",
                                                 "productivity", "efficiency_score"]]

            for idx in percent_indices:
                if isinstance(values[idx], (int, float)):
                    values[idx] = f"{values[idx]:.1f}%"

            # Format time variance with + sign for delays
            time_var_idx = [i for i, col in enumerate(self.columns[1:])
                            if col["key"] == "time_variance"][0]

            if isinstance(item.get("time_variance"), (int, float)):
                time_var = item["time_variance"]
                if time_var > 0:
                    values[time_var_idx] = f"+{time_var:.1f}%"
                else:
                    values[time_var_idx] = f"{time_var:.1f}%"

            # Add tag based on efficiency score
            if "efficiency_score" in item:
                score = item["efficiency_score"]
                if score < 70:
                    tag = "low_efficiency"
                elif score < 85:
                    tag = "medium_efficiency"
                else:
                    tag = "high_efficiency"
            else:
                tag = "medium_efficiency"

            self.tree.insert("", tk.END, values=values, tags=(tag,))

        # Configure tag colors
        self.tree.tag_configure("low_efficiency", background="#FFCDD2")  # Light red
        self.tree.tag_configure("medium_efficiency", background="#FFF9C4")  # Light yellow
        self.tree.tag_configure("high_efficiency", background="#C8E6C9")  # Light green

    def _update_time_variance_view(self):
        """Update the time variance view with visualization."""
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Clear the canvas
        self.time_canvas.delete("all")

        if not self.report_data or len(self.report_data) == 0:
            self.time_canvas.create_text(
                200, 100,
                text="No project data available for time variance visualization.",
                fill="#666666",
                font=("TkDefaultFont", 10)
            )
            return

        # Get canvas dimensions
        canvas_width = self.time_canvas.winfo_width() or 600
        canvas_height = self.time_canvas.winfo_height() or 400

        # Set chart margins
        margin_left = 180  # For project names
        margin_right = 50
        margin_top = 40
        margin_bottom = 30

        # Calculate chart area
        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        # Draw title
        self.time_canvas.create_text(
            canvas_width // 2, margin_top // 2,
            text="Project Time Variance",
            font=("TkDefaultFont", 12, "bold")
        )

        # Sort projects by time variance
        sorted_projects = sorted(self.report_data,
                                 key=lambda x: x.get("time_variance", 0))

        # Limit to top/bottom 15 for readability
        max_projects = min(15, len(sorted_projects))
        display_projects = sorted_projects[:max_projects]

        # Find min/max time variance for scaling
        min_variance = min((p.get("time_variance", 0) for p in display_projects), default=0)
        max_variance = max((p.get("time_variance", 0) for p in display_projects), default=0)

        # Ensure a reasonable range
        if abs(min_variance) > abs(max_variance):
            max_range = abs(min_variance)
        else:
            max_range = abs(max_variance)

        max_range = max(max_range, 10)  # At least ±10% range

        # Draw baseline (0% variance)
        baseline_x = margin_left + chart_width // 2

        self.time_canvas.create_line(
            baseline_x, margin_top,
            baseline_x, canvas_height - margin_bottom,
            width=1, dash=(5, 3)
        )

        self.time_canvas.create_text(
            baseline_x, margin_top - 10,
            text="On Time",
            font=("TkDefaultFont", 8)
        )

        # Draw scale lines and labels
        for pct in [-75, -50, -25, 0, 25, 50, 75]:
            if -max_range <= pct <= max_range:
                x_pos = baseline_x + (pct * chart_width / (2 * max_range))

                # Vertical grid line
                self.time_canvas.create_line(
                    x_pos, margin_top,
                    x_pos, canvas_height - margin_bottom,
                    width=1, dash=(1, 3), fill="#CCCCCC"
                )

                # Label
                if pct != 0:  # Skip 0 as it's labeled already
                    self.time_canvas.create_text(
                        x_pos, canvas_height - margin_bottom + 15,
                        text=f"{pct}%",
                        font=("TkDefaultFont", 8)
                    )

        # Draw variance bars
        bar_height = min(20, chart_height / (len(display_projects) + 1))
        spacing = (chart_height - bar_height * len(display_projects)) / (len(display_projects) + 1)

        for i, project in enumerate(display_projects):
            # Get project name and variance
            project_name = project.get("name", f"Project {i + 1}")
            time_variance = project.get("time_variance", 0)

            # Truncate long names
            truncated_name = project_name[:20] + "..." if len(project_name) > 20 else project_name

            # Calculate bar dimensions
            y_pos = margin_top + spacing * (i + 1) + bar_height * i

            # For bars: positive variance (delay) extends right, negative (early) extends left
            bar_width = time_variance * chart_width / (2 * max_range)

            if bar_width >= 0:
                # Delayed project (positive variance)
                x_start = baseline_x
                x_end = baseline_x + bar_width
                bar_color = "#F44336"  # Red
            else:
                # Early project (negative variance)
                x_start = baseline_x + bar_width
                x_end = baseline_x
                bar_color = "#4CAF50"  # Green

            # Draw the bar
            self.time_canvas.create_rectangle(
                x_start, y_pos,
                x_end, y_pos + bar_height,
                fill=bar_color,
                outline=""
            )

            # Add project name
            self.time_canvas.create_text(
                margin_left - 10, y_pos + bar_height // 2,
                text=truncated_name,
                anchor=tk.E,
                font=("TkDefaultFont", 9)
            )

            # Add variance label
            self.time_canvas.create_text(
                x_end + (10 if bar_width >= 0 else -10),
                y_pos + bar_height // 2,
                text=f"{time_variance:+.1f}%",
                anchor=tk.W if bar_width >= 0 else tk.E,
                font=("TkDefaultFont", 8),
                fill="#000000"
            )

    def _update_productivity_view(self):
        """Update the productivity view with visualization."""
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visualization

        # Clear the canvas
        self.productivity_canvas.delete("all")

        if not self.report_data or len(self.report_data) == 0:
            self.productivity_canvas.create_text(
                200, 100,
                text="No project data available for productivity visualization.",
                fill="#666666",
                font=("TkDefaultFont", 10)
            )
            return

        # Get canvas dimensions
        canvas_width = self.productivity_canvas.winfo_width() or 600
        canvas_height = self.productivity_canvas.winfo_height() or 400

        # Set chart margins
        margin_left = 60
        margin_right = 30
        margin_top = 40
        margin_bottom = 60

        # Calculate chart area
        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        # Draw title
        self.productivity_canvas.create_text(
            canvas_width // 2, margin_top // 2,
            text="Project Productivity Analysis",
            font=("TkDefaultFont", 12, "bold")
        )

        # Group projects by type
        project_types = {}
        for project in self.report_data:
            p_type = project.get("type", "Unknown")
            if p_type not in project_types:
                project_types[p_type] = {
                    "count": 0,
                    "productivity": 0,
                    "labor_hours": 0,
                    "material_efficiency": 0
                }

            project_types[p_type]["count"] += 1
            project_types[p_type]["productivity"] += project.get("productivity", 0)
            project_types[p_type]["labor_hours"] += project.get("labor_hours", 0)
            project_types[p_type]["material_efficiency"] += project.get("material_efficiency", 0)

        # Calculate averages
        for p_type in project_types:
            count = project_types[p_type]["count"]
            if count > 0:
                project_types[p_type]["avg_productivity"] = project_types[p_type]["productivity"] / count
                project_types[p_type]["avg_material_efficiency"] = project_types[p_type]["material_efficiency"] / count
                project_types[p_type]["avg_labor_hours"] = project_types[p_type]["labor_hours"] / count

        # Create a bar chart of productivity by project type
        bar_width = min(50, chart_width / (len(project_types) + 1))
        spacing = (chart_width - bar_width * len(project_types)) / (len(project_types) + 1)

        # Find max productivity for scaling
        max_productivity = max((data["avg_productivity"] for data in project_types.values()), default=100)

        # Sort types by productivity
        sorted_types = sorted(project_types.items(),
                              key=lambda x: x[1]["avg_productivity"],
                              reverse=True)

        # Draw bars
        for i, (p_type, data) in enumerate(sorted_types):
            # Calculate bar dimensions
            x_pos = margin_left + spacing * (i + 1) + bar_width * i

            productivity = data["avg_productivity"]
            bar_height = (productivity / max_productivity) * chart_height if max_productivity > 0 else 0

            # Draw the bar
            self.productivity_canvas.create_rectangle(
                x_pos, canvas_height - margin_bottom - bar_height,
                       x_pos + bar_width, canvas_height - margin_bottom,
                fill="#2196F3",  # Blue
                outline="#000000"
            )

            # Add type label
            self.productivity_canvas.create_text(
                x_pos + bar_width // 2, canvas_height - margin_bottom + 15,
                text=p_type,
                font=("TkDefaultFont", 8),
                angle=45,
                anchor=tk.NW
            )

            # Add productivity value
            self.productivity_canvas.create_text(
                x_pos + bar_width // 2, canvas_height - margin_bottom - bar_height - 10,
                text=f"{productivity:.1f}%",
                font=("TkDefaultFont", 8)
            )

            # Add count label
            self.productivity_canvas.create_text(
                x_pos + bar_width // 2, canvas_height - margin_bottom - bar_height - 25,
                text=f"({data['count']} projects)",
                font=("TkDefaultFont", 7)
            )

        # Draw axes
        # X-axis
        self.productivity_canvas.create_line(
            margin_left, canvas_height - margin_bottom,
                         canvas_width - margin_right, canvas_height - margin_bottom,
            width=1
        )

        # Y-axis
        self.productivity_canvas.create_line(
            margin_left, margin_top,
            margin_left, canvas_height - margin_bottom,
            width=1
        )

        # Y-axis labels
        for i in range(6):
            y_value = max_productivity * i / 5
            y_pos = canvas_height - margin_bottom - (i * chart_height / 5)

            # Grid line
            self.productivity_canvas.create_line(
                margin_left, y_pos,
                canvas_width - margin_right, y_pos,
                dash=(2, 4),
                fill="#CCCCCC"
            )

            # Label
            self.productivity_canvas.create_text(
                margin_left - 10, y_pos,
                text=f"{y_value:.0f}%",
                anchor=tk.E,
                font=("TkDefaultFont", 8)
            )

    def _update_summary_section(self):
        """Update the summary section with aggregated metrics."""
        if not self.report_data:
            return

        # Calculate summary metrics
        total_projects = len(self.report_data)

        # Average efficiency metrics
        avg_efficiency = sum(
            p.get("efficiency_score", 0) for p in self.report_data) / total_projects if total_projects > 0 else 0
        avg_time_variance = sum(
            p.get("time_variance", 0) for p in self.report_data) / total_projects if total_projects > 0 else 0
        avg_material_efficiency = sum(
            p.get("material_efficiency", 0) for p in self.report_data) / total_projects if total_projects > 0 else 0

        # Count on-time projects (variance <= 0)
        on_time_count = sum(1 for p in self.report_data if p.get("time_variance", 0) <= 0)
        on_time_percentage = (on_time_count / total_projects) * 100 if total_projects > 0 else 0

        # Find most efficient project
        most_efficient = max(self.report_data,
                             key=lambda x: x.get("efficiency_score", 0),
                             default=None)
        most_efficient_name = most_efficient.get("name", "None") if most_efficient else "None"

        # Update summary labels
        self.total_projects_label.config(text=str(total_projects))
        self.avg_efficiency_label.config(text=f"{avg_efficiency:.1f}%")
        self.on_time_label.config(text=f"{on_time_count} ({on_time_percentage:.1f}%)")
        self.avg_variance_label.config(text=f"{avg_time_variance:+.1f}%")
        self.avg_material_label.config(text=f"{avg_material_efficiency:.1f}%")
        self.most_efficient_label.config(text=most_efficient_name)

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")

        try:
            # Create summary data for the report
            total_projects = len(self.report_data)
            avg_efficiency = sum(
                p.get("efficiency_score", 0) for p in self.report_data) / total_projects if total_projects > 0 else 0
            on_time_count = sum(1 for p in self.report_data if p.get("time_variance", 0) <= 0)

            summary_data = {
                "Total Projects": str(total_projects),
                "Average Efficiency": f"{avg_efficiency:.1f}%",
                "On-Time Projects": f"{on_time_count} ({(on_time_count / total_projects) * 100:.1f}% if total_projects > 0 else 0:.1f}%)",
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
            total_projects = len(self.report_data)
            avg_efficiency = sum(
                p.get("efficiency_score", 0) for p in self.report_data) / total_projects if total_projects > 0 else 0
            on_time_count = sum(1 for p in self.report_data if p.get("time_variance", 0) <= 0)

            summary_data = {
                "Total Projects": str(total_projects),
                "Average Efficiency": f"{avg_efficiency:.1f}%",
                "On-Time Projects": f"{on_time_count} ({(on_time_count / total_projects) * 100:.1f}% if total_projects > 0 else 0:.1f}%)",
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

    def _get_sample_efficiency_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample project efficiency data for demonstration purposes.

        In a real implementation, this would fetch data from the project service.

        Args:
            criteria: Filter criteria

        Returns:
            List of project records with efficiency metrics
        """
        sample_data = []

        # Get date range from criteria
        start_date = criteria.get("start_date", datetime.now() - timedelta(days=180))
        end_date = criteria.get("end_date", datetime.now())

        # Project types from enum
        project_types = [t.value for t in ProjectType
                         if t.value not in ["sample", "prototype"]]  # Filter out non-client types

        # Filter by project type if specified
        if criteria.get("project_type") and criteria["project_type"] != "All":
            project_types = [t for t in project_types if t == criteria["project_type"]]

        # Simplified statuses for this report
        statuses = ["In Progress", "Completed", "On Hold", "Cancelled"]

        # Sample project names based on type
        type_projects = {
            "wallet": ["Classic Bifold", "Slim Card Wallet", "Passport Holder", "Money Clip"],
            "briefcase": ["Executive Briefcase", "Laptop Case", "Document Holder"],
            "messenger_bag": ["Casual Messenger", "Professional Satchel", "Campus Bag"],
            "tote_bag": ["Market Tote", "Beach Bag", "Shopping Bag"],
            "backpack": ["Commuter Pack", "Adventure Backpack", "Day Hiker"],
            "belt": ["Dress Belt", "Casual Belt", "Woven Belt"],
            "watch_strap": ["Classic Watch Band", "Rally Strap", "NATO Style"],
            "notebook_cover": ["Journal Cover", "Planner Wrap", "Notebook Sleeve"],
            "phone_case": ["Phone Sleeve", "Card Wallet Case", "Folio Phone Case"],
            "key_case": ["Key Holder", "Key Organizer", "Keychain"],
            "custom": ["Custom Commission", "Bespoke Design", "Client Order"]
        }

        # Generate project data
        project_id = 1000

        for i in range(40):  # Generate 40 sample projects
            # Pick a project type
            project_type = project_types[i % len(project_types)]

            # Pick a project name
            project_names = type_projects.get(project_type, ["Unknown Project"])
            project_name = f"{project_names[i % len(project_names)]} #{project_id}"

            # Pick a status - bias toward completed for better data
            if i % 5 == 0:
                status = "In Progress"
            elif i % 15 == 0:
                status = "On Hold"
            elif i % 20 == 0:
                status = "Cancelled"
            else:
                status = "Completed"

            # Only include completed projects if that filter is set
            if criteria.get("completed_only") and status != "Completed":
                continue

            # Generate baseline efficiency metrics with variation based on status

            # 1. Time metrics
            base_planned_days = 0

            # Different project types have different baseline durations
            if project_type in ["briefcase", "messenger_bag", "backpack"]:
                base_planned_days = 14  # Larger projects
            elif project_type in ["wallet", "key_case", "phone_case"]:
                base_planned_days = 5  # Smaller projects
            else:
                base_planned_days = 10  # Medium projects

            # Add some variation
            planned_days = base_planned_days + (i % 7)

            # Actual days based on efficiency factors
            # Projects in progress will show current days to date
            if status == "In Progress":
                # Still in progress, so show days to date
                days_factor = 0.5 + (i % 10) / 10  # 0.5-1.4
                actual_days = int(planned_days * days_factor)

                # Ensure we don't exceed planned days * 2
                actual_days = min(actual_days, planned_days * 2)

            elif status == "Completed":
                # Completed projects - vary based on efficiency
                efficiency_factor = 0.8 + (i % 40) / 100  # 0.8-1.2
                actual_days = int(planned_days * efficiency_factor)

            elif status == "On Hold":
                # On hold projects - usually delayed
                actual_days = planned_days + (i % 10)

            else:  # Cancelled
                # Cancelled projects - typically at some partial completion
                actual_days = int(planned_days * (0.3 + (i % 7) / 10))  # 0.3-1.0 of planned

            # Calculate time variance percentage
            if planned_days > 0:
                time_variance = ((actual_days - planned_days) / planned_days) * 100
            else:
                time_variance = 0

            # 2. Material efficiency metrics
            # Base efficiency varies by project type and status
            base_material_efficiency = 85  # Base value

            if status == "Completed":
                # Completed projects tend to have better efficiency
                material_variance = -5 + (i % 20)  # -5 to +14
            elif status == "In Progress":
                # In progress projects might have waste
                material_variance = -15 + (i % 20)  # -15 to +4
            elif status == "On Hold":
                # On hold projects often have waste
                material_variance = -25 + (i % 15)  # -25 to -11
            else:  # Cancelled
                # Cancelled projects typically waste materials
                material_variance = -40 + (i % 20)  # -40 to -21

            material_efficiency = base_material_efficiency + material_variance
            material_efficiency = max(30, min(100, material_efficiency))  # Cap between 30-100%

            # 3. Labor hours
            # Base labor varies by project type
            if project_type in ["briefcase", "messenger_bag", "backpack"]:
                base_labor = 20  # Larger projects
            elif project_type in ["wallet", "key_case", "phone_case"]:
                base_labor = 6  # Smaller projects
            else:
                base_labor = 12  # Medium projects

            # Adjust labor based on efficiency factors
            labor_hours = base_labor * (actual_days / planned_days) if planned_days > 0 else base_labor

            # 4. Productivity metric (output per labor hour)
            if labor_hours > 0:
                productivity = (100 / labor_hours) * base_labor
            else:
                productivity = 0

            # Cap productivity between 0-150%
            productivity = max(0, min(150, productivity))

            # 5. Overall efficiency score
            # Weight the components: time (40%), materials (30%), productivity (30%)
            time_component = max(0, 100 - abs(time_variance))

            efficiency_score = (
                    (time_component * 0.4) +
                    (material_efficiency * 0.3) +
                    (productivity * 0.3)
            )

            # Check minimum completion filter
            if criteria.get("min_completion") and material_efficiency < criteria["min_completion"]:
                continue

            # Create the project efficiency record
            project = {
                "id": project_id,
                "name": project_name,
                "type": project_type,
                "status": status,
                "planned_days": planned_days,
                "actual_days": actual_days,
                "time_variance": time_variance,
                "material_efficiency": material_efficiency,
                "labor_hours": labor_hours,
                "productivity": productivity,
                "efficiency_score": efficiency_score,
                "original_i": i  # Used for consistent sorting if needed
            }

            sample_data.append(project)
            project_id += 1

        # Sort the data if requested
        sort_field = criteria.get("sort_by", "efficiency_score")
        reverse = True  # Higher values typically better

        if sort_field == "time_variance":
            # Lower time variance is better (negative = ahead of schedule)
            reverse = False

        sample_data.sort(key=lambda x: x.get(sort_field, 0), reverse=reverse)

        return sample_data


class ProjectCostAnalysisReport(BaseReportView):
    """
    Project Cost Analysis Report.

    Provides detailed cost breakdown for projects, including material costs,
    labor costs, overhead, and profitability analysis.
    """

    REPORT_TITLE = "Project Cost Analysis Report"
    REPORT_DESCRIPTION = "Detailed breakdown of project costs and profitability"

    def __init__(self, parent):
        """
        Initialize the project cost analysis report view.

        Args:
            parent: The parent widget
        """
        # Initialize filter variables
        self.project_type_filter = tk.StringVar()
        self.min_value_filter = tk.StringVar()
        self.sort_by = tk.StringVar()

        # Initialize report columns
        self.columns = [
            {"name": "Project ID", "key": "id", "width": 80},
            {"name": "Project Name", "key": "name", "width": 180},
            {"name": "Status", "key": "status", "width": 100},
            {"name": "Material Cost", "key": "material_cost", "width": 110},
            {"name": "Labor Cost", "key": "labor_cost", "width": 100},
            {"name": "Tool Cost", "key": "tool_cost", "width": 100},
            {"name": "Overhead", "key": "overhead", "width": 100},
            {"name": "Total Cost", "key": "total_cost", "width": 100},
            {"name": "Revenue", "key": "revenue", "width": 100},
            {"name": "Profit", "key": "profit", "width": 100},
            {"name": "Margin", "key": "margin", "width": 80}
        ]

        # Call parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the project cost analysis report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the filter controls
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Project Type Filter
        type_frame = ttk.Frame(filter_container)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(type_frame, text="Project Type:").pack(side=tk.LEFT, padx=(0, 5))

        # Get project types from enum
        project_types = ["All"] + [t.value for t in ProjectType]
        type_combo = ttk.Combobox(type_frame, textvariable=self.project_type_filter,
                                  values=project_types, state="readonly", width=15)
        type_combo.pack(side=tk.LEFT)
        self.project_type_filter.set("All")  # Default value

        # Minimum Value Filter
        min_value_frame = ttk.Frame(filter_container)
        min_value_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(min_value_frame, text="Min Value ($):").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(min_value_frame, textvariable=self.min_value_filter, width=8).pack(side=tk.LEFT)

        # Sort options
        sort_frame = ttk.Frame(filter_container)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sort By:").pack(side=tk.LEFT, padx=(0, 5))

        sort_options = ["Total Cost", "Profit", "Margin", "Revenue"]
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by,
                                  values=sort_options, state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT)
        self.sort_by.set("Total Cost")  # Default value

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.project_type_filter.set("All")
        self.min_value_filter.set("")
        self.sort_by.set("Total Cost")

    def create_report_content(self, parent):
        """
        Create the main content area for the project cost analysis report.

        Args:
            parent: The parent widget
        """
        # Create notebook for tabbed views
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create cost breakdown tab
        self.cost_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cost_frame, text="Cost Breakdown")

        # Create profitability tab
        self.profit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.profit_frame, text="Profitability Analysis")

        # Create type comparison tab
        self.comparison_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.comparison_frame, text="Type Comparison")

        # Set up the cost breakdown view
        self._create_cost_view(self.cost_frame)

        # Set up the profitability view
        self._create_profitability_view(self.profit_frame)

        # Set up the type comparison view
        self._create_comparison_view(self.comparison_frame)

        # Create summary section
        self._create_summary_section(parent)

    def _create_cost_view(self, parent):
        """
        Create the cost breakdown view tab.

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

    def _create_profitability_view(self, parent):
        """
        Create the profitability analysis view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Create a frame for the profitability chart
        profit_frame = ttk.Frame(parent)
        profit_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the profit margin chart
        self.profit_canvas = tk.Canvas(
            profit_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.profit_canvas.pack(fill=tk.BOTH, expand=True)

    def _create_comparison_view(self, parent):
        """
        Create the project type comparison view tab.

        Args:
            parent: The parent widget
        """
        # In a real implementation, this would use a proper charting library
        # For now, we'll create a simple visual representation with canvas

        # Create a frame for the type comparison chart
        comparison_frame = ttk.Frame(parent)
        comparison_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a canvas for the type comparison chart
        self.comparison_canvas = tk.Canvas(
            comparison_frame,
            background="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CCCCCC"
        )
        self.comparison_canvas.pack(fill=tk.BOTH, expand=True)

    def _create_summary_section(self, parent):
        """
        Create the summary section below the tabs.

        Args:
            parent: The parent widget
        """
        # Create a summary frame
        summary_frame = ttk.LabelFrame(parent, text="Cost Analysis Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create a grid for the summary values
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Projects:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_projects_label = ttk.Label(summary_grid, text="0")
        self.total_projects_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Revenue:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.total_revenue_label = ttk.Label(summary_grid, text="$0.00")
        self.total_revenue_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Profit:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.total_profit_label = ttk.Label(summary_grid, text="$0.00")
        self.total_profit_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="Avg Material Cost:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.avg_material_label = ttk.Label(summary_grid, text="$0.00")
        self.avg_material_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Avg Labor Cost:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.avg_labor_label = ttk.Label(summary_grid, text="$0.00")
        self.avg_labor_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="Avg Margin:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.avg_margin_label = ttk.Label(summary_grid, text="0.0%")
        self.avg_margin_label.grid(row=1, column=5, sticky=tk.W)