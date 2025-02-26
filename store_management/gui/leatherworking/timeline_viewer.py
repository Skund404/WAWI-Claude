# gui/leatherworking/timeline_viewer.py
"""
Timeline viewer module for leatherworking projects.
Helps track and visualize project deadlines and progress.
"""

import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from gui.base_view import BaseView
from services.project_workflow_manager import ProjectStatus
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


class TimelineViewer(BaseView):
    """Tool for visualizing project timelines and deadlines."""

    def __init__(self, parent, controller):
        """Initialize the TimelineViewer.

        Args:
            parent: The parent widget.
            controller: The application controller or main application instance.
        """
        super().__init__(parent, controller)
        logger.info("Initializing Timeline Viewer")

        # Initialize variables
        self.projects: List[Dict] = []
        self.selected_project_id: Optional[int] = None
        self.canvas_items: Dict[int, int] = {}

        # Setup UI
        self._setup_layout()

        # Load sample projects
        self.load_initial_projects()

        logger.info("Timeline Viewer initialized")

    def _setup_layout(self):
        """Create and arrange UI elements within the frame."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Project Timeline Viewer",
            font=("Helvetica", 16, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # Split into left and right panels
        panel_frame = ttk.Frame(main_frame)
        panel_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Project controls
        left_frame = ttk.Frame(panel_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Project input panel
        input_frame = ttk.LabelFrame(left_frame, text="Add New Project")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        self._create_project_input(input_frame)

        # Project list panel
        list_frame = ttk.LabelFrame(left_frame, text="Projects")
        list_frame.pack(fill=tk.BOTH, expand=True)
        self._create_project_list(list_frame)

        # Right panel - Timeline visualization
        right_frame = ttk.LabelFrame(panel_frame, text="Timeline")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._create_timeline_chart(right_frame)

        # Bottom panel - Status and buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # Footer status variable (for messages)
        self.footer_status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            bottom_frame,
            textvariable=self.footer_status_var,
            anchor=tk.W,
            relief="sunken",
            padding=(2, 2),
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bottom_frame, text="Export Timeline", command=self._export_timeline).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(bottom_frame, text="Reset", command=self._reset).pack(side=tk.RIGHT, padx=5)

    def _create_project_input(self, parent):
        """Create the input form for adding new projects.

        Args:
            parent: Parent widget for the input form.
        """
        # Project name
        ttk.Label(parent, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=2)

        # Project type
        ttk.Label(parent, text="Project Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.type_var = tk.StringVar(value="Wallet")
        types = ["Wallet", "Bag", "Belt", "Notebook", "Custom"]
        ttk.Combobox(parent, textvariable=self.type_var, values=types, state="readonly").grid(
            row=1, column=1, sticky=tk.EW, pady=2
        )

        # Start date
        ttk.Label(parent, text="Start Date:").grid(row=2, column=0, sticky=tk.W, pady=2)
        start_frame = ttk.Frame(parent)
        start_frame.grid(row=2, column=1, sticky=tk.EW, pady=2)
        today = datetime.now()
        self.start_year_var = tk.IntVar(value=today.year)
        self.start_month_var = tk.IntVar(value=today.month)
        self.start_day_var = tk.IntVar(value=today.day)
        ttk.Spinbox(start_frame, from_=2023, to=2030, textvariable=self.start_year_var, width=5).pack(
            side=tk.LEFT
        )
        ttk.Label(start_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(start_frame, from_=1, to=12, textvariable=self.start_month_var, width=3).pack(
            side=tk.LEFT
        )
        ttk.Label(start_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(start_frame, from_=1, to=31, textvariable=self.start_day_var, width=3).pack(
            side=tk.LEFT
        )

        # Deadline
        ttk.Label(parent, text="Deadline:").grid(row=3, column=0, sticky=tk.W, pady=2)
        deadline_frame = ttk.Frame(parent)
        deadline_frame.grid(row=3, column=1, sticky=tk.EW, pady=2)
        deadline_default = today + timedelta(days=14)  # Default: 2 weeks from today
        self.deadline_year_var = tk.IntVar(value=deadline_default.year)
        self.deadline_month_var = tk.IntVar(value=deadline_default.month)
        self.deadline_day_var = tk.IntVar(value=deadline_default.day)
        ttk.Spinbox(deadline_frame, from_=2023, to=2030, textvariable=self.deadline_year_var, width=5).pack(
            side=tk.LEFT
        )
        ttk.Label(deadline_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(deadline_frame, from_=1, to=12, textvariable=self.deadline_month_var, width=3).pack(
            side=tk.LEFT
        )
        ttk.Label(deadline_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(deadline_frame, from_=1, to=31, textvariable=self.deadline_day_var, width=3).pack(
            side=tk.LEFT
        )

        # Status (for new project)
        ttk.Label(parent, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=2)
        # Use a different variable name here to avoid conflict with footer status
        self.project_status_var = tk.StringVar(value="PLANNING")
        statuses = [status.name for status in ProjectStatus]
        ttk.Combobox(
            parent, textvariable=self.project_status_var, values=statuses, state="readonly"
        ).grid(row=4, column=1, sticky=tk.EW, pady=2)

        # Estimated hours
        ttk.Label(parent, text="Estimated Hours:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.hours_var = tk.DoubleVar(value=10.0)
        ttk.Spinbox(parent, from_=1, to=100, increment=0.5, textvariable=self.hours_var, width=5).grid(
            row=5, column=1, sticky=tk.W, pady=2
        )

        # Add button
        ttk.Button(parent, text="Add Project", command=self.add_project).grid(
            row=6, column=0, columnspan=2, pady=10
        )

        # Configure grid
        parent.columnconfigure(1, weight=1)

    def _create_project_list(self, parent):
        """Create the list of projects in a treeview.

        Args:
            parent: Parent widget for the project list.
        """
        # Columns for the treeview
        columns = ("id", "name", "type", "start_date", "deadline", "status", "hours")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        # Configure headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Project Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("start_date", text="Start Date")
        self.tree.heading("deadline", text="Deadline")
        self.tree.heading("status", text="Status")
        self.tree.heading("hours", text="Hours")
        # Configure columns width and alignment
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=150)
        self.tree.column("type", width=80)
        self.tree.column("start_date", width=80, anchor=tk.CENTER)
        self.tree.column("deadline", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("hours", width=50, anchor=tk.CENTER)
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_project_select)
        self.tree.bind("<Delete>", lambda e: self.delete_selected_project())
        self.tree.bind("<Button-3>", self.show_context_menu)

    def _create_timeline_chart(self, parent):
        """Create the visual timeline chart.

        Args:
            parent: Parent widget for the timeline chart.
        """
        self.canvas = tk.Canvas(parent, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def add_project(self):
        """Add a new project to the timeline."""
        try:
            # Get input values
            name = self.name_var.get().strip()
            project_type = self.type_var.get()
            status = self.project_status_var.get()
            hours = self.hours_var.get()

            # Validate project name
            if not name:
                raise ValueError("Project name is required")

            # Create start date
            try:
                start_date = datetime(
                    year=self.start_year_var.get(),
                    month=self.start_month_var.get(),
                    day=self.start_day_var.get(),
                )
            except ValueError as e:
                raise ValueError(f"Invalid start date: {e}")

            # Create deadline
            try:
                deadline = datetime(
                    year=self.deadline_year_var.get(),
                    month=self.deadline_month_var.get(),
                    day=self.deadline_day_var.get(),
                )
            except ValueError as e:
                raise ValueError(f"Invalid deadline: {e}")

            # Validate date order
            if deadline < start_date:
                raise ValueError("Deadline cannot be before start date")

            # Create project object with a new ID
            project_id = len(self.projects) + 1
            project = {
                "id": project_id,
                "name": name,
                "type": project_type,
                "start_date": start_date,
                "deadline": deadline,
                "status": status,
                "hours": hours,
            }
            self.projects.append(project)
            # Insert project into the treeview
            self.tree.insert("", "end", values=(
                project_id,
                name,
                project_type,
                start_date.strftime("%Y-%m-%d"),
                deadline.strftime("%Y-%m-%d"),
                status,
                hours,
            ))
            self.update_timeline_chart()
            self.name_var.set("")
            self.footer_status_var.set(f"Added project: {name}")
            logger.info(f"Added project: {name}")
        except Exception as e:
            logger.error(f"Error adding project: {str(e)}", exc_info=True)
            self.show_error("Input Error", f"Failed to add project: {str(e)}")

    def update_timeline_chart(self):
        """Update the visual timeline chart with current project data."""
        self.canvas.delete("all")
        self.canvas_items = {}

        # If no projects, show a notification message.
        if not self.projects:
            self.canvas.create_text(
                self.canvas.winfo_width() / 2,
                self.canvas.winfo_height() / 2,
                text="No projects to display",
                font=("Helvetica", 12),
                fill="#999999",
            )
            return

        # Determine date range across all projects
        min_date = min(p["start_date"] for p in self.projects)
        max_date = max(p["deadline"] for p in self.projects)
        # Ensure at least a 30-day span
        if (max_date - min_date).days < 30:
            max_date = min_date + timedelta(days=30)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        header_height = 30
        margin_left = 150
        margin_right = 20
        margin_bottom = 20
        row_height = 50
        timeline_width = canvas_width - margin_left - margin_right
        total_days = (max_date - min_date).days + 1
        pixels_per_day = timeline_width / total_days

        # Draw grid rows (for each project)
        y = header_height
        for i, project in enumerate(self.projects):
            fill = "#f5f5f5" if i % 2 == 0 else "white"
            self.canvas.create_rectangle(
                0, y, canvas_width, y + row_height, fill=fill, outline=""
            )
            self.canvas.create_text(
                10, y + row_height / 2,
                text=project["name"],
                anchor="w",
                font=("Helvetica", 10),
            )
            y += row_height

        # Draw timeline background rectangle
        self.canvas.create_rectangle(
            margin_left, header_height,
            canvas_width - margin_right, canvas_height - margin_bottom,
            fill="white", outline="#cccccc"
        )

        # Draw date grid and labels
        current_date = min_date
        day_counter = 0
        label_interval = max(1, round(100 / pixels_per_day))
        while current_date <= max_date:
            x = margin_left + (day_counter * pixels_per_day)
            self.canvas.create_line(
                x, header_height,
                x, canvas_height - margin_bottom,
                fill="#eeeeee"
            )
            if day_counter % label_interval == 0:
                self.canvas.create_text(
                    x, header_height / 2,
                    text=current_date.strftime("%b %d"),
                    font=("Helvetica", 8)
                )
            current_date += timedelta(days=1)
            day_counter += 1

        # Draw project bars in the timeline
        y = header_height
        for project in self.projects:
            days_from_start = (project["start_date"] - min_date).days
            project_duration = (project["deadline"] - project["start_date"]).days + 1
            x1 = margin_left + (days_from_start * pixels_per_day)
            x2 = x1 + (project_duration * pixels_per_day)
            y1 = y + 10
            y2 = y + row_height - 10

            # Choose color based on project status
            if project["status"] == "COMPLETED":
                color = "#4CAF50"  # Green
            elif project["status"] == "ON_HOLD":
                color = "#FFC107"  # Amber
            elif project["status"] == "CANCELLED":
                color = "#F44336"  # Red
            elif project["status"] == "PLANNING":
                color = "#2196F3"  # Blue
            else:
                color = "#9C27B0"  # Purple

            bar_id = self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline="white", width=1,
                tags=f"project_{project['id']}"
            )
            self.canvas_items[project["id"]] = bar_id
            if (x2 - x1) > 50:
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=project["name"],
                    fill="white",
                    font=("Helvetica", 9),
                    tags=f"project_{project['id']}"
                )
            # Draw progress marker for current day within the project's timespan
            today = datetime.now()
            if project["start_date"] <= today <= project["deadline"]:
                days_progress = (today - project["start_date"]).days
                progress_x = x1 + (days_progress * pixels_per_day)
                self.canvas.create_line(
                    progress_x, y1, progress_x, y2,
                    fill="white", width=2, dash=(4, 2),
                    tags=f"project_{project['id']}"
                )
            y += row_height

        # Draw a vertical line indicating today's date
        today = datetime.now()
        if min_date <= today <= max_date:
            days_from_min = (today - min_date).days
            today_x = margin_left + (days_from_min * pixels_per_day)
            self.canvas.create_line(
                today_x, header_height,
                today_x, canvas_height - margin_bottom,
                fill="#FF5722", width=2
            )
            self.canvas.create_text(
                today_x, header_height - 15,
                text="TODAY",
                fill="#FF5722",
                font=("Helvetica", 8, "bold")
            )

    def delete_selected_project(self):
        """Delete the currently selected project."""
        selected = self.tree.selection()
        if not selected:
            return
        try:
            item_id = selected[0]
            values = self.tree.item(item_id, "values")
            project_id = int(values[0])
            if not messagebox.askyesno("Confirm", f"Delete project '{values[1]}'?"):
                return
            self.tree.delete(item_id)
            self.projects = [p for p in self.projects if p["id"] != project_id]
            self.update_timeline_chart()
            logger.info(f"Deleted project ID {project_id}")
            self.footer_status_var.set(f"Deleted project ID {project_id}")
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}", exc_info=True)
            self.show_error("Error", f"Failed to delete project: {str(e)}")

    def show_context_menu(self, event):
        """Show a context menu for the project list.

        Args:
            event: The event that triggered the context menu.
        """
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        self.tree.selection_set(item_id)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit Project", command=self._edit_selected_project)
        menu.add_command(label="Delete Project", command=self.delete_selected_project)
        status_menu = tk.Menu(menu, tearoff=0)
        for status in ProjectStatus:
            status_menu.add_command(
                label=status.name,
                command=lambda s=status.name: self._change_project_status(s)
            )
        menu.add_cascade(label="Change Status", menu=status_menu)
        menu.post(event.x_root, event.y_root)

    def _on_project_select(self, event):
        """Handle projects being selected in the treeview.

        Args:
            event: The selection event.
        """
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        self.selected_project_id = int(values[0])
        # Highlight the selected project on the timeline
        for pid, cid in self.canvas_items.items():
            # Reset width for all project bars
            self.canvas.itemconfig(f"project_{pid}", width=1)
        if self.selected_project_id in self.canvas_items:
            self.canvas.itemconfig(f"project_{self.selected_project_id}", width=2)

    def _on_canvas_click(self, event):
        """Handle click events on the timeline canvas.

        Args:
            event: The click event.
        """
        item_ids = self.canvas.find_withtag("current")
        if not item_ids:
            return
        for item_id in item_ids:
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("project_"):
                    project_id = int(tag.split("_")[1])
                    self._on_project_bar_click(project_id)
                    return

    def _on_project_bar_click(self, project_id):
        """When a project bar is clicked, select it in the treeview.

        Args:
            project_id: The ID of the clicked project.
        """
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            if int(values[0]) == project_id:
                self.tree.selection_set(item_id)
                self.tree.see(item_id)
                break

    def _on_canvas_resize(self, event):
        """Redraw the timeline when the canvas is resized.

        Args:
            event: The resize event.
        """
        self.update_timeline_chart()

    def _change_project_status(self, new_status):
        """Change the status of the selected project.

        Args:
            new_status: The new status to set.
        """
        if self.selected_project_id is None:
            return
        project = next((p for p in self.projects if p["id"] == self.selected_project_id), None)
        if not project:
            return
        project["status"] = new_status
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            if int(values[0]) == project["id"]:
                new_values = list(values)
                new_values[5] = new_status
                self.tree.item(item_id, values=tuple(new_values))
                break
        self.update_timeline_chart()
        logger.info(f"Changed project {project['id']} status to {new_status}")
        self.footer_status_var.set(f"Changed project status to {new_status}")

    def _edit_selected_project(self):
        """Open a dialog to edit the selected project."""
        if self.selected_project_id is None:
            return
        project = next((p for p in self.projects if p["id"] == self.selected_project_id), None)
        if not project:
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Project: {project['name']}")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Project name
        ttk.Label(frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        name_var = tk.StringVar(value=project["name"])
        ttk.Entry(frame, textvariable=name_var).grid(row=0, column=1, sticky=tk.EW, pady=2)

        # Project type
        ttk.Label(frame, text="Project Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        type_var = tk.StringVar(value=project["type"])
        types = ["Wallet", "Bag", "Belt", "Notebook", "Custom"]
        ttk.Combobox(frame, textvariable=type_var, values=types, state="readonly").grid(
            row=1, column=1, sticky=tk.EW, pady=2
        )

        # Start date
        ttk.Label(frame, text="Start Date:").grid(row=2, column=0, sticky=tk.W, pady=2)
        start_frame = ttk.Frame(frame)
        start_frame.grid(row=2, column=1, sticky=tk.EW, pady=2)
        start_year_var = tk.IntVar(value=project["start_date"].year)
        start_month_var = tk.IntVar(value=project["start_date"].month)
        start_day_var = tk.IntVar(value=project["start_date"].day)
        ttk.Spinbox(start_frame, from_=2023, to=2030, textvariable=start_year_var, width=5).pack(
            side=tk.LEFT
        )
        ttk.Label(start_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(start_frame, from_=1, to=12, textvariable=start_month_var, width=3).pack(
            side=tk.LEFT
        )
        ttk.Label(start_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(start_frame, from_=1, to=31, textvariable=start_day_var, width=3).pack(
            side=tk.LEFT
        )

        # Deadline
        ttk.Label(frame, text="Deadline:").grid(row=3, column=0, sticky=tk.W, pady=2)
        deadline_frame = ttk.Frame(frame)
        deadline_frame.grid(row=3, column=1, sticky=tk.EW, pady=2)
        deadline_year_var = tk.IntVar(value=project["deadline"].year)
        deadline_month_var = tk.IntVar(value=project["deadline"].month)
        deadline_day_var = tk.IntVar(value=project["deadline"].day)
        ttk.Spinbox(deadline_frame, from_=2023, to=2030, textvariable=deadline_year_var, width=5).pack(
            side=tk.LEFT
        )
        ttk.Label(deadline_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(deadline_frame, from_=1, to=12, textvariable=deadline_month_var, width=3).pack(
            side=tk.LEFT
        )
        ttk.Label(deadline_frame, text="-").pack(side=tk.LEFT)
        ttk.Spinbox(deadline_frame, from_=1, to=31, textvariable=deadline_day_var, width=3).pack(
            side=tk.LEFT
        )

        # Status
        ttk.Label(frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=2)
        status_var = tk.StringVar(value=project["status"])
        statuses = [status.name for status in ProjectStatus]
        ttk.Combobox(frame, textvariable=status_var, values=statuses, state="readonly").grid(
            row=4, column=1, sticky=tk.EW, pady=2
        )

        # Estimated hours
        ttk.Label(frame, text="Estimated Hours:").grid(row=5, column=0, sticky=tk.W, pady=2)
        hours_var = tk.DoubleVar(value=project["hours"])
        ttk.Spinbox(frame, from_=1, to=100, increment=0.5, textvariable=hours_var, width=5).grid(
            row=5, column=1, sticky=tk.W, pady=2
        )

        # Save changes button
        def save_changes():
            try:
                new_name = name_var.get().strip()
                new_type = type_var.get()
                new_status = status_var.get()
                new_hours = hours_var.get()
                if not new_name:
                    raise ValueError("Project name is required")
                new_start_date = datetime(
                    year=start_year_var.get(),
                    month=start_month_var.get(),
                    day=start_day_var.get(),
                )
                new_deadline = datetime(
                    year=deadline_year_var.get(),
                    month=deadline_month_var.get(),
                    day=deadline_day_var.get(),
                )
                if new_deadline < new_start_date:
                    raise ValueError("Deadline cannot be before start date")
                # Update the project dictionary
                project["name"] = new_name
                project["type"] = new_type
                project["start_date"] = new_start_date
                project["deadline"] = new_deadline
                project["status"] = new_status
                project["hours"] = new_hours
                # Update treeview row
                for item_id in self.tree.get_children():
                    values = self.tree.item(item_id, "values")
                    if int(values[0]) == project["id"]:
                        self.tree.item(item_id, values=(
                            project["id"],
                            new_name,
                            new_type,
                            new_start_date.strftime("%Y-%m-%d"),
                            new_deadline.strftime("%Y-%m-%d"),
                            new_status,
                            new_hours,
                        ))
                        break
                self.update_timeline_chart()
                dialog.destroy()
                self.footer_status_var.set(f"Updated project: {new_name}")
                logger.info(f"Updated project {project['id']}: {new_name}")
            except Exception as e:
                logger.error(f"Error updating project: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Failed to update project: {str(e)}", parent=dialog)

        ttk.Button(frame, text="Save Changes", command=save_changes).grid(
            row=6, column=0, columnspan=2, pady=10
        )
        frame.columnconfigure(1, weight=1)

    def load_initial_projects(self):
        """Load initial projects data."""
        sample_projects = [
            {
                "name": "Bifold Wallet",
                "type": "Wallet",
                "start_date": datetime.now() - timedelta(days=5),
                "deadline": datetime.now() + timedelta(days=10),
                "status": "PLANNING",
                "hours": 8.0,
            },
            {
                "name": "Laptop Sleeve",
                "type": "Custom",
                "start_date": datetime.now() - timedelta(days=15),
                "deadline": datetime.now() + timedelta(days=5),
                "status": "CUTTING",
                "hours": 12.0,
            },
            {
                "name": "Messenger Bag",
                "type": "Bag",
                "start_date": datetime.now() + timedelta(days=8),
                "deadline": datetime.now() + timedelta(days=30),
                "status": "PLANNING",
                "hours": 25.0,
            },
            {
                "name": "Custom Belt",
                "type": "Belt",
                "start_date": datetime.now() - timedelta(days=20),
                "deadline": datetime.now() - timedelta(days=5),
                "status": "COMPLETED",
                "hours": 6.0,
            },
            {
                "name": "Journal Cover",
                "type": "Notebook",
                "start_date": datetime.now() - timedelta(days=10),
                "deadline": datetime.now() - timedelta(days=2),
                "status": "QUALITY_CHECK",
                "hours": 10.0,
            },
        ]

        # Add sample projects with generated IDs
        for i, project_data in enumerate(sample_projects):
            project_id = i + 1
            project = {"id": project_id, **project_data}
            self.projects.append(project)
            self.tree.insert("", "end", values=(
                project_id,
                project["name"],
                project["type"],
                project["start_date"].strftime("%Y-%m-%d"),
                project["deadline"].strftime("%Y-%m-%d"),
                project["status"],
                project["hours"],
            ))
        # Redraw timeline after projects load
        self.after(100, self.update_timeline_chart)
        logger.info("Loaded initial projects")

    def _export_timeline(self):
        """Export the current timeline as an image."""
        messagebox.showinfo("Export", "Timeline export would be implemented here")
        logger.info("Timeline export requested")

    def _reset(self):
        """Reset the timeline to default state."""
        if not messagebox.askyesno("Reset", "Clear all projects and reset the timeline?"):
            return
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        self.projects.clear()
        self.selected_project_id = None
        self.update_timeline_chart()
        logger.info("Reset timeline")
        self.footer_status_var.set("Timeline reset")

    def show_error(self, title: str, message: str):
        """Show an error message dialog.

        Args:
            title: The title of the error message.
            message: The error message content.
        """
        messagebox.showerror(title, message, parent=self)


class MockController:
    """Mock controller for standalone testing."""

    def get_service(self, service_type):
        return None


def main():
    """Main function to run the timeline viewer as a standalone application."""
    root = tk.Tk()
    root.title("Project Timeline Viewer")
    root.geometry("1000x600")
    app = MockController()
    viewer = TimelineViewer(root, app)
    viewer.pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
