# gui/leatherworking/project_dashboard.py
"""
Project dashboard view for leatherworking store management system.
Provides functionality to view, add, edit, and track leatherworking projects.
"""

import logging
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from typing import Any, Dict, List, Optional, Type

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel

# Configure logger
logger = logging.getLogger(__name__)


class ProjectDashboard(BaseView):
    """
    Dashboard view for managing leatherworking projects.

    Provides a visual overview of current projects, their status, and relevant metrics.
    Includes functionality to add, edit, and track projects.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the project dashboard.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance for accessing services
        """
        super().__init__(parent, app)

        self._project_service = None
        self._material_service = None
        self._selected_project_id = None

        # Initialize UI components
        self._create_ui()
        self._load_data()

        logger.info("Project dashboard initialized")

    def get_service(self, service_type: Type) -> Any:
        """
        Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            return self._app.get_service(service_type)
        except Exception as e:
            logger.error(f"Failed to get service {service_type.__name__}: {str(e)}")
            raise

    @property
    def project_service(self) -> IProjectService:
        """
        Lazy-loaded project service property.

        Returns:
            IProjectService: Project service instance
        """
        if self._project_service is None:
            self._project_service = self.get_service(IProjectService)
        return self._project_service

    @property
    def material_service(self) -> IMaterialService:
        """
        Lazy-loaded material service property.

        Returns:
            IMaterialService: Material service instance
        """
        if self._material_service is None:
            self._material_service = self.get_service(IMaterialService)
        return self._material_service

    def _create_ui(self) -> None:
        """Create and configure the dashboard UI."""
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # Create overview section
        self._create_overview_section()

        # Create project list section
        self._create_project_list()

        # Create quick actions section
        self._create_quick_actions()

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.status_var.set("Ready")

    def _create_overview_section(self) -> None:
        """Create project overview section with key metrics."""
        overview_frame = ttk.LabelFrame(self, text="Project Overview", padding=10)
        overview_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Configure grid
        overview_frame.columnconfigure(0, weight=1)
        overview_frame.columnconfigure(1, weight=1)
        overview_frame.columnconfigure(2, weight=1)
        overview_frame.columnconfigure(3, weight=1)

        # Create metric cards
        self._create_metric_card(overview_frame, "Total Projects", "0", 0, 0)
        self._create_metric_card(overview_frame, "In Progress", "0", 0, 1)
        self._create_metric_card(overview_frame, "Completed", "0", 0, 2)
        self._create_metric_card(overview_frame, "On Hold", "0", 0, 3)

        self._create_metric_card(overview_frame, "Materials Used", "0", 1, 0)
        self._create_metric_card(overview_frame, "Time Invested", "0 hrs", 1, 1)
        self._create_metric_card(overview_frame, "Cost", "$0.00", 1, 2)
        self._create_metric_card(overview_frame, "Revenue", "$0.00", 1, 3)

    def _create_metric_card(self, parent: ttk.Frame, title: str, value: str, row: int, col: int) -> None:
        """
        Create a metric card for the overview section.

        Args:
            parent: Parent frame
            title: Metric title
            value: Metric value
            row: Grid row
            col: Grid column
        """
        card_frame = ttk.Frame(parent, relief="ridge", borderwidth=1, padding=8)
        card_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        # Value label (large)
        value_var = tk.StringVar(value=value)
        value_label = ttk.Label(card_frame, textvariable=value_var, font=("", 16, "bold"))
        value_label.pack(pady=(0, 5))

        # Store the variable for later updates
        setattr(self, f"_{title.lower().replace(' ', '_')}_var", value_var)

        # Title label
        ttk.Label(card_frame, text=title, font=("", 9)).pack()

    def _create_project_list(self) -> None:
        """Create a treeview to display project list."""
        list_frame = ttk.LabelFrame(self, text="Project List", padding=10)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Configure grid
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=0)
        list_frame.rowconfigure(1, weight=1)

        # Toolbar for filtering and searching
        toolbar = ttk.Frame(list_frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # Status filter
        ttk.Label(toolbar, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_filter = ttk.Combobox(toolbar, width=15, state="readonly")
        self.status_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.status_filter["values"] = ["All", "Planning", "In Progress", "On Hold", "Completed", "Cancelled"]
        self.status_filter.current(0)
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self._load_data())

        # Type filter
        ttk.Label(toolbar, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.type_filter = ttk.Combobox(toolbar, width=15, state="readonly")
        self.type_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.type_filter["values"] = ["All", "Wallet", "Bag", "Belt", "Case", "Accessory", "Custom"]
        self.type_filter.current(0)
        self.type_filter.bind("<<ComboboxSelected>>", lambda e: self._load_data())

        # Search box
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", lambda e: self._load_data())
        ttk.Button(toolbar, text="Search", command=self._load_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Reset", command=self._reset_filters).pack(side=tk.LEFT)

        # Create treeview
        columns = (
            "id", "name", "type", "skill_level", "status", "start_date",
            "deadline", "progress", "materials_cost"
        )
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        # Configure headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Project Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("skill_level", text="Skill Level")
        self.tree.heading("status", text="Status")
        self.tree.heading("start_date", text="Start Date")
        self.tree.heading("deadline", text="Deadline")
        self.tree.heading("progress", text="Progress")
        self.tree.heading("materials_cost", text="Materials Cost")

        # Configure columns
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("name", width=200)
        self.tree.column("type", width=100)
        self.tree.column("skill_level", width=100)
        self.tree.column("status", width=100)
        self.tree.column("start_date", width=100)
        self.tree.column("deadline", width=100)
        self.tree.column("progress", width=80, anchor=tk.CENTER)
        self.tree.column("materials_cost", width=120, anchor=tk.E)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)

        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scrollbar.grid(row=1, column=1, sticky="ns")
        x_scrollbar.grid(row=2, column=0, sticky="ew")

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_project_select)
        self.tree.bind("<Double-1>", lambda e: self._edit_project())

    def _create_quick_actions(self) -> None:
        """Create quick action buttons."""
        actions_frame = ttk.LabelFrame(self, text="Quick Actions", padding=10)
        actions_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Configure grid
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)
        actions_frame.columnconfigure(2, weight=1)
        actions_frame.rowconfigure(0, weight=0)
        actions_frame.rowconfigure(1, weight=0)

        # Action buttons - row 1
        self._create_action_button(actions_frame, "New Project", self.new_project, 0, 0)
        self._create_action_button(actions_frame, "Import Project", self.import_project, 0, 1)
        self._create_action_button(actions_frame, "Generate Report", self.generate_report, 0, 2)

        # Action buttons - row 2
        self._create_action_button(actions_frame, "Edit Selected", self._edit_project, 1, 0)
        self._create_action_button(actions_frame, "View Timeline", self._view_timeline, 1, 1)
        self._create_action_button(actions_frame, "Archive Completed", self._archive_completed, 1, 2)

    def _create_action_button(self, parent: ttk.Frame, text: str, command, row: int, col: int) -> None:
        """
        Create an action button for the quick actions section.

        Args:
            parent: Parent frame
            text: Button text
            command: Button command
            row: Grid row
            col: Grid column
        """
        btn = ttk.Button(parent, text=text, command=command, width=15)
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def _load_data(self) -> None:
        """
        Load project data and populate the treeview.
        Update overview metrics.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get projects from service
            # In a real implementation, this would be:
            # projects = self.project_service.get_projects()
            # For now, using mock data
            projects = self._get_mock_projects()

            # Apply filters
            status_filter = self.status_filter.get()
            type_filter = self.type_filter.get()
            search_term = self.search_var.get().strip().lower()

            filtered_projects = projects

            if status_filter != "All":
                filtered_projects = [p for p in filtered_projects if p["status"] == status_filter]

            if type_filter != "All":
                filtered_projects = [p for p in filtered_projects if p["type"] == type_filter]

            if search_term:
                filtered_projects = [p for p in filtered_projects if
                                     search_term in p["name"].lower() or
                                     search_term in p.get("description", "").lower()]

            # Populate treeview
            for project in filtered_projects:
                # Format data for display
                progress = f"{project.get('progress', 0)}%"
                materials_cost = f"${project.get('materials_cost', 0):.2f}"

                self.tree.insert("", tk.END, values=(
                    project.get("id", ""),
                    project.get("name", ""),
                    project.get("type", ""),
                    project.get("skill_level", ""),
                    project.get("status", ""),
                    project.get("start_date", ""),
                    project.get("deadline", ""),
                    progress,
                    materials_cost
                ))

            # Update metrics
            self._update_metrics(projects)

            # Update status
            self.status_var.set(f"Loaded {len(filtered_projects)} projects")
            logger.info(f"Loaded {len(filtered_projects)} projects")

        except Exception as e:
            error_message = f"Error loading projects: {str(e)}"
            self.show_error("Data Loading Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error loading data")

    def _get_mock_projects(self) -> List[Dict[str, Any]]:
        """
        Generate mock project data for testing.

        Returns:
            List[Dict[str, Any]]: List of project dictionaries
        """
        return [
            {
                "id": 1,
                "name": "Classic Bifold Wallet",
                "type": "Wallet",
                "skill_level": "Beginner",
                "status": "Completed",
                "start_date": "2025-01-10",
                "deadline": "2025-01-15",
                "progress": 100,
                "materials_cost": 35.50,
                "description": "Simple bifold wallet project"
            },
            {
                "id": 2,
                "name": "Messenger Bag",
                "type": "Bag",
                "skill_level": "Intermediate",
                "status": "In Progress",
                "start_date": "2025-02-01",
                "deadline": "2025-03-01",
                "progress": 65,
                "materials_cost": 120.75,
                "description": "Leather messenger bag with laptop compartment"
            },
            {
                "id": 3,
                "name": "Leather Belt",
                "type": "Belt",
                "skill_level": "Beginner",
                "status": "Planning",
                "start_date": "2025-02-15",
                "deadline": "2025-02-28",
                "progress": 0,
                "materials_cost": 45.00,
                "description": "Simple belt with antique brass buckle"
            },
            {
                "id": 4,
                "name": "Watch Strap",
                "type": "Accessory",
                "skill_level": "Intermediate",
                "status": "On Hold",
                "start_date": "2025-01-20",
                "deadline": "2025-02-10",
                "progress": 30,
                "materials_cost": 25.25,
                "description": "Custom watch strap for vintage watch"
            },
            {
                "id": 5,
                "name": "Laptop Sleeve",
                "type": "Case",
                "skill_level": "Beginner",
                "status": "In Progress",
                "start_date": "2025-02-10",
                "deadline": "2025-02-20",
                "progress": 50,
                "materials_cost": 65.80,
                "description": "Padded leather sleeve for 15-inch laptop"
            }
        ]

    def _update_metrics(self, projects: List[Dict[str, Any]]) -> None:
        """
        Update the overview metrics based on project data.

        Args:
            projects: List of project dictionaries
        """
        # Calculate metrics
        total = len(projects)
        in_progress = sum(1 for p in projects if p["status"] == "In Progress")
        completed = sum(1 for p in projects if p["status"] == "Completed")
        on_hold = sum(1 for p in projects if p["status"] == "On Hold")

        # Calculate materials usage and costs
        total_cost = sum(p.get("materials_cost", 0) for p in projects)

        # Mock revenue (in a real app, this would come from the service)
        revenue = total_cost * 1.5

        # Update metric cards
        self._total_projects_var.set(str(total))
        self._in_progress_var.set(str(in_progress))
        self._completed_var.set(str(completed))
        self._on_hold_var.set(str(on_hold))

        self._materials_used_var.set(str(total))  # Simplified for mock
        self._time_invested_var.set("120 hrs")  # Mock value
        self._cost_var.set(f"${total_cost:.2f}")
        self._revenue_var.set(f"${revenue:.2f}")

    def _reset_filters(self) -> None:
        """Reset all filters and search criteria."""
        self.status_filter.current(0)
        self.type_filter.current(0)
        self.search_var.set("")
        self._load_data()

    def _on_project_select(self, event=None) -> None:
        """
        Handle selection of a project in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self._selected_project_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            self._selected_project_id = values[0]  # ID is the first column

    def new_project(self) -> None:
        """Open dialog to create a new project."""
        # Placeholder - in a real app, this would open a dialog
        self.show_info("New Project", "Project creation dialog would open here.")
        logger.info("New project functionality called")

    def import_project(self) -> None:
        """Import a project from external source."""
        # Placeholder - in a real app, this would open an import dialog
        self.show_info("Import Project", "Project import dialog would open here.")
        logger.info("Import project functionality called")

    def generate_report(self) -> None:
        """Generate a project report."""
        # Placeholder - in a real app, this would generate a report
        self.show_info("Generate Report", "Report generation dialog would open here.")
        logger.info("Generate report functionality called")

    def _edit_project(self) -> None:
        """Show dialog to edit the selected project."""
        if not self._selected_project_id:
            self.show_warning("Warning", "Please select a project to edit.")
            return

        # Placeholder - in a real app, this would open a dialog
        self.show_info("Edit Project",
                       f"Project editing dialog would open here for project ID {self._selected_project_id}.")
        logger.info(f"Edit project called for ID: {self._selected_project_id}")

    def _view_timeline(self) -> None:
        """View project timeline visualization."""
        # Placeholder - in a real app, this would open a timeline view
        self.show_info("View Timeline", "Project timeline visualization would open here.")
        logger.info("View timeline functionality called")

    def _archive_completed(self) -> None:
        """Archive all completed projects."""
        # Ask for confirmation
        if not messagebox.askyesno("Confirm Archive",
                                   "Are you sure you want to archive all completed projects?\n"
                                   "This will move them to the archive section."):
            return

        # Placeholder - in a real app, this would call a service to archive projects
        self.show_info("Archive Projects", "Completed projects would be archived.")
        logger.info("Archive completed projects functionality called")

        # Refresh the view
        self._load_data()