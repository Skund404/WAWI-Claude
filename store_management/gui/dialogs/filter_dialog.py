# gui/dialogs/filter_dialog.py
"""
Filter dialog for filtering data in treeviews.
Provides a reusable dialog for applying various filters to displayed data.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable

from gui.base.base_dialog import BaseDialog
from gui.components.form_builder import FormBuilder
from gui.theme import get_color

logger = logging.getLogger(__name__)


class FilterDialog(BaseDialog):
    """Dialog for configuring and applying filters to data views."""

    def __init__(self, parent: tk.Widget, title: str, filters: Dict[str, Dict[str, Any]],
                 callback: Callable[[Dict[str, Any]], None],
                 current_values: Optional[Dict[str, Any]] = None,
                 entity_type: Optional[str] = None,
                 size: tuple = (500, 400)):
        """Initialize the filter dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            filters: Dictionary defining filter fields and their properties
                    Format: {field_name: {type: str|int|float|bool|choice, label: str,
                             [choices: list], [range: (min, max)]}}
            callback: Function to call with the filter values when applied
            current_values: Current filter values, if any
            entity_type: Optional entity type name for the dialog title
            size: Dialog size (width, height)
        """
        self.filters = filters
        self.callback = callback
        self.current_values = current_values or {}
        self.filter_widgets = {}
        self.form_builder = None
        self.entity_type = entity_type or "Items"

        # Customize title if entity type is provided
        if entity_type and "Filter" not in title:
            title = f"Filter {entity_type}"

        # Set dialog size
        self.width, self.height = size

        super().__init__(parent, title)

    def _create_body(self) -> ttk.Frame:
        """Create the dialog body with filter controls.

        Returns:
            ttk.Frame: The dialog body frame
        """
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a form builder with filter fields
        fields = {}
        for field_name, field_def in self.filters.items():
            field_type = field_def.get('type', 'str')
            field_config = {
                'label': field_def.get('label', field_name.replace('_', ' ').title()),
                'type': field_type,
                'required': False,
            }

            # Add type-specific properties
            if field_type == 'choice':
                field_config['choices'] = field_def.get('choices', [])
            elif field_type in ('int', 'float'):
                if 'range' in field_def:
                    field_config['min_value'] = field_def['range'][0]
                    field_config['max_value'] = field_def['range'][1]

            fields[field_name] = field_config

        self.form_builder = FormBuilder(
            body,
            fields=fields,
            layout="vertical",
            submit_btn_text="Apply Filters",
            cancel_btn_text="Reset",
            on_submit=self._on_apply,
            on_cancel=self._on_reset
        )

        # Set current values if any
        if self.current_values:
            self.form_builder.set_data(self.current_values)

        # Create a separator
        ttk.Separator(body, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create Apply button
        apply_btn = ttk.Button(
            button_frame,
            text="Apply",
            command=self._on_ok,
            style="Accent.TButton"
        )
        apply_btn.pack(side=tk.RIGHT, padx=5)

        # Create Close button
        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self._on_cancel
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

        # Create Reset button
        reset_btn = ttk.Button(
            button_frame,
            text="Reset",
            command=self._on_reset
        )
        reset_btn.pack(side=tk.LEFT, padx=5)

        return button_frame

    def _validate(self) -> bool:
        """Validate filter inputs.

        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        return self.form_builder._validate()

    def _apply(self) -> None:
        """Apply the filters by calling the callback function."""
        try:
            filter_values = {}
            form_data = self.form_builder.get_data()

            # Only include non-empty values
            for field, value in form_data.items():
                if value is not None and value != "":
                    # Convert string values for numeric fields
                    field_type = self.filters[field].get('type')
                    if field_type == 'int' and isinstance(value, str):
                        try:
                            value = int(value)
                        except ValueError:
                            continue
                    elif field_type == 'float' and isinstance(value, str):
                        try:
                            value = float(value)
                        except ValueError:
                            continue

                    filter_values[field] = value

            # Call the callback with filter values
            self.callback(filter_values)
            logger.debug(f"Applied filters: {filter_values}")
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            raise

    def _on_reset(self, event=None) -> None:
        """Reset all filters to default values.

        Args:
            event: Optional event that triggered the reset
        """
        self.form_builder.clear()
        self.callback({})  # Call callback with empty filters
        logger.debug("Filters reset")

    def get_filters(self) -> Dict[str, Any]:
        """Get the current filter values.

        Returns:
            Dict[str, Any]: Dictionary of current filter values
        """
        return self.form_builder.get_data()

    @staticmethod
    def show_dialog(parent: tk.Widget,
                    filters: Dict[str, Dict[str, Any]],
                    title: str = "Filter Data",
                    entity_type: Optional[str] = None,
                    current_values: Optional[Dict[str, Any]] = None,
                    size: tuple = (500, 400)) -> Optional[Dict[str, Any]]:
        """Show a filter dialog and return the result.

        Args:
            parent: Parent widget
            filters: Dictionary defining filter fields and their properties
            title: Dialog title
            entity_type: Optional entity type name
            current_values: Current filter values, if any
            size: Dialog size (width, height)

        Returns:
            The filter values if applied, None if cancelled
        """
        # Create a variable to hold the result
        result_data = None

        # Define callback
        def on_apply(data):
            nonlocal result_data
            result_data = data

        # Create and show the dialog
        dialog = FilterDialog(
            parent,
            title=title,
            filters=filters,
            callback=on_apply,
            current_values=current_values,
            entity_type=entity_type,
            size=size
        )

        # Return the result (None if cancelled)
        return result_data