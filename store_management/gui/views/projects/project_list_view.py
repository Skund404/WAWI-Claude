# gui/views/projects/project_list_view.py
"""
Project list view for displaying and managing projects.

This view displays a list of projects with filtering, sorting, and timeline visualization.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import ProjectStatus, ProjectType
from gui.base.base_list_view import BaseListView
from gui.theme import COLORS, get_status_style
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge
from gui.views.projects.project_details_view import ProjectDetailsView
from gui.views.projects.project_timeline_dialog import ProjectTimelineDialog


class ProjectListView(BaseListView):
    """
    View for displaying and managing projects.
    """

    def __init__(self, parent):
        """Initialize the project list view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Projects"
        self.icon = "📋"
        self.logger = logging.getLogger(__name__)

        # Initialize project service
        self.project_service = get_service("project_service")

        # Additional attributes for project filtering
        self.status_filter = tk.StringVar(value="All")
        self.type_filter = tk.StringVar(value="All")
        self.date_range = tk.StringVar(value="All")

        # Build the view
        self.build()

    def build(self):
        """Build the project list view."""
        super().build()

        # Configure treeview columns
        self.treeview.configure(
            columns=(
                "id", "name", "type", "status", "customer", "start_date",
                "end_date", "progress", "next_milestone"
            )
        )

        self.treeview.heading("id", text="ID", command=lambda: self.on_sort("id", "asc"))
        self.treeview.heading("name", text="Project Name", command=lambda: self.on_sort("name", "asc"))
        self.treeview.heading("type", text="Type", command=lambda: self.on_sort("type", "asc"))
        self.treeview.heading("status", text="Status", command=lambda: self.on_sort("status", "asc"))
        self.treeview.heading("customer", text="Customer", command=lambda: self.on_sort("customer", "asc"))
        self.treeview.heading("start_date", text="Start Date", command=lambda: self.on_sort("start_date", "asc"))
        self.treeview.heading("end_date", text="Due Date", command=lambda: self.on_sort("end_date", "asc"))
        self.treeview.heading("progress", text="Progress", command=lambda: self.on_sort("progress", "asc"))
        self.treeview.heading("next_milestone", text="Next Milestone",
                              command=lambda: self.on_sort("next_milestone", "asc"))

        # Column widths
        self.treeview.column("id", width=50, minwidth=50)
        self.treeview.column("name", width=200, minwidth=150)
        self.treeview.column("type", width=120, minwidth=100)
        self.treeview.column("status", width=120, minwidth=100)
        self.treeview.column("customer", width=150, minwidth=120)
        self.treeview.column("start_date", width=100, minwidth=100)
        self.treeview.column("end_date", width=100, minwidth=100)
        self.treeview.column("progress", width=100, minwidth=100)
        self.treeview.column("next_milestone", width=150, minwidth=150)

        # Create search fields
        self.search_frame.add_search_fields([
            {"name": "name", "label": "Project Name", "type": "text"},
            {"name": "status", "label": "Status", "type": "enum", "enum_class": ProjectStatus},
            {"name": "type", "label": "Type", "type": "enum", "enum_class": ProjectType},
            {"name": "customer", "label": "Customer", "type": "text"},
            {"name": "start_date_from", "label": "Start Date From", "type": "date"},
            {"name": "start_date_to", "label": "Start Date To", "type": "date"},
            {"name": "due_date_from", "label": "Due Date From", "type": "date"},
            {"name": "due_date_to", "label": "Due Date To", "type": "date"},
        ])

        # Add project dashboard section
        self.create_project_dashboard(self.content_frame)

        # Add custom action buttons
        self.add_item_action_buttons(self.action_frame)

        # Load initial data
        self.load_data()

    def create_project_dashboard(self, parent):
        """Create project dashboard with status metrics and timeline.

        Args:
            parent: The parent widget for the dashboard
        """
        # Create a frame for the dashboard
        dashboard_frame = ttk.LabelFrame(parent, text="Project Dashboard")
        dashboard_frame.pack(fill=tk.X, padx=10, pady=(0, 10), anchor=tk.W)

        # Status metrics section
        metrics_frame = ttk.Frame(dashboard_frame)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create status count widgets (will be populated in update_dashboard)
        self.status_metrics = {}
        statuses = [s for s in ProjectStatus]
        for idx, status in enumerate(statuses[:6]):  # Show first 6 statuses
            status_frame = ttk.Frame(metrics_frame)
            status_frame.grid(row=0, column=idx, padx=5, pady=5)

            # Status badge
            badge = StatusBadge(status_frame, status.value.title().replace('_', ' '), status.value)
            badge.pack(pady=(0, 5))

            # Count label
            count_var = tk.StringVar(value="0")
            count_label = ttk.Label(status_frame, textvariable=count_var, font=("TkDefaultFont", 12, "bold"))
            count_label.pack()

            self.status_metrics[status.value] = count_var

        # Upcoming deadlines section
        deadlines_frame = ttk.Frame(dashboard_frame)
        deadlines_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(deadlines_frame, text="Upcoming Deadlines (7 days):", font=("TkDefaultFont", 10, "bold")).pack(
            anchor=tk.W, pady=(5, 0))

        # Create a small treeview for upcoming deadlines
        self.deadlines_tree = ttk.Treeview(deadlines_frame, columns=("name", "due_date", "status"), show="headings",
                                           height=3)
        self.deadlines_tree.heading("name", text="Project Name")
        self.deadlines_tree.heading("due_date", text="Due Date")
        self.deadlines_tree.heading("status", text="Status")

        self.deadlines_tree.column("name", width=200)
        self.deadlines_tree.column("due_date", width=100)
        self.deadlines_tree.column("status", width=120)

        self.deadlines_tree.pack(fill=tk.X, pady=5)

        # Button to view timeline
        timeline_btn = ttk.Button(dashboard_frame, text="View Timeline", command=self.show_timeline)
        timeline_btn.pack(anchor=tk.E, padx=10, pady=5)

    def add_item_action_buttons(self, parent):
        """Add additional action buttons for projects.

        Args:
            parent: The parent widget for the buttons
        """
        # Add standard buttons
        ttk.Button(parent, text="Add Project", command=self.on_add).pack(side=tk.LEFT, padx=5)
        self.view_btn = ttk.Button(parent, text="View Project", command=self.on_view, state=tk.DISABLED)
        self.view_btn.pack(side=tk.LEFT, padx=5)
        self.edit_btn = ttk.Button(parent, text="Edit Project", command=self.on_edit, state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn = ttk.Button(parent, text="Delete Project", command=self.on_delete, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        # Add separator
        ttk.Separator(parent, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y, pady=5)

        # Add project-specific buttons
        self.picking_list_btn = ttk.Button(
            parent, text="Picking List", command=self.on_picking_list, state=tk.DISABLED
        )
        self.picking_list_btn.pack(side=tk.LEFT, padx=5)

        self.tool_list_btn = ttk.Button(
            parent, text="Tool List", command=self.on_tool_list, state=tk.DISABLED
        )
        self.tool_list_btn.pack(side=tk.LEFT, padx=5)

        self.update_status_btn = ttk.Button(
            parent, text="Update Status", command=self.on_update_status, state=tk.DISABLED
        )
        self.update_status_btn.pack(side=tk.LEFT, padx=5)

    def add_context_menu_items(self, menu):
        """Add additional context menu items for projects.

        Args:
            menu: The context menu to add items to
        """
        menu.add_command(label="View Project", command=self.on_view)
        menu.add_command(label="Edit Project", command=self.on_edit)
        menu.add_separator()
        menu.add_command(label="Picking List", command=self.on_picking_list)
        menu.add_command(label="Tool List", command=self.on_tool_list)
        menu.add_command(label="Update Status", command=self.on_update_status)
        menu.add_separator()
        menu.add_command(label="Delete Project", command=self.on_delete)

    def extract_item_values(self, item):
        """Extract values from a project item for display in the treeview.

        Args:
            item: The project item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Calculate progress based on current status
        statuses = list(ProjectStatus)
        current_status_idx = next((i for i, s in enumerate(statuses) if s.value == item.status), 0)
        progress = f"{int((current_status_idx / (len(statuses) - 1)) * 100)}%"

        # Format dates
        start_date = item.start_date.strftime("%Y-%m-%d") if item.start_date else ""
        end_date = item.end_date.strftime("%Y-%m-%d") if item.end_date else ""

        # Determine next milestone based on status
        next_milestone = self.get_next_milestone(item.status)

        # Customer info
        customer_name = f"{item.customer.first_name} {item.customer.last_name}" if hasattr(item,
                                                                                           'customer') and item.customer else "N/A"

        return [
            item.id,
            item.name,
            item.type.value.replace('_', ' ').title() if hasattr(item, 'type') and item.type else "N/A",
            item.status.value.replace('_', ' ').title() if hasattr(item, 'status') and item.status else "N/A",
            customer_name,
            start_date,
            end_date,
            progress,
            next_milestone
        ]

    def get_next_milestone(self, status):
        """Determine the next milestone based on current status.

        Args:
            status: Current project status

        Returns:
            String describing the next milestone
        """
        status_to_milestone = {
            ProjectStatus.INITIAL_CONSULTATION: "Design Phase",
            ProjectStatus.DESIGN_PHASE: "Pattern Development",
            ProjectStatus.PATTERN_DEVELOPMENT: "Client Approval",
            ProjectStatus.CLIENT_APPROVAL: "Material Selection",
            ProjectStatus.MATERIAL_SELECTION: "Material Purchase",
            ProjectStatus.MATERIAL_PURCHASED: "Cutting",
            ProjectStatus.CUTTING: "Skiving",
            ProjectStatus.SKIVING: "Preparation",
            ProjectStatus.PREPARATION: "Assembly",
            ProjectStatus.ASSEMBLY: "Stitching",
            ProjectStatus.STITCHING: "Edge Finishing",
            ProjectStatus.EDGE_FINISHING: "Hardware Installation",
            ProjectStatus.HARDWARE_INSTALLATION: "Conditioning",
            ProjectStatus.CONDITIONING: "Quality Check",
            ProjectStatus.QUALITY_CHECK: "Final Touches",
            ProjectStatus.FINAL_TOUCHES: "Photography",
            ProjectStatus.PHOTOGRAPHY: "Packaging",
            ProjectStatus.PACKAGING: "Completion",
            ProjectStatus.COMPLETED: "Delivered",
            ProjectStatus.ON_HOLD: "Resume Work",
            ProjectStatus.CANCELLED: "N/A"
        }

        return status_to_milestone.get(status, "Unknown")

    def load_data(self):
        """Load project data into the treeview."""
        try:
            # Clear existing items
            self.treeview.clear()

            # Get current search criteria
            search_criteria = self.search_frame.get_search_criteria() if hasattr(self, 'search_frame') else {}

            # Get project data from service
            projects = self.project_service.get_projects(
                filters=search_criteria,
                offset=self.current_page * self.page_size,
                limit=self.page_size,
                sort_by=self.sort_column,
                sort_order=self.sort_direction
            )

            # Get total count for pagination
            total_count = self.project_service.get_project_count(filters=search_criteria)

            # Insert projects into treeview
            for project in projects:
                values = self.extract_item_values(project)
                self.treeview.insert_item(project.id, values)

                # Apply status styling
                status_style = get_status_style(values[3].lower().replace(' ', '_'))
                self.treeview.item(project.id, tags=(status_style.get('tag', ''),))

            # Update pagination
            self.update_pagination_display(self.calculate_total_pages(total_count))

            # Update dashboard
            self.update_dashboard()

        except Exception as e:
            self.logger.error(f"Error loading projects: {e}")
            messagebox.showerror("Error", f"Failed to load projects: {str(e)}")

    def update_dashboard(self):
        """Update the project dashboard with current metrics."""
        try:
            # Get status metrics
            status_counts = self.project_service.get_status_counts()

            # Update status count labels
            for status, count in status_counts.items():
                if status in self.status_metrics:
                    self.status_metrics[status].set(str(count))

            # Get upcoming deadlines
            upcoming_deadlines = self.project_service.get_upcoming_deadlines(days=7)

            # Clear existing items
            for item in self.deadlines_tree.get_children():
                self.deadlines_tree.delete(item)

            # Add upcoming deadlines
            for deadline in upcoming_deadlines:
                due_date = deadline.get('end_date', '').strftime('%Y-%m-%d') if deadline.get('end_date') else 'N/A'
                status = deadline.get('status', '').value.replace('_', ' ').title() if deadline.get('status') else 'N/A'

                self.deadlines_tree.insert('', 'end', values=(
                    deadline.get('name', 'Unknown'),
                    due_date,
                    status
                ))

        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")

    def on_search(self, criteria):
        """Handle search.

        Args:
            criteria: Dictionary of search criteria
        """
        # Reset to first page when searching
        self.current_page = 0

        # Load data with search criteria
        self.load_data()

    def on_select(self):
        """Handle item selection."""
        selected_id = self.treeview.get_selected_id()

        # Enable/disable buttons based on selection
        state = tk.NORMAL if selected_id else tk.DISABLED
        self.view_btn.configure(state=state)
        self.edit_btn.configure(state=state)
        self.delete_btn.configure(state=state)
        self.picking_list_btn.configure(state=state)
        self.tool_list_btn.configure(state=state)
        self.update_status_btn.configure(state=state)

    def on_add(self):
        """Handle add new project action."""
        # Navigate to project details view in create mode
        self.parent.master.show_view("project_details", add_to_history=True, view_data={"create_new": True})

    def on_view(self):
        """Handle view project action."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to view.")
            return

        # Navigate to project details view in view mode
        self.parent.master.show_view(
            "project_details",
            add_to_history=True,
            view_data={"project_id": selected_id, "readonly": True}
        )

    def on_edit(self):
        """Handle edit project action."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to edit.")
            return

        # Navigate to project details view in edit mode
        self.parent.master.show_view(
            "project_details",
            add_to_history=True,
            view_data={"project_id": selected_id, "readonly": False}
        )

    def on_delete(self):
        """Handle delete project action."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to delete.")
            return

        # Get selected project name
        selected_values = self.treeview.get_selected_item_values()
        project_name = selected_values[1] if len(selected_values) > 1 else "this project"

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete {project_name}?\nThis action cannot be undone."
        ):
            return

        try:
            # Delete project via service
            self.project_service.delete_project(selected_id)

            # Refresh the view
            self.load_data()
            messagebox.showinfo("Success", f"Project '{project_name}' has been deleted.")

        except Exception as e:
            self.logger.error(f"Error deleting project: {e}")
            messagebox.showerror("Delete Error", f"Failed to delete project: {str(e)}")

    def on_picking_list(self):
        """Handle picking list button click."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to view picking list.")
            return

        # Navigate to picking list view for this project
        self.parent.master.show_view(
            "picking_list",
            add_to_history=True,
            view_data={"project_id": selected_id}
        )

    def on_tool_list(self):
        """Handle tool list button click."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to view tool list.")
            return

        # Navigate to tool list view for this project
        self.parent.master.show_view(
            "tool_list",
            add_to_history=True,
            view_data={"project_id": selected_id}
        )

    def on_update_status(self):
        """Handle update status button click."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to update status.")
            return

        # Get current status
        selected_values = self.treeview.get_selected_item_values()
        current_status = selected_values[3] if len(selected_values) > 3 else None

        # Create a dialog for status update
        dialog = tk.Toplevel(self)
        dialog.title("Update Project Status")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Add form elements
        ttk.Label(dialog, text="Current Status:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Label(dialog, text=current_status).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="New Status:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(dialog, textvariable=status_var, state="readonly")
        status_combo['values'] = [s.value.replace('_', ' ').title() for s in ProjectStatus]
        status_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.NW)
        notes_text = tk.Text(dialog, width=30, height=5)
        notes_text.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text="Update",
            command=lambda: self.update_project_status(
                selected_id,
                status_var.get(),
                notes_text.get("1.0", tk.END).strip(),
                dialog
            )
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)

    def update_project_status(self, project_id, new_status, notes, dialog):
        """Update project status.

        Args:
            project_id: ID of the project to update
            new_status: New status string
            notes: Status change notes
            dialog: Dialog to close on success
        """
        if not new_status:
            messagebox.showwarning("Input Error", "Please select a new status.", parent=dialog)
            return

        try:
            # Convert display status back to enum value
            status_value = new_status.lower().replace(' ', '_')

            # Update status via service
            self.project_service.update_project_status(project_id, status_value, notes)

            # Close dialog
            dialog.destroy()

            # Refresh the view
            self.load_data()
            messagebox.showinfo("Success", "Project status has been updated.")

        except Exception as e:
            self.logger.error(f"Error updating project status: {e}")
            messagebox.showerror("Update Error", f"Failed to update status: {str(e)}", parent=dialog)

    def show_timeline(self):
        """Show project timeline visualization dialog."""
        try:
            # Get all active projects for timeline
            projects = self.project_service.get_projects(
                filters={"status__not": "completed,cancelled"},
                include_components=True,
                include_timeline=True
            )

            if not projects:
                messagebox.showinfo("No Projects", "No active projects to display in the timeline.")
                return

            # Create and show timeline dialog
            dialog = ProjectTimelineDialog(self, projects)
            dialog.show()

        except Exception as e:
            self.logger.error(f"Error showing timeline: {e}")
            messagebox.showerror("Error", f"Failed to display timeline: {str(e)}")

    def refresh(self):
        """Refresh the view."""
        self.load_data()