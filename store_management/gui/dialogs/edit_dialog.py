"""
Edit dialog for modifying existing items.
Provides a standardized dialog for editing items in the application.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Type, Union

from gui.base.base_dialog import FormDialog
from gui.components.form_builder import FormBuilder

logger = logging.getLogger(__name__)


class EditDialog(FormDialog):
    """
    Dialog for editing existing items in the application.

    Features:
    - Dynamic form generation with existing values
    - Field validation
    - Change tracking
    - Customizable appearance
    """

    def __init__(self, parent: tk.Widget,
                 title: str = "Edit Item",
                 fields: List[Dict[str, Any]] = None,
                 item_data: Dict[str, Any] = None,
                 callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                 entity_type: Optional[str] = None,
                 readonly_fields: List[str] = None,
                 size: tuple = (500, 400),
                 **kwargs):
        """
        Initialize the edit dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            fields: List of field definitions
            item_data: Data for the item being edited
            callback: Function to call with the form data when submitted
            entity_type: Optional entity type name for the dialog title
            readonly_fields: List of field names that should be read-only
            size: Dialog size (width, height)
            **kwargs: Additional arguments for the FormDialog
        """
        # Store parameters
        self.fields = fields or []
        self.item_data = item_data or {}
        self.callback = callback
        self.entity_type = entity_type or "Item"
        self.readonly_fields = readonly_fields or []

        # Customize title if entity type is provided
        if entity_type and "Edit" not in title:
            title = f"Edit {entity_type}"

        # Track original data for change detection
        self.original_data = dict(self.item_data)

        # Initialize the form dialog
        super().__init__(parent, title, size=size, **kwargs)

        logger.debug(f"EditDialog initialized: {title}")

    def _create_body(self):
        """Create the dialog body with a form builder."""
        # Apply readonly flag to fields
        for field in self.fields:
            if field["name"] in self.readonly_fields:
                field["readonly"] = True

        # Create the main form builder
        self.form_builder = FormBuilder(
            self.body_frame,
            self.fields,
            initial_data=self.item_data,
            on_submit=self._on_ok  # Use the FormDialog's OK button instead of form submit
        )

        # Set initial focus to the first editable field
        self.initial_focus = self.form_builder.form_frame

    def _validate(self):
        """
        Validate the form data.

        Returns:
            True if the data is valid, False otherwise
        """
        return self.form_builder.validate()

    def _apply(self):
        """Apply the form data by calling the callback."""
        data = self.form_builder.get_data()

        # Add ID if present in original data but not in form
        if "id" in self.original_data and "id" not in data:
            data["id"] = self.original_data["id"]

        if self.callback:
            try:
                logger.debug(f"Applying edit dialog data for {self.entity_type}")
                self.callback(data)
            except Exception as e:
                logger.error(f"Error in edit dialog callback: {e}")
                raise

    def has_changes(self) -> bool:
        """
        Check if the form data has changes compared to the original data.

        Returns:
            True if there are changes, False otherwise
        """
        current_data = self.form_builder.get_data()

        # Compare current data with original data
        for key, value in current_data.items():
            if key in self.original_data:
                # Convert values to strings for comparison to handle different types
                if str(value) != str(self.original_data[key]):
                    return True
            else:
                # New field
                return True

        return False

    @staticmethod
    def show_dialog(parent: tk.Widget,
                    fields: List[Dict[str, Any]],
                    item_data: Dict[str, Any],
                    title: str = "Edit Item",
                    entity_type: Optional[str] = None,
                    readonly_fields: List[str] = None,
                    size: tuple = (500, 400)) -> Optional[Dict[str, Any]]:
        """
        Show an edit dialog and return the result.

        Args:
            parent: Parent widget
            fields: List of field definitions
            item_data: Data for the item being edited
            title: Dialog title
            entity_type: Optional entity type name
            readonly_fields: List of field names that should be read-only
            size: Dialog size (width, height)

        Returns:
            The updated data if confirmed, None if cancelled
        """
        # Create a variable to hold the result
        result_data = None

        # Define callback
        def on_submit(data):
            nonlocal result_data
            result_data = data

        # Create and show the dialog
        dialog = EditDialog(
            parent,
            title=title,
            fields=fields,
            item_data=item_data,
            callback=on_submit,
            entity_type=entity_type,
            readonly_fields=readonly_fields,
            size=size
        )

        # Return the result (None if cancelled)
        return result_data


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Edit Dialog Example")

    # Define fields for a material
    material_fields = [
        {
            "name": "id",
            "type": "integer",
            "label": "Material ID",
            "required": True
        },
        {
            "name": "name",
            "type": "string",
            "label": "Material Name",
            "required": True,
            "help_text": "Enter the name of the material"
        },
        {
            "name": "type",
            "type": "choice",
            "label": "Material Type",
            "choices": ["Leather", "Hardware", "Supplies", "Adhesive", "Other"],
            "required": True
        },
        {
            "name": "quantity",
            "type": "float",
            "label": "Quantity",
            "required": True
        },
        {
            "name": "unit",
            "type": "choice",
            "label": "Unit",
            "choices": ["Piece", "Meter", "Square Meter", "Kilogram", "Gram"],
            "required": True
        },
        {
            "name": "price",
            "type": "float",
            "label": "Price (per unit)",
            "required": True
        },
        {
            "name": "supplier",
            "type": "string",
            "label": "Supplier",
        },
        {
            "name": "description",
            "type": "text",
            "label": "Description",
            "height": 3
        },
        {
            "name": "in_stock",
            "type": "boolean",
            "label": "In Stock"
        }
    ]

    # Sample material data
    material_data = {
        "id": 1001,
        "name": "Vegetable Tanned Leather",
        "type": "Leather",
        "quantity": 5.5,
        "unit": "Square Meter",
        "price": 45.99,
        "supplier": "Premium Leather Supplies",
        "description": "High-quality vegetable tanned leather for crafting wallets and bags.",
        "in_stock": True
    }


    def show_edit_dialog():
        result = EditDialog.show_dialog(
            root,
            fields=material_fields,
            item_data=material_data,
            title="Edit Material",
            entity_type="Material",
            readonly_fields=["id"]
        )

        if result:
            print("Updated material data:", result)
        else:
            print("Dialog cancelled")


    # Create test button
    button = ttk.Button(root, text="Show Edit Dialog", command=show_edit_dialog)
    button.pack(padx=20, pady=20)

    root.mainloop()