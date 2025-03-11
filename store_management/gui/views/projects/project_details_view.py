# gui/views/projects/project_details_view.py
"""
Project details view for creating, viewing, and editing project information.

This view provides a detailed interface for managing individual projects
with tabs for general info, components, status history, and timelines.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import ProjectStatus, ProjectType, SkillLevel
from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.utils.service_access import get_service
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.widgets.status_badge import StatusBadge


class ProjectDetailsView(BaseView):
    """
    View for displaying and editing the details of a project.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the project details view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                project_id: ID of the project to view/edit (None for new projects)
                create_new: Whether to create a new project
                readonly: Whether the view should be read-only
        """
        super().__init__(parent)
        self.title = "Project Details"
        self.icon = "📋"
        self.logger = logging.getLogger(__name__)

        # Store view parameters
        self.project_id = kwargs.get("project_id")
        self.create_new = kwargs.get("create_new", False)
        self.readonly = kwargs.get("readonly", False)

        if self.create_new:
            self.title = "New Project"
            self.readonly = False
        elif self.readonly:
            self.title = "View Project"
        else:
            self.title = "Edit Project"

        # Initialize services
        self.project_service = get_service("project_service")
        self.customer_service = get_service("customer_service")

        # Initialize form variables
        self.form_vars = {}
        self.status_history = []
        self.components = []

        # Build the view
        self.build()

        # Subscribe to events
        subscribe("project_updated", self.on_project_updated)
        subscribe("component_updated", self.on_component_updated)

        # Load data if viewing or editing an existing project
        if self.project_id:
            self.load_project()

    def build(self):
        """Build the project details view."""
        super().build()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.info_tab = ttk.Frame(self.notebook)
        self.components_tab = ttk.Frame(self.notebook)
        self.status_history_tab = ttk.Frame(self.notebook)
        self.resources_tab = ttk.Frame(self.notebook)
        self.timeline_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.info_tab, text="General Info")
        self.notebook.add(self.components_tab, text="Components")
        self.notebook.add(self.status_history_tab, text="Status History")
        self.notebook.add(self.resources_tab, text="Resources")
        self.notebook.add(self.timeline_tab, text="Timeline")

        # Create content for each tab
        self.create_info_tab()
        self.create_components_tab()
        self.create_status_history_tab()
        self.create_resources_tab()
        self.create_timeline_tab()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        actions_frame = ttk.Frame(self.header)
        actions_frame.pack(side=tk.RIGHT, padx=10)

        # In read-only mode, show Edit button
        if self.readonly:
            ttk.Button(
                actions_frame,
                text="Edit",
                command=self.on_edit
            ).pack(side=tk.RIGHT, padx=5)
        else:
            # In edit mode, show Save and Cancel buttons
            ttk.Button(
                actions_frame,
                text="Save",
                command=self.on_save
            ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Back",
            command=self.on_back
        ).pack(side=tk.RIGHT, padx=5)

    def create_info_tab(self):
        """Create the general information tab content."""
        frame = ttk.Frame(self.info_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create two-column layout
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Left column: Basic information
        basic_info_frame = ttk.LabelFrame(left_frame, text="Project Information")
        basic_info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create form fields
        row = 0

        # Project name
        ttk.Label(basic_info_frame, text="Project Name:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["name"] = tk.StringVar()
        name_entry = ttk.Entry(basic_info_frame, textvariable=self.form_vars["name"], width=30)
        name_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        name_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")
        row += 1

        # Project type
        ttk.Label(basic_info_frame, text="Project Type:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["type"] = tk.StringVar()
        type_combo = ttk.Combobox(basic_info_frame, textvariable=self.form_vars["type"], width=28)
        type_combo["values"] = [t.value.replace("_", " ").title() for t in ProjectType]
        type_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        type_combo.configure(state="readonly" if not self.readonly else tk.DISABLED)
        row += 1

        # Status
        ttk.Label(basic_info_frame, text="Status:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        status_frame = ttk.Frame(basic_info_frame)
        status_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        self.form_vars["status"] = tk.StringVar()
        self.status_badge = StatusBadge(status_frame, "New", "new")
        self.status_badge.pack(side=tk.LEFT)

        if not self.readonly and not self.create_new:
            ttk.Button(
                status_frame,
                text="Update Status",
                command=self.on_update_status,
                width=15
            ).pack(side=tk.LEFT, padx=(10, 0))
        row += 1

        # Skill level
        ttk.Label(basic_info_frame, text="Skill Level:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["skill_level"] = tk.StringVar()
        skill_combo = ttk.Combobox(basic_info_frame, textvariable=self.form_vars["skill_level"], width=28)
        skill_combo["values"] = [s.value.title() for s in SkillLevel]
        skill_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        skill_combo.configure(state="readonly" if not self.readonly else tk.DISABLED)
        row += 1

        # Description
        ttk.Label(basic_info_frame, text="Description:").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=5)
        self.description_text = tk.Text(basic_info_frame, width=30, height=5)
        self.description_text.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        self.description_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)
        row += 1

        # Right column: Dates, customer, and other details
        dates_frame = ttk.LabelFrame(right_frame, text="Dates and Customer")
        dates_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        row = 0

        # Start date
        ttk.Label(dates_frame, text="Start Date:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["start_date"] = tk.StringVar()
        start_date_frame = ttk.Frame(dates_frame)
        start_date_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        start_date_entry = ttk.Entry(start_date_frame, textvariable=self.form_vars["start_date"], width=15)
        start_date_entry.pack(side=tk.LEFT)
        start_date_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

        if not self.readonly:
            ttk.Button(
                start_date_frame,
                text="...",
                command=lambda: self.show_date_picker(self.form_vars["start_date"]),
                width=3
            ).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # End date
        ttk.Label(dates_frame, text="Due Date:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["end_date"] = tk.StringVar()
        end_date_frame = ttk.Frame(dates_frame)
        end_date_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        end_date_entry = ttk.Entry(end_date_frame, textvariable=self.form_vars["end_date"], width=15)
        end_date_entry.pack(side=tk.LEFT)
        end_date_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

        if not self.readonly:
            ttk.Button(
                end_date_frame,
                text="...",
                command=lambda: self.show_date_picker(self.form_vars["end_date"]),
                width=3
            ).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # Customer
        ttk.Label(dates_frame, text="Customer:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["customer_id"] = tk.StringVar()
        self.form_vars["customer_name"] = tk.StringVar()

        customer_frame = ttk.Frame(dates_frame)
        customer_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        customer_entry = ttk.Entry(customer_frame, textvariable=self.form_vars["customer_name"], width=15)
        customer_entry.pack(side=tk.LEFT)
        customer_entry.configure(state="readonly")

        if not self.readonly:
            ttk.Button(
                customer_frame,
                text="...",
                command=self.select_customer,
                width=3
            ).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # Notes
        notes_frame = ttk.LabelFrame(right_frame, text="Notes")
        notes_frame.pack(fill=tk.BOTH, expand=True)

        self.notes_text = tk.Text(notes_frame, width=30, height=5)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notes_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)

    def create_components_tab(self):
        """Create the components tab content."""
        frame = ttk.Frame(self.components_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Header with actions
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Project Components",
            font=("TkDefaultFont", 12, "bold")
        ).pack(side=tk.LEFT)

        if not self.readonly:
            ttk.Button(
                header_frame,
                text="Add Component",
                command=self.on_add_component
            ).pack(side=tk.RIGHT, padx=5)

        # Components treeview
        self.components_tree = EnhancedTreeview(
            frame,
            columns=("id", "component_name", "type", "quantity", "status", "assigned_to"),
            height=10
        )

        self.components_tree.heading("id", text="ID")
        self.components_tree.heading("component_name", text="Component")
        self.components_tree.heading("type", text="Type")
        self.components_tree.heading("quantity", text="Quantity")
        self.components_tree.heading("status", text="Status")
        self.components_tree.heading("assigned_to", text="Assigned To")

        self.components_tree.column("id", width=50, minwidth=50)
        self.components_tree.column("component_name", width=200, minwidth=150)
        self.components_tree.column("type", width=100, minwidth=100)
        self.components_tree.column("quantity", width=80, minwidth=80)
        self.components_tree.column("status", width=100, minwidth=100)
        self.components_tree.column("assigned_to", width=150, minwidth=150)

        self.components_tree.pack(fill=tk.BOTH, expand=True)

        # Component actions
        actions_frame = ttk.Frame(frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            actions_frame,
            text="View Component",
            command=self.on_view_component,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            ttk.Button(
                actions_frame,
                text="Edit Component",
                command=self.on_edit_component,
                state=tk.DISABLED
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                actions_frame,
                text="Remove Component",
                command=self.on_remove_component,
                state=tk.DISABLED
            ).pack(side=tk.LEFT, padx=5)

        # Material requirements summary
        summary_frame = ttk.LabelFrame(frame, text="Material Requirements Summary")
        summary_frame.pack(fill=tk.X, pady=(10, 0))

        self.materials_summary_tree = EnhancedTreeview(
            summary_frame,
            columns=("material", "type", "total_quantity", "unit", "available", "status"),
            height=5
        )

        self.materials_summary_tree.heading("material", text="Material")
        self.materials_summary_tree.heading("type", text="Type")
        self.materials_summary_tree.heading("total_quantity", text="Total Quantity")
        self.materials_summary_tree.heading("unit", text="Unit")
        self.materials_summary_tree.heading("available", text="Available")
        self.materials_summary_tree.heading("status", text="Status")

        self.materials_summary_tree.column("material", width=200, minwidth=150)
        self.materials_summary_tree.column("type", width=100, minwidth=100)
        self.materials_summary_tree.column("total_quantity", width=100, minwidth=100)
        self.materials_summary_tree.column("unit", width=80, minwidth=80)
        self.materials_summary_tree.column("available", width=80, minwidth=80)
        self.materials_summary_tree.column("status", width=100, minwidth=100)

        self.materials_summary_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Bind selection events
        self.components_tree.bind("<<TreeviewSelect>>", self.on_component_select)

    def create_status_history_tab(self):
        """Create the status history tab content."""
        frame = ttk.Frame(self.status_history_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Status history treeview
        self.status_history_tree = EnhancedTreeview(
            frame,
            columns=("timestamp", "old_status", "new_status", "user", "notes"),
            height=15
        )

        self.status_history_tree.heading("timestamp", text="Timestamp")
        self.status_history_tree.heading("old_status", text="Previous Status")
        self.status_history_tree.heading("new_status", text="New Status")
        self.status_history_tree.heading("user", text="Updated By")
        self.status_history_tree.heading("notes", text="Notes")

        self.status_history_tree.column("timestamp", width=150, minwidth=150)
        self.status_history_tree.column("old_status", width=120, minwidth=120)
        self.status_history_tree.column("new_status", width=120, minwidth=120)
        self.status_history_tree.column("user", width=120, minwidth=120)
        self.status_history_tree.column("notes", width=300, minwidth=200)

        self.status_history_tree.pack(fill=tk.BOTH, expand=True)

    def create_resources_tab(self):
        """Create the resources tab content."""
        frame = ttk.Frame(self.resources_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for resource tabs
        resource_notebook = ttk.Notebook(frame)
        resource_notebook.pack(fill=tk.BOTH, expand=True)

        # Create resource tabs
        picking_list_tab = ttk.Frame(resource_notebook)
        tool_list_tab = ttk.Frame(resource_notebook)
        documents_tab = ttk.Frame(resource_notebook)

        resource_notebook.add(picking_list_tab, text="Picking Lists")
        resource_notebook.add(tool_list_tab, text="Tool Lists")
        resource_notebook.add(documents_tab, text="Documents")

        # Picking lists
        self.create_picking_lists_tab(picking_list_tab)

        # Tool lists
        self.create_tool_lists_tab(tool_list_tab)

        # Documents
        self.create_documents_tab(documents_tab)

    def create_picking_lists_tab(self, parent):
        """Create the picking lists tab content.

        Args:
            parent: The parent widget for the tab content
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Label(
            header_frame,
            text="Material Picking Lists",
            font=("TkDefaultFont", 11, "bold")
        ).pack(side=tk.LEFT)

        if not self.readonly and not self.create_new:
            ttk.Button(
                header_frame,
                text="Create Picking List",
                command=self.on_create_picking_list
            ).pack(side=tk.RIGHT, padx=5)

        # Picking lists treeview
        self.picking_lists_tree = EnhancedTreeview(
            parent,
            columns=("id", "created_at", "status", "items_count", "progress"),
            height=8
        )

        self.picking_lists_tree.heading("id", text="ID")
        self.picking_lists_tree.heading("created_at", text="Created")
        self.picking_lists_tree.heading("status", text="Status")
        self.picking_lists_tree.heading("items_count", text="Items")
        self.picking_lists_tree.heading("progress", text="Progress")

        self.picking_lists_tree.column("id", width=50, minwidth=50)
        self.picking_lists_tree.column("created_at", width=150, minwidth=150)
        self.picking_lists_tree.column("status", width=120, minwidth=120)
        self.picking_lists_tree.column("items_count", width=80, minwidth=80)
        self.picking_lists_tree.column("progress", width=150, minwidth=150)

        self.picking_lists_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Actions frame
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(5, 10))

        self.view_picking_list_btn = ttk.Button(
            actions_frame,
            text="View Picking List",
            command=self.on_view_picking_list,
            state=tk.DISABLED
        )
        self.view_picking_list_btn.pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            self.update_picking_list_btn = ttk.Button(
                actions_frame,
                text="Update Picking List",
                command=self.on_update_picking_list,
                state=tk.DISABLED
            )
            self.update_picking_list_btn.pack(side=tk.LEFT, padx=5)

        # Bind selection event
        self.picking_lists_tree.bind("<<TreeviewSelect>>", self.on_picking_list_select)

    def create_tool_lists_tab(self, parent):
        """Create the tool lists tab content.

        Args:
            parent: The parent widget for the tab content
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Label(
            header_frame,
            text="Tool Lists",
            font=("TkDefaultFont", 11, "bold")
        ).pack(side=tk.LEFT)

        if not self.readonly and not self.create_new:
            ttk.Button(
                header_frame,
                text="Create Tool List",
                command=self.on_create_tool_list
            ).pack(side=tk.RIGHT, padx=5)

        # Tool lists treeview
        self.tool_lists_tree = EnhancedTreeview(
            parent,
            columns=("id", "created_at", "status", "tools_count", "progress"),
            height=8
        )

        self.tool_lists_tree.heading("id", text="ID")
        self.tool_lists_tree.heading("created_at", text="Created")
        self.tool_lists_tree.heading("status", text="Status")
        self.tool_lists_tree.heading("tools_count", text="Tools")
        self.tool_lists_tree.heading("progress", text="Progress")

        self.tool_lists_tree.column("id", width=50, minwidth=50)
        self.tool_lists_tree.column("created_at", width=150, minwidth=150)
        self.tool_lists_tree.column("status", width=120, minwidth=120)
        self.tool_lists_tree.column("tools_count", width=80, minwidth=80)
        self.tool_lists_tree.column("progress", width=150, minwidth=150)

        self.tool_lists_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Actions frame
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(5, 10))

        self.view_tool_list_btn = ttk.Button(
            actions_frame,
            text="View Tool List",
            command=self.on_view_tool_list,
            state=tk.DISABLED
        )
        self.view_tool_list_btn.pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            self.update_tool_list_btn = ttk.Button(
                actions_frame,
                text="Update Tool List",
                command=self.on_update_tool_list,
                state=tk.DISABLED
            )
            self.update_tool_list_btn.pack(side=tk.LEFT, padx=5)

        # Bind selection event
        self.tool_lists_tree.bind("<<TreeviewSelect>>", self.on_tool_list_select)

    def create_documents_tab(self, parent):
        """Create the documents tab content.

        Args:
            parent: The parent widget for the tab content
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(10, 10))

        ttk.Label(
            header_frame,
            text="Project Documents",
            font=("TkDefaultFont", 11, "bold")
        ).pack(side=tk.LEFT)

        if not self.readonly:
            ttk.Button(
                header_frame,
                text="Upload Document",
                command=self.on_upload_document
            ).pack(side=tk.RIGHT, padx=5)

        # Documents treeview
        self.documents_tree = EnhancedTreeview(
            parent,
            columns=("id", "name", "type", "size", "uploaded_at", "uploaded_by"),
            height=8
        )

        self.documents_tree.heading("id", text="ID")
        self.documents_tree.heading("name", text="Document Name")
        self.documents_tree.heading("type", text="Type")
        self.documents_tree.heading("size", text="Size")
        self.documents_tree.heading("uploaded_at", text="Uploaded")
        self.documents_tree.heading("uploaded_by", text="Uploaded By")

        self.documents_tree.column("id", width=50, minwidth=50)
        self.documents_tree.column("name", width=200, minwidth=150)
        self.documents_tree.column("type", width=80, minwidth=80)
        self.documents_tree.column("size", width=80, minwidth=80)
        self.documents_tree.column("uploaded_at", width=150, minwidth=150)
        self.documents_tree.column("uploaded_by", width=120, minwidth=120)

        self.documents_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        # Actions frame
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(5, 10))

        self.view_document_btn = ttk.Button(
            actions_frame,
            text="View Document",
            command=self.on_view_document,
            state=tk.DISABLED
        )
        self.view_document_btn.pack(side=tk.LEFT, padx=5)

        self.download_document_btn = ttk.Button(
            actions_frame,
            text="Download",
            command=self.on_download_document,
            state=tk.DISABLED
        )
        self.download_document_btn.pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            self.delete_document_btn = ttk.Button(
                actions_frame,
                text="Delete",
                command=self.on_delete_document,
                state=tk.DISABLED
            )
            self.delete_document_btn.pack(side=tk.LEFT, padx=5)

        # Bind selection event
        self.documents_tree.bind("<<TreeviewSelect>>", self.on_document_select)

    def create_timeline_tab(self):
        """Create the timeline tab content."""
        frame = ttk.Frame(self.timeline_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(
            frame,
            text="Project Timeline",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        # Timeline visualization will be a canvas
        self.timeline_canvas = tk.Canvas(frame, bg="white", height=300)
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True)

        # Timeline controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(controls_frame, text="Zoom:").pack(side=tk.LEFT, padx=(0, 5))

        self.zoom_var = tk.StringVar(value="Month")
        zoom_combo = ttk.Combobox(controls_frame, textvariable=self.zoom_var, width=10, state="readonly")
        zoom_combo["values"] = ["Day", "Week", "Month", "Quarter", "Year"]
        zoom_combo.pack(side=tk.LEFT, padx=5)
        zoom_combo.bind("<<ComboboxSelected>>", self.on_zoom_change)

        ttk.Button(
            controls_frame,
            text="Print Timeline",
            command=self.on_print_timeline
        ).pack(side=tk.RIGHT, padx=5)

    def load_project(self):
        """Load project data from the service."""
        try:
            # Get project data from service
            project = self.project_service.get_project(
                self.project_id,
                include_components=True,
                include_status_history=True,
                include_picking_lists=True,
                include_tool_lists=True,
                include_documents=True
            )

            if not project:
                messagebox.showerror("Error", f"Project not found with ID {self.project_id}")
                self.on_back()
                return

            # Update title
            self.title = f"{project.name} - {'View' if self.readonly else 'Edit'} Project"
            project_name_label = self.header.winfo_children()[0]
            if isinstance(project_name_label, ttk.Label):
                project_name_label.configure(text=self.title)

            # Populate form variables
            self.form_vars["name"].set(project.name)

            type_str = project.type.value.replace("_", " ").title() if hasattr(project, 'type') and project.type else ""
            self.form_vars["type"].set(type_str)

            status_str = project.status.value.replace("_", " ").title() if hasattr(project,
                                                                                   'status') and project.status else ""
            self.status_badge.set_text(status_str,
                                       project.status.value if hasattr(project, 'status') and project.status else None)

            skill_level_str = project.skill_level.value.title() if hasattr(project,
                                                                           'skill_level') and project.skill_level else ""
            self.form_vars["skill_level"].set(skill_level_str)

            # Description
            if hasattr(project, 'description') and project.description:
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert("1.0", project.description)

            # Notes
            if hasattr(project, 'notes') and project.notes:
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", project.notes)

            # Dates
            if hasattr(project, 'start_date') and project.start_date:
                self.form_vars["start_date"].set(project.start_date.strftime("%Y-%m-%d"))

            if hasattr(project, 'end_date') and project.end_date:
                self.form_vars["end_date"].set(project.end_date.strftime("%Y-%m-%d"))

            # Customer information
            if hasattr(project, 'customer') and project.customer:
                self.form_vars["customer_id"].set(str(project.customer.id))
                customer_name = f"{project.customer.first_name} {project.customer.last_name}"
                self.form_vars["customer_name"].set(customer_name)

            # Store components
            if hasattr(project, 'components'):
                self.components = project.components
                self.update_components_list()

            # Store status history
            if hasattr(project, 'status_history'):
                self.status_history = project.status_history
                self.update_status_history_list()

            # Update picking lists
            if hasattr(project, 'picking_lists'):
                self.update_picking_lists(project.picking_lists)

            # Update tool lists
            if hasattr(project, 'tool_lists'):
                self.update_tool_lists(project.tool_lists)

            # Update documents
            if hasattr(project, 'documents'):
                self.update_documents(project.documents)

            # Draw timeline
            self.draw_timeline()

        except Exception as e:
            self.logger.error(f"Error loading project: {e}")
            messagebox.showerror("Error", f"Failed to load project: {str(e)}")

    def update_components_list(self):
        """Update the components list in the treeview."""
        # Clear existing items
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)

        # Insert components
        for component in self.components:
            # Extract component values
            component_id = component.id if hasattr(component, 'id') else "N/A"
            component_name = component.name if hasattr(component, 'name') else "Unnamed"

            component_type = ""
            if hasattr(component, 'type') and component.type:
                component_type = component.type.value.replace("_", " ").title()

            quantity = component.quantity if hasattr(component, 'quantity') else 1

            status = "Not Started"
            if hasattr(component, 'status') and component.status:
                status = component.status.replace("_", " ").title()

            assigned_to = "Unassigned"
            if hasattr(component, 'assigned_to') and component.assigned_to:
                assigned_to = component.assigned_to

            # Insert into treeview
            self.components_tree.insert(
                '', 'end',
                iid=component_id,
                values=(component_id, component_name, component_type, quantity, status, assigned_to)
            )

        # Update material requirements summary
        self.update_material_requirements()

    def update_material_requirements(self):
        """Update the material requirements summary."""
        # Clear existing items
        for item in self.materials_summary_tree.get_children():
            self.materials_summary_tree.delete(item)

        # Calculate material requirements
        material_requirements = {}
        for component in self.components:
            if hasattr(component, 'materials'):
                for material in component.materials:
                    material_id = material.material_id if hasattr(material, 'material_id') else material.id
                    quantity = material.quantity if hasattr(material, 'quantity') else 1

                    if material_id in material_requirements:
                        material_requirements[material_id]['quantity'] += quantity
                    else:
                        material_name = material.name if hasattr(material, 'name') else "Unknown"
                        material_type = "Unknown"
                        if hasattr(material, 'type') and material.type:
                            material_type = material.type.value.replace("_", " ").title()

                        unit = "piece"
                        if hasattr(material, 'unit') and material.unit:
                            unit = material.unit.value

                        material_requirements[material_id] = {
                            'name': material_name,
                            'type': material_type,
                            'quantity': quantity,
                            'unit': unit,
                            'available': 0,
                            'status': "Not Checked"
                        }

        # Get inventory availability
        if material_requirements and not self.create_new:
            try:
                inventory_status = self.project_service.check_material_availability(
                    self.project_id, list(material_requirements.keys())
                )

                # Update availability information
                for material_id, info in inventory_status.items():
                    if material_id in material_requirements:
                        material_requirements[material_id]['available'] = info.get('available', 0)
                        material_requirements[material_id]['status'] = info.get('status', "Not Available")

            except Exception as e:
                self.logger.error(f"Error checking material availability: {e}")

        # Insert into treeview
        for material_id, info in material_requirements.items():
            status = info['status']
            tag = "available" if status == "Available" else "unavailable" if status == "Not Available" else ""

            self.materials_summary_tree.insert(
                '', 'end',
                values=(
                    info['name'],
                    info['type'],
                    info['quantity'],
                    info['unit'],
                    info['available'],
                    status
                ),
                tags=(tag,)
            )

        # Configure tags
        self.materials_summary_tree.tag_configure("available", background=COLORS['success_light'])
        self.materials_summary_tree.tag_configure("unavailable", background=COLORS['error_light'])

    def update_status_history_list(self):
        """Update the status history list in the treeview."""
        # Clear existing items
        for item in self.status_history_tree.get_children():
            self.status_history_tree.delete(item)

        # Insert status history entries, newest first
        for idx, entry in enumerate(
                sorted(self.status_history, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else 0, reverse=True)):
            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(entry,
                                                                              'timestamp') and entry.timestamp else "N/A"

            old_status = ""
            if hasattr(entry, 'old_status') and entry.old_status:
                old_status = entry.old_status.replace("_", " ").title()

            new_status = ""
            if hasattr(entry, 'new_status') and entry.new_status:
                new_status = entry.new_status.replace("_", " ").title()

            user = entry.user_name if hasattr(entry, 'user_name') and entry.user_name else "System"
            notes = entry.notes if hasattr(entry, 'notes') and entry.notes else ""

            self.status_history_tree.insert(
                '', 'end',
                iid=f"history_{idx}",
                values=(timestamp, old_status, new_status, user, notes)
            )

    def update_picking_lists(self, picking_lists):
        """Update the picking lists treeview.

        Args:
            picking_lists: List of picking lists to display
        """
        # Clear existing items
        for item in self.picking_lists_tree.get_children():
            self.picking_lists_tree.delete(item)

        # Insert picking lists
        for picking_list in picking_lists:
            list_id = picking_list.id if hasattr(picking_list, 'id') else "N/A"

            created_at = "N/A"
            if hasattr(picking_list, 'created_at') and picking_list.created_at:
                created_at = picking_list.created_at.strftime("%Y-%m-%d %H:%M")

            status = "Unknown"
            if hasattr(picking_list, 'status') and picking_list.status:
                status = picking_list.status.value.replace("_", " ").title()

            items_count = 0
            if hasattr(picking_list, 'items') and picking_list.items:
                items_count = len(picking_list.items)

            progress = "0%"
            if hasattr(picking_list, 'progress') and picking_list.progress is not None:
                progress = f"{picking_list.progress}%"

            self.picking_lists_tree.insert(
                '', 'end',
                iid=list_id,
                values=(list_id, created_at, status, items_count, progress)
            )

    def update_tool_lists(self, tool_lists):
        """Update the tool lists treeview.

        Args:
            tool_lists: List of tool lists to display
        """
        # Clear existing items
        for item in self.tool_lists_tree.get_children():
            self.tool_lists_tree.delete(item)

        # Insert tool lists
        for tool_list in tool_lists:
            list_id = tool_list.id if hasattr(tool_list, 'id') else "N/A"

            created_at = "N/A"
            if hasattr(tool_list, 'created_at') and tool_list.created_at:
                created_at = tool_list.created_at.strftime("%Y-%m-%d %H:%M")

            status = "Unknown"
            if hasattr(tool_list, 'status') and tool_list.status:
                status = tool_list.status.value.replace("_", " ").title()

            tools_count = 0
            if hasattr(tool_list, 'items') and tool_list.items:
                tools_count = len(tool_list.items)

            progress = "0%"
            if hasattr(tool_list, 'progress') and tool_list.progress is not None:
                progress = f"{tool_list.progress}%"

            self.tool_lists_tree.insert(
                '', 'end',
                iid=list_id,
                values=(list_id, created_at, status, tools_count, progress)
            )

    def update_documents(self, documents):
        """Update the documents treeview.

        Args:
            documents: List of documents to display
        """
        # Clear existing items
        for item in self.documents_tree.get_children():
            self.documents_tree.delete(item)

        # Insert documents
        for document in documents:
            doc_id = document.id if hasattr(document, 'id') else "N/A"
            name = document.name if hasattr(document, 'name') else "Unnamed"

            doc_type = "Unknown"
            if hasattr(document, 'file_type') and document.file_type:
                doc_type = document.file_type.upper()

            size = "0 KB"
            if hasattr(document, 'file_size') and document.file_size:
                size = self.format_file_size(document.file_size)

            uploaded_at = "N/A"
            if hasattr(document, 'uploaded_at') and document.uploaded_at:
                uploaded_at = document.uploaded_at.strftime("%Y-%m-%d %H:%M")

            uploaded_by = "Unknown"
            if hasattr(document, 'uploaded_by') and document.uploaded_by:
                uploaded_by = document.uploaded_by

            self.documents_tree.insert(
                '', 'end',
                iid=doc_id,
                values=(doc_id, name, doc_type, size, uploaded_at, uploaded_by)
            )

    def format_file_size(self, size_bytes):
        """Format file size for display.

        Args:
            size_bytes: The file size in bytes

        Returns:
            A formatted string with appropriate units
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def draw_timeline(self):
        """Draw the project timeline visualization."""
        if not hasattr(self, 'timeline_canvas'):
            return

        # Clear canvas
        self.timeline_canvas.delete("all")

        # If this is a new project, show placeholder
        if self.create_new:
            self.timeline_canvas.create_text(
                self.timeline_canvas.winfo_width() // 2,
                self.timeline_canvas.winfo_height() // 2,
                text="Timeline will be available after saving the project",
                font=("TkDefaultFont", 12)
            )
            return

        # Get project timeline data
        try:
            timeline_data = self.project_service.get_project_timeline(self.project_id)

            if not timeline_data:
                self.timeline_canvas.create_text(
                    self.timeline_canvas.winfo_width() // 2,
                    self.timeline_canvas.winfo_height() // 2,
                    text="No timeline data available",
                    font=("TkDefaultFont", 12)
                )
                return

            # Draw timeline based on timeline_data
            # This is a simplified placeholder - in a real implementation,
            # you would draw a proper Gantt chart or similar visualization

            # Draw project timeline
            margin = 50
            timeline_height = 100

            # Calculate timeline width
            canvas_width = self.timeline_canvas.winfo_width()
            timeline_width = canvas_width - (2 * margin)

            # Draw timeline line
            self.timeline_canvas.create_line(
                margin, timeline_height,
                margin + timeline_width, timeline_height,
                width=2
            )

            # Get start and end dates
            start_date = datetime.datetime.strptime(self.form_vars["start_date"].get(), "%Y-%m-%d") if self.form_vars[
                "start_date"].get() else datetime.datetime.now()
            end_date = datetime.datetime.strptime(self.form_vars["end_date"].get(), "%Y-%m-%d") if self.form_vars[
                "end_date"].get() else start_date + datetime.timedelta(days=30)

            # Draw timeline segments for status changes
            if "status_changes" in timeline_data:
                status_points = timeline_data["status_changes"]

                # Helper function to map date to x position
                def date_to_x(date):
                    total_days = (end_date - start_date).days
                    if total_days == 0:
                        return margin
                    days_from_start = (date - start_date).days
                    return margin + (days_from_start / total_days) * timeline_width

                # Sort status changes by date
                sorted_points = sorted(status_points, key=lambda x: x.get("date", start_date))

                # Draw timeline events
                for i, point in enumerate(sorted_points):
                    event_date = point.get("date", start_date)
                    status = point.get("status", "unknown").replace("_", " ").title()

                    x_pos = date_to_x(event_date)

                    # Draw milestone
                    self.timeline_canvas.create_oval(
                        x_pos - 5, timeline_height - 5,
                        x_pos + 5, timeline_height + 5,
                        fill=COLORS["primary"]
                    )

                    # Draw status text
                    self.timeline_canvas.create_text(
                        x_pos,
                        timeline_height - 20,
                        text=status,
                        anchor=tk.S,
                        font=("TkDefaultFont", 8)
                    )

                    # Draw date text
                    self.timeline_canvas.create_text(
                        x_pos,
                        timeline_height + 20,
                        text=event_date.strftime("%Y-%m-%d"),
                        anchor=tk.N,
                        font=("TkDefaultFont", 8)
                    )

                    # Connect milestones with lines
                    if i > 0:
                        prev_x = date_to_x(sorted_points[i - 1].get("date", start_date))
                        self.timeline_canvas.create_line(
                            prev_x, timeline_height,
                            x_pos, timeline_height,
                            width=2,
                            fill=COLORS["primary"]
                        )

            # Draw today's marker if within project timeframe
            today = datetime.datetime.now()
            if start_date <= today <= end_date:
                today_x = margin + ((today - start_date).days / (end_date - start_date).days) * timeline_width

                self.timeline_canvas.create_line(
                    today_x, timeline_height - 30,
                    today_x, timeline_height + 30,
                    width=2,
                    dash=(4, 2),
                    fill="red"
                )

                self.timeline_canvas.create_text(
                    today_x,
                    timeline_height - 40,
                    text="Today",
                    anchor=tk.S,
                    font=("TkDefaultFont", 9, "bold"),
                    fill="red"
                )

        except Exception as e:
            self.logger.error(f"Error drawing timeline: {e}")
            self.timeline_canvas.create_text(
                self.timeline_canvas.winfo_width() // 2,
                self.timeline_canvas.winfo_height() // 2,
                text=f"Error loading timeline: {str(e)}",
                font=("TkDefaultFont", 10)
            )

    def collect_form_data(self):
        """Collect data from form fields.

        Returns:
            Dictionary of form data
        """
        data = {}

        # Basic fields
        data["name"] = self.form_vars["name"].get()

        # Convert display values back to enum values
        type_str = self.form_vars["type"].get()
        if type_str:
            data["type"] = type_str.lower().replace(" ", "_")

        skill_level_str = self.form_vars["skill_level"].get()
        if skill_level_str:
            data["skill_level"] = skill_level_str.lower()

        # Text fields
        data["description"] = self.description_text.get("1.0", tk.END).strip()
        data["notes"] = self.notes_text.get("1.0", tk.END).strip()

        # Dates
        start_date_str = self.form_vars["start_date"].get()
        if start_date_str:
            try:
                data["start_date"] = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                pass

        end_date_str = self.form_vars["end_date"].get()
        if end_date_str:
            try:
                data["end_date"] = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                pass

        # Customer ID
        customer_id_str = self.form_vars["customer_id"].get()
        if customer_id_str and customer_id_str.isdigit():
            data["customer_id"] = int(customer_id_str)

        return data

    def validate_form(self):
        """Validate form data.

        Returns:
            Tuple of (valid, error_message)
        """
        # Check required fields
        if not self.form_vars["name"].get():
            return False, "Project name is required."

        if not self.form_vars["type"].get():
            return False, "Project type is required."

        # Validate dates
        start_date_str = self.form_vars["start_date"].get()
        end_date_str = self.form_vars["end_date"].get()

        if start_date_str and end_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

                if end_date < start_date:
                    return False, "Due date cannot be before start date."
            except ValueError:
                return False, "Invalid date format. Use YYYY-MM-DD."

        # For new projects, require customer
        if self.create_new and not self.form_vars["customer_id"].get():
            return False, "Customer is required for new projects."

        return True, ""

    def on_save(self):
        """Handle save button click."""
        # Validate form
        valid, error_message = self.validate_form()
        if not valid:
            messagebox.showerror("Validation Error", error_message)
            return

        # Collect form data
        data = self.collect_form_data()

        try:
            if self.create_new:
                # Create new project
                project = self.project_service.create_project(data)
                self.project_id = project.id

                # Update view state
                self.create_new = False

                # Show success message
                messagebox.showinfo("Success", f"Project '{project.name}' created successfully.")

                # Navigate back to project list
                self.parent.master.show_view("project_list")
            else:
                # Update existing project
                project = self.project_service.update_project(self.project_id, data)

                # Show success message
                messagebox.showinfo("Success", f"Project '{project.name}' updated successfully.")

                # Reload project data
                self.load_project()

        except Exception as e:
            self.logger.error(f"Error saving project: {e}")
            messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")

    def on_edit(self):
        """Handle edit button click (from readonly mode)."""
        # Change to edit mode
        self.readonly = False

        # Navigate to edit view
        self.parent.master.show_view(
            "project_details",
            add_to_history=True,
            view_data={"project_id": self.project_id, "readonly": False}
        )

    def on_back(self):
        """Handle back button click."""
        self.parent.master.show_view("project_list")

    def on_update_status(self):
        """Handle update status button click."""
        # Create a dialog for status update
        dialog = tk.Toplevel(self)
        dialog.title("Update Project Status")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Add form elements
        ttk.Label(dialog, text="Current Status:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        current_status = self.status_badge.cget("text") if hasattr(self, 'status_badge') else ""
        ttk.Label(dialog, text=current_status).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="New Status:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(dialog, textvariable=status_var, state="readonly")
        status_combo['values'] = [s.value.replace("_", " ").title() for s in ProjectStatus]
        status_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.NW)
        notes_text = tk.Text(dialog, width=30, height=5)
        notes_text.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        def update_status():
            """Update the project status."""
            if not status_var.get():
                messagebox.showwarning("Input Error", "Please select a new status.", parent=dialog)
                return

            try:
                # Convert display status back to enum value
                status_value = status_var.get().lower().replace(" ", "_")
                notes = notes_text.get("1.0", tk.END).strip()

                # Update status via service
                self.project_service.update_project_status(
                    self.project_id, status_value, notes
                )

                # Close dialog
                dialog.destroy()

                # Refresh project data
                self.load_project()

                # Show success message
                messagebox.showinfo("Success", "Project status has been updated.")

            except Exception as e:
                self.logger.error(f"Error updating project status: {e}")
                messagebox.showerror("Update Error", f"Failed to update status: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Update",
            command=update_status
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)

    def select_customer(self):
        """Open customer selection dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Select Customer")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

        # Create search frame
        search_frame = ttk.Frame(dialog, padding=5)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        def search_customers():
            """Search customers based on search text."""
            search_text = search_var.get()
            try:
                # Get customers from service
                customers = self.customer_service.search_customers(search_text)

                # Clear existing items
                for item in customers_tree.get_children():
                    customers_tree.delete(item)

                # Insert customers
                for customer in customers:
                    customer_id = customer.id if hasattr(customer, 'id') else "N/A"
                    first_name = customer.first_name if hasattr(customer, 'first_name') else ""
                    last_name = customer.last_name if hasattr(customer, 'last_name') else ""
                    email = customer.email if hasattr(customer, 'email') else ""
                    phone = customer.phone if hasattr(customer, 'phone') else ""

                    customers_tree.insert(
                        '', 'end',
                        iid=customer_id,
                        values=(customer_id, first_name, last_name, email, phone)
                    )

            except Exception as e:
                self.logger.error(f"Error searching customers: {e}")
                messagebox.showerror("Search Error", f"Failed to search customers: {str(e)}", parent=dialog)

        ttk.Button(
            search_frame,
            text="Search",
            command=search_customers
        ).pack(side=tk.LEFT, padx=5)

        # Create customers treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "first_name", "last_name", "email", "phone")
        customers_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        customers_tree.heading("id", text="ID")
        customers_tree.heading("first_name", text="First Name")
        customers_tree.heading("last_name", text="Last Name")
        customers_tree.heading("email", text="Email")
        customers_tree.heading("phone", text="Phone")

        customers_tree.column("id", width=50)
        customers_tree.column("first_name", width=100)
        customers_tree.column("last_name", width=100)
        customers_tree.column("email", width=150)
        customers_tree.column("phone", width=100)

        customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=customers_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        customers_tree.configure(yscrollcommand=scrollbar.set)

        # Handle selection
        def select_customer():
            """Select the highlighted customer."""
            selected_id = customers_tree.focus()
            if not selected_id:
                messagebox.showwarning("No Selection", "Please select a customer.", parent=dialog)
                return

            # Get customer data
            customer_data = customers_tree.item(selected_id, "values")

            # Update form variables
            self.form_vars["customer_id"].set(customer_data[0])
            customer_name = f"{customer_data[1]} {customer_data[2]}"
            self.form_vars["customer_name"].set(customer_name)

            # Close dialog
            dialog.destroy()

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Select",
            command=select_customer
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Initial search
        search_customers()

        # Set focus to search entry
        search_entry.focus_set()

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        current_date = datetime.date.today()

        # Try to parse current value
        if date_var.get():
            try:
                current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Create calendar dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Date")
        dialog.geometry("300x280")
        dialog.transient(self)
        dialog.grab_set()

        # Calendar year and month selection
        cal_header = ttk.Frame(dialog)
        cal_header.pack(fill=tk.X, padx=10, pady=5)

        # Year selection
        ttk.Label(cal_header, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        year_var = tk.StringVar(value=str(current_date.year))
        year_spin = ttk.Spinbox(
            cal_header,
            from_=2000,
            to=2100,
            textvariable=year_var,
            width=5
        )
        year_spin.pack(side=tk.LEFT, padx=5)

        # Month selection
        ttk.Label(cal_header, text="Month:").pack(side=tk.LEFT, padx=(10, 5))
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        month_var = tk.StringVar(value=months[current_date.month - 1])
        month_combo = ttk.Combobox(
            cal_header,
            textvariable=month_var,
            values=months,
            width=10,
            state="readonly"
        )
        month_combo.pack(side=tk.LEFT, padx=5)

        # Calendar frame
        cal_frame = ttk.Frame(dialog, padding=5)
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Day of week headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(
                cal_frame,
                text=day,
                width=3,
                anchor=tk.CENTER,
                font=("TkDefaultFont", 9, "bold")
            ).grid(row=0, column=i, padx=2, pady=2)

        # Day buttons
        day_buttons = []
        for row in range(6):
            for col in range(7):
                btn = ttk.Button(
                    cal_frame,
                    text="",
                    width=3,
                    style="Calendar.TButton"
                )
                btn.grid(row=row + 1, column=col, padx=2, pady=2)
                day_buttons.append(btn)

        # Selected date
        selected_date = None

        # Update calendar when month/year changes
        def update_calendar():
            """Update the calendar display based on selected month and year."""
            nonlocal selected_date

            # Get year and month
            year = int(year_var.get())
            month = months.index(month_var.get()) + 1

            # Get first day of month and number of days
            first_day = datetime.date(year, month, 1)
            if month == 12:
                last_day = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            # Get day of week for first day (0 = Monday, 6 = Sunday)
            first_weekday = first_day.weekday()

            # Clear all buttons
            for btn in day_buttons:
                btn.configure(text="", state=tk.DISABLED)

            # Fill in days
            for day in range(1, last_day.day + 1):
                index = first_weekday + day - 1

                day_buttons[index].configure(
                    text=str(day),
                    state=tk.NORMAL,
                    command=lambda d=day: select_day(d)
                )

                # Highlight current date if it matches
                this_date = datetime.date(year, month, day)

                if this_date == current_date:
                    day_buttons[index].configure(style="Calendar.Accent.TButton")
                else:
                    day_buttons[index].configure(style="Calendar.TButton")

                # Highlight selected date
                if selected_date and this_date == selected_date:
                    day_buttons[index].configure(style="Calendar.Selected.TButton")

        # Select day
        def select_day(day):
            """Select a day in the calendar.

            Args:
                day: The day number to select
            """
            nonlocal selected_date

            # Get year and month
            year = int(year_var.get())
            month = months.index(month_var.get()) + 1

            # Create date object
            selected_date = datetime.date(year, month, day)

            # Update calendar to highlight selected date
            update_calendar()

        # Navigate to previous/next month
        def prev_month():
            """Go to previous month."""
            month_idx = months.index(month_var.get())
            year = int(year_var.get())

            if month_idx == 0:
                # December of previous year
                month_var.set(months[11])
                year_var.set(str(year - 1))
            else:
                # Previous month
                month_var.set(months[month_idx - 1])

            update_calendar()

        def next_month():
            """Go to next month."""
            month_idx = months.index(month_var.get())
            year = int(year_var.get())

            if month_idx == 11:
                # January of next year
                month_var.set(months[0])
                year_var.set(str(year + 1))
            else:
                # Next month
                month_var.set(months[month_idx + 1])

            update_calendar()

        # Navigation buttons
        nav_frame = ttk.Frame(dialog)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            nav_frame,
            text="◀",
            width=3,
            command=prev_month
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame,
            text="▶",
            width=3,
            command=next_month
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame,
            text="Today",
            command=lambda: (
                year_var.set(str(datetime.date.today().year)),
                month_var.set(months[datetime.date.today().month - 1]),
                update_calendar()
            )
        ).pack(side=tk.LEFT, padx=5)

        # OK/Cancel buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_ok():
            """Handle OK button click."""
            if selected_date:
                date_var.set(selected_date.strftime("%Y-%m-%d"))
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="OK",
            command=on_ok
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Bind month and year changes
        month_combo.bind("<<ComboboxSelected>>", lambda e: update_calendar())
        year_spin.bind("<Return>", lambda e: update_calendar())
        year_spin.bind("<FocusOut>", lambda e: update_calendar())

        # Define calendar button styles
        style = ttk.Style()
        style.configure("Calendar.TButton", width=3, padding=1)
        style.configure("Calendar.Accent.TButton", background=COLORS["primary_light"])
        style.configure("Calendar.Selected.TButton", background=COLORS["primary"])

        # Initialize calendar
        update_calendar()

    def on_component_select(self, event):
        """Handle component selection in the treeview.

        Args:
            event: The selection event
        """
        component_id = self.components_tree.focus()

        # Enable/disable buttons based on selection
        state = tk.NORMAL if component_id else tk.DISABLED

        for child in self.components_tab.winfo_children():
            if isinstance(child, ttk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Button) and widget.cget("text") in ["View Component", "Edit Component",
                                                                                  "Remove Component"]:
                        widget.configure(state=state)

    def on_picking_list_select(self, event):
        """Handle picking list selection in the treeview.

        Args:
            event: The selection event
        """
        list_id = self.picking_lists_tree.focus()

        # Enable/disable buttons based on selection
        state = tk.NORMAL if list_id else tk.DISABLED
        self.view_picking_list_btn.configure(state=state)

        if hasattr(self, 'update_picking_list_btn'):
            self.update_picking_list_btn.configure(state=state)

    def on_tool_list_select(self, event):
        """Handle tool list selection in the treeview.

        Args:
            event: The selection event
        """
        list_id = self.tool_lists_tree.focus()

        # Enable/disable buttons based on selection
        state = tk.NORMAL if list_id else tk.DISABLED
        self.view_tool_list_btn.configure(state=state)

        if hasattr(self, 'update_tool_list_btn'):
            self.update_tool_list_btn.configure(state=state)

    def on_document_select(self, event):
        """Handle document selection in the treeview.

        Args:
            event: The selection event
        """
        doc_id = self.documents_tree.focus()

        # Enable/disable buttons based on selection
        state = tk.NORMAL if doc_id else tk.DISABLED
        self.view_document_btn.configure(state=state)
        self.download_document_btn.configure(state=state)

        if hasattr(self, 'delete_document_btn'):
            self.delete_document_btn.configure(state=state)

    def on_add_component(self):
        """Handle add component button click."""
        if self.create_new:
            messagebox.showwarning("Not Available", "You must save the project before adding components.")
            return

        # Navigate to component details in create mode
        self.parent.master.show_view(
            "project_component",
            add_to_history=True,
            view_data={
                "project_id": self.project_id,
                "create_new": True
            }
        )

    def on_view_component(self):
        """Handle view component button click."""
        component_id = self.components_tree.focus()
        if not component_id:
            messagebox.showwarning("No Selection", "Please select a component to view.")
            return

        # Navigate to component details in view mode
        self.parent.master.show_view(
            "project_component",
            add_to_history=True,
            view_data={
                "project_id": self.project_id,
                "component_id": component_id,
                "readonly": True
            }
        )

    def on_edit_component(self):
        """Handle edit component button click."""
        component_id = self.components_tree.focus()
        if not component_id:
            messagebox.showwarning("No Selection", "Please select a component to edit.")
            return

        # Navigate to component details in edit mode
        self.parent.master.show_view(
            "project_component",
            add_to_history=True,
            view_data={
                "project_id": self.project_id,
                "component_id": component_id,
                "readonly": False
            }
        )

    def on_remove_component(self):
        """Handle remove component button click."""
        component_id = self.components_tree.focus()
        if not component_id:
            messagebox.showwarning("No Selection", "Please select a component to remove.")
            return

        # Get component name
        component_values = self.components_tree.item(component_id, "values")
        component_name = component_values[1] if len(component_values) > 1 else "this component"

        # Confirm removal
        if not messagebox.askyesno(
                "Confirm Remove",
                f"Are you sure you want to remove {component_name} from the project?"
        ):
            return

        try:
            # Remove component from project
            self.project_service.remove_component_from_project(
                self.project_id, component_id
            )

            # Refresh project data
            self.load_project()

            # Show success message
            messagebox.showinfo("Success", f"Component '{component_name}' has been removed from the project.")

        except Exception as e:
            self.logger.error(f"Error removing component: {e}")
            messagebox.showerror("Remove Error", f"Failed to remove component: {str(e)}")

    def on_create_picking_list(self):
        """Handle create picking list button click."""
        try:
            # Create picking list via service
            picking_list = self.project_service.create_picking_list(self.project_id)

            # Refresh project data
            self.load_project()

            # Show success message
            messagebox.showinfo("Success", "Picking list has been created.")

            # Navigate to picking list view
            self.parent.master.show_view(
                "picking_list",
                add_to_history=True,
                view_data={"picking_list_id": picking_list.id}
            )

        except Exception as e:
            self.logger.error(f"Error creating picking list: {e}")
            messagebox.showerror("Create Error", f"Failed to create picking list: {str(e)}")

    def on_view_picking_list(self):
        """Handle view picking list button click."""
        list_id = self.picking_lists_tree.focus()
        if not list_id:
            messagebox.showwarning("No Selection", "Please select a picking list to view.")
            return

        # Navigate to picking list view
        self.parent.master.show_view(
            "picking_list",
            add_to_history=True,
            view_data={"picking_list_id": list_id, "readonly": True}
        )

    def on_update_picking_list(self):
        """Handle update picking list button click."""
        list_id = self.picking_lists_tree.focus()
        if not list_id:
            messagebox.showwarning("No Selection", "Please select a picking list to update.")
            return

        # Navigate to picking list view in edit mode
        self.parent.master.show_view(
            "picking_list",
            add_to_history=True,
            view_data={"picking_list_id": list_id, "readonly": False}
        )

    def on_create_tool_list(self):
        """Handle create tool list button click."""
        try:
            # Create tool list via service
            tool_list = self.project_service.create_tool_list(self.project_id)

            # Refresh project data
            self.load_project()

            # Show success message
            messagebox.showinfo("Success", "Tool list has been created.")

            # Navigate to tool list view
            self.parent.master.show_view(
                "tool_list",
                add_to_history=True,
                view_data={"tool_list_id": tool_list.id}
            )

        except Exception as e:
            self.logger.error(f"Error creating tool list: {e}")
            messagebox.showerror("Create Error", f"Failed to create tool list: {str(e)}")

    def on_view_tool_list(self):
        """Handle view tool list button click."""
        list_id = self.tool_lists_tree.focus()
        if not list_id:
            messagebox.showwarning("No Selection", "Please select a tool list to view.")
            return

        # Navigate to tool list view
        self.parent.master.show_view(
            "tool_list",
            add_to_history=True,
            view_data={"tool_list_id": list_id, "readonly": True}
        )

    def on_update_tool_list(self):
        """Handle update tool list button click."""
        list_id = self.tool_lists_tree.focus()
        if not list_id:
            messagebox.showwarning("No Selection", "Please select a tool list to update.")
            return

        # Navigate to tool list view in edit mode
        self.parent.master.show_view(
            "tool_list",
            add_to_history=True,
            view_data={"tool_list_id": list_id, "readonly": False}
        )

    def on_upload_document(self):
        """Handle upload document button click."""
        # Implement file selection and upload
        pass

    def on_view_document(self):
        """Handle view document button click."""
        doc_id = self.documents_tree.focus()
        if not doc_id:
            messagebox.showwarning("No Selection", "Please select a document to view.")
            return

        try:
            # View document via service
            self.project_service.view_document(doc_id)

        except Exception as e:
            self.logger.error(f"Error viewing document: {e}")
            messagebox.showerror("View Error", f"Failed to view document: {str(e)}")

    def on_download_document(self):
        """Handle download document button click."""
        doc_id = self.documents_tree.focus()
        if not doc_id:
            messagebox.showwarning("No Selection", "Please select a document to download.")
            return

        try:
            # Download document via service
            self.project_service.download_document(doc_id)

        except Exception as e:
            self.logger.error(f"Error downloading document: {e}")
            messagebox.showerror("Download Error", f"Failed to download document: {str(e)}")

    def on_delete_document(self):
        """Handle delete document button click."""
        doc_id = self.documents_tree.focus()
        if not doc_id:
            messagebox.showwarning("No Selection", "Please select a document to delete.")
            return

        # Get document name
        doc_values = self.documents_tree.item(doc_id, "values")
        doc_name = doc_values[1] if len(doc_values) > 1 else "this document"

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete {doc_name}?"
        ):
            return

        try:
            # Delete document via service
            self.project_service.delete_document(doc_id)

            # Refresh project data
            self.load_project()

            # Show success message
            messagebox.showinfo("Success", f"Document '{doc_name}' has been deleted.")

        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
            messagebox.showerror("Delete Error", f"Failed to delete document: {str(e)}")

    def on_zoom_change(self, event):
        """Handle timeline zoom level change.

        Args:
            event: The combobox selection event
        """
        # Redraw timeline with new zoom level
        self.draw_timeline()

    def on_print_timeline(self):
        """Handle print timeline button click."""
        messagebox.showinfo("Not Implemented", "Timeline printing is not implemented yet.")

    def on_project_updated(self, data):
        """Handle project updated event.

        Args:
            data: Event data including project_id
        """
        if data.get("project_id") == self.project_id:
            self.load_project()

    def on_component_updated(self, data):
        """Handle component updated event.

        Args:
            data: Event data including project_id and component_id
        """
        if data.get("project_id") == self.project_id:
            self.load_project()

    def refresh(self):
        """Refresh the view."""
        if self.project_id:
            self.load_project()

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("project_updated", self.on_project_updated)
        unsubscribe("component_updated", self.on_component_updated)

        super().destroy()