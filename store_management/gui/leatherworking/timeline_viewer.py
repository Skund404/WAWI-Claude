# path: gui/leatherworking/timeline_viewer.py
"""
Timeline Viewer Module for Leatherworking Projects

This module provides a graphical interface for viewing and managing project timelines
in the leatherworking context. It allows users to visualize project schedules,
track progress, and manage project timelines.
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union

# Add the project root to system path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from the project modules
try:
    from di.container import DependencyContainer
    from services.project_workflow_manager import ProjectWorkflowManager, ProjectStatus

    # Import base view if available in the project structure
    try:
        from gui.base_view import BaseView
    except ImportError:
        # If BaseView is not available, we'll create a basic implementation
        BaseView = ttk.Frame
except ImportError as e:
    logging.error(f"Import error: {e}")
    # Fallbacks for testing
    DependencyContainer = object
    ProjectWorkflowManager = object
    ProjectStatus = object

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TimelineViewer(BaseView if BaseView != ttk.Frame else ttk.Frame):
    """
    A graphical timeline viewer for leatherworking projects.

    This class provides a user interface to:
    - View project schedules on a timeline
    - Filter projects by status
    - Add new projects
    - Update project dates and durations
    """

    def __init__(self, parent, controller):
        """
        Initialize the TimelineViewer.

        Args:
            parent: The parent widget
            controller: The application controller or main application instance
        """
        super().__init__(parent, controller if BaseView != ttk.Frame else None)
        self.parent = parent
        self.controller = controller

        # Initialize variables
        self.projects = []
        self.selected_project_id = None

        # Initialize UI components
        self._setup_layout()

        # Load initial data
        self.load_initial_projects()

    def _setup_layout(self):
        """Create and arrange UI elements within the frame."""
        # Configure the main frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Create a frame for input controls
        self._create_project_input()

        # Create the timeline chart
        self._create_timeline_chart()

        # Create the project list
        self._create_project_list()

    def _create_project_input(self):
        """Create the input form for adding new projects."""
        input_frame = ttk.LabelFrame(self, text="Add Project")
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Project name
        ttk.Label(input_frame, text="Project Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Start date
        ttk.Label(input_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.start_date_var = tk.StringVar()
        self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(input_frame, textvariable=self.start_date_var, width=15).grid(row=0, column=3, padx=5, pady=5,
                                                                                sticky="w")

        # Duration in days
        ttk.Label(input_frame, text="Duration (days):").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.duration_var = tk.StringVar()
        self.duration_var.set("14")
        ttk.Entry(input_frame, textvariable=self.duration_var, width=5).grid(row=0, column=5, padx=5, pady=5,
                                                                             sticky="w")

        # Add button
        ttk.Button(input_frame, text="Add Project", command=self.add_project).grid(
            row=0, column=6, padx=10, pady=5, sticky="e"
        )

    def _create_timeline_chart(self):
        """Create the visual timeline chart."""
        chart_frame = ttk.LabelFrame(self, text="Timeline Chart")
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

        # Create a canvas for drawing the timeline
        self.canvas = tk.Canvas(chart_frame, bg="white", bd=1, relief="solid")
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add scrollbars
        x_scrollbar = ttk.Scrollbar(chart_frame, orient="horizontal", command=self.canvas.xview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        y_scrollbar = ttk.Scrollbar(chart_frame, orient="vertical", command=self.canvas.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")

        self.canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

        # Bind events for zooming and scrolling
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)

    def _create_project_list(self):
        """Create the list of projects in a treeview."""
        list_frame = ttk.LabelFrame(self, text="Project List")
        list_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Create treeview
        columns = ("name", "start_date", "end_date", "duration", "status")
        self.project_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Define column headings
        self.project_tree.heading("name", text="Project Name")
        self.project_tree.heading("start_date", text="Start Date")
        self.project_tree.heading("end_date", text="End Date")
        self.project_tree.heading("duration", text="Duration (days)")
        self.project_tree.heading("status", text="Status")

        # Configure column widths
        self.project_tree.column("name", width=200)
        self.project_tree.column("start_date", width=100)
        self.project_tree.column("end_date", width=100)
        self.project_tree.column("duration", width=100)
        self.project_tree.column("status", width=100)

        # Place the treeview
        self.project_tree.pack(fill="both", expand=True)

        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.project_tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        self.project_tree.configure(yscrollcommand=tree_scrollbar.set)

        # Bind selection event
        self.project_tree.bind("<<TreeviewSelect>>", self._on_project_select)
        self.project_tree.bind("<Button-3>", self.show_context_menu)

    def add_project(self):
        """Add a new project to the timeline."""
        try:
            # Validate inputs
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a project name.")
                return

            try:
                start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
                return

            try:
                duration = int(self.duration_var.get())
                if duration <= 0:
                    raise ValueError("Duration must be positive")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid duration (positive integer).")
                return

            # Calculate end date
            end_date = start_date + timedelta(days=duration)

            # Create project object
            project = {
                "id": f"P{len(self.projects) + 1}",
                "name": name,
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration,
                "status": "Planned"
            }

            # Add to projects list
            self.projects.append(project)

            # Add to treeview
            self.project_tree.insert(
                "", "end",
                values=(
                    name,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    duration,
                    "Planned"
                ),
                tags=(project["id"],)
            )

            # Clear form fields
            self.name_var.set("")
            self.start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.duration_var.set("14")

            # Update timeline
            self.update_timeline_chart()

            logger.info(f"Added new project: {name}")

        except Exception as e:
            logger.error(f"Error adding project: {e}")
            messagebox.showerror("Error", f"Failed to add project: {str(e)}")

    def update_timeline_chart(self):
        """Update the visual timeline chart with current project data."""
        try:
            # Clear canvas
            self.canvas.delete("all")

            if not self.projects:
                self.canvas.create_text(
                    self.canvas.winfo_width() // 2,
                    self.canvas.winfo_height() // 2,
                    text="No projects to display",
                    fill="gray"
                )
                return

            # Determine date range
            all_dates = []
            for project in self.projects:
                all_dates.append(project["start_date"])
                all_dates.append(project["end_date"])

            min_date = min(all_dates)
            max_date = max(all_dates)
            total_days = (max_date - min_date).days + 14  # Add padding

            # Configure canvas for the timeline
            canvas_width = self.canvas.winfo_width()
            canvas_height = max(400, 50 * len(self.projects))
            self.canvas.configure(scrollregion=(0, 0, max(canvas_width, total_days * 20), canvas_height))

            # Draw timeline grid
            day_width = 20
            row_height = 40

            # Draw horizontal axis (time)
            for i in range(total_days):
                day_date = min_date + timedelta(days=i)
                x = i * day_width

                # Draw date markers
                self.canvas.create_line(x, 0, x, canvas_height, fill="#eee")

                if i % 7 == 0:  # Weekly markers
                    self.canvas.create_text(
                        x + day_width // 2,
                        15,
                        text=day_date.strftime("%Y-%m-%d"),
                        angle=90,
                        anchor="w"
                    )

            # Draw project bars
            for i, project in enumerate(self.projects):
                days_from_start = (project["start_date"] - min_date).days
                project_x_start = days_from_start * day_width
                project_x_end = project_x_start + (project["duration"] * day_width)

                y_center = 50 + (i * row_height)

                # Determine color based on status
                if project["status"] == "Completed":
                    color = "#4CAF50"  # Green
                elif project["status"] == "In Progress":
                    color = "#2196F3"  # Blue
                else:
                    color = "#FFC107"  # Amber/Yellow

                # Draw the project bar
                bar_id = self.canvas.create_rectangle(
                    project_x_start, y_center - 15,
                    project_x_end, y_center + 15,
                    fill=color, outline="black",
                    tags=("project", project["id"])
                )

                # Project name
                self.canvas.create_text(
                    project_x_start + 5, y_center,
                    text=project["name"],
                    anchor="w",
                    tags=("project_text", project["id"])
                )

                # Make the bar clickable
                self.canvas.tag_bind(bar_id, "<Button-1>",
                                     lambda e, p=project["id"]: self._on_project_bar_click(p))

            logger.info("Timeline chart updated")

        except Exception as e:
            logger.error(f"Error updating timeline chart: {e}")
            messagebox.showerror("Error", f"Failed to update timeline: {str(e)}")

    def delete_selected_project(self):
        """Delete the currently selected project."""
        selected_items = self.project_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a project to delete.")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected project?"):
            try:
                for item_id in selected_items:
                    # Get the project ID from the treeview item
                    item_values = self.project_tree.item(item_id, "values")
                    project_name = item_values[0]

                    # Remove from projects list
                    self.projects = [p for p in self.projects if p["name"] != project_name]

                    # Remove from treeview
                    self.project_tree.delete(item_id)

                # Update timeline
                self.update_timeline_chart()

                logger.info(
                    f"Deleted project(s): {', '.join([self.project_tree.item(i, 'values')[0] for i in selected_items])}")

            except Exception as e:
                logger.error(f"Error deleting project: {e}")
                messagebox.showerror("Error", f"Failed to delete project: {str(e)}")

    def show_context_menu(self, event):
        """Show context menu for the project list."""
        # Identify the item clicked on
        item_id = self.project_tree.identify_row(event.y)
        if item_id:
            # Select the item
            self.project_tree.selection_set(item_id)

            # Create context menu
            context_menu = tk.Menu(self, tearoff=0)

            # Add menu items
            context_menu.add_command(label="Edit", command=self._edit_selected_project)
            context_menu.add_command(label="Delete", command=self.delete_selected_project)
            context_menu.add_separator()

            # Status submenu
            status_menu = tk.Menu(context_menu, tearoff=0)
            statuses = ["Planned", "In Progress", "Completed", "On Hold", "Canceled"]
            for status in statuses:
                status_menu.add_command(
                    label=status,
                    command=lambda s=status: self._change_project_status(s)
                )
            context_menu.add_cascade(label="Change Status", menu=status_menu)

            # Display the context menu
            context_menu.post(event.x_root, event.y_root)

    def load_initial_projects(self):
        """Load initial projects data."""
        try:
            # In a real implementation, this would fetch data from your service layer
            # For now, we'll create some sample data
            sample_projects = [
                {
                    "id": "P1",
                    "name": "Leather Wallet Project",
                    "start_date": datetime.now() - timedelta(days=10),
                    "duration": 20,
                    "status": "In Progress"
                },
                {
                    "id": "P2",
                    "name": "Leather Bag Design",
                    "start_date": datetime.now() - timedelta(days=5),
                    "duration": 30,
                    "status": "Planned"
                },
                {
                    "id": "P3",
                    "name": "Belt Collection",
                    "start_date": datetime.now() - timedelta(days=30),
                    "duration": 15,
                    "status": "Completed"
                }
            ]

            # Calculate end dates and add to the list
            for project in sample_projects:
                project["end_date"] = project["start_date"] + timedelta(days=project["duration"])
                self.projects.append(project)

                # Add to treeview
                self.project_tree.insert(
                    "", "end",
                    values=(
                        project["name"],
                        project["start_date"].strftime("%Y-%m-%d"),
                        project["end_date"].strftime("%Y-%m-%d"),
                        project["duration"],
                        project["status"]
                    ),
                    tags=(project["id"],)
                )

            # Update timeline
            self.update_timeline_chart()

            logger.info("Loaded initial projects data")

        except Exception as e:
            logger.error(f"Error loading initial projects: {e}")
            messagebox.showerror("Error", f"Failed to load initial projects: {str(e)}")

    def _on_project_select(self, event):
        """Handle project selection in the treeview."""
        selected_items = self.project_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            # Get the project details
            item_values = self.project_tree.item(selected_item, "values")
            project_name = item_values[0]

            # Find the project in our list
            for project in self.projects:
                if project["name"] == project_name:
                    self.selected_project_id = project["id"]

                    # Highlight the selected project in the timeline
                    self.canvas.itemconfig("project", width=1)  # Reset all projects
                    self.canvas.itemconfig(f"project && {project['id']}", width=3)  # Highlight selected

                    logger.info(f"Selected project: {project_name}")
                    break

    def _on_project_bar_click(self, project_id):
        """Handle clicks on project bars in the timeline."""
        # Find corresponding item in treeview
        for item in self.project_tree.get_children():
            if project_id in self.project_tree.item(item, "tags"):
                self.project_tree.selection_set(item)
                self.project_tree.see(item)
                break

    def _on_canvas_click(self, event):
        """Handle clicks on the canvas."""
        # This could be used for additional interactivity like adding tasks
        pass

    def _on_canvas_resize(self, event):
        """Handle canvas resize events."""
        self.update_timeline_chart()

    def _edit_selected_project(self):
        """Open dialog to edit the selected project."""
        selected_items = self.project_tree.selection()
        if not selected_items:
            return

        selected_item = selected_items[0]
        values = self.project_tree.item(selected_item, "values")

        # Create a dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Edit Project")
        dialog.transient(self)
        dialog.grab_set()

        # Project name
        ttk.Label(dialog, text="Project Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_var = tk.StringVar(value=values[0])
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Start date
        ttk.Label(dialog, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        start_date_var = tk.StringVar(value=values[1])
        ttk.Entry(dialog, textvariable=start_date_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Duration
        ttk.Label(dialog, text="Duration (days):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        duration_var = tk.StringVar(value=values[3])
        ttk.Entry(dialog, textvariable=duration_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Status
        ttk.Label(dialog, text="Status:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        status_var = tk.StringVar(value=values[4])
        statuses = ["Planned", "In Progress", "Completed", "On Hold", "Canceled"]
        ttk.Combobox(dialog, textvariable=status_var, values=statuses).grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Save function
        def save_changes():
            try:
                # Validate inputs
                start_date = datetime.strptime(start_date_var.get(), "%Y-%m-%d")
                duration = int(duration_var.get())

                # Find and update the project
                for project in self.projects:
                    if project["name"] == values[0]:  # Match by name
                        project["name"] = name_var.get()
                        project["start_date"] = start_date
                        project["duration"] = duration
                        project["end_date"] = start_date + timedelta(days=duration)
                        project["status"] = status_var.get()

                        # Update treeview
                        self.project_tree.item(
                            selected_item,
                            values=(
                                project["name"],
                                project["start_date"].strftime("%Y-%m-%d"),
                                project["end_date"].strftime("%Y-%m-%d"),
                                project["duration"],
                                project["status"]
                            )
                        )

                        # Update timeline
                        self.update_timeline_chart()

                        break

                dialog.destroy()
                logger.info(f"Updated project: {name_var.get()}")

            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
            except Exception as e:
                logger.error(f"Error updating project: {e}")
                messagebox.showerror("Error", f"Failed to update project: {str(e)}")

        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", command=save_changes).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

    def _change_project_status(self, new_status):
        """Change the status of the selected project."""
        selected_items = self.project_tree.selection()
        if not selected_items:
            return

        try:
            for item_id in selected_items:
                values = list(self.project_tree.item(item_id, "values"))
                project_name = values[0]

                # Update status in values list (status is at index 4)
                values[4] = new_status

                # Update treeview
                self.project_tree.item(item_id, values=values)

                # Update project in our data
                for project in self.projects:
                    if project["name"] == project_name:
                        project["status"] = new_status
                        break

            # Update timeline
            self.update_timeline_chart()

            logger.info(f"Changed status to {new_status} for selected projects")

        except Exception as e:
            logger.error(f"Error changing project status: {e}")
            messagebox.showerror("Error", f"Failed to change project status: {str(e)}")


def main():
    """Main function to run the timeline viewer as a standalone application."""
    root = tk.Tk()
    root.title("Leatherworking Project Timeline Viewer")
    root.geometry("1200x700")

    # Create a mock controller
    class MockController:
        def get_service(self, service_type):
            return None

    app = TimelineViewer(root, MockController())
    app.pack(fill="both", expand=True)

    # Center the window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    main()