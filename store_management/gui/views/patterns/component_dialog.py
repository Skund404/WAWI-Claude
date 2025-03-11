# gui/views/patterns/component_dialog.py
"""
Component dialog for creating and editing pattern components.

Allows defining component properties and material requirements.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional

from database.models.enums import ComponentType, MeasurementUnit
from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from gui.utils.service_access import get_service
from gui.utils.event_bus import publish

logger = logging.getLogger(__name__)


class ComponentDialog(BaseDialog):
    """
    Dialog for creating and editing pattern components.
    """

    def __init__(self, parent, component_id=None, pattern_id=None, readonly=False):
        """
        Initialize the component dialog.

        Args:
            parent: The parent widget
            component_id: ID of the component to edit (None for new components)
            pattern_id: ID of the pattern the component belongs to (required for new components)
            readonly: Whether the dialog should be read-only
        """
        self.component_id = component_id
        self.pattern_id = pattern_id
        self.readonly = readonly
        self.component = None

        # Form variables
        self.form_vars = {}
        self.dimension_vars = {}

        # Materials list
        self.materials_list = []

        # Call parent constructor
        title = "Component Details" if readonly else ("Edit Component" if component_id else "New Component")
        super().__init__(parent, title=title, width=600, height=500)

    def create_layout(self):
        """Create the dialog layout."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.info_tab = ttk.Frame(self.notebook)
        self.dimensions_tab = ttk.Frame(self.notebook)
        self.materials_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.info_tab, text="Information")
        self.notebook.add(self.dimensions_tab, text="Dimensions")
        self.notebook.add(self.materials_tab, text="Materials")

        # Create tab contents
        self.create_info_tab()
        self.create_dimensions_tab()
        self.create_materials_tab()

        # Create buttons
        button_frame = ttk.Frame(self.dialog_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        if not self.readonly:
            save_btn = ttk.Button(
                button_frame,
                text="Save",
                command=self.on_save
            )
            save_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ttk.Button(
            button_frame,
            text="Close" if self.readonly else "Cancel",
            command=self.on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Load component data if editing an existing component
        if self.component_id:
            self.load_component()

    def create_info_tab(self):
        """Create the information tab."""
        # Create form container
        form_frame = ttk.Frame(self.info_tab, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Component Name
        ttk.Label(form_frame, text="Component Name:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["name"] = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=self.form_vars["name"], width=40)
        name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        if self.readonly:
            name_entry.configure(state="readonly")

        # Component Type
        ttk.Label(form_frame, text="Type:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        self.form_vars["type"] = tk.StringVar()
        type_combo = ttk.Combobox(form_frame, textvariable=self.form_vars["type"], width=30)
        type_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        type_combo["values"] = self._get_component_type_values()

        if self.readonly:
            type_combo.configure(state="readonly")

        # Bind type change to update dimensions fields
        type_combo.bind("<<ComboboxSelected>>", self.on_type_changed)

        # Description
        ttk.Label(form_frame, text="Description:").grid(
            row=2, column=0, sticky="nw", padx=5, pady=5)

        description_frame = ttk.Frame(form_frame)
        description_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        self.form_vars["description"] = tk.Text(description_frame, height=5, width=40, wrap=tk.WORD)
        self.form_vars["description"].pack(fill=tk.BOTH, expand=True)

        if self.readonly:
            self.form_vars["description"].configure(state="disabled")

        # Notes
        ttk.Label(form_frame, text="Notes:").grid(
            row=3, column=0, sticky="nw", padx=5, pady=5)

        notes_frame = ttk.Frame(form_frame)
        notes_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        self.form_vars["notes"] = tk.Text(notes_frame, height=5, width=40, wrap=tk.WORD)
        self.form_vars["notes"].pack(fill=tk.BOTH, expand=True)

        if self.readonly:
            self.form_vars["notes"].configure(state="disabled")

    def create_dimensions_tab(self):
        """Create the dimensions tab."""
        # Create dimensions container
        dim_frame = ttk.Frame(self.dimensions_tab, padding=10)
        dim_frame.pack(fill=tk.BOTH, expand=True)

        # Create dimension fields container - will be populated based on component type
        self.dimensions_container = ttk.LabelFrame(dim_frame, text="Dimensions")
        self.dimensions_container.pack(fill=tk.BOTH, expand=True)

        # Add help text
        help_frame = ttk.Frame(dim_frame)
        help_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        help_text = ttk.Label(
            help_frame,
            text="Note: Select a component type on the Information tab to define dimensions.",
            foreground=COLORS["text_secondary"],
            wraplength=400,
            justify="left"
        )
        help_text.pack(anchor="w")

    def create_materials_tab(self):
        """Create the materials tab."""
        # Create materials container
        materials_frame = ttk.Frame(self.materials_tab, padding=10)
        materials_frame.pack(fill=tk.BOTH, expand=True)

        # Create toolbar with buttons
        toolbar = ttk.Frame(materials_frame)
        toolbar.pack(fill=tk.X, expand=False, pady=(0, 10))

        if not self.readonly:
            add_btn = ttk.Button(
                toolbar,
                text="Add Material",
                command=self.on_add_material
            )
            add_btn.pack(side=tk.LEFT, padx=(0, 5))

            remove_btn = ttk.Button(
                toolbar,
                text="Remove Material",
                command=self.on_remove_material
            )
            remove_btn.pack(side=tk.LEFT)

        # Create materials list with treeview
        list_frame = ttk.Frame(materials_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("material", "type", "quantity", "unit")
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

        # Define columns
        self.materials_tree.column("material", width=200)
        self.materials_tree.column("type", width=100)
        self.materials_tree.column("quantity", width=80)
        self.materials_tree.column("unit", width=80)

        # Add scrollbar
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=y_scrollbar.set)

        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add double-click binding for editing materials (if not readonly)
        if not self.readonly:
            self.materials_tree.bind("<Double-1>", self.on_edit_material)

    def load_component(self):
        """Load component data from service."""
        try:
            # Get the component service
            service = get_service("IComponentService")

            # Get component data
            self.component = service.get_component_by_id(
                self.component_id,
                include_materials=True
            )

            if not self.component:
                messagebox.showerror("Error", "Component not found.")
                self.on_cancel()
                return

            # Get pattern ID from component
            self.pattern_id = self.component.get("pattern_id")

            # Populate form fields
            self.populate_form()

            # Populate materials list
            self.materials_list = self.component.get("materials", [])
            self.update_materials_list()
        except Exception as e:
            logger.error(f"Error loading component: {str(e)}")
            messagebox.showerror("Error", f"Failed to load component: {str(e)}")
            self.on_cancel()

    def populate_form(self):
        """Populate form fields with component data."""
        if not self.component:
            return

        # Basic information
        self.form_vars["name"].set(self.component.get("name", ""))
        self.form_vars["type"].set(self.component.get("type", "").replace("_", " ").title())

        # Description and notes
        if isinstance(self.form_vars["description"], tk.Text):
            self.form_vars["description"].delete("1.0", tk.END)
            self.form_vars["description"].insert("1.0", self.component.get("description", ""))

        if isinstance(self.form_vars["notes"], tk.Text):
            self.form_vars["notes"].delete("1.0", tk.END)
            self.form_vars["notes"].insert("1.0", self.component.get("notes", ""))

        # Update dimension fields based on type
        self.on_type_changed(None)

        # Populate dimension fields
        if self.component.get("type") in ["rectangular", "rectangular_panel"]:
            if "width" in self.dimension_vars and "width" in self.component:
                self.dimension_vars["width"].set(str(self.component.get("width", 0)))
            if "height" in self.dimension_vars and "height" in self.component:
                self.dimension_vars["height"].set(str(self.component.get("height", 0)))
            if "thickness" in self.dimension_vars and "thickness" in self.component:
                self.dimension_vars["thickness"].set(str(self.component.get("thickness", 0)))
        elif self.component.get("type") in ["circular", "ring"]:
            if "diameter" in self.dimension_vars and "diameter" in self.component:
                self.dimension_vars["diameter"].set(str(self.component.get("diameter", 0)))
            if "thickness" in self.dimension_vars and "thickness" in self.component:
                self.dimension_vars["thickness"].set(str(self.component.get("thickness", 0)))
        elif self.component.get("type") in ["strap", "strip"]:
            if "length" in self.dimension_vars and "length" in self.component:
                self.dimension_vars["length"].set(str(self.component.get("length", 0)))
            if "width" in self.dimension_vars and "width" in self.component:
                self.dimension_vars["width"].set(str(self.component.get("width", 0)))
            if "thickness" in self.dimension_vars and "thickness" in self.component:
                self.dimension_vars["thickness"].set(str(self.component.get("thickness", 0)))

    def on_type_changed(self, event):
        """
        Handle component type change.

        Args:
            event: The combobox selection event
        """
        # Get selected type
        component_type = self.form_vars["type"].get().lower().replace(" ", "_")

        # Clear dimension fields
        for widget in self.dimensions_container.winfo_children():
            widget.destroy()

        self.dimension_vars = {}

        # Create appropriate dimension fields based on type
        if component_type in ["rectangular", "rectangular_panel"]:
            self._create_rectangular_dimensions()
        elif component_type in ["circular", "ring"]:
            self._create_circular_dimensions()
        elif component_type in ["strap", "strip"]:
            self._create_strap_dimensions()
        else:
            # Add message that dimensions depend on the component type
            ttk.Label(
                self.dimensions_container,
                text="Please select a component type to define specific dimensions.",
                wraplength=400,
                padding=20
            ).pack(anchor="center", expand=True)

    def _create_rectangular_dimensions(self):
        """Create dimension fields for rectangular components."""
        # Create grid layout
        form_frame = ttk.Frame(self.dimensions_container, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Width
        ttk.Label(form_frame, text="Width:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["width"] = tk.StringVar()
        width_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["width"], width=10)
        width_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=0, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            width_entry.configure(state="readonly")

        # Height
        ttk.Label(form_frame, text="Height:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["height"] = tk.StringVar()
        height_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["height"], width=10)
        height_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=1, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            height_entry.configure(state="readonly")

        # Thickness
        ttk.Label(form_frame, text="Thickness:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["thickness"] = tk.StringVar()
        thickness_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["thickness"], width=10)
        thickness_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=2, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            thickness_entry.configure(state="readonly")

    def _create_circular_dimensions(self):
        """Create dimension fields for circular components."""
        # Create grid layout
        form_frame = ttk.Frame(self.dimensions_container, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Diameter
        ttk.Label(form_frame, text="Diameter:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["diameter"] = tk.StringVar()
        diameter_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["diameter"], width=10)
        diameter_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=0, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            diameter_entry.configure(state="readonly")

        # Thickness
        ttk.Label(form_frame, text="Thickness:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["thickness"] = tk.StringVar()
        thickness_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["thickness"], width=10)
        thickness_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=1, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            thickness_entry.configure(state="readonly")

    def _create_strap_dimensions(self):
        """Create dimension fields for strap or strip components."""
        # Create grid layout
        form_frame = ttk.Frame(self.dimensions_container, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Length
        ttk.Label(form_frame, text="Length:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["length"] = tk.StringVar()
        length_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["length"], width=10)
        length_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=0, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            length_entry.configure(state="readonly")

        # Width
        ttk.Label(form_frame, text="Width:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["width"] = tk.StringVar()
        width_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["width"], width=10)
        width_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=1, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            width_entry.configure(state="readonly")

        # Thickness
        ttk.Label(form_frame, text="Thickness:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)

        self.dimension_vars["thickness"] = tk.StringVar()
        thickness_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["thickness"], width=10)
        thickness_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form_frame, text="mm").grid(
            row=2, column=2, sticky="w", padx=(0, 10))

        if self.readonly:
            thickness_entry.configure(state="readonly")

    def update_materials_list(self):
        """Update the materials list in the treeview."""
        # Clear current items
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)

        # Add materials
        for i, material in enumerate(self.materials_list):
            self.materials_tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    material.get("name", "Unknown"),
                    material.get("type", "").replace("_", " ").title(),
                    material.get("quantity", 0),
                    material.get("unit", "").replace("_", " ").title()
                )
            )

    def collect_form_data(self):
        """
        Collect data from form fields.

        Returns:
            Dictionary of form data
        """
        data = {}

        # Basic information
        data["name"] = self.form_vars["name"].get()
        data["type"] = self.form_vars["type"].get().lower().replace(" ", "_")

        # Description and notes
        if isinstance(self.form_vars["description"], tk.Text):
            data["description"] = self.form_vars["description"].get("1.0", tk.END).strip()

        if isinstance(self.form_vars["notes"], tk.Text):
            data["notes"] = self.form_vars["notes"].get("1.0", tk.END).strip()

        # Pattern ID
        if self.pattern_id:
            data["pattern_id"] = self.pattern_id

        # Dimensions based on type
        if data["type"] in ["rectangular", "rectangular_panel"]:
            if "width" in self.dimension_vars:
                try:
                    data["width"] = float(self.dimension_vars["width"].get())
                except ValueError:
                    pass

            if "height" in self.dimension_vars:
                try:
                    data["height"] = float(self.dimension_vars["height"].get())
                except ValueError:
                    pass

            if "thickness" in self.dimension_vars:
                try:
                    data["thickness"] = float(self.dimension_vars["thickness"].get())
                except ValueError:
                    pass

        elif data["type"] in ["circular", "ring"]:
            if "diameter" in self.dimension_vars:
                try:
                    data["diameter"] = float(self.dimension_vars["diameter"].get())
                except ValueError:
                    pass

            if "thickness" in self.dimension_vars:
                try:
                    data["thickness"] = float(self.dimension_vars["thickness"].get())
                except ValueError:
                    pass

        elif data["type"] in ["strap", "strip"]:
            if "length" in self.dimension_vars:
                try:
                    data["length"] = float(self.dimension_vars["length"].get())
                except ValueError:
                    pass

            if "width" in self.dimension_vars:
                try:
                    data["width"] = float(self.dimension_vars["width"].get())
                except ValueError:
                    pass

            if "thickness" in self.dimension_vars:
                try:
                    data["thickness"] = float(self.dimension_vars["thickness"].get())
                except ValueError:
                    pass

        # Include component ID if editing
        if self.component_id:
            data["id"] = self.component_id

        # Include materials
        if self.materials_list:
            data["materials"] = self.materials_list

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
            return False, "Component name is required."

        if not data.get("type"):
            return False, "Component type is required."

        # Validate dimensions based on type
        if data["type"] in ["rectangular", "rectangular_panel"]:
            if "width" not in data:
                return False, "Width is required for rectangular components."
            if "height" not in data:
                return False, "Height is required for rectangular components."

        elif data["type"] in ["circular", "ring"]:
            if "diameter" not in data:
                return False, "Diameter is required for circular components."

        elif data["type"] in ["strap", "strip"]:
            if "length" not in data:
                return False, "Length is required for strap components."
            if "width" not in data:
                return False, "Width is required for strap components."

        return True, ""

    def _get_component_type_values(self):
        """
        Get component type values for dropdown.

        Returns:
            List of component type values
        """
        try:
            # Try to get component types from the enum service
            enum_service = get_service("IEnumService")
            return [t.value.replace("_", " ").title() for t in enum_service.get_component_types()]
        except Exception as e:
            logger.error(f"Error getting component types: {str(e)}")
            # Fallback to hardcoded values
            return [
                "Rectangular Panel",
                "Strap",
                "Pocket",
                "Gusset",
                "Binding",
                "Lining",
                "Reinforcement",
                "Hardware Mount",
                "Circular",
                "Ring",
                "Strip",
                "Other"
            ]

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

            # Get the component service
            service = get_service("IComponentService")

            # Save the component
            if self.component_id:
                # Update existing component
                result = service.update_component(self.component_id, data)
                if result:
                    messagebox.showinfo("Success", "Component updated successfully.")

                    # Publish event
                    publish("component_updated", {
                        "component_id": self.component_id,
                        "pattern_id": self.pattern_id
                    })

                    self.result = "ok"
                    self.close()
                else:
                    messagebox.showerror("Error", "Failed to update component.")
            else:
                # Create new component
                result = service.create_component(data)
                if result:
                    messagebox.showinfo("Success", "Component created successfully.")

                    # Publish event
                    publish("component_created", {
                        "component_id": result.get("id"),
                        "pattern_id": self.pattern_id
                    })

                    self.result = "ok"
                    self.close()
                else:
                    messagebox.showerror("Error", "Failed to create component.")
        except Exception as e:
            logger.error(f"Error saving component: {str(e)}")
            messagebox.showerror("Error", f"Failed to save component: {str(e)}")

    def on_add_material(self):
        """Handle add material button click."""
        try:
            # Open material selection dialog
            self._show_material_dialog()
        except Exception as e:
            logger.error(f"Error adding material: {str(e)}")
            messagebox.showerror("Error", f"Failed to add material: {str(e)}")

    def on_edit_material(self, event):
        """
        Handle edit material from double-click.

        Args:
            event: The double-click event
        """
        if self.readonly:
            return

        # Get selected material
        selection = self.materials_tree.selection()
        if not selection:
            return

        selected_index = int(selection[0])
        if selected_index < 0 or selected_index >= len(self.materials_list):
            return

        # Open material dialog with selected material
        selected_material = self.materials_list[selected_index]
        self._show_material_dialog(selected_material, selected_index)

    def on_remove_material(self):
        """Handle remove material button click."""
        # Get selected material
        selection = self.materials_tree.selection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a material to remove.")
            return

        selected_index = int(selection[0])
        if selected_index < 0 or selected_index >= len(self.materials_list):
            return

        # Confirm removal
        if not messagebox.askyesno(
                "Remove Material",
                "Are you sure you want to remove this material requirement?"
        ):
            return

        # Remove material
        self.materials_list.pop(selected_index)

        # Update materials list
        self.update_materials_list()

    def _show_material_dialog(self, material=None, material_index=None):
        """
        Show material dialog for adding or editing a material requirement.

        Args:
            material: The material to edit (None for new materials)
            material_index: The index of the material in the list (None for new materials)
        """
        # Create dialog
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Material" if material is None else "Edit Material")
        dialog.geometry("500x400")
        dialog.minsize(400, 300)
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Create dialog content
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Material selection
        ttk.Label(form_frame, text="Material:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        # Material ID (hidden)
        material_id_var = tk.StringVar()
        if material:
            material_id_var.set(str(material.get("material_id", "")))

        # Material name (display)
        material_name_var = tk.StringVar()
        if material:
            material_name_var.set(material.get("name", ""))

        material_name_entry = ttk.Entry(form_frame, textvariable=material_name_var, width=30)
        material_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        material_name_entry.configure(state="readonly")

        # Browse button
        browse_btn = ttk.Button(
            form_frame,
            text="Browse...",
            command=lambda: self._browse_materials(material_id_var, material_name_var)
        )
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # Material type (will be filled from selection)
        ttk.Label(form_frame, text="Type:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)

        material_type_var = tk.StringVar()
        if material:
            material_type_var.set(material.get("type", "").replace("_", " ").title())

        material_type_entry = ttk.Entry(form_frame, textvariable=material_type_var, width=30)
        material_type_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        material_type_entry.configure(state="readonly")

        # Quantity
        ttk.Label(form_frame, text="Quantity:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)

        quantity_var = tk.StringVar()
        if material:
            quantity_var.set(str(material.get("quantity", "")))

        quantity_entry = ttk.Entry(form_frame, textvariable=quantity_var, width=10)
        quantity_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        # Unit
        ttk.Label(form_frame, text="Unit:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5)

        unit_var = tk.StringVar()
        if material:
            unit_var.set(material.get("unit", "").replace("_", " ").title())

        unit_combo = ttk.Combobox(form_frame, textvariable=unit_var, width=15)
        unit_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        unit_combo["values"] = self._get_measurement_unit_values()

        # Notes
        ttk.Label(form_frame, text="Notes:").grid(
            row=4, column=0, sticky="nw", padx=5, pady=5)

        notes_frame = ttk.Frame(form_frame)
        notes_frame.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        notes_text = tk.Text(notes_frame, height=5, width=30, wrap=tk.WORD)
        notes_text.pack(fill=tk.BOTH, expand=True)

        if material and "notes" in material:
            notes_text.insert("1.0", material.get("notes", ""))

        # Add buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        ok_btn = ttk.Button(
            btn_frame,
            text="OK",
            command=lambda: self._save_material(
                material_id_var.get(),
                material_name_var.get(),
                material_type_var.get(),
                quantity_var.get(),
                unit_var.get(),
                notes_text.get("1.0", tk.END).strip(),
                material_index,
                dialog
            )
        )
        ok_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT)

    def _browse_materials(self, id_var, name_var):
        """
        Open material browser dialog.

        Args:
            id_var: Variable to store selected material ID
            name_var: Variable to store selected material name
        """
        try:
            # Create dialog
            dialog = tk.Toplevel(self.dialog)
            dialog.title("Select Material")
            dialog.geometry("600x400")
            dialog.minsize(400, 300)
            dialog.transient(self.dialog)
            dialog.grab_set()

            # Create dialog content
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Create search frame
            search_frame = ttk.Frame(main_frame)
            search_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

            ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
            search_entry.pack(side=tk.LEFT, padx=(0, 5))

            search_btn = ttk.Button(
                search_frame,
                text="Search",
                command=lambda: self._search_materials(search_var.get(), materials_tree)
            )
            search_btn.pack(side=tk.LEFT)

            # Create materials list
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)

            columns = ("name", "type", "description")
            materials_tree = ttk.Treeview(
                list_frame,
                columns=columns,
                show="headings",
                selectmode="browse"
            )

            # Define headings
            materials_tree.heading("name", text="Material")
            materials_tree.heading("type", text="Type")
            materials_tree.heading("description", text="Description")

            # Define columns
            materials_tree.column("name", width=150)
            materials_tree.column("type", width=100)
            materials_tree.column("description", width=250)

            # Add scrollbar
            y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=materials_tree.yview)
            materials_tree.configure(yscrollcommand=y_scrollbar.set)

            materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Load materials
            self._load_materials(materials_tree)

            # Bind double-click to select
            materials_tree.bind("<Double-1>", lambda e: self._select_material(
                materials_tree, id_var, name_var, dialog))

            # Add buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

            select_btn = ttk.Button(
                btn_frame,
                text="Select",
                command=lambda: self._select_material(materials_tree, id_var, name_var, dialog)
            )
            select_btn.pack(side=tk.RIGHT, padx=(5, 0))

            cancel_btn = ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            )
            cancel_btn.pack(side=tk.RIGHT)
        except Exception as e:
            logger.error(f"Error browsing materials: {str(e)}")
            messagebox.showerror("Error", f"Failed to browse materials: {str(e)}")

    def _load_materials(self, tree):
        """
        Load materials into the treeview.

        Args:
            tree: The treeview to load materials into
        """
        try:
            # Clear current items
            for item in tree.get_children():
                tree.delete(item)

            # Get material service
            service = get_service("IMaterialService")

            # Get materials
            materials = service.get_materials(limit=100)

            # Add materials to tree
            for i, material in enumerate(materials):
                tree.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=(
                        material.get("name", "Unknown"),
                        material.get("type", "").replace("_", " ").title(),
                        material.get("description", "")[:50] + (
                            "..." if len(material.get("description", "")) > 50 else ""
                        )
                    ),
                    tags=(str(material.get("id")),)
                )
        except Exception as e:
            logger.error(f"Error loading materials: {str(e)}")
            messagebox.showerror("Error", f"Failed to load materials: {str(e)}")

    def _search_materials(self, search_text, tree):
        """
        Search for materials.

        Args:
            search_text: The text to search for
            tree: The treeview to load results into
        """
        try:
            # Clear current items
            for item in tree.get_children():
                tree.delete(item)

            if not search_text:
                # If search is empty, load all materials
                self._load_materials(tree)
                return

            # Get material service
            service = get_service("IMaterialService")

            # Search materials
            materials = service.search_materials(search_text, limit=100)

            # Add materials to tree
            for i, material in enumerate(materials):
                tree.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=(
                        material.get("name", "Unknown"),
                        material.get("type", "").replace("_", " ").title(),
                        material.get("description", "")[:50] + (
                            "..." if len(material.get("description", "")) > 50 else ""
                        )
                    ),
                    tags=(str(material.get("id")),)
                )
        except Exception as e:
            logger.error(f"Error searching materials: {str(e)}")
            messagebox.showerror("Error", f"Failed to search materials: {str(e)}")

    def _select_material(self, tree, id_var, name_var, dialog):
        """
        Select a material from the tree.

        Args:
            tree: The treeview with materials
            id_var: Variable to update with material ID
            name_var: Variable to update with material name
            dialog: The dialog to close
        """
        # Get selected item
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a material.")
            return

        selected_iid = selection[0]
        selected_values = tree.item(selected_iid, "values")
        selected_tags = tree.item(selected_iid, "tags")

        if not selected_tags:
            return

        # Update variables
        material_id = selected_tags[0]
        material_name = selected_values[0]

        id_var.set(material_id)
        name_var.set(material_name)

        # Close dialog
        dialog.destroy()

    def _save_material(self, material_id, name, type_str, quantity_str, unit, notes, index, dialog):
        """
        Save material requirement.

        Args:
            material_id: The material ID
            name: The material name
            type_str: The material type
            quantity_str: The quantity
            unit: The unit
            notes: The notes
            index: The index for editing (None for new)
            dialog: The dialog to close
        """
        # Validate
        if not material_id or not name:
            messagebox.showerror("Error", "Please select a material.")
            return

        try:
            quantity = float(quantity_str)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number.")
            return

        if not unit:
            messagebox.showerror("Error", "Please select a unit.")
            return

        # Create material requirement
        material_req = {
            "material_id": int(material_id),
            "name": name,
            "type": type_str.lower().replace(" ", "_"),
            "quantity": quantity,
            "unit": unit.lower().replace(" ", "_"),
            "notes": notes
        }

        # Add or update material
        if index is not None:
            # Update existing
            self.materials_list[index] = material_req
        else:
            # Add new
            self.materials_list.append(material_req)

        # Update materials list
        self.update_materials_list()

        # Close dialog
        dialog.destroy()

    def _get_measurement_unit_values(self):
        """
        Get measurement unit values for dropdown.

        Returns:
            List of measurement unit values
        """
        try:
            # Try to get measurement units from the enum service
            enum_service = get_service("IEnumService")
            return [u.value.replace("_", " ").title() for u in enum_service.get_measurement_units()]
        except Exception as e:
            logger.error(f"Error getting measurement units: {str(e)}")
            # Fallback to hardcoded values
            return [
                "Piece",
                "Square Meter",
                "Square Foot",
                "Meter",
                "Centimeter",
                "Foot",
                "Inch",
                "Kilogram",
                "Gram",
                "Ounce"
            ]