# gui/leatherworking/project_dashboard.py
"""
Project dashboard module for managing leatherworking projects.
Provides an overview of all projects with status tracking and analysis.
"""

import logging
import os
import sys
import math
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

# Ensure the project root is in the Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from gui.base_view import BaseView

# Import services and enums
try:
    from di.core import inject
    from services.interfaces.project_service import (
        IProjectService,
        ProjectType,
        SkillLevel,
        ProjectStatus
    )
except ImportError:
    # Fallback decorator and definitions if imports fail
    def inject(func):
        """Fallback inject decorator for standalone testing."""
        return func


    from enum import Enum, auto


    class ProjectType(Enum):
        BAG = auto()
        WALLET = auto()
        BELT = auto()
        NOTEBOOK = auto()
        CUSTOM = auto()
        OTHER = auto()


    class SkillLevel(Enum):
        BEGINNER = auto()
        INTERMEDIATE = auto()
        ADVANCED = auto()
        EXPERT = auto()


    class ProjectStatus(Enum):
        PLANNING = auto()
        DESIGN = auto()
        MATERIAL_SELECTION = auto()
        CUTTING = auto()
        ASSEMBLY = auto()
        STITCHING = auto()
        FINISHING = auto()
        QUALITY_CHECK = auto()
        COMPLETED = auto()
        ON_HOLD = auto()
        CANCELLED = auto()
        PROTOTYPE = auto()


    class IProjectService:
        """Mock Project Service for standalone testing."""

        def get_all_projects(self):
            """Return sample projects."""
            from datetime import datetime, timedelta

            class MockProject:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)

            return [
                MockProject(
                    id=1,
                    name="Leather Wallet",
                    project_type=ProjectType.WALLET.name,
                    start_date=datetime.now() - timedelta(days=10),
                    deadline=datetime.now() + timedelta(days=20),
                    status=ProjectStatus.DESIGN.name,
                    progress=30,
                    estimated_hours=15.5
                ),
                MockProject(
                    id=2,
                    name="Messenger Bag",
                    project_type=ProjectType.BAG.name,
                    start_date=datetime.now() - timedelta(days=5),
                    deadline=datetime.now() + timedelta(days=25),
                    status=ProjectStatus.MATERIAL_SELECTION.name,
                    progress=15,
                    estimated_hours=40.0
                ),
                MockProject(
                    id=3,
                    name="Custom Belt",
                    project_type=ProjectType.BELT.name,
                    start_date=datetime.now() - timedelta(days=15),
                    deadline=datetime.now() - timedelta(days=2),
                    status=ProjectStatus.COMPLETED.name,
                    progress=100,
                    estimated_hours=8.0
                )
            ]

        def get_project_by_id(self, project_id):
            """Return a specific project by ID."""
            projects = self.get_all_projects()
            return next((p for p in projects if p.id == project_id), None)

        def create_project(self, project_data):
            """Create a new project."""
            return len(self.get_all_projects()) + 1

        def update_project(self, project_data):
            """Update a project."""
            pass

        def delete_project(self, project_id):
            """Delete a project."""
            pass

        def update_project_status(self, update_data):
            """Update project status."""
            pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectDashboard(BaseView):
    """Dashboard for managing and tracking leatherworking projects."""

    @inject
    @inject
    def __init__(self, parent, controller, project_service: Optional[IProjectService] = None):
        """Initialize the Project Dashboard.

        Args:
            parent: The parent widget.
            controller: The application controller or main application instance.
            project_service: Service for interacting with project data.
        """
        # Call parent constructor
        super().__init__(parent, controller)

        # Use provided service or create a default mock service
        self.project_service = project_service or IProjectService()

        logger.info("Initializing Project Dashboard")

        # Initialize variables
        self.projects: List[Dict] = []
        self.selected_project_id: Optional[int] = None
        self.stats: Dict[str, Any] = {
            "total": 0,
            "active": 0,
            "completed": 0,
            "on_hold": 0,
            "overdue": 0,
        }

        # Setup UI components
        self._setup_layout()

        # Load projects
        self.load_projects()

        logger.info("Project Dashboard initialized")

    def _setup_layout(self):
        """Create and arrange UI elements within the frame."""
        try:
            # Ensure the parent frame is configured
            self.configure(padding=10)

            # Main frame with padding
            main_frame = ttk.Frame(self, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Title
            title_label = ttk.Label(
                main_frame,
                text="Project Dashboard",
                font=("Helvetica", 16, "bold"),
            )
            title_label.pack(pady=(0, 10))

            # Top panels - Overview cards
            overview_frame = ttk.Frame(main_frame)
            overview_frame.pack(fill=tk.X, pady=(0, 10))
            self._create_overview_cards(overview_frame)

            # Middle panels - Project list and charts
            middle_frame = ttk.Frame(main_frame)
            middle_frame.pack(fill=tk.BOTH, expand=True)

            # Create tabs for different views
            notebook = ttk.Notebook(middle_frame)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Projects list tab
            projects_frame = ttk.Frame(notebook)
            notebook.add(projects_frame, text="Projects")
            self._create_projects_tab(projects_frame)

            # Timeline view tab
            timeline_frame = ttk.Frame(notebook)
            notebook.add(timeline_frame, text="Timeline")
            self._create_timeline_tab(timeline_frame)

            # Statistics tab
            stats_frame = ttk.Frame(notebook)
            notebook.add(stats_frame, text="Statistics")
            self._create_stats_tab(stats_frame)

            # Bottom panel - Status bar
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill=tk.X, pady=(10, 0))

            # Status variable for messages
            self.status_var = tk.StringVar(value="Ready")
            status_label = ttk.Label(
                status_frame,
                textvariable=self.status_var,
                anchor=tk.W,
                relief="sunken",
                padding=(2, 2),
            )
            status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Action buttons
            ttk.Button(status_frame, text="Export Report", command=self._export_report).pack(
                side=tk.RIGHT, padx=5
            )
            ttk.Button(status_frame, text="Refresh", command=self.on_refresh).pack(
                side=tk.RIGHT, padx=5
            )
        except Exception as e:
            logger.error(f"Error in _setup_layout: {e}")
            messagebox.showerror("Layout Error", str(e))

    def _create_overview_cards(self, parent):
        """Create overview cards with project statistics.

        Args:
            parent: Parent widget for the overview cards.
        """
        # Create a frame with 5 cards showing project stats
        cards_frame = ttk.Frame(parent)
        cards_frame.pack(fill=tk.X)

        # Configure grid for equal-width cards
        for i in range(5):
            cards_frame.columnconfigure(i, weight=1, uniform="card")

        # Total projects card
        total_frame = ttk.LabelFrame(cards_frame, text="Total Projects")
        total_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.total_var = tk.StringVar(value="0")
        ttk.Label(total_frame, textvariable=self.total_var, font=("Helvetica", 24)).pack(pady=10)

        # Active projects card
        active_frame = ttk.LabelFrame(cards_frame, text="Active Projects")
        active_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.active_var = tk.StringVar(value="0")
        ttk.Label(active_frame, textvariable=self.active_var, font=("Helvetica", 24)).pack(pady=10)

        # Completed projects card
        completed_frame = ttk.LabelFrame(cards_frame, text="Completed")
        completed_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.completed_var = tk.StringVar(value="0")
        ttk.Label(completed_frame, textvariable=self.completed_var, font=("Helvetica", 24)).pack(pady=10)

        # On Hold projects card
        on_hold_frame = ttk.LabelFrame(cards_frame, text="On Hold")
        on_hold_frame.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        self.on_hold_var = tk.StringVar(value="0")
        ttk.Label(on_hold_frame, textvariable=self.on_hold_var, font=("Helvetica", 24)).pack(pady=10)

        # Overdue projects card
        overdue_frame = ttk.LabelFrame(cards_frame, text="Overdue")
        overdue_frame.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        self.overdue_var = tk.StringVar(value="0")
        ttk.Label(overdue_frame, textvariable=self.overdue_var, font=("Helvetica", 24), foreground="red").pack(pady=10)

    def _create_projects_tab(self, parent):
        """Create the projects tab with list and controls.

        Args:
            parent: Parent widget for the projects tab.
        """
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Controls frame
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Project action buttons
        ttk.Button(controls_frame, text="New Project", command=self._new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Edit Project", command=self._edit_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Delete Project", command=self._delete_project).pack(side=tk.LEFT, padx=2)

        # Filter controls
        filter_frame = ttk.LabelFrame(controls_frame, text="Filter")
        filter_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Status filter
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.status_filter = ttk.Combobox(filter_frame, width=15, state="readonly")
        self.status_filter.grid(row=0, column=1, padx=5, pady=2)
        status_values = ["All"] + [status.name for status in ProjectStatus]
        self.status_filter.configure(values=status_values)
        self.status_filter.current(0)
        self.status_filter.bind("<<ComboboxSelected>>", self._apply_filters)

        # Type filter
        ttk.Label(filter_frame, text="Type:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.type_filter = ttk.Combobox(filter_frame, width=15, state="readonly")
        self.type_filter.grid(row=1, column=1, padx=5, pady=2)
        type_values = ["All"] + [project_type.name for project_type in ProjectType]
        self.type_filter.configure(values=type_values)
        self.type_filter.current(0)
        self.type_filter.bind("<<ComboboxSelected>>", self._apply_filters)

        # Search field
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", self._on_search)
        ttk.Button(search_frame, text="Search", command=self._on_search).pack(side=tk.LEFT)

        # Projects treeview
        self._create_projects_treeview(parent)

    def _create_projects_treeview(self, parent):
        """Create the projects treeview with scrollbar.

        Args:
            parent: Parent widget for the treeview.
        """
        # Frame for treeview and scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Define columns
        columns = ("id", "name", "type", "start_date", "deadline", "status", "progress", "hours")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        # Configure headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Project Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("start_date", text="Start Date")
        self.tree.heading("deadline", text="Deadline")
        self.tree.heading("status", text="Status")
        self.tree.heading("progress", text="Progress")
        self.tree.heading("hours", text="Hours")

        # Configure columns width and alignment
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=200)
        self.tree.column("type", width=80)
        self.tree.column("start_date", width=80, anchor=tk.CENTER)
        self.tree.column("deadline", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.CENTER)
        self.tree.column("progress", width=80, anchor=tk.CENTER)
        self.tree.column("hours", width=50, anchor=tk.CENTER)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Position treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_project_select)
        self.tree.bind("<Double-1>", lambda e: self._edit_project())
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _create_timeline_tab(self, parent):
        """Create the timeline visualization tab.

        Args:
            parent: Parent widget for the timeline tab.
        """
        # Canvas for timeline visualization
        self.timeline_canvas = tk.Canvas(parent, bg="white", bd=0, highlightthickness=0)
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True)
        self.timeline_canvas.bind("<Configure>", self._update_timeline)

    def _create_stats_tab(self, parent):
        """Create the statistics tab with charts and metrics.

        Args:
            parent: Parent widget for the statistics tab.
        """
        # Create a frame for statistics
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Info label
        ttk.Label(
            stats_frame,
            text="Project Statistics and Metrics",
            font=("Helvetica", 12, "bold")
        ).pack(pady=5)

        # Create placeholder for charts
        chart_placeholder = ttk.LabelFrame(stats_frame, text="Project Type Distribution")
        chart_placeholder.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(
            chart_placeholder,
            text="Chart visualization would appear here",
            font=("Helvetica", 10),
            foreground="gray"
        ).pack(pady=50)

        # Create metrics section
        metrics_frame = ttk.LabelFrame(stats_frame, text="Key Metrics")
        metrics_frame.pack(fill=tk.X, pady=10)

        # Grid for metrics
        for i in range(2):
            metrics_frame.columnconfigure(i, weight=1)

        # Metrics data would typically come from project service
        metrics = [
            ("Average Project Duration:", "15 days"),
            ("On-time Completion Rate:", "85%"),
            ("Resource Utilization:", "72%"),
            ("Average Complexity Score:", "3.2/5")
        ]

        for i, (label, value) in enumerate(metrics):
            row, col = divmod(i, 2)
            ttk.Label(metrics_frame, text=label).grid(row=row, column=col * 2, sticky=tk.E, padx=5, pady=2)
            ttk.Label(metrics_frame, text=value).grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=5, pady=2)

    def load_projects(self):
        """Load projects from the project service."""
        try:
            # Attempt to retrieve projects from the service
            projects = self.project_service.get_all_projects()

            # Clear existing projects
            self.projects.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add projects to the treeview and internal list
            for project in projects:
                project_dict = {
                    "id": project.id,
                    "name": project.name,
                    "type": project.project_type,
                    "start_date": project.start_date,
                    "deadline": project.deadline,
                    "status": project.status,
                    "progress": project.progress,
                    "hours": project.estimated_hours or 0.0,
                }
                self.projects.append(project_dict)

                # Insert into treeview
                self.tree.insert("", "end", values=(
                    project_dict["id"],
                    project_dict["name"],
                    project_dict["type"],
                    project_dict["start_date"].strftime("%Y-%m-%d") if project_dict["start_date"] else "",
                    project_dict["deadline"].strftime("%Y-%m-%d") if project_dict["deadline"] else "",
                    project_dict["status"],
                    f"{project_dict['progress']}%",
                    project_dict["hours"],
                ))

            # Update statistics
            self._update_stats()

            # Update timeline
            self._update_timeline()

            logger.info(f"Loaded {len(self.projects)} projects")
            self.status_var.set(f"Loaded {len(self.projects)} projects")

        except Exception as e:
            logger.error(f"Error loading projects: {e}")
            messagebox.showerror("Load Error", f"Could not load projects: {e}")

            # Fallback to sample projects if service fails
            self._load_sample_projects()

    def _load_sample_projects(self):
        """Load sample projects when service retrieval fails."""
        sample_projects = [
            {
                "id": 1,
                "name": "Bifold Wallet",
                "type": ProjectType.WALLET.name,
                "start_date": datetime.now() - timedelta(days=5),
                "deadline": datetime.now() + timedelta(days=10),
                "status": ProjectStatus.PLANNING.name,
                "progress": 15,
                "hours": 8.0,
            },
            {
                "id": 2,
                "name": "Laptop Sleeve",
                "type": ProjectType.CUSTOM.name,
                "start_date": datetime.now() - timedelta(days=15),
                "deadline": datetime.now() + timedelta(days=5),
                "status": ProjectStatus.MATERIAL_SELECTION.name,
                "progress": 40,
                "hours": 12.0,
            },
            {
                "id": 3,
                "name": "Messenger Bag",
                "type": ProjectType.BAG.name,
                "start_date": datetime.now() + timedelta(days=8),
                "deadline": datetime.now() + timedelta(days=30),
                "status": ProjectStatus.DESIGN.name,
                "progress": 5,
                "hours": 25.0,
            },
        ]

        # Clear existing projects
        self.projects.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add sample projects
        for project_dict in sample_projects:
            self.projects.append(project_dict)

            # Insert into treeview
            self.tree.insert("", "end", values=(
                project_dict["id"],
                project_dict["name"],
                project_dict["type"],
                project_dict["start_date"].strftime("%Y-%m-%d"),
                project_dict["deadline"].strftime("%Y-%m-%d"),
                project_dict["status"],
                f"{project_dict['progress']}%",
                project_dict["hours"],
            ))

        # Update statistics
        self._update_stats()

        # Update timeline
        self._update_timeline()

        logger.warning("Loaded sample projects due to service retrieval failure")
        self.status_var.set("Loaded sample projects")

    def _new_project(self):
        """Open dialog to create a new project."""
        try:
            # Create a new project dialog
            dialog = tk.Toplevel(self)
            dialog.title("New Project")
            dialog.geometry("500x600")
            dialog.transient(self)
            dialog.grab_set()

            # Project name
            ttk.Label(dialog, text="Project Name:").pack(pady=(10, 0))
            name_entry = ttk.Entry(dialog, width=50)
            name_entry.pack(pady=(0, 10))

            # Project type
            ttk.Label(dialog, text="Project Type:").pack(pady=(10, 0))
            type_combo = ttk.Combobox(dialog, values=[t.name for t in ProjectType], state="readonly")
            type_combo.pack(pady=(0, 10))
            type_combo.current(0)

            # Start date
            ttk.Label(dialog, text="Start Date:").pack(pady=(10, 0))
            start_date_entry = ttk.Entry(dialog, width=50)
            start_date_entry.pack(pady=(0, 10))
            start_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

            # Deadline
            ttk.Label(dialog, text="Deadline:").pack(pady=(10, 0))
            deadline_entry = ttk.Entry(dialog, width=50)
            deadline_entry.pack(pady=(0, 10))

            # Status
            ttk.Label(dialog, text="Status:").pack(pady=(10, 0))
            status_combo = ttk.Combobox(dialog, values=[s.name for s in ProjectStatus], state="readonly")
            status_combo.pack(pady=(0, 10))
            status_combo.current(0)

            # Estimated hours
            ttk.Label(dialog, text="Estimated Hours:").pack(pady=(10, 0))
            hours_entry = ttk.Entry(dialog, width=50)
            hours_entry.pack(pady=(0, 10))

            # Save function
            def save_project():
                try:
                    # Validate inputs
                    name = name_entry.get().strip()
                    if not name:
                        messagebox.showerror("Validation Error", "Project name is required")
                        return

                    # Create project object
                    new_project = {
                        "name": name,
                        "type": type_combo.get(),
                        "start_date": datetime.strptime(start_date_entry.get(), "%Y-%m-%d"),
                        "deadline": datetime.strptime(deadline_entry.get(),
                                                      "%Y-%m-%d") if deadline_entry.get() else None,
                        "status": status_combo.get(),
                        "progress": 0,
                        "hours": float(hours_entry.get()) if hours_entry.get() else 0.0
                    }

                    # Save via service
                    project_id = self.project_service.create_project(new_project)
                    new_project["id"] = project_id

                    # Add to local list
                    self.projects.append(new_project)

                    # Add to treeview
                    self.tree.insert("", "end", values=(
                        project_id,
                        new_project["name"],
                        new_project["type"],
                        new_project["start_date"].strftime("%Y-%m-%d"),
                        new_project["deadline"].strftime("%Y-%m-%d") if new_project["deadline"] else "",
                        new_project["status"],
                        "0%",
                        new_project["hours"],
                    ))

                    # Update stats
                    self._update_stats()
                    self._update_timeline()

                    # Close dialog
                    dialog.destroy()

                    # Update status
                    self.status_var.set(f"Created new project: {name}")
                    logger.info(f"New project created: {name}")

                except ValueError as ve:
                    messagebox.showerror("Input Error", str(ve))
                except Exception as e:
                    messagebox.showerror("Save Error", f"Could not save project: {e}")
                    logger.error(f"Error saving project: {e}")

            # Save and Cancel buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Save", command=save_project).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

        except Exception as e:
            logger.error(f"Error opening new project dialog: {e}")
            messagebox.showerror("Error", f"Could not open new project dialog: {e}")

    def _edit_project(self):
        """Edit the currently selected project."""
        # Get selected project
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Edit Project", "Please select a project to edit")
            return

        try:
            # Get project details
            item_id = selected[0]
            values = self.tree.item(item_id, "values")
            project_id = int(values[0])

            # Retrieve full project details from service
            project = self.project_service.get_project_by_id(project_id)

            # Create edit dialog
            dialog = tk.Toplevel(self)
            dialog.title(f"Edit Project: {project.name}")
            dialog.geometry("500x600")
            dialog.transient(self)
            dialog.grab_set()

            # Project name
            ttk.Label(dialog, text="Project Name:").pack(pady=(10, 0))
            name_entry = ttk.Entry(dialog, width=50)
            name_entry.pack(pady=(0, 10))
            name_entry.insert(0, project.name)

            # Project type
            ttk.Label(dialog, text="Project Type:").pack(pady=(10, 0))
            type_combo = ttk.Combobox(dialog, values=[t.name for t in ProjectType], state="readonly")
            type_combo.pack(pady=(0, 10))
            type_combo.set(project.project_type)

            # Start date
            ttk.Label(dialog, text="Start Date:").pack(pady=(10, 0))
            start_date_entry = ttk.Entry(dialog, width=50)
            start_date_entry.pack(pady=(0, 10))
            start_date_entry.insert(0, project.start_date.strftime("%Y-%m-%d") if project.start_date else "")

            # Deadline
            ttk.Label(dialog, text="Deadline:").pack(pady=(10, 0))
            deadline_entry = ttk.Entry(dialog, width=50)
            deadline_entry.pack(pady=(0, 10))
            deadline_entry.insert(0, project.deadline.strftime("%Y-%m-%d") if project.deadline else "")

            # Status
            ttk.Label(dialog, text="Status:").pack(pady=(10, 0))
            status_combo = ttk.Combobox(dialog, values=[s.name for s in ProjectStatus], state="readonly")
            status_combo.pack(pady=(0, 10))
            status_combo.set(project.status)

            # Progress
            ttk.Label(dialog, text="Progress (%):").pack(pady=(10, 0))
            progress_entry = ttk.Entry(dialog, width=50)
            progress_entry.pack(pady=(0, 10))
            progress_entry.insert(0, str(project.progress))

            # Estimated hours
            ttk.Label(dialog, text="Estimated Hours:").pack(pady=(10, 0))
            hours_entry = ttk.Entry(dialog, width=50)
            hours_entry.pack(pady=(0, 10))
            hours_entry.insert(0, str(project.estimated_hours or 0.0))

            # Save function
            def save_changes():
                try:
                    # Validate inputs
                    name = name_entry.get().strip()
                    if not name:
                        messagebox.showerror("Validation Error", "Project name is required")
                        return

                    # Prepare updated project data
                    updated_project = {
                        "id": project_id,
                        "name": name,
                        "project_type": type_combo.get(),
                        "start_date": datetime.strptime(start_date_entry.get(),
                                                        "%Y-%m-%d") if start_date_entry.get() else None,
                        "deadline": datetime.strptime(deadline_entry.get(),
                                                      "%Y-%m-%d") if deadline_entry.get() else None,
                        "status": status_combo.get(),
                        "progress": int(progress_entry.get()) if progress_entry.get() else 0,
                        "estimated_hours": float(hours_entry.get()) if hours_entry.get() else 0.0
                    }

                    # Update via service
                    self.project_service.update_project(updated_project)

                    # Update local list and treeview
                    for i, proj in enumerate(self.projects):
                        if proj["id"] == project_id:
                            self.projects[i] = updated_project
                            break

                    # Update treeview item
                    self.tree.item(item_id, values=(
                        project_id,
                        updated_project["name"],
                        updated_project["project_type"],
                        updated_project["start_date"].strftime("%Y-%m-%d") if updated_project[
                            "start_date"] else "",
                        updated_project["deadline"].strftime("%Y-%m-%d") if updated_project["deadline"] else "",
                        updated_project["status"],
                        f"{updated_project['progress']}%",
                        updated_project["estimated_hours"],
                    ))

                    # Update stats and timeline
                    self._update_stats()
                    self._update_timeline()

                    # Close dialog
                    dialog.destroy()

                    # Update status
                    self.status_var.set(f"Updated project: {name}")
                    logger.info(f"Project updated: {name}")

                except ValueError as ve:
                    messagebox.showerror("Input Error", str(ve))
                except Exception as e:
                    messagebox.showerror("Update Error", f"Could not update project: {e}")
                    logger.error(f"Error updating project: {e}")

            # Save and Cancel buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Save Changes", command=save_changes).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)

        except Exception as e:
            logger.error(f"Error opening edit project dialog: {e}")
            messagebox.showerror("Error", f"Could not open edit project dialog: {e}")

    def _delete_project(self):
        """Delete the currently selected project."""
        # Get selected project
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Delete Project", "Please select a project to delete")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete the selected project?"):
            return

        try:
            # Get project details
            item_id = selected[0]
            values = self.tree.item(item_id, "values")
            project_id = int(values[0])
            project_name = values[1]

            # Delete project via service
            self.project_service.delete_project(project_id)

            # Remove from local list
            self.projects = [p for p in self.projects if p["id"] != project_id]

            # Remove from treeview
            self.tree.delete(item_id)

            # Update stats and timeline
            self._update_stats()
            self._update_timeline()

            # Update status
            self.status_var.set(f"Deleted project: {project_name}")
            logger.info(f"Project deleted: {project_name}")

        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            messagebox.showerror("Delete Error", f"Could not delete project: {e}")

    def _on_project_select(self, event):
        """Handle project selection in treeview.

        Args:
            event: The selection event.
        """
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        self.selected_project_id = int(values[0])

        # Update status bar with selected project info
        project_name = values[1]
        project_status = values[5]
        self.status_var.set(f"Selected: {project_name} (Status: {project_status})")

        logger.debug(f"Selected project ID {self.selected_project_id}")

    def _show_context_menu(self, event):
        """Show context menu for project actions.

        Args:
            event: The right-click event.
        """
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # Select the row that was right-clicked
        self.tree.selection_set(item_id)

        # Create context menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit Project", command=self._edit_project)
        menu.add_command(label="Delete Project", command=self._delete_project)

        # Add status submenu
        status_menu = tk.Menu(menu, tearoff=0)
        for status in ProjectStatus:
            status_menu.add_command(
                label=status.name,
                command=lambda s=status.name: self._change_project_status(s)
            )
        menu.add_cascade(label="Change Status", menu=status_menu)

        # Show the menu
        menu.post(event.x_root, event.y_root)

    def _change_project_status(self, new_status):
        """Change the status of the selected project.

        Args:
            new_status: The new status to set.
        """
        if self.selected_project_id is None:
            return

        try:
            # Find the project in local list
            project = next((p for p in self.projects if p["id"] == self.selected_project_id), None)
            if not project:
                return

            # Prepare update data
            update_data = {
                "id": self.selected_project_id,
                "status": new_status
            }

            # Update via service
            self.project_service.update_project_status(update_data)

            # Update local list
            project["status"] = new_status

            # Update the treeview
            for item_id in self.tree.get_children():
                values = list(self.tree.item(item_id, "values"))
                if int(values[0]) == self.selected_project_id:
                    values[5] = new_status
                    self.tree.item(item_id, values=values)
                    break

            # Update stats and timeline
            self._update_stats()
            self._update_timeline()

            logger.info(f"Changed project {self.selected_project_id} status to {new_status}")
            self.status_var.set(f"Changed project status to {new_status}")

        except Exception as e:
            logger.error(f"Error changing project status: {e}")
            messagebox.showerror("Status Change Error", f"Could not change project status: {e}")

    def _on_search(self, event=None):
        """Handle search in projects.

        Args:
            event: Optional event that triggered the search.
        """
        search_text = self.search_var.get().strip().lower()
        if not search_text:
            # If search is empty, show all items
            self._apply_filters()
            return

        # Clear current treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add only matching projects
        for project in self.projects:
            if (search_text in project["name"].lower() or
                    search_text in project["type"].lower() or
                    search_text in project["status"].lower()):
                self.tree.insert("", "end", values=(
                    project["id"],
                    project["name"],
                    project["type"],
                    project["start_date"].strftime("%Y-%m-%d") if project.get("start_date") else "",
                    project["deadline"].strftime("%Y-%m-%d") if project.get("deadline") else "",
                    project["status"],
                    f"{project['progress']}%",
                    project["hours"],
                ))

        self.status_var.set(f"Search results for: {search_text}")

    def _apply_filters(self, event=None):
        """Apply selected filters to the project list.

        Args:
            event: Optional event that triggered the filter change.
        """
        status_filter = self.status_filter.get()
        type_filter = self.type_filter.get()

        # Clear current treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add filtered projects
        for project in self.projects:
            # Apply status filter
            if status_filter != "All" and project["status"] != status_filter:
                continue

            # Apply type filter
            if type_filter != "All" and project["type"] != type_filter:
                continue

            # Add to treeview
            self.tree.insert("", "end", values=(
                project["id"],
                project["name"],
                project["type"],
                project["start_date"].strftime("%Y-%m-%d") if project.get("start_date") else "",
                project["deadline"].strftime("%Y-%m-%d") if project.get("deadline") else "",
                project["status"],
                f"{project['progress']}%",
                project["hours"],
            ))

        filter_text = []
        if status_filter != "All":
            filter_text.append(f"Status: {status_filter}")
        if type_filter != "All":
            filter_text.append(f"Type: {type_filter}")

        if filter_text:
            self.status_var.set(f"Filtered by {' and '.join(filter_text)}")
        else:
            self.status_var.set("Showing all projects")

    def _export_report(self):
        """Export project dashboard report."""
        try:
            # Open file dialog to choose export location
            export_file = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if not export_file:
                return  # User cancelled

            # Prepare export data
            export_data = []
            for project in self.projects:
                export_data.append({
                    "ID": project["id"],
                    "Name": project["name"],
                    "Type": project["type"],
                    "Start Date": project["start_date"].strftime("%Y-%m-%d") if project.get(
                        "start_date") else "",
                    "Deadline": project["deadline"].strftime("%Y-%m-%d") if project.get("deadline") else "",
                    "Status": project["status"],
                    "Progress": f"{project['progress']}%",
                    "Estimated Hours": project["hours"]
                })

            # Import pandas for CSV export (could use csv module as alternative)
            import pandas as pd

            # Convert to DataFrame and export
            df = pd.DataFrame(export_data)
            df.to_csv(export_file, index=False)

            logger.info(f"Exported project report to {export_file}")
            messagebox.showinfo("Export Successful", f"Project report exported to {export_file}")
            self.status_var.set(f"Exported report to {export_file}")

        except Exception as e:
            logger.error(f"Error exporting project report: {e}")
            messagebox.showerror("Export Error", f"Could not export project report: {e}")

    def on_refresh(self):
        """Refresh all project data."""
        try:
            # Reload projects from service
            self.load_projects()

            # Reapply current filters
            self._apply_filters()

            logger.info("Dashboard refreshed")
            self.status_var.set("Dashboard refreshed")

        except Exception as e:
            logger.error(f"Error refreshing dashboard: {e}")
            messagebox.showerror("Refresh Error", f"Could not refresh dashboard: {e}")

    def _update_timeline(self, event=None):
        """Update the timeline visualization.

        Args:
            event: Optional resize event that triggered the update.
        """
        try:
            canvas = self.timeline_canvas
            canvas.delete("all")

            # If no projects, show a message
            if not self.projects:
                canvas.create_text(
                    canvas.winfo_width() / 2,
                    canvas.winfo_height() / 2,
                    text="No projects to display",
                    font=("Helvetica", 12),
                    fill="#999999",
                )
                return

            # Determine the date range for all projects
            all_dates = []
            for project in self.projects:
                if project.get("start_date"):
                    all_dates.append(project["start_date"])
                if project.get("deadline"):
                    all_dates.append(project["deadline"])

            if not all_dates:
                canvas.create_text(
                    canvas.winfo_width() / 2,
                    canvas.winfo_height() / 2,
                    text="No valid project dates",
                    font=("Helvetica", 12),
                    fill="#999999",
                )
                return

            min_date = min(all_dates)
            max_date = max(all_dates)

            # Add some padding to the date range
            min_date = min_date - timedelta(days=3)
            max_date = max_date + timedelta(days=3)

            # Ensure a minimum span of 30 days
            if (max_date - min_date).days < 30:
                max_date = min_date + timedelta(days=30)

            # Layout constants
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            header_height = 30
            margin_left = 150
            margin_right = 20
            margin_bottom = 20
            row_height = 40
            timeline_width = canvas_width - margin_left - margin_right

            # Calculate days and pixels per day
            total_days = (max_date - min_date).days + 1
            pixels_per_day = timeline_width / total_days

            # Draw background grid
            y = header_height
            for i, project in enumerate(self.projects):
                # Alternating row colors
                fill = "#f5f5f5" if i % 2 == 0 else "white"
                canvas.create_rectangle(
                    0, y, canvas_width, y + row_height, fill=fill, outline=""
                )
                # Project name on the left
                canvas.create_text(
                    10, y + row_height / 2,
                    text=project["name"],
                    anchor="w",
                    font=("Helvetica", 10),
                )
                y += row_height

            # Draw timeline area background
            canvas.create_rectangle(
                margin_left, header_height,
                canvas_width - margin_right, y,
                fill="white", outline="#cccccc"
            )

            # Draw date grid and labels
            current_date = min_date
            day_counter = 0
            date_format = "%b %d"  # Format: "Jan 15"

            # Determine label frequency based on timeline length
            if total_days > 60:
                label_interval = 7  # Weekly labels for long timelines
            elif total_days > 30:
                label_interval = 3  # Every 3 days for medium timelines
            else:
                label_interval = 1  # Daily labels for short timelines

            while current_date <= max_date:
                x = margin_left + (day_counter * pixels_per_day)
                # Vertical grid line
                canvas.create_line(
                    x, header_height,
                    x, y,
                    fill="#eeeeee"
                )

                # Date label (only on certain intervals)
                if day_counter % label_interval == 0:
                    canvas.create_text(
                        x, header_height / 2,
                        text=current_date.strftime(date_format),
                        font=("Helvetica", 8)
                    )

                current_date += timedelta(days=1)
                day_counter += 1

            # Draw project timeline bars
            y = header_height
            for project in self.projects:
                # Skip projects without dates
                if not project.get("start_date") or not project.get("deadline"):
                    continue

                days_from_start = (project["start_date"] - min_date).days
                project_duration = (project["deadline"] - project["start_date"]).days + 1

                # Position calculations
                x1 = margin_left + (days_from_start * pixels_per_day)
                x2 = x1 + (project_duration * pixels_per_day)
                y1 = y + 5
                y2 = y + row_height - 5

                # Choose color based on project status
                if project["status"] == ProjectStatus.COMPLETED.name:
                    color = "#4CAF50"  # Green
                elif project["status"] == ProjectStatus.ON_HOLD.name:
                    color = "#FFC107"  # Amber
                elif project["status"] == ProjectStatus.CANCELLED.name:
                    color = "#F44336"  # Red
                else:
                    color = "#2196F3"  # Blue

                # Project background bar
                canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline="white",
                    tags=f"project_{project['id']}"
                )

                # Progress bar
                progress_width = (x2 - x1) * (project["progress"] / 100)
                if progress_width > 0:
                    canvas.create_rectangle(
                        x1, y1, x1 + progress_width, y2,
                        fill="#123456", outline="",
                        tags=f"progress_{project['id']}"
                    )

                # Add project name if there's enough space
                if (x2 - x1) > 50:
                    canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text=f"{project['name']} ({project['progress']}%",
                        font=("Helvetica", 9),
                        fill="white",
                        tags=f"label_{project['id']}"
                    )

                y += row_height

        except Exception as e:
            logger.error(f"Error updating timeline: {e}")
            messagebox.showerror("Timeline Error", f"Could not update timeline: {e}")

    def _update_stats(self):
        """Update project statistics based on current projects."""
        try:
            today = datetime.now()

            # Reset counters
            active_count = 0
            completed_count = 0
            on_hold_count = 0
            overdue_count = 0

            # Count projects by status and check for overdue
            for project in self.projects:
                # Status-based counting with fallback
                status = project.get("status", "")
                if status in [ProjectStatus.COMPLETED.name, "COMPLETED"]:
                    completed_count += 1
                elif status in [ProjectStatus.ON_HOLD.name, "ON_HOLD"]:
                    on_hold_count += 1
                elif status not in [ProjectStatus.COMPLETED.name, ProjectStatus.ON_HOLD.name, "COMPLETED", "ON_HOLD"]:
                    active_count += 1

                # Check for overdue projects
                deadline = project.get("deadline")
                if (deadline and
                        status not in [ProjectStatus.COMPLETED.name, "COMPLETED"] and
                        isinstance(deadline, datetime) and
                        deadline < today):
                    overdue_count += 1

            # Update statistics variables
            total_count = len(self.projects)

            # Update StringVars if they exist
            if hasattr(self, 'total_var'):
                self.total_var.set(str(total_count))
            if hasattr(self, 'active_var'):
                self.active_var.set(str(active_count))
            if hasattr(self, 'completed_var'):
                self.completed_var.set(str(completed_count))
            if hasattr(self, 'on_hold_var'):
                self.on_hold_var.set(str(on_hold_count))
            if hasattr(self, 'overdue_var'):
                self.overdue_var.set(str(overdue_count))

            # Store stats in dictionary
            self.stats = {
                "total": total_count,
                "active": active_count,
                "completed": completed_count,
                "on_hold": on_hold_count,
                "overdue": overdue_count,
            }

            logger.debug(f"Updated project stats: {self.stats}")

        except Exception as e:
            logger.error(f"Error updating project statistics: {e}", exc_info=True)
            # Reset all stats if there's an error
            if hasattr(self, 'total_var'):
                self.total_var.set("0")
            if hasattr(self, 'active_var'):
                self.active_var.set("0")
            if hasattr(self, 'completed_var'):
                self.completed_var.set("0")
            if hasattr(self, 'on_hold_var'):
                self.on_hold_var.set("0")
            if hasattr(self, 'overdue_var'):
                self.overdue_var.set("0")

            # Re-raise the exception to ensure it's noticed
            raise

    def _create_pie_chart(self, parent):
        """Create a pie chart showing project type distribution.

        This is a placeholder method that would typically use a charting library.
        """
        try:
            # Count project types
            type_counts = {}
            for project in self.projects:
                project_type = project.get("type", "Unknown")
                type_counts[project_type] = type_counts.get(project_type, 0) + 1

            # Create a basic canvas representation
            canvas = tk.Canvas(parent, bg="white")
            canvas.pack(fill=tk.BOTH, expand=True)

            # Get canvas dimensions
            width = canvas.winfo_reqwidth()
            height = canvas.winfo_reqheight()
            center_x = width // 2
            center_y = height // 2
            radius = min(width, height) // 3

            # Color palette
            colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']

            # Draw pie chart segments
            total = sum(type_counts.values())
            start_angle = 0
            for i, (type_name, count) in enumerate(type_counts.items()):
                percentage = count / total
                end_angle = start_angle + 360 * percentage
                color = colors[i % len(colors)]

                # Draw pie segment
                canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=start_angle, extent=end_angle - start_angle,
                    fill=color, outline='white'
                )

                # Add label
                mid_angle = (start_angle + end_angle) / 2
                label_x = center_x + radius * 0.7 * math.cos(math.radians(mid_angle))
                label_y = center_y - radius * 0.7 * math.sin(math.radians(mid_angle))
                canvas.create_text(
                    label_x, label_y,
                    text=f"{type_name}\n{count} ({percentage:.1%})",
                    font=("Helvetica", 8)
                )

                start_angle = end_angle

        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            canvas.create_text(
                center_x, center_y,
                text="Unable to create chart",
                font=("Helvetica", 10),
                fill="red"
            )

    def _export_detailed_report(self):
        """Generate a comprehensive project report."""
        try:
            # Open file dialog to choose export location
            export_file = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )

            if not export_file:
                return  # User cancelled

            # Prepare detailed export data
            export_data = []
            for project in self.projects:
                export_data.append({
                    "ID": project["id"],
                    "Name": project["name"],
                    "Type": project["type"],
                    "Start Date": project["start_date"].strftime("%Y-%m-%d") if project.get("start_date") else "",
                    "Deadline": project["deadline"].strftime("%Y-%m-%d") if project.get("deadline") else "",
                    "Status": project["status"],
                    "Progress": f"{project['progress']}%",
                    "Estimated Hours": project["hours"],
                    "Overdue": (project.get("deadline") and project["deadline"] < datetime.now()) if project.get(
                        "deadline") else False
                })

            # Import pandas for export flexibility
            import pandas as pd

            # Convert to DataFrame
            df = pd.DataFrame(export_data)

            # Export based on file extension
            if export_file.endswith('.xlsx'):
                df.to_excel(export_file, index=False, sheet_name='Projects')
            else:
                df.to_csv(export_file, index=False)

            # Optional: Add some summary statistics to the report
            summary = f"""
            Project Report Summary
            ---------------------
            Total Projects: {self.stats['total']}
            Active Projects: {self.stats['active']}
            Completed Projects: {self.stats['completed']}
            On Hold Projects: {self.stats['on_hold']}
            Overdue Projects: {self.stats['overdue']}

            Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """

            # Append summary to the file
            with open(export_file, 'a') as f:
                f.write("\n\n" + summary)

            logger.info(f"Exported detailed project report to {export_file}")
            messagebox.showinfo("Export Successful", f"Detailed project report exported to {export_file}")
            self.status_var.set(f"Exported detailed report to {export_file}")

        except Exception as e:
            logger.error(f"Error exporting detailed project report: {e}")
            messagebox.showerror("Export Error", f"Could not export detailed project report: {e}")

    # Add a main function for standalone testing
def main():
    """Main function to run the dashboard as a standalone application."""
    try:
        root = tk.Tk()
        root.title("Project Dashboard")
        root.geometry("1200x800")

        # Create a mock project service for testing
        project_service = IProjectService()

        # Create the dashboard
        dashboard = ProjectDashboard(root, None, project_service)
        dashboard.pack(fill=tk.BOTH, expand=True)

        # Start the main event loop
        root.mainloop()
    except Exception as e:
        logger.error(f"Fatal error in standalone run: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", str(e))

if __name__ == "__main__":
    main()