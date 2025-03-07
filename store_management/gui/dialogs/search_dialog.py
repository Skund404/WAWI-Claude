# gui/dialogs/search_dialog.py
"""
Advanced search dialog for searching across multiple fields with various options.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable, Tuple, Union

from gui.base.base_dialog import BaseDialog
from gui.components.form_builder import FormBuilder
from gui.theme import get_color

logger = logging.getLogger(__name__)


class SearchCondition:
    """Class representing a search condition with field, operator, and value."""

    OPERATORS = {
        'text': ['contains', 'equals', 'starts with', 'ends with', 'not contains'],
        'number': ['equals', 'greater than', 'less than', 'between'],
        'date': ['equals', 'after', 'before', 'between'],
        'boolean': ['is'],
        'choice': ['equals', 'not equals']
    }

    def __init__(self, field: str, field_type: str, operator: str, value: Any, value2: Any = None):
        """Initialize a search condition.

        Args:
            field: Field name to search in
            field_type: Type of the field ('text', 'number', 'date', 'boolean', 'choice')
            operator: Search operator
            value: Search value
            value2: Second search value for 'between' operator
        """
        self.field = field
        self.field_type = field_type
        self.operator = operator
        self.value = value
        self.value2 = value2

    def to_dict(self) -> Dict[str, Any]:
        """Convert the condition to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the condition
        """
        result = {
            'field': self.field,
            'field_type': self.field_type,
            'operator': self.operator,
            'value': self.value
        }
        if self.value2 is not None:
            result['value2'] = self.value2
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchCondition':
        """Create a SearchCondition from a dictionary.

        Args:
            data: Dictionary with condition data

        Returns:
            SearchCondition: New instance
        """
        return cls(
            data['field'],
            data['field_type'],
            data['operator'],
            data['value'],
            data.get('value2')
        )


class SearchDialog(BaseDialog):
    """Advanced search dialog for configuring complex search queries."""

    def __init__(self, parent: tk.Widget, title: str, fields: Dict[str, Dict[str, Any]],
                 callback: Callable[[List[SearchCondition], bool], None],
                 current_conditions: Optional[List[SearchCondition]] = None,
                 entity_type: Optional[str] = None,
                 size: tuple = (650, 500)):
        """Initialize the search dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            fields: Dictionary of searchable fields with their properties
                   Format: {field_name: {type: text|number|date|boolean|choice,
                            label: str, [choices: list]}}
            callback: Function to call with search conditions when applied
            current_conditions: Current search conditions, if any
            entity_type: Optional entity type name for the dialog title
            size: Dialog size (width, height)
        """
        self.fields = fields
        self.callback = callback
        self.conditions = current_conditions or []
        self.condition_frames = []
        self.entity_type = entity_type or "Items"

        # Customize title if entity type is provided
        if entity_type and "Search" not in title:
            title = f"Search {entity_type}"

        # Set dialog size
        self.width, self.height = size

        super().__init__(parent, title)

    def _create_body(self) -> ttk.Frame:
        """Create the dialog body with search controls.

        Returns:
            ttk.Frame: The dialog body frame
        """
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create top frame for general search options
        top_frame = ttk.Frame(body)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Create match option (all conditions or any condition)
        self.match_var = tk.StringVar(value="all")
        ttk.Label(top_frame, text="Match:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(top_frame, text="All conditions", variable=self.match_var,
                        value="all").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(top_frame, text="Any condition", variable=self.match_var,
                        value="any").pack(side=tk.LEFT)

        # Create frame for conditions
        self.conditions_frame = ttk.Frame(body)
        self.conditions_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame with scrollbar for conditions
        canvas_frame = ttk.Frame(self.conditions_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.conditions_container = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.conditions_container, anchor=tk.NW)

        self.conditions_container.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Add existing conditions if any
        if self.conditions:
            for condition in self.conditions:
                self._add_condition_frame(condition)
        else:
            # Add an empty condition frame
            self._add_condition_frame()

        # Button frame for adding conditions
        button_frame = ttk.Frame(body)
        button_frame.pack(fill=tk.X, pady=10)

        add_btn = ttk.Button(button_frame, text="Add Condition", command=self._add_condition_frame)
        add_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(button_frame, text="Clear All", command=self._clear_conditions)
        clear_btn.pack(side=tk.RIGHT)

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create Search button
        search_btn = ttk.Button(
            button_frame,
            text="Search",
            command=self._on_ok,
            style="Accent.TButton"
        )
        search_btn.pack(side=tk.RIGHT, padx=5)

        # Create Close button
        close_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

        return button_frame

    def _add_condition_frame(self, condition: Optional[SearchCondition] = None) -> None:
        """Add a new condition frame to the dialog.

        Args:
            condition: Optional existing condition to populate the frame
        """
        frame_index = len(self.condition_frames)
        condition_frame = ttk.Frame(self.conditions_container)
        condition_frame.pack(fill=tk.X, pady=5)

        # Create a frame for the condition controls
        controls_frame = ttk.Frame(condition_frame)
        controls_frame.pack(fill=tk.X, side=tk.LEFT, expand=True)

        # Field selection
        field_var = tk.StringVar()
        field_label = ttk.Label(controls_frame, text="Field:")
        field_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        field_names = list(self.fields.keys())
        field_labels = [self.fields[field].get('label', field) for field in field_names]
        field_combo = ttk.Combobox(controls_frame, textvariable=field_var, values=field_labels, state="readonly")
        field_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))

        # Operator selection
        operator_var = tk.StringVar()
        operator_label = ttk.Label(controls_frame, text="Operator:")
        operator_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 5))

        operator_combo = ttk.Combobox(controls_frame, textvariable=operator_var, state="readonly")
        operator_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))

        # Value entry
        value_var = tk.StringVar()
        value_label = ttk.Label(controls_frame, text="Value:")
        value_label.grid(row=0, column=4, sticky=tk.W, padx=(0, 5))

        value_entry = ttk.Entry(controls_frame, textvariable=value_var)
        value_entry.grid(row=0, column=5, sticky=tk.W + tk.E, padx=(0, 10))

        # Second value for 'between' operator
        value2_var = tk.StringVar()
        value2_frame = ttk.Frame(controls_frame)
        value2_frame.grid(row=0, column=6, sticky=tk.W)
        value2_frame.grid_remove()  # Hide initially

        value2_label = ttk.Label(value2_frame, text="and")
        value2_label.pack(side=tk.LEFT, padx=(0, 5))
        value2_entry = ttk.Entry(value2_frame, textvariable=value2_var)
        value2_entry.pack(side=tk.LEFT)

        # Remove button
        remove_btn = ttk.Button(
            condition_frame,
            text="✕",
            width=3,
            command=lambda: self._remove_condition_frame(condition_frame)
        )
        remove_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Store widgets in a dictionary
        condition_widgets = {
            'frame': condition_frame,
            'field_var': field_var,
            'field_combo': field_combo,
            'operator_var': operator_var,
            'operator_combo': operator_combo,
            'value_var': value_var,
            'value_entry': value_entry,
            'value2_var': value2_var,
            'value2_frame': value2_frame,
            'value2_entry': value2_entry,
            'remove_btn': remove_btn
        }

        self.condition_frames.append(condition_widgets)

        # Set up field change event
        def on_field_change(event=None):
            selected_label = field_var.get()
            selected_index = field_labels.index(selected_label) if selected_label in field_labels else 0
            selected_field = field_names[selected_index] if selected_index < len(field_names) else ""

            if selected_field:
                field_type = self.fields[selected_field].get('type', 'text')
                operators = SearchCondition.OPERATORS.get(field_type, [])
                operator_combo['values'] = operators

                if operators and (not operator_var.get() or operator_var.get() not in operators):
                    operator_combo.current(0)

                # If field type is choice, replace entry with combobox
                if field_type == 'choice' and 'choices' in self.fields[selected_field]:
                    choices = self.fields[selected_field]['choices']
                    # TODO: Replace value_entry with combobox

            on_operator_change()

        # Set up operator change event
        def on_operator_change(event=None):
            operator = operator_var.get()
            if operator == 'between':
                value2_frame.grid()
            else:
                value2_frame.grid_remove()

        field_combo.bind("<<ComboboxSelected>>", on_field_change)
        operator_combo.bind("<<ComboboxSelected>>", on_operator_change)

        # Set initial values if condition is provided
        if condition:
            # Find the field label by name
            field_index = field_names.index(condition.field) if condition.field in field_names else 0
            field_combo.current(field_index)

            # Set operator
            operators = SearchCondition.OPERATORS.get(condition.field_type, [])
            operator_combo['values'] = operators
            if condition.operator in operators:
                operator_var.set(condition.operator)
            elif operators:
                operator_var.set(operators[0])

            # Set values
            value_var.set(str(condition.value) if condition.value is not None else "")
            if condition.value2 is not None:
                value2_var.set(str(condition.value2))
                if condition.operator == 'between':
                    value2_frame.grid()
        else:
            # Set defaults
            if field_labels:
                field_combo.current(0)
                on_field_change()

    def _remove_condition_frame(self, frame: ttk.Frame) -> None:
        """Remove a condition frame from the dialog.

        Args:
            frame: The frame to remove
        """
        # Find the index of the frame in the list
        for i, condition_widgets in enumerate(self.condition_frames):
            if condition_widgets['frame'] == frame:
                # Remove the frame from the UI
                frame.destroy()
                # Remove from the list
                del self.condition_frames[i]
                break

        # If no conditions left, add an empty one
        if not self.condition_frames:
            self._add_condition_frame()

    def _clear_conditions(self) -> None:
        """Clear all search conditions."""
        for condition_widgets in self.condition_frames:
            condition_widgets['frame'].destroy()

        self.condition_frames = []
        self._add_condition_frame()

    def _on_configure(self, event=None) -> None:
        """Handle configure event for the conditions container."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event=None) -> None:
        """Handle resize event for the canvas."""
        if event and event.width > 0:
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _validate(self) -> bool:
        """Validate search inputs.

        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        for condition_widgets in self.condition_frames:
            field_var = condition_widgets['field_var']
            operator_var = condition_widgets['operator_var']
            value_var = condition_widgets['value_var']

            if not field_var.get() or not operator_var.get():
                return False

            if operator_var.get() != 'is empty' and not value_var.get():
                return False

            if operator_var.get() == 'between' and not condition_widgets['value2_var'].get():
                return False

        return True

    def _apply(self) -> None:
        """Apply the search by calling the callback function."""
        try:
            conditions = []
            field_names = list(self.fields.keys())
            field_labels = [self.fields[field].get('label', field) for field in field_names]

            for condition_widgets in self.condition_frames:
                selected_label = condition_widgets['field_var'].get()
                selected_index = field_labels.index(selected_label) if selected_label in field_labels else -1

                if selected_index >= 0:
                    field_name = field_names[selected_index]
                    field_type = self.fields[field_name].get('type', 'text')
                    operator = condition_widgets['operator_var'].get()
                    value = condition_widgets['value_var'].get()
                    value2 = condition_widgets['value2_var'].get() if operator == 'between' else None

                    # Convert values based on field type
                    if field_type == 'number':
                        try:
                            value = float(value) if '.' in value else int(value)
                            if value2:
                                value2 = float(value2) if '.' in value2 else int(value2)
                        except ValueError:
                            # Skip invalid number values
                            continue
                    elif field_type == 'boolean':
                        value = value.lower() in ('true', 'yes', '1')

                    condition = SearchCondition(field_name, field_type, operator, value, value2)
                    conditions.append(condition)

            # Call the callback with search conditions and match option
            match_all = self.match_var.get() == "all"
            self.callback(conditions, match_all)
            logger.debug(f"Applied search: {len(conditions)} conditions, match_all={match_all}")
        except Exception as e:
            logger.error(f"Error applying search: {str(e)}")
            raise

    def get_conditions(self) -> List[Dict[str, Any]]:
        """Get the current search conditions.

        Returns:
            List[Dict[str, Any]]: List of condition dictionaries
        """
        return [self._get_condition_from_widgets(widgets).to_dict()
                for widgets in self.condition_frames]

    @staticmethod
    def show_dialog(parent: tk.Widget,
                    fields: Dict[str, Dict[str, Any]],
                    title: str = "Advanced Search",
                    entity_type: Optional[str] = None,
                    current_conditions: Optional[List[SearchCondition]] = None,
                    size: tuple = (650, 500)) -> Optional[Tuple[List[SearchCondition], bool]]:
        """Show a search dialog and return the result.

        Args:
            parent: Parent widget
            fields: Dictionary of searchable fields with their properties
            title: Dialog title
            entity_type: Optional entity type name
            current_conditions: Current search conditions, if any
            size: Dialog size (width, height)

        Returns:
            Tuple of search conditions and match_all flag if applied, None if cancelled
        """
        # Create variables to hold the result
        result_conditions = None
        result_match_all = True

        # Define callback
        def on_apply(conditions, match_all):
            nonlocal result_conditions, result_match_all
            result_conditions = conditions
            result_match_all = match_all

        # Create and show the dialog
        dialog = SearchDialog(
            parent,
            title=title,
            fields=fields,
            callback=on_apply,
            current_conditions=current_conditions,
            entity_type=entity_type,
            size=size
        )

        # Return the result (None if cancelled)
        if result_conditions is not None:
            return (result_conditions, result_match_all)
        return None

    def _get_condition_from_widgets(self, widgets: Dict[str, Any]) -> SearchCondition:
        """Get a SearchCondition from the widgets.

        Args:
            widgets: Dictionary of condition widgets

        Returns:
            SearchCondition: The condition
        """
        field_names = list(self.fields.keys())
        field_labels = [self.fields[field].get('label', field) for field in field_names]

        selected_label = widgets['field_var'].get()
        selected_index = field_labels.index(selected_label) if selected_label in field_labels else 0
        field_name = field_names[selected_index]
        field_type = self.fields[field_name].get('type', 'text')

        operator = widgets['operator_var'].get()
        value = widgets['value_var'].get()
        value2 = widgets['value2_var'].get() if operator == 'between' else None

        # Convert values based on field type
        if field_type == 'number':
            try:
                value = float(value) if '.' in value else int(value)
                if value2:
                    value2 = float(value2) if '.' in value2 else int(value2)
            except ValueError:
                pass
        elif field_type == 'boolean':
            value = value.lower() in ('true', 'yes', '1')

        return SearchCondition(field_name, field_type, operator, value, value2)