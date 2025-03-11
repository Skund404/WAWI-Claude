# gui/base/base_form_view.py
"""
Base Form View class for data entry and editing.
Provides common functionality for form-based views.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Type, Union

from gui.base.base_view import BaseView
from gui.widgets.enum_combobox import EnumCombobox
from gui import theme, config


class FormField:
    """Class representing a form field configuration."""

    def __init__(
            self,
            name: str,
            label: str,
            field_type: str = "text",
            required: bool = False,
            default: Any = None,
            enum_class: Optional[Type] = None,
            options: Optional[List[Any]] = None,
            validators: Optional[List[Any]] = None,
            readonly: bool = False,
            width: int = 30,
            help_text: Optional[str] = None
    ):
        """
        Initialize a form field configuration.

        Args:
            name: The field name (attribute/key name in data model)
            label: Display label for the field
            field_type: Type of field (text, password, number, date, enum, boolean, etc.)
            required: Whether the field is required
            default: Default value for the field
            enum_class: For enum fields, the enum class
            options: For option fields, list of available options
            validators: List of validator functions
            readonly: Whether the field is read-only
            width: Width of the field control
            help_text: Help text to display for the field
        """
        self.name = name
        self.label = label
        self.field_type = field_type
        self.required = required
        self.default = default
        self.enum_class = enum_class
        self.options = options
        self.validators = validators or []
        self.readonly = readonly
        self.width = width
        self.help_text = help_text

        # Control variable and widget (set during form creation)
        self.var = None
        self.widget = None


class BaseFormView(BaseView):
    """
    Base class for all form views in the application.
    Provides common functionality for data entry and editing forms.
    """

    def __init__(self, parent, item_id=None):
        """
        Initialize the base form view.

        Args:
            parent: The parent widget
            item_id: ID of the item to edit (None for new items)
        """
        super().__init__(parent)
        self.item_id = item_id
        self.title = "Form View"
        self.service_name = None  # Service name to resolve via DI
        self.is_edit_mode = item_id is not None
        self.fields = []  # List of FormField instances
        self.data = {}  # Current form data
        self.frame = None
        self.form_frame = None
        self.form_sections = {}  # Dict of section frames
        self.validation_errors = {}  # Dict of field name -> error message
        self.error_labels = {}  # Dict of field name -> error label widget

    def build(self):
        """Build the form view layout."""
        super().build()

        # Create main content frame
        content = ttk.Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollable form container
        form_container = ttk.Frame(content)
        form_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(form_container)
        scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=canvas.yview)
        self.form_frame = ttk.Frame(canvas)

        self.form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Build the form fields
        self.create_form_fields()

        # Create form buttons
        self.create_form_buttons(content)

        # Load data if in edit mode
        if self.is_edit_mode:
            self.load_item_data()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Back button
        btn_back = ttk.Button(
            self.action_buttons,
            text="Back",
            command=self.on_back)
        btn_back.pack(side=tk.LEFT, padx=5)

    def create_form_fields(self):
        """Create form fields based on field definitions."""
        # Create a dictionary to hold error labels for each field
        self.error_labels = {}

        for i, field in enumerate(self.fields):
            # Create field container
            field_container = ttk.Frame(self.form_frame)
            field_container.pack(fill=tk.X, padx=10, pady=5)

            # Add required indicator to label if needed
            if field.required:
                label_text = f"{field.label} *"
            else:
                label_text = field.label

            # Create label
            ttk.Label(field_container, text=label_text).grid(
                row=0, column=0, sticky="w", padx=5)

            # Create field widget based on field type
            field.var, field.widget = self.create_field_widget(field_container, field)
            field.widget.grid(row=0, column=1, sticky="ew", padx=5)

            # Add help text if provided
            if field.help_text:
                ttk.Label(
                    field_container,
                    text=field.help_text,
                    foreground=theme.COLORS["text_secondary"],
                    font=theme.create_custom_font(theme.FONTS["small"])
                ).grid(row=1, column=1, sticky="w", padx=5)

            # Add error label (initially empty)
            error_label = ttk.Label(
                field_container,
                text="",
                foreground=theme.COLORS["error"],
                font=theme.create_custom_font(theme.FONTS["small"])
            )
            error_label.grid(row=2, column=1, sticky="w", padx=5)
            self.error_labels[field.name] = error_label

            # Configure grid column weights
            field_container.grid_columnconfigure(1, weight=1)

    def create_field_widget(self, parent, field):
        """
        Create a widget for a form field.

        Args:
            parent: The parent widget
            field: The FormField configuration

        Returns:
            Tuple of (variable, widget)
        """
        readonly = field.readonly or (self.is_edit_mode and not self.is_field_editable(field.name))
        state = "readonly" if readonly else "normal"

        if field.field_type == "text":
            var = tk.StringVar(value=field.default or "")
            widget = ttk.Entry(parent, textvariable=var, width=field.width, state=state)

        elif field.field_type == "password":
            var = tk.StringVar(value=field.default or "")
            widget = ttk.Entry(parent, textvariable=var, width=field.width, show="*", state=state)

        elif field.field_type == "number":
            var = tk.DoubleVar(value=field.default or 0.0)
            validate_cmd = parent.register(self.validate_number)
            widget = ttk.Entry(
                parent,
                textvariable=var,
                width=field.width,
                validate="key",
                validatecommand=(validate_cmd, "%P"),
                state=state
            )

        elif field.field_type == "integer":
            var = tk.IntVar(value=field.default or 0)
            validate_cmd = parent.register(self.validate_integer)
            widget = ttk.Entry(
                parent,
                textvariable=var,
                width=field.width,
                validate="key",
                validatecommand=(validate_cmd, "%P"),
                state=state
            )

        elif field.field_type == "date":
            var = tk.StringVar(value=field.default or "")
            frame = ttk.Frame(parent)
            entry = ttk.Entry(frame, textvariable=var, width=field.width - 5, state=state)
            entry.pack(side=tk.LEFT, padx=(0, 5))
            if not readonly:
                btn = ttk.Button(frame, text="...", width=3, command=lambda: self.show_date_picker(var))
                btn.pack(side=tk.LEFT)
            widget = frame

        elif field.field_type == "boolean":
            var = tk.BooleanVar(value=field.default or False)
            widget = ttk.Checkbutton(
                parent,
                variable=var,
                onvalue=True,
                offvalue=False,
                state=state
            )

        elif field.field_type == "enum" and field.enum_class:
            var = tk.StringVar(value=str(field.default) if field.default else "")
            widget = EnumCombobox(
                parent,
                enum_class=field.enum_class,
                textvariable=var,
                width=field.width,
                state=state
            )

        elif field.field_type == "combobox" and field.options:
            var = tk.StringVar(value=field.default or "")
            widget = ttk.Combobox(
                parent,
                textvariable=var,
                values=field.options,
                width=field.width,
                state=state
            )

        elif field.field_type == "textarea":
            var = tk.StringVar(value=field.default or "")
            frame = ttk.Frame(parent)
            text = tk.Text(frame, width=field.width, height=5, wrap=tk.WORD)
            if field.default:
                text.insert("1.0", field.default)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            if readonly:
                text.configure(state="disabled")
            widget = frame
            # Custom getter/setter for Text widget
            var.get_from_widget = lambda: text.get("1.0", "end-1c")
            var.set_to_widget = lambda value: (text.delete("1.0", tk.END), text.insert("1.0", value or ""))

        else:
            # Default to text field
            var = tk.StringVar(value=field.default or "")
            widget = ttk.Entry(parent, textvariable=var, width=field.width, state=state)

        return var, widget

    def create_form_buttons(self, parent):
        """
        Create form action buttons.

        Args:
            parent: The parent widget
        """
        button_frame = ttk.Frame(parent)

        # Cancel button
        btn_cancel = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel)
        btn_cancel.pack(side=tk.LEFT, padx=5, pady=10)

        # Save button
        btn_save = ttk.Button(
            button_frame,
            text="Save",
            command=self.on_save)
        btn_save.pack(side=tk.RIGHT, padx=5, pady=10)

        button_frame.pack(fill=tk.X, padx=10, pady=10)

    def load_item_data(self):
        """Load item data for editing."""
        if not self.is_edit_mode or not self.item_id:
            return

        try:
            service = self.get_service(self.service_name)
            if not service:
                return

            # Load item data
            item = service.get_by_id(self.item_id)
            if not item:
                self.show_error("Not Found", f"Item with ID {self.item_id} not found")
                self.on_cancel()
                return

            # Convert to dictionary if not already
            if hasattr(item, '__dict__'):
                self.data = self.item_to_dict(item)
            elif isinstance(item, dict):
                self.data = item
            else:
                self.data = {"id": self.item_id}

            # Populate form fields
            self.populate_fields()

        except Exception as e:
            self.logger.error(f"Error loading item data: {str(e)}")
            self.show_error("Data Load Error", f"Failed to load item data: {str(e)}")

    def item_to_dict(self, item):
        """
        Convert an item model to a dictionary.

        Args:
            item: The item model to convert

        Returns:
            Dictionary representation of the item
        """
        # Default implementation - override in subclasses for more complex conversions
        result = {}
        for field in self.fields:
            if hasattr(item, field.name):
                result[field.name] = getattr(item, field.name)
        return result

    def populate_fields(self):
        """Populate form fields from data dictionary."""
        for field in self.fields:
            if field.name in self.data:
                value = self.data[field.name]

                # Handle different field types
                if field.field_type == "textarea" and hasattr(field.var, "set_to_widget"):
                    field.var.set_to_widget(str(value) if value is not None else "")
                elif field.field_type == "enum" and value is not None:
                    field.var.set(str(value))
                elif field.field_type in ["date", "datetime"] and value is not None:
                    # Format date/datetime values
                    if hasattr(value, "strftime"):
                        formatted = value.strftime(
                            config.DATETIME_FORMAT if field.field_type == "datetime" else config.DATE_FORMAT
                        )
                        field.var.set(formatted)
                    else:
                        field.var.set(str(value))
                else:
                    # Default handling
                    field.var.set(value if value is not None else "")

    def is_field_editable(self, field_name):
        """
        Determine if a field is editable in edit mode.
        Can be overridden by subclasses.

        Args:
            field_name: The name of the field

        Returns:
            True if the field is editable, False otherwise
        """
        # By default, all fields are editable except ID
        return field_name != "id"

    def collect_form_data(self):
        """
        Collect data from form fields.

        Returns:
            Dictionary of form data
        """
        result = {}
        for field in self.fields:
            if field.field_type == "textarea" and hasattr(field.var, "get_from_widget"):
                result[field.name] = field.var.get_from_widget()
            else:
                result[field.name] = field.var.get()
        return result

    def validate_form(self):
        """
        Validate form data.

        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = {}
        data = self.collect_form_data()

        # Apply field validations
        for field in self.fields:
            # Skip validation for read-only fields
            if field.readonly:
                continue

            value = data.get(field.name)

            # Check required fields
            if field.required and (value is None or value == ""):
                self.validation_errors[field.name] = "This field is required"
                continue

            # Apply field-specific validators
            for validator in field.validators:
                try:
                    valid, message = validator(value)
                    if not valid:
                        self.validation_errors[field.name] = message
                        break
                except Exception as e:
                    self.logger.error(f"Validation error for {field.name}: {str(e)}")
                    self.validation_errors[field.name] = f"Validation error: {str(e)}"

        # Apply additional validations from subclasses
        additional_errors = self.validate_additional()
        self.validation_errors.update(additional_errors)

        # Update error display
        self.display_validation_errors()

        return len(self.validation_errors) == 0

    def validate_additional(self):
        """
        Apply additional validations beyond field-level validations.

        Returns:
            Dictionary of field name -> error message
        """
        # Override in subclasses for custom validation
        return {}

    def display_validation_errors(self):
        """Display validation errors in the form."""
        # First clear all error messages
        for error_label in self.error_labels.values():
            error_label.config(text="")

        # Display new error messages
        for field_name, error_message in self.validation_errors.items():
            if field_name in self.error_labels:
                self.error_labels[field_name].config(text=error_message)

    def on_save(self):
        """Handle form save action."""
        if not self.validate_form():
            self.show_error("Validation Error", "Please correct the errors in the form")
            return

        try:
            service = self.get_service(self.service_name)
            if not service:
                return

            # Collect form data
            data = self.collect_form_data()

            # Process data before save
            processed_data = self.process_data_before_save(data)

            # Save or update
            if self.is_edit_mode:
                result = service.update(self.item_id, processed_data)
                message = "Item updated successfully"
            else:
                result = service.create(processed_data)
                message = "Item created successfully"

            # Show success message
            self.show_info("Success", message)

            # Call on_save_success (can be used for navigation, etc.)
            self.on_save_success(result)

        except Exception as e:
            self.logger.error(f"Error saving form: {str(e)}")
            self.show_error("Save Error", f"Failed to save: {str(e)}")

    def process_data_before_save(self, data):
        """
        Process form data before saving.

        Args:
            data: The form data to process

        Returns:
            Processed data ready for saving
        """
        # Override in subclasses to process data
        return data

    def on_save_success(self, result):
        """
        Handle successful save action.

        Args:
            result: The result of the save operation
        """
        # Override in subclasses for custom behavior
        self.on_cancel()  # Default behavior: close form

    def on_cancel(self):
        """Handle form cancel action."""
        # Override in subclasses if needed
        self.destroy()

    def on_back(self):
        """Handle back button action."""
        self.on_cancel()

    def show_date_picker(self, var):
        """
        Show a date picker dialog.

        Args:
            var: The StringVar to update with selected date
        """
        # This is a placeholder for a date picker implementation
        # In a real application, you would integrate with a calendar widget
        self.show_info("Date Picker", "Date picker not implemented yet")

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

    def validate_integer(self, value):
        """
        Validate an integer input.

        Args:
            value: The input value to validate

        Returns:
            True if valid, False otherwise
        """
        if value == "":
            return True

        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return True

        return False