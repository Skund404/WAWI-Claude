# gui/views/projects/project_timeline_dialog.py
"""
Project timeline dialog for visualizing project timelines.

This dialog provides a visual representation of project timelines,
allowing users to see project schedules and progress at a glance.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import ProjectStatus, ProjectType
from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS, get_status_style
from gui.utils.service_access import get_service


class ProjectTimelineDialog(BaseDialog):
    """
    Dialog for visualizing project timelines.

    This dialog shows projects on a timeline view to help with
    workload management and scheduling.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the project timeline dialog.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                projects: List of projects to display (optional)
                start_date: Start date for timeline (optional)
                end_date: End date for timeline (optional)
        """
        self.logger = logging.getLogger(__name__)

        # Set default dimensions for the timeline view
        width = kwargs.pop('width', 800)
        height = kwargs.pop('height', 600)

        # Initialize with projects if provided, otherwise will load from service
        self.projects = kwargs.pop('projects', None)
        self.start_date = kwargs.pop('start_date', None)
        self.end_date = kwargs.pop('end_date', None)
        self.filter_status = kwargs.pop('filter_status', None)
        self.filter_type = kwargs.pop('filter_type', None)

        # Zoom level for timeline (1.0 is normal)
        self.zoom_level = 1.0

        # Canvas coordinates and settings
        self.timeline_width = 0
        self.row_height = 40
        self.header_height = 60
        self.left_margin = 200
        self.date_interval = 'month'  # 'day', 'week', 'month'

        # Initialize services
        self.project_service = get_service("project_service")

        # Call parent constructor
        super().__init__(parent, title="Project Timeline", width=width, height=height)

    def create_layout(self):
        """Create the dialog layout."""
        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create timeline controls
        self.create_controls(main_frame)

        # Create timeline canvas
        self.create_timeline_canvas(main_frame)

        # Load timeline data
        self.load_timeline_data()

        # Draw the timeline
        self.draw_timeline()

    def create_controls(self, parent):
        """Create timeline controls.

        Args:
            parent: The parent widget
        """
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Date range selector
        date_frame = ttk.LabelFrame(controls_frame, text="Timeline Range")
        date_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(date_frame, text="Start:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_var = tk.StringVar()
        if self.start_date:
            self.start_date_var.set(self.start_date.strftime("%Y-%m-%d"))
        else:
            # Default to current month start
            today = datetime.datetime.now()
            self.start_date = datetime.datetime(today.year, today.month, 1)
            self.start_date_var.set(self.start_date.strftime("%Y-%m-%d"))

        start_date_entry = ttk.Entry(date_frame, textvariable=self.start_date_var, width=12)
        start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(
            date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.start_date_var)
        ).grid(row=0, column=2, padx=(0, 5), pady=5)

        ttk.Label(date_frame, text="End:").grid(row=0, column=3, padx=5, pady=5)
        self.end_date_var = tk.StringVar()
        if self.end_date:
            self.end_date_var.set(self.end_date.strftime("%Y-%m-%d"))
        else:
            # Default to 3 months from start
            self.end_date = self.start_date + datetime.timedelta(days=90)
            self.end_date_var.set(self.end_date.strftime("%Y-%m-%d"))

        end_date_entry = ttk.Entry(date_frame, textvariable=self.end_date_var, width=12)
        end_date_entry.grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(
            date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.end_date_var)
        ).grid(row=0, column=5, padx=(0, 5), pady=5)

        ttk.Button(
            date_frame,
            text="Apply",
            command=self.on_date_range_change
        ).grid(row=0, column=6, padx=5, pady=5)

        # Interval selector
        interval_frame = ttk.LabelFrame(controls_frame, text="Interval")
        interval_frame.pack(side=tk.LEFT, padx=5)

        self.interval_var = tk.StringVar(value="Month")
        ttk.Radiobutton(
            interval_frame,
            text="Day",
            variable=self.interval_var,
            value="Day",
            command=self.on_interval_change
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Radiobutton(
            interval_frame,
            text="Week",
            variable=self.interval_var,
            value="Week",
            command=self.on_interval_change
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Radiobutton(
            interval_frame,
            text="Month",
            variable=self.interval_var,
            value="Month",
            command=self.on_interval_change
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Zoom controls
        zoom_frame = ttk.LabelFrame(controls_frame, text="Zoom")
        zoom_frame.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            zoom_frame,
            text="-",
            width=2,
            command=self.zoom_out
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.zoom_label = ttk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            zoom_frame,
            text="+",
            width=2,
            command=self.zoom_in
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Filter controls
        filter_frame = ttk.LabelFrame(controls_frame, text="Filters")
        filter_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, padx=5, pady=5)
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var, width=15, state="readonly")
        status_values = ["All"] + [s.name for s in ProjectStatus]
        status_combo["values"] = status_values
        status_combo.grid(row=0, column=1, padx=5, pady=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.on_filter_change())

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=2, padx=5, pady=5)
        self.type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_frame, textvariable=self.type_var, width=15, state="readonly")
        type_values = ["All"] + [t.name for t in ProjectType]
        type_combo["values"] = type_values
        type_combo.grid(row=0, column=3, padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.on_filter_change())

        # Export button
        export_frame = ttk.Frame(controls_frame)
        export_frame.pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            export_frame,
            text="Export PDF",
            command=self.on_export_pdf
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            export_frame,
            text="Print",
            command=self.on_print_timeline
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def create_timeline_canvas(self, parent):
        """Create the timeline canvas.

        Args:
            parent: The parent widget
        """
        # Create canvas frame with scrollbars
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create vertical scrollbar
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='white',
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        # Enable mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", lambda e: self.on_mouse_wheel(e, 1))  # Linux
        self.canvas.bind("<Button-5>", lambda e: self.on_mouse_wheel(e, -1))  # Linux

        # Bind canvas click event
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Tooltip data
        self.tooltip = None
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # Create tooltip
        self.tooltip_frame = ttk.Frame(self.canvas)
        self.tooltip_text = ttk.Label(
            self.tooltip_frame,
            background=COLORS["info_light"],
            justify=tk.LEFT,
            wraplength=300
        )
        self.tooltip_text.pack(padx=5, pady=5)
        self.tooltip_frame.place_forget()

    def load_timeline_data(self):
        """Load timeline data from the project service."""
        if self.projects is None:
            try:
                # Load projects from service with date range and filters
                filters = {}

                if self.start_date:
                    filters['start_date'] = self.start_date
                if self.end_date:
                    filters['end_date'] = self.end_date
                if self.filter_status and self.filter_status != "All":
                    filters['status'] = self.filter_status
                if self.filter_type and self.filter_type != "All":
                    filters['type'] = self.filter_type

                self.projects = self.project_service.search_projects(filters=filters)

                # Sort projects by start date
                self.projects = sorted(
                    self.projects,
                    key=lambda p: p.start_date if hasattr(p, 'start_date') and p.start_date else datetime.datetime.max
                )

            except Exception as e:
                self.logger.error(f"Error loading projects: {e}")
                messagebox.showerror("Error", f"Failed to load projects: {str(e)}")
                self.projects = []

    def draw_timeline(self):
        """Draw the timeline on the canvas."""
        # Clear canvas
        self.canvas.delete("all")

        # Calculate timeline dimensions
        self.calculate_timeline_dimensions()

        # Draw date headers
        self.draw_date_header()

        # Draw projects
        self.draw_projects()

        # Configure canvas scrolling
        self.canvas.config(
            scrollregion=(0, 0, self.timeline_width + self.left_margin + 20,
                          (len(self.projects) + 1) * self.row_height + self.header_height + 20)
        )

    def calculate_timeline_dimensions(self):
        """Calculate timeline dimensions based on date range and zoom level."""
        if not self.start_date or not self.end_date:
            return

        date_range = (self.end_date - self.start_date).days

        # Calculate timeline width based on date range and zoom level
        if self.date_interval == 'day':
            self.timeline_width = date_range * 30 * self.zoom_level
        elif self.date_interval == 'week':
            self.timeline_width = (date_range / 7) * 100 * self.zoom_level
        else:  # month
            # Calculate number of months
            months = (self.end_date.year - self.start_date.year) * 12 + (
                        self.end_date.month - self.start_date.month) + 1
            self.timeline_width = months * 120 * self.zoom_level

    def draw_date_header(self):
        """Draw the date header with time intervals."""
        # Draw header background
        self.canvas.create_rectangle(
            0, 0, self.timeline_width + self.left_margin, self.header_height,
            fill=COLORS["background_light"], outline=""
        )

        # Draw vertical divider
        self.canvas.create_line(
            self.left_margin, 0, self.left_margin, (len(self.projects) + 1) * self.row_height + self.header_height,
            fill=COLORS["border"]
        )

        # Draw "Project" header
        self.canvas.create_text(
            self.left_margin / 2, self.header_height / 2,
            text="Project", font=("Helvetica", 10, "bold")
        )

        # Draw date intervals
        if self.date_interval == 'day':
            self.draw_daily_intervals()
        elif self.date_interval == 'week':
            self.draw_weekly_intervals()
        else:  # month
            self.draw_monthly_intervals()

    def draw_daily_intervals(self):
        """Draw daily interval markers on the timeline."""
        current_date = self.start_date
        x_pos = self.left_margin
        day_width = 30 * self.zoom_level

        while current_date <= self.end_date:
            # Draw day marker
            self.canvas.create_line(
                x_pos, self.header_height, x_pos, (len(self.projects) + 1) * self.row_height + self.header_height,
                fill=COLORS["border_light"], dash=(1, 2)
            )

            # Draw date text - show day of month and day name
            day_text = current_date.strftime("%d\n%a")
            self.canvas.create_text(
                x_pos + day_width / 2, self.header_height / 2,
                text=day_text, font=("Helvetica", 8)
            )

            # Draw month name at the first day of month
            if current_date.day == 1:
                month_text = current_date.strftime("%B %Y")
                self.canvas.create_text(
                    x_pos + day_width / 2, 15,
                    text=month_text, font=("Helvetica", 9, "bold")
                )

                # Draw stronger vertical line for month start
                self.canvas.create_line(
                    x_pos, 0, x_pos, (len(self.projects) + 1) * self.row_height + self.header_height,
                    fill=COLORS["border"]
                )

            # Move to next day
            current_date += datetime.timedelta(days=1)
            x_pos += day_width

    def draw_weekly_intervals(self):
        """Draw weekly interval markers on the timeline."""
        current_date = self.start_date
        # Adjust to start of week (Monday)
        days_to_subtract = current_date.weekday()
        if days_to_subtract > 0:
            current_date -= datetime.timedelta(days=days_to_subtract)

        x_pos = self.left_margin
        week_width = 100 * self.zoom_level

        while current_date <= self.end_date:
            # Draw week marker
            self.canvas.create_line(
                x_pos, self.header_height, x_pos, (len(self.projects) + 1) * self.row_height + self.header_height,
                fill=COLORS["border_light"], dash=(1, 2)
            )

            # Draw week text - show week number
            week_text = f"Week {current_date.isocalendar()[1]}"
            self.canvas.create_text(
                x_pos + week_width / 2, self.header_height / 2,
                text=week_text, font=("Helvetica", 8)
            )

            # Draw month name at the first week of month
            if current_date.day <= 7:
                month_text = current_date.strftime("%B %Y")
                self.canvas.create_text(
                    x_pos + week_width / 2, 15,
                    text=month_text, font=("Helvetica", 9, "bold")
                )

                # Draw stronger vertical line for month start
                if current_date.day == 1:
                    self.canvas.create_line(
                        x_pos, 0, x_pos, (len(self.projects) + 1) * self.row_height + self.header_height,
                        fill=COLORS["border"]
                    )

            # Move to next week
            current_date += datetime.timedelta(days=7)
            x_pos += week_width

    def draw_monthly_intervals(self):
        """Draw monthly interval markers on the timeline."""
        current_date = datetime.datetime(self.start_date.year, self.start_date.month, 1)
        x_pos = self.left_margin
        month_width = 120 * self.zoom_level

        while current_date <= self.end_date:
            # Draw month marker
            self.canvas.create_line(
                x_pos, self.header_height, x_pos, (len(self.projects) + 1) * self.row_height + self.header_height,
                fill=COLORS["border"]
            )

            # Draw month text
            month_text = current_date.strftime("%B %Y")
            self.canvas.create_text(
                x_pos + month_width / 2, self.header_height / 2,
                text=month_text, font=("Helvetica", 10)
            )

            # Draw year marker for January
            if current_date.month == 1:
                year_text = current_date.strftime("%Y")
                self.canvas.create_text(
                    x_pos + month_width / 2, 15,
                    text=year_text, font=("Helvetica", 12, "bold")
                )

            # Move to next month
            if current_date.month == 12:
                current_date = datetime.datetime(current_date.year + 1, 1, 1)
            else:
                current_date = datetime.datetime(current_date.year, current_date.month + 1, 1)

            x_pos += month_width

    def draw_projects(self):
        """Draw projects on the timeline."""
        for i, project in enumerate(self.projects):
            # Calculate y position
            y_pos = self.header_height + i * self.row_height

            # Draw row background (alternating colors)
            bg_color = COLORS["background_light"] if i % 2 == 0 else "white"
            self.canvas.create_rectangle(
                0, y_pos, self.timeline_width + self.left_margin, y_pos + self.row_height,
                fill=bg_color, outline=""
            )

            # Draw project name in left column
            project_name = project.name if hasattr(project, 'name') else f"Project #{project.id}"
            self.canvas.create_text(
                10, y_pos + self.row_height / 2,
                text=project_name, anchor=tk.W,
                font=("Helvetica", 9)
            )

            # Draw project bar
            self.draw_project_bar(project, y_pos)

    def draw_project_bar(self, project, y_pos):
        """Draw a project timeline bar.

        Args:
            project: The project to draw
            y_pos: The y position of the project row
        """
        # Skip if project doesn't have dates
        if not hasattr(project, 'start_date') or not project.start_date or \
                not hasattr(project, 'end_date') or not project.end_date:
            return

        # Calculate bar position
        bar_start = self.date_to_x(project.start_date)

        # If project end date is None, use today's date
        if project.end_date:
            bar_end = self.date_to_x(project.end_date)
        else:
            bar_end = self.date_to_x(datetime.datetime.now())

        # Minimum width for visibility
        if bar_end - bar_start < 5:
            bar_end = bar_start + 5

        # Get status color
        if hasattr(project, 'status') and project.status:
            status_style = get_status_style(project.status.value)
            bar_color = status_style.get('bg', COLORS.get('primary'))
        else:
            bar_color = COLORS.get('primary')

        # Draw project bar
        bar_height = self.row_height * 0.6
        bar_y = y_pos + (self.row_height - bar_height) / 2

        # Create project bar with rounded corners
        bar_id = self.canvas.create_rectangle(
            bar_start, bar_y, bar_end, bar_y + bar_height,
            fill=bar_color, outline=COLORS.get('border'),
            width=1, tags=(f"project_{project.id}",)
        )

        # Draw project status indicator
        if hasattr(project, 'status') and project.status:
            status_text = project.status.value.replace("_", " ").title()
            self.canvas.create_text(
                bar_start + 5, bar_y + bar_height / 2,
                text=status_text,
                fill="white", anchor=tk.W,
                font=("Helvetica", 8),
                tags=(f"project_{project.id}",)
            )

        # Draw progress indicator if we have start_date, end_date, and today is between them
        now = datetime.datetime.now()
        if project.start_date and project.end_date and project.start_date <= now <= project.end_date:
            # Calculate progress percentage
            total_days = (project.end_date - project.start_date).days
            days_passed = (now - project.start_date).days
            if total_days > 0:
                progress = min(100, days_passed / total_days * 100)

                # Draw progress line
                progress_x = bar_start + (bar_end - bar_start) * (progress / 100)
                self.canvas.create_line(
                    progress_x, bar_y, progress_x, bar_y + bar_height,
                    fill="white", width=2, dash=(4, 2),
                    tags=(f"project_{project.id}",)
                )

    def date_to_x(self, date):
        """Convert a date to x coordinate on the timeline.

        Args:
            date: The date to convert

        Returns:
            X coordinate for the date
        """
        if not date or not self.start_date:
            return self.left_margin

        # Calculate days from start date
        days_from_start = (date - self.start_date).days

        if self.date_interval == 'day':
            return self.left_margin + days_from_start * 30 * self.zoom_level
        elif self.date_interval == 'week':
            return self.left_margin + (days_from_start / 7) * 100 * self.zoom_level
        else:  # month
            # Calculate months between dates
            months = (date.year - self.start_date.year) * 12 + (date.month - self.start_date.month)

            # Add partial month
            if date.day > self.start_date.day:
                day_ratio = (date.day - self.start_date.day) / 30.0
                months += day_ratio
            elif date.day < self.start_date.day:
                day_ratio = (self.start_date.day - date.day) / 30.0
                months -= day_ratio

            return self.left_margin + months * 120 * self.zoom_level

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create a simple date picker dialog
        date_dialog = tk.Toplevel(self.window)
        date_dialog.title("Select Date")
        date_dialog.transient(self.window)
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

    def on_date_range_change(self):
        """Handle date range change."""
        try:
            # Parse date strings
            if self.start_date_var.get():
                self.start_date = datetime.datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")

            if self.end_date_var.get():
                self.end_date = datetime.datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")

            # Validate dates
            if self.start_date and self.end_date and self.start_date > self.end_date:
                messagebox.showwarning("Invalid Date Range", "Start date must be before end date.")
                return

            # Reload data and redraw timeline
            self.load_timeline_data()
            self.draw_timeline()

        except ValueError:
            messagebox.showwarning("Invalid Date", "Please enter dates in YYYY-MM-DD format.")

    def on_interval_change(self):
        """Handle interval change."""
        interval = self.interval_var.get().lower()
        if interval in ['day', 'week', 'month']:
            self.date_interval = interval
            self.draw_timeline()

    def on_filter_change(self):
        """Handle filter change."""
        # Update filter values
        self.filter_status = None if self.status_var.get() == "All" else self.status_var.get().upper()
        self.filter_type = None if self.type_var.get() == "All" else self.type_var.get().upper()

        # Reload data and redraw timeline
        self.projects = None  # Force reload
        self.load_timeline_data()
        self.draw_timeline()

    def zoom_in(self):
        """Zoom in the timeline."""
        if self.zoom_level < 3.0:
            self.zoom_level += 0.2
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            self.draw_timeline()

    def zoom_out(self):
        """Zoom out the timeline."""
        if self.zoom_level > 0.4:
            self.zoom_level -= 0.2
            self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
            self.draw_timeline()

    def on_mouse_wheel(self, event, direction=None):
        """Handle mouse wheel for scrolling.

        Args:
            event: The mouse wheel event
            direction: Force scroll direction (for Linux)
        """
        if direction is not None:
            # Linux scroll direction
            self.canvas.yview_scroll(-direction, "units")
        else:
            # Windows scroll direction
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_canvas_click(self, event):
        """Handle canvas click event.

        Args:
            event: The mouse click event
        """
        # Get the item under the cursor
        item = self.canvas.find_closest(event.x, event.y)
        if not item:
            return

        # Check if it's a project bar
        tags = self.canvas.gettags(item)
        for tag in tags:
            if tag.startswith("project_"):
                # Extract project ID
                project_id = int(tag.split("_")[1])
                self.on_project_click(project_id)
                break

    def on_mouse_move(self, event):
        """Handle mouse move event for tooltips.

        Args:
            event: The mouse move event
        """
        # Hide existing tooltip
        self.tooltip_frame.place_forget()

        # Get the item under the cursor
        item = self.canvas.find_closest(event.x, event.y)
        if not item:
            return

        # Check if it's a project bar
        tags = self.canvas.gettags(item)
        for tag in tags:
            if tag.startswith("project_"):
                # Extract project ID
                project_id = int(tag.split("_")[1])

                # Find the project data
                project = next((p for p in self.projects if p.id == project_id), None)
                if project:
                    self.show_project_tooltip(project, event.x, event.y)
                break

    def show_project_tooltip(self, project, x, y):
        """Show tooltip for a project.

        Args:
            project: The project to show tooltip for
            x: X coordinate
            y: Y coordinate
        """
        # Create tooltip text
        tooltip_content = f"Project: {project.name if hasattr(project, 'name') else f'Project #{project.id}'}\n"

        if hasattr(project, 'status') and project.status:
            tooltip_content += f"Status: {project.status.value.replace('_', ' ').title()}\n"

        if hasattr(project, 'start_date') and project.start_date:
            tooltip_content += f"Start: {project.start_date.strftime('%Y-%m-%d')}\n"

        if hasattr(project, 'end_date') and project.end_date:
            tooltip_content += f"End: {project.end_date.strftime('%Y-%m-%d')}\n"

        if hasattr(project, 'description') and project.description:
            # Truncate description if too long
            desc = project.description
            if len(desc) > 100:
                desc = desc[:97] + "..."
            tooltip_content += f"Description: {desc}"

        # Update tooltip text
        self.tooltip_text.configure(text=tooltip_content)

        # Show tooltip
        self.tooltip_frame.place(x=x + 15, y=y + 10)

    def on_project_click(self, project_id):
        """Handle project click event.

        Args:
            project_id: The ID of the clicked project
        """
        # Ask if user wants to open project details
        if messagebox.askyesno("Open Project", "Do you want to open the project details?"):
            # Close dialog and navigate to project details
            self.result = {"action": "open_project", "project_id": project_id}
            self.close()

    def on_export_pdf(self):
        """Handle export to PDF button click."""
        # This would integrate with a PDF generation library
        # For this implementation, we'll just show a message
        messagebox.showinfo("Export PDF", "Timeline would be exported to PDF.")

    def on_print_timeline(self):
        """Handle print timeline button click."""
        # This would integrate with a printing functionality
        # For this implementation, we'll just show a message
        messagebox.showinfo("Print Timeline", "Timeline would be sent to printer.")