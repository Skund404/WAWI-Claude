# gui/views/patterns/pattern_detail_view.py
"""
Pattern detail view for viewing and editing pattern information.

Provides a comprehensive interface for managing pattern details, components,
material requirements, and associated files.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional, Tuple

from database.models.enums import SkillLevel, ProjectType
from gui.base.base_view import BaseView
from gui.utils.service_access import get_service
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.theme import COLORS, get_status_style
from gui.widgets.status_badge import StatusBadge

logger = logging.getLogger(__name__)


class PatternDetailView(BaseView):
    """
    View for displaying and editing pattern details.
    """

    def __init__(self, parent, pattern_id=None, create_new=False, readonly=False):
        """
        Initialize the pattern detail view.

        Args:
            parent: The parent widget
            pattern_id: ID of the pattern to view/edit (None for new patterns)
            create_new: Whether to create a new pattern
            readonly: Whether the view should be read-only
        """
        self.pattern_id = pattern_id
        self.create_new = create_new
        self.readonly = readonly
        self.pattern = None

        # Form variables
        self.form_vars = {}

        # Components list
        self.components = []

        # Call parent constructor
        super().__init__(parent)

        # Set window title based on mode
        if self.create_new:
            self.title = "New Pattern"
            self.description = "Create a new leatherworking pattern"
        elif self.readonly:
            self.title = "Pattern Details"
            self.description = "View pattern information and components"
        else:
            self.title = "Edit Pattern"
            self.description = "Modify pattern details and components"

    def build(self):
        """Build the pattern detail view layout."""
        # Create header with back button
        self.create_header()

        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.info_tab = ttk.Frame(self.notebook)
        self.components_tab = ttk.Frame(self.notebook)
        self.materials_tab = ttk.Frame(self.notebook)
        self.files_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.info_tab, text="Information")
        self.notebook.add(self.components_tab, text="Components")
        self.notebook.add(self.materials_tab, text="Materials")
        self.notebook.add(self.files_tab, text="Files & Diagrams")

        # Create tab contents
        self.create_info_tab()
        self.create_components_tab()
        self.create_materials_tab()
        self.create_files_tab()

        # Create footer with action buttons
        self.footer_frame = ttk.Frame(self)
        self.footer_frame.pack(fill=tk.X, padx=10, pady=10)

        # Add buttons based on mode
        if self.readonly:
            # Close button for readonly mode
            self.close_btn = ttk.Button(
                self.footer_frame,
                text="Close",
                command=self.on_back
            )
            self.close_btn.pack(side=tk.RIGHT)

            # Edit button for readonly mode
            self.edit_btn = ttk.Button(
                self.footer_frame,
                text="Edit Pattern",
                command=self.on_edit
            )
            self.edit_btn.pack(side=tk.RIGHT, padx=(0, 10))
        else:
            # Save button
            self.save_btn = ttk.Button(
                self.footer_frame,
                text="Save",
                command=self.on_save
            )
            self.save_btn.pack(side=tk.RIGHT)

            # Cancel button
            self.cancel_btn = ttk.Button(
                self.footer_frame,
                text="Cancel",
                command=self.on_back
            )
            self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Load pattern data if editing an existing pattern
        if self.pattern_id:
            self.load_pattern()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Back button to return to pattern list
        self.back_btn = ttk.Button(
            self.header_btn_frame,
            text="Back to List",
            command=self.on_back
        )
        self.back_btn.pack(side=tk.LEFT)

    def create_info_tab(self):
        """Create the information tab content."""
        # Create form container
        form_frame = ttk.Frame(self.info_tab, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Create two-column layout
        left_col = ttk.Frame(form_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_col = ttk.Frame(form_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Left column fields

        # Pattern Name
        ttk.Label(left_col, text="Pattern Name:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["name"] = tk.StringVar()
        name_entry = ttk.Entry(left_col, textvariable=self.form_vars["name"], width=40)
        name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        if self.readonly:
            name_entry.configure(state="readonly")

        # Skill Level
        ttk.Label(left_col, text="Skill Level:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["skill_level"] = tk.StringVar()
        skill_combo = ttk.Combobox(left_col, textvariable=self.form_vars["skill_level"], width=20)
        skill_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        skill_levels = [level.name.replace("_", " ").title() for level in SkillLevel]
        skill_combo["values"] = skill_levels

        if self.readonly:
            skill_combo.configure(state="readonly")

        # Project Type
        ttk.Label(left_col, text="Project Type:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["project_type"] = tk.StringVar()
        type_combo = ttk.Combobox(left_col, textvariable=self.form_vars["project_type"], width=20)
        type_combo.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        project_types = [ptype.name.replace("_", " ").title() for ptype in ProjectType]
        type_combo["values"] = project_types

        if self.readonly:
            type_combo.configure(state="readonly")

        # Description
        ttk.Label(left_col, text="Description:").grid(
            row=3, column=0, sticky="nw", padx=5, pady=5)

        description_frame = ttk.Frame(left_col)
        description_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        self.form_vars["description"] = tk.Text(description_frame, height=5, width=38, wrap=tk.WORD)
        self.form_vars["description"].pack(fill=tk.BOTH, expand=True)

        if self.readonly:
            self.form_vars["description"].configure(state="disabled")

        # Right column fields

        # Created Date (read-only)
        ttk.Label(right_col, text="Created:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["created_at"] = tk.StringVar()
        created_entry = ttk.Entry(right_col, textvariable=self.form_vars["created_at"], width=20)
        created_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        created_entry.configure(state="readonly")

        # Last Updated (read-only)
        ttk.Label(right_col, text="Last Updated:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["updated_at"] = tk.StringVar()
        updated_entry = ttk.Entry(right_col, textvariable=self.form_vars["updated_at"], width=20)
        updated_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        updated_entry.configure(state="readonly")

        # Component Count (read-only)
        ttk.Label(right_col, text="Components:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["component_count"] = tk.StringVar()
        comp_count_entry = ttk.Entry(right_col, textvariable=self.form_vars["component_count"], width=10)
        comp_count_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        comp_count_entry.configure(state="readonly")

        # Notes
        ttk.Label(right_col, text="Notes:").grid(
            row=3, column=0, sticky="nw", padx=5, pady=5)

        notes_frame = ttk.Frame(right_col)
        notes_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        self.form_vars["notes"] = tk.Text(notes_frame, height=5, width=38, wrap=tk.WORD)
        self.form_vars["notes"].pack(fill=tk.BOTH, expand=True)

        if self.readonly:
            self.form_vars["notes"].configure(state="disabled")

    def create_components_tab(self):
        """Create the components tab content."""
        # Create components toolbar
        toolbar = ttk.Frame(self.components_tab)
        toolbar.pack(fill=tk.X, pady=(10, 5), padx=10)

        # Title label
        ttk.Label(
            toolbar,
            text="Pattern Components",
            font=("TkDefaultFont", 11, "bold")
        ).pack(side=tk.LEFT)

        if not self.readonly:
            # Add component button
            self.add_component_btn = ttk.Button(
                toolbar,
                text="Add Component",
                command=self.on_add_component
            )
            self.add_component_btn.pack(side=tk.RIGHT)

        # Create components list with treeview
        list_frame = ttk.Frame(self.components_tab, padding=(10, 5))
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "type", "dimensions", "materials")
        self.components_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        self.components_tree.heading("name", text="Component Name")
        self.components_tree.heading("type", text="Type")
        self.components_tree.heading("dimensions", text="Dimensions")
        self.components_tree.heading("materials", text="Materials")

        # Define columns
        self.components_tree.column("name", width=200)
        self.components_tree.column("type", width=120)
        self.components_tree.column("dimensions", width=150)
        self.components_tree.column("materials", width=200)

        # Add scrollbar
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.components_tree.yview)
        self.components_tree.configure(yscrollcommand=y_scrollbar.set)

        self.components_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add Component actions
        actions_frame = ttk.Frame(self.components_tab, padding=(10, 5))
        actions_frame.pack(fill=tk.X)

        # View component button
        self.view_component_btn = ttk.Button(
            actions_frame,
            text="View Component",
            command=self.on_view_component,
            state=tk.DISABLED
        )
        self.view_component_btn.pack(side=tk.LEFT, padx=(0, 5))

        if not self.readonly:
            # Edit component button
            self.edit_component_btn = ttk.Button(
                actions_frame,
                text="Edit Component",
                command=self.on_edit_component,
                state=tk.DISABLED
            )
            self.edit_component_btn.pack(side=tk.LEFT, padx=(0, 5))

            # Delete component button
            self.delete_component_btn = ttk.Button(
                actions_frame,
                text="Delete Component",
                command=self.on_delete_component,
                state=tk.DISABLED
            )
            self.delete_component_btn.pack(side=tk.LEFT)

        # Bind selection event
        self.components_tree.bind("<<TreeviewSelect>>", self.on_component_select)

        # Bind double-click for quick view/edit
        self.components_tree.bind("<Double-1>", self.on_component_double_click)

    def create_materials_tab(self):
        """Create the materials tab content."""
        # Create materials container
        materials_frame = ttk.Frame(self.materials_tab, padding=10)
        materials_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        ttk.Label(
            materials_frame,
            text="Material Requirements",
            font=("TkDefaultFont", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Create materials list with treeview
        list_frame = ttk.Frame(materials_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("material", "type", "quantity", "unit", "components")
        self.materials_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        self.materials_tree.heading("material", text="Material")
        self.materials_tree.heading("type", text="Type")
        self.materials_tree.heading("quantity", text="Quantity")
        self.materials_tree.heading("unit", text="Unit")
        self.materials_tree.heading("components", text="Used In Components")

        # Define columns
        self.materials_tree.column("material", width=200)
        self.materials_tree.column("type", width=100)
        self.materials_tree.column("quantity", width=70, anchor="e")
        self.materials_tree.column("unit", width=80)
        self.materials_tree.column("components", width=200)

        # Add scrollbar
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=y_scrollbar.set)

        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add action buttons
        actions_frame = ttk.Frame(materials_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))

        # Check inventory button
        self.check_inventory_btn = ttk.Button(
            actions_frame,
            text="Check Inventory",
            command=self.on_check_inventory
        )
        self.check_inventory_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Export material list button
        self.export_materials_btn = ttk.Button(
            actions_frame,
            text="Export Material List",
            command=self.on_export_materials
        )
        self.export_materials_btn.pack(side=tk.LEFT)

    def create_files_tab(self):
        """Create the files tab content."""
        # Create files container
        files_frame = ttk.Frame(self.files_tab, padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True)

        # Create two-column layout
        left_col = ttk.Frame(files_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_col = ttk.Frame(files_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Left column - File list
        file_list_frame = ttk.LabelFrame(left_col, text="Pattern Files")
        file_list_frame.pack(fill=tk.BOTH, expand=True)

        # File toolbar
        file_toolbar = ttk.Frame(file_list_frame)
        file_toolbar.pack(fill=tk.X, pady=(5, 0), padx=5)

        if not self.readonly:
            # Add file button
            self.add_file_btn = ttk.Button(
                file_toolbar,
                text="Add File",
                command=self.on_add_file
            )
            self.add_file_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Create file list with treeview
        file_list_container = ttk.Frame(file_list_frame)
        file_list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("name", "type", "size")
        self.files_tree = ttk.Treeview(
            file_list_container,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        self.files_tree.heading("name", text="File Name")
        self.files_tree.heading("type", text="Type")
        self.files_tree.heading("size", text="Size")

        # Define columns
        self.files_tree.column("name", width=200)
        self.files_tree.column("type", width=80)
        self.files_tree.column("size", width=80)

        # Add scrollbar
        y_scrollbar = ttk.Scrollbar(file_list_container, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=y_scrollbar.set)

        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # File action buttons
        file_actions = ttk.Frame(file_list_frame)
        file_actions.pack(fill=tk.X, padx=5, pady=5)

        # View file button
        self.view_file_btn = ttk.Button(
            file_actions,
            text="View File",
            command=self.on_view_file,
            state=tk.DISABLED
        )
        self.view_file_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Download file button
        self.download_file_btn = ttk.Button(
            file_actions,
            text="Download File",
            command=self.on_download_file,
            state=tk.DISABLED
        )
        self.download_file_btn.pack(side=tk.LEFT, padx=(0, 5))

        if not self.readonly:
            # Delete file button
            self.delete_file_btn = ttk.Button(
                file_actions,
                text="Delete File",
                command=self.on_delete_file,
                state=tk.DISABLED
            )
            self.delete_file_btn.pack(side=tk.LEFT)

        # Right column - File preview
        preview_frame = ttk.LabelFrame(right_col, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # Preview placeholder
        self.preview_placeholder = ttk.Label(
            preview_frame,
            text="Select a file to preview",
            anchor="center"
        )
        self.preview_placeholder.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create preview container (hidden initially)
        self.preview_container = ttk.Frame(preview_frame)

        # Bind selection event for files
        self.files_tree.bind("<<TreeviewSelect>>", self.on_file_select)

    def load_pattern(self):
        """Load pattern data from service."""
        try:
            # Get the pattern service
            service = get_service("IPatternService")

            # Get pattern data
            self.pattern = service.get_pattern_by_id(
                self.pattern_id,
                include_components=True,
                include_files=True
            )

            if not self.pattern:
                messagebox.showerror("Error", "Pattern not found.")
                self.on_back()
                return

            # Update title with pattern name
            if self.readonly:
                self.title = f"Pattern: {self.pattern.get('name', '')}"
            else:
                self.title = f"Edit Pattern: {self.pattern.get('name', '')}"

            # Call create_header again to update the title
            self.header_title_label.configure(text=self.title)

            # Update form fields
            self.populate_form()

            # Update components list
            self.components = self.pattern.get("components", [])
            self.update_components_list()

            # Update materials list
            self.update_materials_list()

            # Update files list
            self.update_files_list()
        except Exception as e:
            logger.error(f"Error loading pattern: {str(e)}")
            messagebox.showerror("Error", f"Failed to load pattern: {str(e)}")
            self.on_back()

    def populate_form(self):
        """Populate form fields with pattern data."""
        if not self.pattern:
            return

        # Basic information
        self.form_vars["name"].set(self.pattern.get("name", ""))

        # Format skill level for display
        skill_level = self.pattern.get("skill_level", "")
        if skill_level:
            if isinstance(skill_level, str):
                skill_level = skill_level.replace("_", " ").title()
            self.form_vars["skill_level"].set(skill_level)

        # Format project type for display
        project_type = self.pattern.get("project_type", "")
        if project_type:
            if isinstance(project_type, str):
                project_type = project_type.replace("_", " ").title()
            self.form_vars["project_type"].set(project_type)

        # Description field (Text widget)
        if isinstance(self.form_vars["description"], tk.Text):
            self.form_vars["description"].delete("1.0", tk.END)
            self.form_vars["description"].insert("1.0", self.pattern.get("description", ""))

        # Notes field (Text widget)
        if isinstance(self.form_vars["notes"], tk.Text):
            self.form_vars["notes"].delete("1.0", tk.END)
            self.form_vars["notes"].insert("1.0", self.pattern.get("notes", ""))

        # Format dates for display
        created_at = self.pattern.get("created_at", "")
        if created_at:
            if isinstance(created_at, str):
                created_at = created_at[:19].replace("T", " ")  # Extract date and time
            else:
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.form_vars["created_at"].set(created_at)

        updated_at = self.pattern.get("updated_at", "")
        if updated_at:
            if isinstance(updated_at, str):
                updated_at = updated_at[:19].replace("T", " ")  # Extract date and time
            else:
                updated_at = updated_at.strftime("%Y-%m-%d %H:%M:%S")
            self.form_vars["updated_at"].set(updated_at)

        # Component count
        component_count = len(self.pattern.get("components", []))
        self.form_vars["component_count"].set(str(component_count))

    def update_components_list(self):
        """Update the components list in the treeview."""
        # Clear current items
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)

        # Add components
        for i, component in enumerate(self.components):
            # Format dimensions based on component type
            dimensions = self.format_component_dimensions(component)

            # Count materials used
            material_count = len(component.get("materials", []))
            materials_text = f"{material_count} material(s)"

            component_type = component.get("type", "").replace("_", " ").title()

            self.components_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    component.get("name", "Unknown"),
                    component_type,
                    dimensions,
                    materials_text
                ),
                tags=[str(component.get("id"))]
            )

        # Show message if no components
        if not self.components:
            self.components_tree.insert(
                "",
                "end",
                iid="empty",
                values=("No components found", "", "", ""),
                tags=["empty"]
            )

    def format_component_dimensions(self, component):
        """
        Format component dimensions for display.

        Args:
            component: The component data

        Returns:
            A formatted string with component dimensions
        """
        component_type = component.get("type", "").lower()

        if component_type in ["rectangular", "rectangular_panel"]:
            width = component.get("width", 0)
            height = component.get("height", 0)
            thickness = component.get("thickness", 0)

            if thickness:
                return f"{width:.1f} × {height:.1f} × {thickness:.1f} mm"
            else:
                return f"{width:.1f} × {height:.1f} mm"

        elif component_type in ["circular", "ring"]:
            diameter = component.get("diameter", 0)
            thickness = component.get("thickness", 0)

            if thickness:
                return f"Ø {diameter:.1f} × {thickness:.1f} mm"
            else:
                return f"Ø {diameter:.1f} mm"

        elif component_type in ["strap", "strip"]:
            length = component.get("length", 0)
            width = component.get("width", 0)
            thickness = component.get("thickness", 0)

            if thickness:
                return f"{length:.1f} × {width:.1f} × {thickness:.1f} mm"
            else:
                return f"{length:.1f} × {width:.1f} mm"

        else:
            # Generic dimensions format
            dimensions = []
            for dim in ["length", "width", "height", "diameter", "thickness"]:
                if dim in component and component[dim]:
                    value = component[dim]
                    dimensions.append(f"{dim.title()}: {value:.1f} mm")

            return ", ".join(dimensions) if dimensions else "No dimensions"

    def update_materials_list(self):
        """Update the materials list in the treeview."""
        # Clear current items
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)

        # Collect all materials from all components
        all_materials = {}
        component_usage = {}

        for component in self.components:
            component_name = component.get("name", "Unknown")

            for material in component.get("materials", []):
                material_id = material.get("material_id")

                if material_id in all_materials:
                    # Update existing material
                    all_materials[material_id]["quantity"] += material.get("quantity", 0)
                    component_usage[material_id].append(component_name)
                else:
                    # Add new material
                    all_materials[material_id] = material.copy()
                    component_usage[material_id] = [component_name]

        # Add materials to tree
        for i, (material_id, material) in enumerate(all_materials.items()):
            material_type = material.get("type", "").replace("_", " ").title()
            quantity = material.get("quantity", 0)
            unit = material.get("unit", "").replace("_", " ").title()

            # Format components list
            used_in = ", ".join(component_usage[material_id])

            self.materials_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    material.get("name", "Unknown"),
                    material_type,
                    f"{quantity:.2f}",
                    unit,
                    used_in
                ),
                tags=[str(material_id)]
            )

        # Show message if no materials
        if not all_materials:
            self.materials_tree.insert(
                "",
                "end",
                iid="empty",
                values=("No materials required", "", "", "", ""),
                tags=["empty"]
            )

    def update_files_list(self):
        """Update the files list in the treeview."""
        # Clear current items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)

        # Add files
        files = self.pattern.get("files", [])

        for i, file in enumerate(files):
            file_name = file.get("name", "Unknown")
            file_type = file.get("file_type", "").upper()

            # Format file size
            file_size = file.get("size", 0)
            size_text = self.format_file_size(file_size)

            self.files_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    file_name,
                    file_type,
                    size_text
                ),
                tags=[str(file.get("id"))]
            )

        # Show message if no files
        if not files:
            self.files_tree.insert(
                "",
                "end",
                iid="empty",
                values=("No files attached", "", ""),
                tags=["empty"]
            )

    def format_file_size(self, size_bytes):
        """
        Format file size for display.

        Args:
            size_bytes: The file size in bytes

        Returns:
            A formatted string with appropriate units
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def collect_form_data(self):
        """
        Collect data from form fields.

        Returns:
            Dictionary of form data
        """
        data = {}

        # Basic information
        data["name"] = self.form_vars["name"].get()

        # Convert skill level to backend format
        skill_level = self.form_vars["skill_level"].get()
        if skill_level:
            data["skill_level"] = skill_level.lower().replace(" ", "_")

        # Convert project type to backend format
        project_type = self.form_vars["project_type"].get()
        if project_type:
            data["project_type"] = project_type.lower().replace(" ", "_")

        # Description and notes fields (Text widgets)
        if isinstance(self.form_vars["description"], tk.Text):
            data["description"] = self.form_vars["description"].get("1.0", tk.END).strip()

        if isinstance(self.form_vars["notes"], tk.Text):
            data["notes"] = self.form_vars["notes"].get("1.0", tk.END).strip()

        # Include pattern ID if editing
        if self.pattern_id:
            data["id"] = self.pattern_id

        return data

    def validate_form(self):
        """
        Validate form data.

        Returns:
            Tuple of (valid, error_message)
        """
        # Get form data
        data = self.collect_form_data()

        # Validate required fields
        if not data.get("name"):
            return False, "Pattern name is required."

        if not data.get("skill_level"):
            return False, "Skill level is required."

        if not data.get("project_type"):
            return False, "Project type is required."

        return True, ""

    def on_save(self):
        """Handle save button click."""
        # Validate form
        valid, error_message = self.validate_form()
        if not valid:
            messagebox.showerror("Validation Error", error_message)
            return

        try:
            # Get form data
            data = self.collect_form_data()

            # Get the pattern service
            service = get_service("IPatternService")

            if self.create_new:
                # Create new pattern
                result = service.create_pattern(data)
                if result:
                    messagebox.showinfo("Success", "Pattern created successfully.")

                    # Publish event
                    publish("pattern_updated", {"pattern_id": result.get("id")})

                    # Navigate to pattern list
                    self.on_back()
                else:
                    messagebox.showerror("Error", "Failed to create pattern.")
            else:
                # Update existing pattern
                result = service.update_pattern(self.pattern_id, data)
                if result:
                    messagebox.showinfo("Success", "Pattern updated successfully.")

                    # Publish event
                    publish("pattern_updated", {"pattern_id": self.pattern_id})

                    # Navigate to pattern list
                    self.on_back()
                else:
                    messagebox.showerror("Error", "Failed to update pattern.")
        except Exception as e:
            logger.error(f"Error saving pattern: {str(e)}")
            messagebox.showerror("Error", f"Failed to save pattern: {str(e)}")

    def on_back(self):
        """Handle back button click."""
        try:
            # Import the pattern list view
            from gui.views.patterns.pattern_list_view import PatternListView

            # Create and display the list view
            list_view = PatternListView(self.parent)
            list_view.pack(fill=tk.BOTH, expand=True)

            # Remove current view
            self.destroy()
        except Exception as e:
            logger.error(f"Error navigating back: {str(e)}")
            messagebox.showerror("Error", f"Failed to navigate back: {str(e)}")

    def on_edit(self):
        """Handle edit button click (from readonly mode)."""
        try:
            # Create edit view for current pattern
            edit_view = PatternDetailView(self.parent, pattern_id=self.pattern_id, readonly=False)
            edit_view.pack(fill=tk.BOTH, expand=True)

            # Remove current view
            self.destroy()
        except Exception as e:
            logger.error(f"Error editing pattern: {str(e)}")
            messagebox.showerror("Error", f"Failed to edit pattern: {str(e)}")

    def on_component_select(self, event):
        """
        Handle component selection.

        Args:
            event: The TreeviewSelect event
        """
        # Get selected component
        selected = self.components_tree.selection()
        if not selected:
            # Disable action buttons when no selection
            self.view_component_btn.configure(state=tk.DISABLED)
            if not self.readonly:
                self.edit_component_btn.configure(state=tk.DISABLED)
                self.delete_component_btn.configure(state=tk.DISABLED)
            return

        # Check if "empty" placeholder is selected
        if "empty" in self.components_tree.item(selected[0], "tags"):
            return

        # Enable action buttons
        self.view_component_btn.configure(state=tk.NORMAL)
        if not self.readonly:
            self.edit_component_btn.configure(state=tk.NORMAL)
            self.delete_component_btn.configure(state=tk.NORMAL)

    def on_component_double_click(self, event):
        """
        Handle component double-click.

        Args:
            event: The Double-1 event
        """
        # View or edit component based on mode
        if self.readonly:
            self.on_view_component()
        else:
            self.on_edit_component()

    def get_selected_component_id(self):
        """
        Get the ID of the selected component.

        Returns:
            The ID of the selected component, or None if no selection
        """
        selected = self.components_tree.selection()
        if not selected:
            return None

        # Get tags which contain the ID
        tags = self.components_tree.item(selected[0], "tags")
        if not tags or "empty" in tags:
            return None

        # Extract ID from tags
        try:
            return int(tags[0])
        except (ValueError, IndexError):
            return None

    def on_add_component(self):
        """Handle add component button click."""
        try:
            if not self.pattern_id and not self.create_new:
                messagebox.showinfo("Info", "Please save the pattern first before adding components.")
                return

            # Open component dialog for new component
            from gui.views.patterns.component_dialog import ComponentDialog

            # Create and show dialog
            dialog = ComponentDialog(self, pattern_id=self.pattern_id)
            result = dialog.show()

            # Refresh if component was added
            if result == "ok":
                self.refresh()
        except Exception as e:
            logger.error(f"Error adding component: {str(e)}")
            messagebox.showerror("Error", f"Failed to add component: {str(e)}")

    def on_view_component(self):
        """Handle view component button click."""
        # Get selected component ID
        component_id = self.get_selected_component_id()
        if not component_id:
            return

        try:
            # Open component dialog in readonly mode
            from gui.views.patterns.component_dialog import ComponentDialog

            # Create and show dialog
            dialog = ComponentDialog(self, component_id=component_id, readonly=True)
            dialog.show()
        except Exception as e:
            logger.error(f"Error viewing component: {str(e)}")
            messagebox.showerror("Error", f"Failed to view component: {str(e)}")

    def on_edit_component(self):
        """Handle edit component button click."""
        # Get selected component ID
        component_id = self.get_selected_component_id()
        if not component_id:
            return

        try:
            # Open component dialog for editing
            from gui.views.patterns.component_dialog import ComponentDialog

            # Create and show dialog
            dialog = ComponentDialog(self, component_id=component_id)
            result = dialog.show()

            # Refresh if component was updated
            if result == "ok":
                self.refresh()
        except Exception as e:
            logger.error(f"Error editing component: {str(e)}")
            messagebox.showerror("Error", f"Failed to edit component: {str(e)}")

    def on_delete_component(self):
        """Handle delete component button click."""
        # Get selected component ID
        component_id = self.get_selected_component_id()
        if not component_id:
            return

        # Get component name
        selected = self.components_tree.selection()
        if not selected:
            return

        values = self.components_tree.item(selected[0], "values")
        component_name = values[0]

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the component '{component_name}'?\n\n"
                "This action cannot be undone."
        ):
            return

        try:
            # Get component service
            service = get_service("IComponentService")

            # Delete component
            result = service.delete_component(component_id)

            if result:
                messagebox.showinfo("Success", f"Component '{component_name}' deleted successfully.")
                self.refresh()
            else:
                self.show_error("Error", f"Failed to delete component '{component_name}'.")
        except Exception as e:
            logger.error(f"Error deleting component: {str(e)}")
            self.show_error("Error", f"Failed to delete component: {str(e)}")

    def on_check_inventory(self):
        """Handle check inventory button click."""
        try:
            # Get inventory service
            inventory_service = get_service("IInventoryService")

            # Get material service
            material_service = get_service("IMaterialService")

            # Check inventory for each material
            inventory_status = {}
            missing_materials = []

            # Get all materials from the materials treeview
            for item_id in self.materials_tree.get_children():
                # Skip "empty" placeholder
                if item_id == "empty":
                    continue

                # Get material ID from tags
                tags = self.materials_tree.item(item_id, "tags")
                if not tags:
                    continue

                try:
                    material_id = int(tags[0])
                except (ValueError, IndexError):
                    continue

                # Get material details
                values = self.materials_tree.item(item_id, "values")
                material_name = values[0]
                required_quantity = float(values[2])

                # Check inventory
                inventory_result = inventory_service.check_material_inventory(material_id)

                if not inventory_result:
                    missing_materials.append({
                        "name": material_name,
                        "required": required_quantity,
                        "available": 0
                    })
                    continue

                available_quantity = inventory_result.get("quantity", 0)

                if available_quantity < required_quantity:
                    missing_materials.append({
                        "name": material_name,
                        "required": required_quantity,
                        "available": available_quantity
                    })

            # Show inventory check results
            if not missing_materials:
                messagebox.showinfo(
                    "Inventory Check",
                    "All materials for this pattern are available in inventory."
                )
            else:
                # Format missing materials message
                message = "The following materials are missing or have insufficient quantity:\n\n"

                for item in missing_materials:
                    message += f"• {item['name']}: Needed {item['required']:.2f}, Available {item['available']:.2f}\n"

                # Show message with option to create purchase order
                if messagebox.askyesno(
                        "Inventory Check",
                        message + "\n\nWould you like to create a purchase order for the missing materials?",
                        icon="warning"
                ):
                    self.create_purchase_order(missing_materials)
        except Exception as e:
            logger.error(f"Error checking inventory: {str(e)}")
            self.show_error("Error", f"Failed to check inventory: {str(e)}")

    def create_purchase_order(self, missing_materials):
        """
        Create a purchase order for missing materials.

        Args:
            missing_materials: List of missing materials
        """
        try:
            # Navigate to purchase view
            from gui.views.purchases.purchase_view import PurchaseView

            # Create purchase view
            purchase_view = PurchaseView(self.parent, create_for_materials=missing_materials)
            purchase_view.pack(fill=tk.BOTH, expand=True)

            # Remove current view
            self.destroy()
        except Exception as e:
            logger.error(f"Error creating purchase order: {str(e)}")
            self.show_error("Error", f"Failed to create purchase order: {str(e)}")

    def on_export_materials(self):
        """Handle export materials button click."""
        try:
            # Get file path for saving
            from tkinter import filedialog

            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Material List"
            )

            if not file_path:
                return

            # Get all materials from the materials treeview
            materials_data = []

            for item_id in self.materials_tree.get_children():
                # Skip "empty" placeholder
                if item_id == "empty":
                    continue

                # Get material details
                values = self.materials_tree.item(item_id, "values")

                materials_data.append({
                    "Material": values[0],
                    "Type": values[1],
                    "Quantity": values[2],
                    "Unit": values[3],
                    "Used In": values[4]
                })

            if not materials_data:
                messagebox.showinfo("Export", "No materials to export.")
                return

            # Export to CSV
            import csv

            with open(file_path, "w", newline="") as csvfile:
                fieldnames = ["Material", "Type", "Quantity", "Unit", "Used In"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for material in materials_data:
                    writer.writerow(material)

            messagebox.showinfo("Export", f"Material list exported successfully to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting materials: {str(e)}")
            self.show_error("Error", f"Failed to export materials: {str(e)}")

    def on_file_select(self, event):
        """
        Handle file selection.

        Args:
            event: The TreeviewSelect event
        """
        # Get selected file
        selected = self.files_tree.selection()
        if not selected:
            # Disable action buttons when no selection
            self.view_file_btn.configure(state=tk.DISABLED)
            self.download_file_btn.configure(state=tk.DISABLED)
            if not self.readonly:
                self.delete_file_btn.configure(state=tk.DISABLED)

            # Hide preview
            self.preview_container.pack_forget()
            self.preview_placeholder.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            return

        # Check if "empty" placeholder is selected
        if "empty" in self.files_tree.item(selected[0], "tags"):
            return

        # Enable action buttons
        self.view_file_btn.configure(state=tk.NORMAL)
        self.download_file_btn.configure(state=tk.NORMAL)
        if not self.readonly:
            self.delete_file_btn.configure(state=tk.NORMAL)

        # Show file preview
        self.show_file_preview()

    def get_selected_file_id(self):
        """
        Get the ID of the selected file.

        Returns:
            The ID of the selected file, or None if no selection
        """
        selected = self.files_tree.selection()
        if not selected:
            return None

        # Get tags which contain the ID
        tags = self.files_tree.item(selected[0], "tags")
        if not tags or "empty" in tags:
            return None

        # Extract ID from tags
        try:
            return int(tags[0])
        except (ValueError, IndexError):
            return None

    def on_add_file(self):
        """Handle add file button click."""
        try:
            if not self.pattern_id and not self.create_new:
                messagebox.showinfo("Info", "Please save the pattern first before adding files.")
                return

            # Get file path for upload
            from tkinter import filedialog

            file_paths = filedialog.askopenfilenames(
                title="Select Files",
                filetypes=[
                    ("Pattern Files", "*.pdf;*.svg;*.png;*.jpg;*.jpeg"),
                    ("PDF Files", "*.pdf"),
                    ("SVG Files", "*.svg"),
                    ("Image Files", "*.png;*.jpg;*.jpeg"),
                    ("All Files", "*.*")
                ]
            )

            if not file_paths:
                return

            # Upload each file
            pattern_service = get_service("IPatternService")

            for file_path in file_paths:
                # Get file name
                import os
                file_name = os.path.basename(file_path)

                # Read file content
                with open(file_path, "rb") as f:
                    file_content = f.read()

                # Upload file
                result = pattern_service.add_pattern_file(
                    self.pattern_id,
                    file_name,
                    file_content
                )

                if not result:
                    messagebox.showerror("Error", f"Failed to upload file {file_name}.")

            # Refresh the files list
            self.refresh()

            messagebox.showinfo("Success", "Files uploaded successfully.")
        except Exception as e:
            logger.error(f"Error adding file: {str(e)}")
            self.show_error("Error", f"Failed to add file: {str(e)}")

    def on_view_file(self):
        """Handle view file button click."""
        # Get selected file ID
        file_id = self.get_selected_file_id()
        if not file_id:
            return

        try:
            # Get file service
            service = get_service("IPatternService")

            # Get file content
            file = service.get_pattern_file(file_id)

            if not file:
                messagebox.showerror("Error", "Failed to retrieve file.")
                return

            # View file based on type
            file_type = file.get("file_type", "").lower()

            # For now, just show a preview - full viewer would be implemented in a separate file
            self.show_file_preview()
        except Exception as e:
            logger.error(f"Error viewing file: {str(e)}")
            self.show_error("Error", f"Failed to view file: {str(e)}")

    def show_file_preview(self):
        """Show a preview of the selected file."""
        # Get selected file ID
        file_id = self.get_selected_file_id()
        if not file_id:
            return

        try:
            # Get file details
            selected = self.files_tree.selection()
            values = self.files_tree.item(selected[0], "values")
            file_name = values[0]
            file_type = values[1].lower()

            # Hide placeholder
            self.preview_placeholder.pack_forget()

            # Clear previous preview content
            for widget in self.preview_container.winfo_children():
                widget.destroy()

            # Show preview container
            self.preview_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create preview based on file type
            if file_type in ["pdf"]:
                # PDF preview placeholder
                ttk.Label(
                    self.preview_container,
                    text=f"PDF Preview: {file_name}\n\nPDF preview not implemented yet.",
                    justify="center",
                    anchor="center"
                ).pack(fill=tk.BOTH, expand=True)

            elif file_type in ["svg"]:
                # SVG preview placeholder
                ttk.Label(
                    self.preview_container,
                    text=f"SVG Preview: {file_name}\n\nSVG preview not implemented yet.",
                    justify="center",
                    anchor="center"
                ).pack(fill=tk.BOTH, expand=True)

            elif file_type in ["png", "jpg", "jpeg"]:
                # Image preview placeholder
                ttk.Label(
                    self.preview_container,
                    text=f"Image Preview: {file_name}\n\nImage preview not implemented yet.",
                    justify="center",
                    anchor="center"
                ).pack(fill=tk.BOTH, expand=True)

            else:
                # Generic file preview
                ttk.Label(
                    self.preview_container,
                    text=f"{file_type.upper()} File: {file_name}\n\nNo preview available for this file type.",
                    justify="center",
                    anchor="center"
                ).pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logger.error(f"Error showing file preview: {str(e)}")
            self.preview_placeholder.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def on_download_file(self):
        """Handle download file button click."""
        # Get selected file ID
        file_id = self.get_selected_file_id()
        if not file_id:
            return

        try:
            # Get file details
            selected = self.files_tree.selection()
            values = self.files_tree.item(selected[0], "values")
            file_name = values[0]

            # Get save location
            from tkinter import filedialog

            file_path = filedialog.asksaveasfilename(
                defaultextension="",
                initialfile=file_name,
                title="Download File"
            )

            if not file_path:
                return

            # Get file service
            service = get_service("IPatternService")

            # Get file content
            file = service.get_pattern_file(file_id)

            if not file or not file.get("content"):
                messagebox.showerror("Error", "Failed to retrieve file content.")
                return

            # Save file
            with open(file_path, "wb") as f:
                f.write(file.get("content"))

            messagebox.showinfo("Success", f"File saved to {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            self.show_error("Error", f"Failed to download file: {str(e)}")

    def on_delete_file(self):
        """Handle delete file button click."""
        # Get selected file ID
        file_id = self.get_selected_file_id()
        if not file_id:
            return

        # Get file name
        selected = self.files_tree.selection()
        if not selected:
            return

        values = self.files_tree.item(selected[0], "values")
        file_name = values[0]

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the file '{file_name}'?\n\n"
                "This action cannot be undone."
        ):
            return

        try:
            # Get file service
            service = get_service("IPatternService")

            # Delete file
            result = service.delete_pattern_file(file_id)

            if result:
                messagebox.showinfo("Success", f"File '{file_name}' deleted successfully.")
                self.refresh()
            else:
                self.show_error("Error", f"Failed to delete file '{file_name}'.")
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            self.show_error("Error", f"Failed to delete file: {str(e)}")

    def refresh(self):
        """Refresh the view."""
        if self.pattern_id:
            # Reload the pattern data
            self.load_pattern()
        elif self.create_new:
            # Clear form fields for new pattern
            for var_name, var in self.form_vars.items():
                if isinstance(var, tk.StringVar):
                    var.set("")
                elif isinstance(var, tk.Text):
                    var.delete("1.0", tk.END)

            # Clear components list
            self.components = []
            self.update_components_list()

            # Clear materials list
            self.update_materials_list()

            # Clear files list
            self.update_files_list()