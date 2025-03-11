# gui/views/projects/project_component_view.py
"""
Project component view for creating, viewing, and editing project components.

This view provides a detailed interface for managing individual project components,
with sections for component details, materials, and assembly instructions.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import ComponentType
from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge


class ProjectComponentView(BaseView):
    """
    View for displaying and editing project component details.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the project component view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                project_id: ID of the project
                component_id: ID of the component to view/edit (None for new component)
                create_new: Whether to create a new component
                readonly: Whether the view should be read-only
        """
        super().__init__(parent)
        self.title = "Component Details"
        self.icon = "🧩"
        self.logger = logging.getLogger(__name__)

        # Store view parameters
        self.project_id = kwargs.get("project_id")
        self.component_id = kwargs.get("component_id")
        self.create_new = kwargs.get("create_new", False)
        self.readonly = kwargs.get("readonly", False)

        if not self.project_id:
            messagebox.showerror("Error", "Project ID is required")
            self.on_back()
            return

        if self.create_new:
            self.title = "New Component"
            self.readonly = False
        elif self.readonly:
            self.title = "View Component"
        else:
            self.title = "Edit Component"

        # Initialize services
        self.project_service = get_service("project_service")
        self.component_service = get_service("component_service")
        self.material_service = get_service("material_service")

        # Initialize form variables
        self.form_vars = {}
        self.materials = []

        # Build the view
        self.build()

        # Load data if viewing or editing an existing component
        if self.component_id:
            self.load_component()

    def build(self):
        """Build the component details view."""
        super().build()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.details_tab = ttk.Frame(self.notebook)
        self.materials_tab = ttk.Frame(self.notebook)
        self.assembly_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.details_tab, text="Details")
        self.notebook.add(self.materials_tab, text="Materials")
        self.notebook.add(self.assembly_tab, text="Assembly")

        # Create content for each tab
        self.create_details_tab()
        self.create_materials_tab()
        self.create_assembly_tab()

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

    def create_details_tab(self):
        """Create the details tab content."""
        frame = ttk.Frame(self.details_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Component name
        ttk.Label(frame, text="Component Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["name"] = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable=self.form_vars["name"], width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        name_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

        # Component type
        ttk.Label(frame, text="Component Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["type"] = tk.StringVar()
        type_combo = ttk.Combobox(frame, textvariable=self.form_vars["type"], width=28)
        type_combo["values"] = [t.value.replace("_", " ").title() for t in ComponentType]
        type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        type_combo.configure(state="readonly" if not self.readonly else tk.DISABLED)

        # Quantity
        ttk.Label(frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["quantity"] = tk.StringVar(value="1")
        quantity_spin = ttk.Spinbox(frame, from_=1, to=100, textvariable=self.form_vars["quantity"], width=5)
        quantity_spin.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        quantity_spin.configure(state=tk.NORMAL if not self.readonly else "readonly")

        # Status
        ttk.Label(frame, text="Status:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        status_frame = ttk.Frame(frame)
        status_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        self.form_vars["status"] = tk.StringVar(value="not_started")
        status_options = ["not_started", "in_progress", "completed", "on_hold"]
        status_combo = ttk.Combobox(status_frame, textvariable=self.form_vars["status"], width=15)
        status_combo["values"] = [s.replace("_", " ").title() for s in status_options]
        status_combo.pack(side=tk.LEFT)
        status_combo.configure(state="readonly" if not self.readonly else tk.DISABLED)

        self.status_badge = StatusBadge(status_frame, "Not Started", "not_started")
        self.status_badge.pack(side=tk.LEFT, padx=(10, 0))

        # Description
        ttk.Label(frame, text="Description:").grid(row=4, column=0, sticky=tk.NW, padx=5, pady=5)
        self.description_text = tk.Text(frame, width=30, height=5)
        self.description_text.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        self.description_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)

        # Dimensions frame
        dimensions_frame = ttk.LabelFrame(frame, text="Dimensions")
        dimensions_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=10)

        # Dimensions grid
        dim_grid = ttk.Frame(dimensions_frame)
        dim_grid.pack(fill=tk.X, padx=10, pady=5)

        # Width
        ttk.Label(dim_grid, text="Width:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["width"] = tk.StringVar()
        width_entry = ttk.Entry(dim_grid, textvariable=self.form_vars["width"], width=10)
        width_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        width_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")
        ttk.Label(dim_grid, text="mm").grid(row=0, column=2, sticky=tk.W)

        # Height
        ttk.Label(dim_grid, text="Height:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.form_vars["height"] = tk.StringVar()
        height_entry = ttk.Entry(dim_grid, textvariable=self.form_vars["height"], width=10)
        height_entry.grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        height_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")
        ttk.Label(dim_grid, text="mm").grid(row=0, column=5, sticky=tk.W)

        # Length/Depth
        ttk.Label(dim_grid, text="Length:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["length"] = tk.StringVar()
        length_entry = ttk.Entry(dim_grid, textvariable=self.form_vars["length"], width=10)
        length_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        length_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")
        ttk.Label(dim_grid, text="mm").grid(row=1, column=2, sticky=tk.W)

        # Thickness
        ttk.Label(dim_grid, text="Thickness:").grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        self.form_vars["thickness"] = tk.StringVar()
        thickness_entry = ttk.Entry(dim_grid, textvariable=self.form_vars["thickness"], width=10)
        thickness_entry.grid(row=1, column=4, sticky=tk.W, padx=5, pady=5)
        thickness_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")
        ttk.Label(dim_grid, text="mm").grid(row=1, column=5, sticky=tk.W)

        # Advanced attributes section
        attributes_frame = ttk.LabelFrame(frame, text="Advanced Attributes")
        attributes_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=10)

        attributes_grid = ttk.Frame(attributes_frame)
        attributes_grid.pack(fill=tk.X, padx=10, pady=5)

        # Assigned to
        ttk.Label(attributes_grid, text="Assigned To:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.form_vars["assigned_to"] = tk.StringVar()
        assigned_entry = ttk.Entry(attributes_grid, textvariable=self.form_vars["assigned_to"], width=20)
        assigned_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        assigned_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

        # Priority
        ttk.Label(attributes_grid, text="Priority:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.form_vars["priority"] = tk.StringVar(value="Medium")
        priority_combo = ttk.Combobox(attributes_grid, textvariable=self.form_vars["priority"], width=10)
        priority_combo["values"] = ["Low", "Medium", "High", "Critical"]
        priority_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        priority_combo.configure(state="readonly" if not self.readonly else tk.DISABLED)

        # Custom fields (placeholder for future extensibility)
        custom_fields_frame = ttk.LabelFrame(frame, text="Custom Fields")
        custom_fields_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=10)

        ttk.Label(custom_fields_frame, text="No custom fields defined").pack(padx=10, pady=10)

    def create_materials_tab(self):
        """Create the materials tab content."""
        frame = ttk.Frame(self.materials_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Header with actions
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            header_frame,
            text="Component Materials",
            font=("TkDefaultFont", 12, "bold")
        ).pack(side=tk.LEFT)

        if not self.readonly:
            ttk.Button(
                header_frame,
                text="Add Material",
                command=self.on_add_material
            ).pack(side=tk.RIGHT, padx=5)

        # Materials treeview
        columns = ("id", "material_name", "type", "quantity", "unit", "available", "status")
        self.materials_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=10
        )

        # Configure columns
        self.materials_tree.heading("id", text="ID")
        self.materials_tree.heading("material_name", text="Material")
        self.materials_tree.heading("type", text="Type")
        self.materials_tree.heading("quantity", text="Quantity")
        self.materials_tree.heading("unit", text="Unit")
        self.materials_tree.heading("available", text="Available")
        self.materials_tree.heading("status", text="Status")

        self.materials_tree.column("id", width=50, minwidth=50)
        self.materials_tree.column("material_name", width=200, minwidth=150)
        self.materials_tree.column("type", width=100, minwidth=100)
        self.materials_tree.column("quantity", width=80, minwidth=80)
        self.materials_tree.column("unit", width=80, minwidth=80)
        self.materials_tree.column("available", width=80, minwidth=80)
        self.materials_tree.column("status", width=100, minwidth=100)

        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.materials_tree.configure(yscrollcommand=scrollbar.set)

        # Material actions
        actions_frame = ttk.Frame(frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0))

        if not self.readonly:
            ttk.Button(
                actions_frame,
                text="Edit Material",
                command=self.on_edit_material,
                state=tk.DISABLED
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                actions_frame,
                text="Remove Material",
                command=self.on_remove_material,
                state=tk.DISABLED
            ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="Check Availability",
            command=self.on_check_availability
        ).pack(side=tk.RIGHT, padx=5)

        # Bind selection event
        self.materials_tree.bind("<<TreeviewSelect>>", self.on_material_select)

        # If readonly, disable all buttons except Check Availability
        if self.readonly:
            for child in actions_frame.winfo_children():
                if isinstance(child, ttk.Button) and child.cget("text") != "Check Availability":
                    child.configure(state=tk.DISABLED)

    def create_assembly_tab(self):
        """Create the assembly tab content."""
        frame = ttk.Frame(self.assembly_tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Assembly instructions
        ttk.Label(
            frame,
            text="Assembly Instructions",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        self.assembly_text = tk.Text(frame, wrap=tk.WORD, height=15)
        self.assembly_text.pack(fill=tk.BOTH, expand=True)
        self.assembly_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)

        # Assembly notes
        notes_frame = ttk.LabelFrame(frame, text="Notes")
        notes_frame.pack(fill=tk.X, pady=(10, 0))

        self.notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=5)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notes_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)

    def load_component(self):
        """Load component data from the service."""
        try:
            # Get component data from service
            component = self.component_service.get_component(
                self.component_id,
                include_materials=True
            )

            if not component:
                messagebox.showerror("Error", f"Component not found with ID {self.component_id}")
                self.on_back()
                return

            # Update title
            self.title = f"{component.name} - {'View' if self.readonly else 'Edit'} Component"
            component_name_label = self.header.winfo_children()[0]
            if isinstance(component_name_label, ttk.Label):
                component_name_label.configure(text=self.title)

            # Populate form variables
            self.form_vars["name"].set(component.name)

            type_str = component.type.value.replace("_", " ").title() if hasattr(component,
                                                                                 'type') and component.type else ""
            self.form_vars["type"].set(type_str)

            # Quantity
            if hasattr(component, 'quantity') and component.quantity is not None:
                self.form_vars["quantity"].set(str(component.quantity))

            # Status
            if hasattr(component, 'status') and component.status:
                status_str = component.status.replace("_", " ").title()
                status_value = component.status
                self.form_vars["status"].set(status_value)
                self.status_badge.set_text(status_str, status_value)

            # Description
            if hasattr(component, 'description') and component.description:
                self.description_text.delete("1.0", tk.END)
                self.description_text.insert("1.0", component.description)

            # Dimensions
            if hasattr(component, 'dimensions') and component.dimensions:
                dims = component.dimensions
                if isinstance(dims, dict):
                    for dim_name in ['width', 'height', 'length', 'thickness']:
                        if dim_name in dims and dims[dim_name] is not None:
                            self.form_vars[dim_name].set(str(dims[dim_name]))

            # Advanced attributes
            if hasattr(component, 'assigned_to') and component.assigned_to:
                self.form_vars["assigned_to"].set(component.assigned_to)

            if hasattr(component, 'priority') and component.priority:
                self.form_vars["priority"].set(component.priority)

            # Assembly instructions
            if hasattr(component, 'assembly_instructions') and component.assembly_instructions:
                self.assembly_text.delete("1.0", tk.END)
                self.assembly_text.insert("1.0", component.assembly_instructions)

            # Notes
            if hasattr(component, 'notes') and component.notes:
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", component.notes)

            # Store materials
            if hasattr(component, 'materials'):
                self.materials = component.materials
                self.update_materials_list()

        except Exception as e:
            self.logger.error(f"Error loading component: {e}")
            messagebox.showerror("Error", f"Failed to load component: {str(e)}")

    def update_materials_list(self):
        """Update the materials list in the treeview."""
        # Clear existing items
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)

        # Insert materials
        for material in self.materials:
            # Extract material values
            material_id = material.material_id if hasattr(material, 'material_id') else "N/A"
            name = material.name if hasattr(material, 'name') else "Unnamed"

            type_str = "Unknown"
            if hasattr(material, 'type') and material.type:
                type_str = material.type.value.replace("_", " ").title()

            quantity = material.quantity if hasattr(material, 'quantity') else 1

            unit = "piece"
            if hasattr(material, 'unit') and material.unit:
                unit = material.unit.value

            available = "--"
            status = "Unknown"
            if hasattr(material, 'available') and material.available is not None:
                available = material.available
                status = "Available" if material.available >= quantity else "Limited" if material.available > 0 else "Not Available"

            # Insert into treeview
            item_id = f"mat_{material_id}"
            self.materials_tree.insert(
                '', 'end',
                iid=item_id,
                values=(material_id, name, type_str, quantity, unit, available, status)
            )

            # Apply status styling
            if status == "Available":
                self.materials_tree.tag_configure("available", background=COLORS["success_light"])
                self.materials_tree.item(item_id, tags=("available",))
            elif status == "Not Available":
                self.materials_tree.tag_configure("unavailable", background=COLORS["error_light"])
                self.materials_tree.item(item_id, tags=("unavailable",))
            elif status == "Limited":
                self.materials_tree.tag_configure("limited", background=COLORS["warning_light"])
                self.materials_tree.item(item_id, tags=("limited",))

    def on_material_select(self, event):
        """Handle material selection in the treeview.

        Args:
            event: The selection event
        """
        material_id = self.materials_tree.focus()

        # Enable/disable buttons based on selection
        state = tk.NORMAL if material_id else tk.DISABLED

        for child in self.materials_tab.winfo_children():
            if isinstance(child, ttk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Button) and widget.cget("text") in ["Edit Material", "Remove Material"]:
                        widget.configure(state=state if not self.readonly else tk.DISABLED)

    def collect_form_data(self):
        """Collect data from form fields.

        Returns:
            Dictionary of form data
        """
        data = {}

        # Basic fields
        data["name"] = self.form_vars["name"].get()
        data["project_id"] = self.project_id

        # Convert display values back to enum values
        type_str = self.form_vars["type"].get()
        if type_str:
            data["type"] = type_str.lower().replace(" ", "_")

        # Quantity
        quantity_str = self.form_vars["quantity"].get()
        if quantity_str and quantity_str.isdigit():
            data["quantity"] = int(quantity_str)

        # Status
        status_str = self.form_vars["status"].get()
        if status_str:
            data["status"] = status_str

        # Description
        data["description"] = self.description_text.get("1.0", tk.END).strip()

        # Dimensions
        dimensions = {}
        for dim_name in ['width', 'height', 'length', 'thickness']:
            dim_str = self.form_vars[dim_name].get()
            if dim_str:
                try:
                    dimensions[dim_name] = float(dim_str)
                except ValueError:
                    # Ignore invalid values
                    pass

        if dimensions:
            data["dimensions"] = dimensions

        # Advanced attributes
        data["assigned_to"] = self.form_vars["assigned_to"].get()
        data["priority"] = self.form_vars["priority"].get()

        # Assembly instructions
        data["assembly_instructions"] = self.assembly_text.get("1.0", tk.END).strip()

        # Notes
        data["notes"] = self.notes_text.get("1.0", tk.END).strip()

        # Materials (keep existing materials, add/remove in separate methods)
        if hasattr(self, 'materials') and self.materials:
            material_ids = []
            material_quantities = {}

            for material in self.materials:
                material_id = material.material_id if hasattr(material, 'material_id') else material.id
                quantity = material.quantity if hasattr(material, 'quantity') else 1

                material_ids.append(material_id)
                material_quantities[material_id] = quantity

            data["material_ids"] = material_ids
            data["material_quantities"] = material_quantities

        return data

    def validate_form(self):
        """Validate form data.

        Returns:
            Tuple of (valid, error_message)
        """
        # Check required fields
        if not self.form_vars["name"].get():
            return False, "Component name is required."

        if not self.form_vars["type"].get():
            return False, "Component type is required."

        # Validate quantity
        quantity_str = self.form_vars["quantity"].get()
        if not quantity_str or not quantity_str.isdigit() or int(quantity_str) < 1:
            return False, "Quantity must be a positive integer."

        # Validate dimensions
        for dim_name in ['width', 'height', 'length', 'thickness']:
            dim_str = self.form_vars[dim_name].get()
            if dim_str:
                try:
                    float(dim_str)
                except ValueError:
                    return False, f"{dim_name.title()} must be a number."

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
                # Create new component
                component = self.component_service.create_component(data)
                # Add to project
                self.project_service.add_component_to_project(
                    self.project_id, component.id, int(data.get("quantity", 1))
                )

                self.component_id = component.id

                # Update view state
                self.create_new = False

                # Show success message
                messagebox.showinfo("Success", f"Component '{component.name}' created successfully.")

                # Publish event
                publish("component_updated", {"project_id": self.project_id, "component_id": component.id})

                # Navigate back to project details
                self.on_back()
            else:
                # Update existing component
                component = self.component_service.update_component(
                    self.component_id, data
                )

                # Update project component
                self.project_service.update_project_component(
                    self.project_id,
                    self.component_id,
                    {"quantity": int(data.get("quantity", 1))}
                )

                # Show success message
                messagebox.showinfo("Success", f"Component '{component.name}' updated successfully.")

                # Publish event
                publish("component_updated", {"project_id": self.project_id, "component_id": component.id})

                # Reload component data
                self.load_component()

        except Exception as e:
            self.logger.error(f"Error saving component: {e}")
            messagebox.showerror("Save Error", f"Failed to save component: {str(e)}")

    def on_edit(self):
        """Handle edit button click (from readonly mode)."""
        # Change to edit mode
        self.readonly = False

        # Navigate to edit view
        self.parent.master.show_view(
            "project_component",
            add_to_history=True,
            view_data={
                "project_id": self.project_id,
                "component_id": self.component_id,
                "readonly": False
            }
        )

    def on_back(self):
        """Handle back button click."""
        self.parent.master.show_view(
            "project_details",
            view_data={"project_id": self.project_id}
        )

    def on_add_material(self):
        """Handle add material button click."""
        if self.create_new and not self.component_id:
            messagebox.showwarning(
                "Not Available",
                "You must save the component before adding materials."
            )
            return

        # Create material selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Add Material")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        # Create search frame
        search_frame = ttk.Frame(dialog, padding=5)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Material type filter
        ttk.Label(search_frame, text="Type:").pack(side=tk.LEFT, padx=(10, 5))
        type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(search_frame, textvariable=type_var, width=15, state="readonly")
        type_combo["values"] = ["All", "Leather", "Hardware", "Thread", "Adhesive", "Other"]
        type_combo.pack(side=tk.LEFT, padx=5)

        def search_materials():
            """Search materials based on criteria."""
            search_text = search_var.get()
            material_type = type_var.get() if type_var.get() != "All" else None

            try:
                # Get materials from service
                materials = self.material_service.search_materials(
                    search_text=search_text,
                    material_type=material_type
                )

                # Clear existing items
                for item in materials_tree.get_children():
                    materials_tree.delete(item)

                # Insert materials
                for material in materials:
                    material_id = material.id if hasattr(material, 'id') else "N/A"
                    name = material.name if hasattr(material, 'name') else "Unnamed"

                    type_str = "Unknown"
                    if hasattr(material, 'type') and material.type:
                        type_str = material.type.value.replace("_", " ").title()

                    # Get inventory status
                    inventory_status = "Unknown"
                    quantity_available = 0

                    if hasattr(material, 'inventory') and material.inventory:
                        inventory = material.inventory
                        status = inventory.status.value if hasattr(inventory,
                                                                   'status') and inventory.status else "unknown"
                        inventory_status = status.replace("_", " ").title()
                        quantity_available = inventory.quantity if hasattr(inventory, 'quantity') else 0

                    materials_tree.insert(
                        '', 'end',
                        iid=material_id,
                        values=(material_id, name, type_str, inventory_status, quantity_available)
                    )

            except Exception as e:
                self.logger.error(f"Error searching materials: {e}")
                messagebox.showerror("Search Error", f"Failed to search materials: {str(e)}", parent=dialog)

        ttk.Button(
            search_frame,
            text="Search",
            command=search_materials
        ).pack(side=tk.LEFT, padx=5)

        # Create materials treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "type", "status", "available")
        materials_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        materials_tree.heading("id", text="ID")
        materials_tree.heading("name", text="Name")
        materials_tree.heading("type", text="Type")
        materials_tree.heading("status", text="Status")
        materials_tree.heading("available", text="Available")

        materials_tree.column("id", width=50)
        materials_tree.column("name", width=200)
        materials_tree.column("type", width=100)
        materials_tree.column("status", width=100)
        materials_tree.column("available", width=80)

        materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=materials_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        materials_tree.configure(yscrollcommand=scrollbar.set)

        # Quantity frame
        quantity_frame = ttk.LabelFrame(dialog, text="Quantity")
        quantity_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(quantity_frame, text="Quantity:").grid(row=0, column=0, padx=5, pady=5)
        quantity_var = tk.StringVar(value="1")
        quantity_spin = ttk.Spinbox(quantity_frame, from_=0.1, to=1000, increment=0.1, textvariable=quantity_var)
        quantity_spin.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(quantity_frame, text="Unit:").grid(row=0, column=2, padx=5, pady=5)
        unit_var = tk.StringVar(value="piece")
        unit_combo = ttk.Combobox(quantity_frame, textvariable=unit_var, width=15, state="readonly")
        unit_combo["values"] = ["piece", "meter", "square_meter", "square_foot", "gram", "kilogram"]
        unit_combo.grid(row=0, column=3, padx=5, pady=5)

        # Handle material selection
        def add_selected_material():
            """Add the selected material to the component."""
            selected_id = materials_tree.focus()
            if not selected_id:
                messagebox.showwarning("No Selection", "Please select a material to add.", parent=dialog)
                return

            # Get material data
            material_data = materials_tree.item(selected_id, "values")
            material_id = material_data[0]
            material_name = material_data[1]

            # Check if already added
            for material in self.materials:
                existing_id = material.material_id if hasattr(material, 'material_id') else material.id
                if str(existing_id) == str(material_id):
                    messagebox.showwarning(
                        "Already Added",
                        f"Material '{material_name}' is already added to this component.",
                        parent=dialog
                    )
                    return

            # Get quantity
            try:
                quantity = float(quantity_var.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than zero.", parent=dialog)
                    return
            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a number.", parent=dialog)
                return

            try:
                # Add material to component
                if self.component_id:
                    result = self.component_service.add_material_to_component(
                        self.component_id,
                        material_id,
                        quantity,
                        unit_var.get()
                    )

                    if result:
                        # Reload component to update materials
                        self.load_component()

                        # Close dialog
                        dialog.destroy()

                        # Show success message
                        messagebox.showinfo("Success", f"Material '{material_name}' added to component.")
                else:
                    # Add to local materials list
                    self.materials.append({
                        "material_id": material_id,
                        "name": material_name,
                        "type": material_data[2],
                        "quantity": quantity,
                        "unit": unit_var.get(),
                        "available": material_data[4]
                    })

                    # Update materials list
                    self.update_materials_list()

                    # Close dialog
                    dialog.destroy()

            except Exception as e:
                self.logger.error(f"Error adding material: {e}")
                messagebox.showerror("Error", f"Failed to add material: {str(e)}", parent=dialog)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Add Material",
            command=add_selected_material
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Initial search
        search_materials()

        # Set focus to search entry
        search_entry.focus_set()

    def on_edit_material(self):
        """Handle edit material button click."""
        selected_id = self.materials_tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a material to edit.")
            return

        # Get material data
        material_values = self.materials_tree.item(selected_id, "values")
        material_id = material_values[0]
        material_name = material_values[1]
        current_quantity = material_values[3]
        current_unit = material_values[4]

        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Material: {material_name}")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        # Create form
        ttk.Label(dialog, text="Material:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Label(dialog, text=material_name).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="Quantity:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        quantity_var = tk.StringVar(value=current_quantity)
        quantity_spin = ttk.Spinbox(dialog, from_=0.1, to=1000, increment=0.1, textvariable=quantity_var)
        quantity_spin.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="Unit:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        unit_var = tk.StringVar(value=current_unit)
        unit_combo = ttk.Combobox(dialog, textvariable=unit_var, width=15, state="readonly")
        unit_combo["values"] = ["piece", "meter", "square_meter", "square_foot", "gram", "kilogram"]
        unit_combo.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # Handle save
        def update_material():
            """Update the material quantity."""
            try:
                quantity = float(quantity_var.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than zero.", parent=dialog)
                    return
            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a number.", parent=dialog)
                return

            try:
                # Update material in component
                result = self.component_service.update_component_material(
                    self.component_id,
                    material_id,
                    quantity,
                    unit_var.get()
                )

                if result:
                    # Reload component to update materials
                    self.load_component()

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    messagebox.showinfo("Success", f"Material '{material_name}' updated.")

            except Exception as e:
                self.logger.error(f"Error updating material: {e}")
                messagebox.showerror("Error", f"Failed to update material: {str(e)}", parent=dialog)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text="Update",
            command=update_material
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)

    def on_remove_material(self):
        """Handle remove material button click."""
        selected_id = self.materials_tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a material to remove.")
            return

        # Get material data
        material_values = self.materials_tree.item(selected_id, "values")
        material_id = material_values[0]
        material_name = material_values[1]

        # Confirm removal
        if not messagebox.askyesno(
                "Confirm Remove",
                f"Are you sure you want to remove {material_name} from the component?"
        ):
            return

        try:
            # Remove material from component
            result = self.component_service.remove_material_from_component(
                self.component_id, material_id
            )

            if result:
                # Reload component to update materials
                self.load_component()

                # Show success message
                messagebox.showinfo("Success", f"Material '{material_name}' has been removed from the component.")

        except Exception as e:
            self.logger.error(f"Error removing material: {e}")
            messagebox.showerror("Remove Error", f"Failed to remove material: {str(e)}")

    def on_check_availability(self):
        """Handle check availability button click."""
        if not self.materials:
            messagebox.showinfo("No Materials", "This component has no materials to check.")
            return

        try:
            # Check availability via service
            availability = self.component_service.check_materials_availability(
                self.component_id if self.component_id else None,
                [m.material_id if hasattr(m, 'material_id') else m.id for m in self.materials],
                [m.quantity if hasattr(m, 'quantity') else 1 for m in self.materials]
            )

            # Update materials list with availability info
            for material in self.materials:
                material_id = material.material_id if hasattr(material, 'material_id') else material.id
                if material_id in availability:
                    material.available = availability[material_id].get("available", 0)

            # Update display
            self.update_materials_list()

            # Show summary
            available_count = sum(1 for m in availability.values() if m.get("status") == "available")
            limited_count = sum(1 for m in availability.values() if m.get("status") == "limited")
            unavailable_count = sum(1 for m in availability.values() if m.get("status") == "unavailable")

            message = f"Material availability checked.\n\n"
            message += f"Available: {available_count}\n"
            message += f"Limited: {limited_count}\n"
            message += f"Not Available: {unavailable_count}"

            messagebox.showinfo("Availability Check", message)

        except Exception as e:
            self.logger.error(f"Error checking availability: {e}")
            messagebox.showerror("Check Error", f"Failed to check availability: {str(e)}")

    def refresh(self):
        """Refresh the view."""
        if self.component_id:
            self.load_component()