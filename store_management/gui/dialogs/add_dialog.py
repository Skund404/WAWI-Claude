"""
Add dialog for creating new items.
Provides a standardized dialog for adding items to the application.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Type, Union

from gui.base.base_dialog import FormDialog
from gui.components.form_builder import FormBuilder

logger = logging.getLogger(__name__)


class AddDialog(FormDialog):
    """
    Dialog for adding new items to the application.

    Features:
    - Dynamic form generation
    - Field validation
    - Customizable appearance
    """

    def __init__(self, parent: tk.Widget,
                 title: str = "Add Item",
                 fields: List[Dict[str, Any]] = None,
                 initial_data: Optional[Dict[str, Any]] = None,
                 callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                 entity_type: Optional[str] = None,
                 size: tuple = (500, 400),
                 **kwargs):
        """
        Initialize the add dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            fields: List of field definitions
            initial_data: Optional initial values for fields
            callback: Function to call with the form data when submitted
            entity_type: Optional entity type name for the dialog title
            size: Dialog size (width, height)
            **kwargs: Additional arguments for the FormDialog
        """
        # Store parameters
        self.fields = fields or []
        self.field_values = initial_data or {}
        self.callback = callback
        self.entity_type = entity_type or "Item"

        # Customize title if entity type is provided
        if entity_type and "Add" not in title:
            title = f"Add {entity_type}"

        # Initialize the form dialog
        super().__init__(parent, title, size=size, **kwargs)

        logger.debug(f"AddDialog initialized: {title}")

    def _create_body(self):
        """Create the dialog body with a form builder."""
        # Create the main form builder
        self.form_builder = FormBuilder(
            self.body_frame,
            self.fields,
            initial_data=self.field_values,
            on_submit=self._on_ok  # Use the FormDialog's OK button instead of form submit
        )

        # Set initial focus to the first field
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

        if self.callback:
            try:
                logger.debug(f"Applying add dialog data for {self.entity_type}")
                self.callback(data)
            except Exception as e:
                logger.error(f"Error in add dialog callback: {e}")
                raise

    @staticmethod
    def show_dialog(parent: tk.Widget,
                    fields: List[Dict[str, Any]],
                    title: str = "Add Item",
                    entity_type: Optional[str] = None,
                    initial_data: Optional[Dict[str, Any]] = None,
                    size: tuple = (500, 400)) -> Optional[Dict[str, Any]]:
        """
        Show an add dialog and return the result.

        Args:
            parent: Parent widget
            fields: List of field definitions
            title: Dialog title
            entity_type: Optional entity type name
            initial_data: Optional initial values for fields
            size: Dialog size (width, height)

        Returns:
            The form data if confirmed, None if cancelled
        """
        # Create a variable to hold the result
        result_data = None

        # Define callback
        def on_submit(data):
            nonlocal result_data
            result_data = data

        # Create and show the dialog
        dialog = AddDialog(
            parent,
            title=title,
            fields=fields,
            initial_data=initial_data,
            callback=on_submit,
            entity_type=entity_type,
            size=size
        )

        # Return the result (None if cancelled)
        return result_data


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Add Dialog Example")

    # Define fields for a material
    material_fields = [
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


    def show_add_dialog():
        result = AddDialog.show_dialog(
            root,
            fields=material_fields,
            title="Add Material",
            entity_type="Material"
        )

        if result:
            print("New material data:", result)
        else:
            print("Dialog cancelled")


    # Create test button
    button = ttk.Button(root, text="Show Add Dialog", command=show_add_dialog)
    button.pack(padx=20, pady=20)

    root.mainloop()