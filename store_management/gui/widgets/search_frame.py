# gui/widgets/search_frame.py
"""
Search and filter frame for use in list views.
Provides a reusable search interface with customizable fields.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

from gui import theme, config


class SearchField:
    """Class representing a search field configuration."""

    def __init__(
            self,
            name: str,
            label: str,
            field_type: str = "text",
            options: Optional[List[Any]] = None,
            width: int = 15
    ):
        """
        Initialize a search field configuration.

        Args:
            name: The field name (attribute/key name in data model)
            label: Display label for the field
            field_type: Type of field (text, number, date, select, etc.)
            options: For select fields, list of available options
            width: Width of the field control
        """
        self.name = name
        self.label = label
        self.field_type = field_type
        self.options = options
        self.width = width

        # Control variable and widget (set during form creation)
        self.var = None
        self.widget = None


class SearchFrame(ttk.LabelFrame):
    """
    Frame for search and filter controls.
    Provides a customizable search interface for list views.
    """

    def __init__(
            self,
            parent,
            search_fields: List[Dict[str, Any]],
            on_search: Callable[[Dict[str, Any]], None],
            title: str = "Search"
    ):
        """
        Initialize the search frame.

        Args:
            parent: The parent widget
            search_fields: List of search field configurations
            on_search: Callback when search is performed (receives search criteria)
            title: Title for the frame
        """
        super().__init__(parent, text=title, padding=5)

        self.parent = parent
        self.on_search_callback = on_search
        self.search_fields = []
        self.field_widgets = {}

        # Convert field configurations to SearchField objects
        for field_config in search_fields:
            if isinstance(field_config, dict):
                # Convert dictionary configuration to SearchField
                self.search_fields.append(SearchField(
                    name=field_config.get("name", ""),
                    label=field_config.get("label", ""),
                    field_type=field_config.get("type", "text"),
                    options=field_config.get("options", None),
                    width=field_config.get("width", 15)
                ))
            elif isinstance(field_config, SearchField):
                # Already a SearchField object
                self.search_fields.append(field_config)
            elif isinstance(field_config, tuple) and len(field_config) >= 2:
                # Tuple format (name, label, [field_type], [options], [width])
                name, label = field_config[0:2]
                field_type = field_config[2] if len(field_config) > 2 else "text"
                options = field_config[3] if len(field_config) > 3 else None
                width = field_config[4] if len(field_config) > 4 else 15

                self.search_fields.append(SearchField(
                    name=name,
                    label=label,
                    field_type=field_type,
                    options=options,
                    width=width
                ))

        # Build the search form
        self.build_search_form()

    def get_search_criteria(self):
        """
        Get the current search criteria as a dictionary.

        Returns:
            Dictionary of field name -> value pairs
        """
        criteria = {}
        for field_name, var in self.field_vars.items():
            value = var.get()
            if value and value.strip():  # Only include non-empty values
                criteria[field_name] = value
        return criteria

    def add_search_fields(self, fields):
        """
        Add search fields to the search frame.

        Args:
            fields: List of field configurations
        """
        self.search_fields.extend(fields)
        self.build_search_form()

    def build_search_form(self):
        """Build the search form with fields and buttons."""
        # Create the main form frame
        form_frame = ttk.Frame(self)
        form_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # Calculate layout
        field_count = len(self.search_fields)
        if field_count == 0:
            # No search fields
            ttk.Label(form_frame, text="No search fields configured").pack(pady=5)
            return

        # Determine number of columns based on field count
        if field_count <= 3:
            columns = field_count
        elif field_count <= 6:
            columns = 3
        else:
            columns = 4

        # Create search fields
        row = 0
        col = 0
        for field in self.search_fields:
            # Create field container
            field_container = ttk.Frame(form_frame)
            field_container.grid(row=row, column=col, sticky="w", padx=5, pady=3)

            # Create label
            ttk.Label(field_container, text=field.label).pack(anchor="w")

            # Create field widget based on field type
            field.var, field.widget = self.create_field_widget(field_container, field)
            field.widget.pack(fill=tk.X, expand=True)

            # Store reference to widget
            self.field_widgets[field.name] = field.widget

            # Move to next column
            col += 1
            if col >= columns:
                col = 0
                row += 1

        # Create button frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create search button
        ttk.Button(
            button_frame,
            text="Search",
            command=self.on_search
        ).pack(side=tk.RIGHT, padx=5)

        # Create reset button
        ttk.Button(
            button_frame,
            text="Reset",
            command=self.on_reset
        ).pack(side=tk.RIGHT, padx=5)

    def create_field_widget(self, parent, field):
        """
        Create a widget for a search field.

        Args:
            parent: The parent widget
            field: The SearchField configuration

        Returns:
            Tuple of (variable, widget)
        """
        if field.field_type == "text":
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var, width=field.width)

        elif field.field_type == "number":
            var = tk.StringVar()
            validate_cmd = parent.register(self.validate_number)
            widget = ttk.Entry(
                parent,
                textvariable=var,
                width=field.width,
                validate="key",
                validatecommand=(validate_cmd, "%P")
            )

        elif field.field_type == "date":
            var = tk.StringVar()
            frame = ttk.Frame(parent)
            entry = ttk.Entry(frame, textvariable=var, width=field.width - 3)
            entry.pack(side=tk.LEFT, padx=(0, 5))
            btn = ttk.Button(frame, text="...", width=3, command=lambda: self.show_date_picker(var))
            btn.pack(side=tk.LEFT)
            widget = frame

        elif field.field_type == "select" and field.options:
            var = tk.StringVar()
            combo_options = [""] + list(field.options)  # Add empty option
            widget = ttk.Combobox(
                parent,
                textvariable=var,
                values=combo_options,
                width=field.width,
                state="readonly"
            )

        else:
            # Default to text field
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var, width=field.width)

        return var, widget

    def on_search(self):
        """Handle search button click."""
        # Collect search criteria
        criteria = {}
        for field in self.search_fields:
            value = field.var.get().strip()
            if value:  # Only include non-empty values
                criteria[field.name] = value

        # Call search callback
        if self.on_search_callback:
            self.on_search_callback(criteria)

    def on_reset(self):
        """Handle reset button click."""
        # Clear all search fields
        for field in self.search_fields:
            field.var.set("")

        # Perform search with empty criteria
        if self.on_search_callback:
            self.on_search_callback({})

    def validate_number(self, value):
        """
        Validate a number input.

        Args:
            value: The input value to validate

        Returns:
            True if valid, False otherwise
        """
        if value == "":
            return True

        try:
            float(value)
            return True
        except ValueError:
            return False

    def show_date_picker(self, var):
        """
        Show a date picker dialog.

        Args:
            var: The StringVar to update with selected date
        """
        # This is a placeholder for a date picker implementation
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Date Picker", "Date picker not implemented yet")

    def set_field_value(self, field_name, value):
        """
        Set the value of a search field.

        Args:
            field_name: The name of the field
            value: The value to set
        """
        for field in self.search_fields:
            if field.name == field_name:
                field.var.set(value)
                return

    def get_field_value(self, field_name):
        """
        Get the value of a search field.

        Args:
            field_name: The name of the field

        Returns:
            The field value
        """
        for field in self.search_fields:
            if field.name == field_name:
                return field.var.get()
        return None