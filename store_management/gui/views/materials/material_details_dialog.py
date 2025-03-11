# gui/views/materials/material_details_dialog.py
"""
Material Details Dialog.
Provides a form for viewing, creating and editing materials.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import (
    MaterialType, InventoryStatus, MeasurementUnit, QualityGrade,
    LeatherType, LeatherFinish, HardwareType, HardwareMaterial, HardwareFinish
)
from gui.base.base_dialog import BaseDialog
from gui.base.base_form_view import BaseFormView, FormField
from gui.utils.service_access import get_service
from gui.utils.event_bus import publish


class MaterialDetailsDialog(BaseDialog):
    """Dialog for viewing, creating and editing materials."""

    def __init__(
            self,
            parent,
            material_id: Optional[int] = None,
            material_type: Optional[str] = None,
            create_new: bool = False,
            readonly: bool = False
    ):
        """
        Initialize the material details dialog.

        Args:
            parent: The parent widget
            material_id: ID of the material to edit (None for new materials)
            material_type: Type of material to create/edit
            create_new: Whether to create a new material
            readonly: Whether to show the form in read-only mode
        """
        title = "Material Details"
        if material_id and not create_new:
            title = "Edit Material" if not readonly else "View Material"
        elif create_new:
            title = f"New {material_type.capitalize() if material_type else 'Material'}"

        super().__init__(parent, title=title, width=600, height=650)

        self.material_id = material_id
        self.material_type = material_type
        self.create_new = create_new
        self.readonly = readonly
        self.form_view = None

    def create_layout(self):
        """Create the dialog layout."""
        # Create the form view based on material type
        if self.material_type == "LEATHER":
            self.form_view = LeatherFormView(
                self.dialog,
                self.material_id,
                create_new=self.create_new,
                readonly=self.readonly
            )
        elif self.material_type == "HARDWARE":
            self.form_view = HardwareFormView(
                self.dialog,
                self.material_id,
                create_new=self.create_new,
                readonly=self.readonly
            )
        elif self.material_type == "SUPPLIES":
            self.form_view = SuppliesFormView(
                self.dialog,
                self.material_id,
                create_new=self.create_new,
                readonly=self.readonly
            )
        else:
            # Generic material form
            self.form_view = MaterialFormView(
                self.dialog,
                self.material_id,
                create_new=self.create_new,
                readonly=self.readonly
            )

        # Build the form
        self.form_view.build()

        # Set up save and cancel buttons unless readonly
        if not self.readonly:
            button_frame = ttk.Frame(self.dialog, padding=10)
            button_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                button_frame,
                text="Cancel",
                command=self.on_cancel
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                button_frame,
                text="Save",
                command=self.on_save
            ).pack(side=tk.RIGHT, padx=5)
        else:
            # Just a close button for readonly mode
            button_frame = ttk.Frame(self.dialog, padding=10)
            button_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                button_frame,
                text="Close",
                command=self.on_cancel
            ).pack(side=tk.RIGHT, padx=5)

    def on_save(self):
        """Handle save button click."""
        if self.form_view.validate_form():
            try:
                # Try to save the form
                result = self.form_view.save_form()
                if result:
                    # Publish material updated event
                    publish("material_updated", {
                        "id": result.id if hasattr(result, "id") else None,
                        "type": self.material_type
                    })

                    self.result = result
                    self.close()
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving material: {str(e)}")
        else:
            messagebox.showerror(
                "Validation Error",
                "Please correct the errors in the form before saving."
            )


class MaterialFormView(BaseFormView):
    """Form view for generic material details."""

    def __init__(self, parent, item_id=None, create_new=False, readonly=False):
        """
        Initialize the material form view.

        Args:
            parent: The parent widget
            item_id: ID of the material to edit (None for new materials)
            create_new: Whether to create a new material
            readonly: Whether to show the form in read-only mode
        """
        super().__init__(parent, item_id)
        self.create_new = create_new
        self.readonly = readonly
        self.service_name = "IMaterialService"
        self.title = "Material Details"

        # Define form fields
        self.fields = [
            FormField("id", "ID", "text", readonly=True),
            FormField("name", "Name", "text", required=True, width=30),
            FormField("material_type", "Material Type", "enum", required=True,
                      enum_class=MaterialType, readonly=not create_new),
            FormField("description", "Description", "textarea", width=40),
            FormField("unit", "Unit of Measure", "enum", enum_class=MeasurementUnit),
            FormField("quality", "Quality Grade", "enum", enum_class=QualityGrade),
            FormField("cost", "Cost", "number", width=15),
            FormField("supplier_id", "Supplier", "text", width=15),
            FormField("notes", "Notes", "textarea", width=40)
        ]

    def _add_default_action_buttons(self):
        """Override to prevent adding default action buttons."""
        pass

    def create_form_buttons(self, parent):
        """Override to prevent adding form buttons (handled by dialog)."""
        pass

    def save_form(self):
        """
        Save the form data.

        Returns:
            The saved material object
        """
        # Collect form data
        data = self.collect_form_data()

        # Process data before save
        processed_data = self.process_data_before_save(data)

        try:
            service = self.get_service(self.service_name)
            if not service:
                raise Exception("Could not access material service")

            # Save or update
            if self.is_edit_mode and not self.create_new:
                result = service.update(self.item_id, processed_data)
                self.logger.info(f"Material updated: {result.id if hasattr(result, 'id') else 'unknown'}")
            else:
                result = service.create(processed_data)
                self.logger.info(f"Material created: {result.id if hasattr(result, 'id') else 'unknown'}")

            return result

        except Exception as e:
            self.logger.error(f"Error saving material: {str(e)}")
            raise


class LeatherFormView(MaterialFormView):
    """Form view for leather material details."""

    def __init__(self, parent, item_id=None, create_new=False, readonly=False):
        """
        Initialize the leather form view.

        Args:
            parent: The parent widget
            item_id: ID of the leather to edit (None for new leather)
            create_new: Whether to create a new leather
            readonly: Whether to show the form in read-only mode
        """
        super().__init__(parent, item_id, create_new, readonly)
        self.service_name = "ILeatherService"
        self.title = "Leather Details"

        # Define form fields for leather
        self.fields = [
            FormField("id", "ID", "text", readonly=True),
            FormField("name", "Name", "text", required=True, width=30),
            FormField("material_type", "Material Type", "text", default="LEATHER", readonly=True),
            FormField("description", "Description", "textarea", width=40),
            FormField("leather_type", "Leather Type", "enum", required=True, enum_class=LeatherType),
            FormField("thickness", "Thickness", "number", width=15),
            FormField("area", "Area", "number", width=15),
            FormField("is_full_hide", "Full Hide", "boolean"),
            FormField("finish", "Finish", "enum", enum_class=LeatherFinish),
            FormField("unit", "Unit of Measure", "enum", enum_class=MeasurementUnit),
            FormField("quality", "Quality Grade", "enum", enum_class=QualityGrade),
            FormField("cost", "Cost", "number", width=15),
            FormField("supplier_id", "Supplier", "text", width=15),
            FormField("notes", "Notes", "textarea", width=40)
        ]


class HardwareFormView(MaterialFormView):
    """Form view for hardware material details."""

    def __init__(self, parent, item_id=None, create_new=False, readonly=False):
        """
        Initialize the hardware form view.

        Args:
            parent: The parent widget
            item_id: ID of the hardware to edit (None for new hardware)
            create_new: Whether to create a new hardware
            readonly: Whether to show the form in read-only mode
        """
        super().__init__(parent, item_id, create_new, readonly)
        self.service_name = "IHardwareService"
        self.title = "Hardware Details"

        # Define form fields for hardware
        self.fields = [
            FormField("id", "ID", "text", readonly=True),
            FormField("name", "Name", "text", required=True, width=30),
            FormField("material_type", "Material Type", "text", default="HARDWARE", readonly=True),
            FormField("description", "Description", "textarea", width=40),
            FormField("hardware_type", "Hardware Type", "enum", required=True, enum_class=HardwareType),
            FormField("hardware_material", "Material", "enum", enum_class=HardwareMaterial),
            FormField("finish", "Finish", "enum", enum_class=HardwareFinish),
            FormField("size", "Size", "text", width=15),
            FormField("unit", "Unit of Measure", "enum", enum_class=MeasurementUnit, default="PIECE"),
            FormField("quality", "Quality Grade", "enum", enum_class=QualityGrade),
            FormField("cost", "Cost", "number", width=15),
            FormField("supplier_id", "Supplier", "text", width=15),
            FormField("notes", "Notes", "textarea", width=40)
        ]


class SuppliesFormView(MaterialFormView):
    """Form view for supplies material details."""

    def __init__(self, parent, item_id=None, create_new=False, readonly=False):
        """
        Initialize the supplies form view.

        Args:
            parent: The parent widget
            item_id: ID of the supplies to edit (None for new supplies)
            create_new: Whether to create a new supplies
            readonly: Whether to show the form in read-only mode
        """
        super().__init__(parent, item_id, create_new, readonly)
        self.service_name = "ISuppliesService"
        self.title = "Supplies Details"

        # Define form fields for supplies
        self.fields = [
            FormField("id", "ID", "text", readonly=True),
            FormField("name", "Name", "text", required=True, width=30),
            FormField("material_type", "Material Type", "text", default="SUPPLIES", readonly=True),
            FormField("supplies_type", "Supplies Type", "select", required=True,
                      options=["thread", "adhesive", "dye", "finish", "edge_paint", "wax"]),
            FormField("description", "Description", "textarea", width=40),
            FormField("color", "Color", "text", width=15),
            FormField("thickness", "Thickness", "text", width=15),
            FormField("material_composition", "Material Composition", "text", width=30),
            FormField("unit", "Unit of Measure", "enum", enum_class=MeasurementUnit),
            FormField("quality", "Quality Grade", "enum", enum_class=QualityGrade),
            FormField("cost", "Cost", "number", width=15),
            FormField("supplier_id", "Supplier", "text", width=15),
            FormField("notes", "Notes", "textarea", width=40)
        ]