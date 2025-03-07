"""
Dynamic form builder for creating form interfaces based on field definitions.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
import re

logger = logging.getLogger(__name__)


class FormField:
    """Base class for all form field types."""

    def __init__(self, name: str, label: str, required: bool = False,
                 readonly: bool = False, help_text: str = "",
                 validator: Optional[Callable[[Any], bool]] = None,
                 initial_value: Any = None):
        """
        Initialize a form field.

        Args:
            name: Field name (used as key for data)
            label: Display label for the field
            required: Whether the field is required
            readonly: Whether the field is read-only
            help_text: Optional help text to display
            validator: Optional validation function
            initial_value: Initial value for the field
        """
        self.name = name
        self.label = label
        self.required = required
        self.readonly = readonly
        self.help_text = help_text
        self.validator = validator
        self.initial_value = initial_value
        self.widget = None
        self.error = None

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """
        Create the widget for this field.

        Args:
            parent: Parent widget

        Returns:
            The created widget
        """
        raise NotImplementedError("Subclasses must implement create_widget")

    def get_value(self) -> Any:
        """
        Get the current value of the field.

        Returns:
            The field value
        """
        raise NotImplementedError("Subclasses must implement get_value")

    def set_value(self, value: Any):
        """
        Set the value of the field.

        Args:
            value: The value to set
        """
        raise NotImplementedError("Subclasses must implement set_value")

    def set_error(self, error: Optional[str]):
        """
        Set an error message for the field.

        Args:
            error: Error message or None to clear
        """
        self.error = error
        if hasattr(self, '_error_label') and self._error_label:
            if error:
                self._error_label.config(text=error)
                self._error_label.pack(side=tk.TOP, fill=tk.X, padx=2)
                self._highlight_error()
            else:
                self._error_label.pack_forget()
                self._clear_error()

    def _highlight_error(self):
        """Highlight the field to indicate an error."""
        if self.widget:
            try:
                if isinstance(self.widget, ttk.Entry) or isinstance(self.widget, ttk.Combobox):
                    self.widget.state(['invalid'])
                elif isinstance(self.widget, tk.Entry) or isinstance(self.widget, tk.Text):
                    self.widget.config(background="#ffebee")  # Light red
            except Exception as e:
                logger.error(f"Error highlighting field {self.name}: {e}")

    def _clear_error(self):
        """Clear error highlighting."""
        if self.widget:
            try:
                if isinstance(self.widget, ttk.Entry) or isinstance(self.widget, ttk.Combobox):
                    self.widget.state(['!invalid'])
                elif isinstance(self.widget, tk.Entry) or isinstance(self.widget, tk.Text):
                    self.widget.config(background="white")
            except Exception as e:
                logger.error(f"Error clearing field highlighting: {e}")

    def validate(self) -> bool:
        """
        Validate the field value.

        Returns:
            True if valid, False otherwise
        """
        value = self.get_value()

        # Check required
        if self.required and (value is None or value == ""):
            self.set_error("This field is required")
            return False

        # Apply custom validator if provided
        if self.validator and value:
            try:
                result = self.validator(value)
                if result is not True:
                    self.set_error(result if isinstance(result, str) else "Invalid value")
                    return False
            except Exception as e:
                self.set_error(str(e))
                return False

        # Clear any previous errors
        self.set_error(None)
        return True


class StringField(FormField):
    """Text input field for single-line text."""

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create a string input widget."""
        frame = ttk.Frame(parent)

        # Create variable
        self.var = tk.StringVar(value=str(self.initial_value or ""))

        # Create widget
        self.widget = ttk.Entry(frame, textvariable=self.var)
        self.widget.pack(side=tk.TOP, fill=tk.X)

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed
        if self.readonly:
            self.widget.state(['readonly'])

        return frame

    def get_value(self) -> str:
        """Get the string value."""
        return self.var.get()

    def set_value(self, value: Any):
        """Set the string value."""
        self.var.set(str(value or ""))


class IntegerField(FormField):
    """Text input field for integer values."""

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create an integer input widget."""
        frame = ttk.Frame(parent)

        # Create variable
        self.var = tk.StringVar()
        if self.initial_value is not None:
            try:
                self.var.set(str(int(self.initial_value)))
            except (ValueError, TypeError):
                self.var.set("0")
        else:
            self.var.set("0")

        # Create validator
        validate_cmd = parent.register(self._validate_integer)

        # Create widget
        self.widget = ttk.Entry(
            frame,
            textvariable=self.var,
            validate="key",
            validatecommand=(validate_cmd, '%P')
        )
        self.widget.pack(side=tk.TOP, fill=tk.X)

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed
        if self.readonly:
            self.widget.state(['readonly'])

        return frame

    def _validate_integer(self, value: str) -> bool:
        """Validate that the input is an integer."""
        if value == "":
            return True

        try:
            int(value)
            return True
        except ValueError:
            return False

    def get_value(self) -> Optional[int]:
        """Get the integer value."""
        try:
            return int(self.var.get())
        except ValueError:
            return None

    def set_value(self, value: Any):
        """Set the integer value."""
        try:
            self.var.set(str(int(value)))
        except (ValueError, TypeError):
            self.var.set("0")


class FloatField(FormField):
    """Text input field for floating-point values."""

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create a float input widget."""
        frame = ttk.Frame(parent)

        # Create variable
        self.var = tk.StringVar()
        if self.initial_value is not None:
            try:
                self.var.set(str(float(self.initial_value)))
            except (ValueError, TypeError):
                self.var.set("0.0")
        else:
            self.var.set("0.0")

        # Create validator
        validate_cmd = parent.register(self._validate_float)

        # Create widget
        self.widget = ttk.Entry(
            frame,
            textvariable=self.var,
            validate="key",
            validatecommand=(validate_cmd, '%P')
        )
        self.widget.pack(side=tk.TOP, fill=tk.X)

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed
        if self.readonly:
            self.widget.state(['readonly'])

        return frame

    def _validate_float(self, value: str) -> bool:
        """Validate that the input is a floating-point number."""
        if value == "" or value == "-":
            return True

        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_value(self) -> Optional[float]:
        """Get the float value."""
        try:
            return float(self.var.get())
        except ValueError:
            return None

    def set_value(self, value: Any):
        """Set the float value."""
        try:
            self.var.set(str(float(value)))
        except (ValueError, TypeError):
            self.var.set("0.0")


class BooleanField(FormField):
    """Checkbox field for boolean values."""

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create a boolean input widget."""
        frame = ttk.Frame(parent)

        # Create variable
        self.var = tk.BooleanVar(value=bool(self.initial_value))

        # Create widget - use a shorter label as it appears next to the checkbox
        short_label = self.label
        if len(short_label) > 30:
            short_label = short_label[:27] + "..."

        self.widget = ttk.Checkbutton(
            frame,
            text=short_label,
            variable=self.var
        )
        self.widget.pack(side=tk.TOP, fill=tk.X, anchor=tk.W)

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed
        if self.readonly:
            self.widget.state(['disabled'])

        return frame

    def get_value(self) -> bool:
        """Get the boolean value."""
        return self.var.get()

    def set_value(self, value: Any):
        """Set the boolean value."""
        self.var.set(bool(value))


class TextField(FormField):
    """Multi-line text input field."""

    def __init__(self, *args, height: int = 5, **kwargs):
        """
        Initialize a text field.

        Args:
            height: Height of the text area in lines
            *args: Additional arguments for FormField
            **kwargs: Additional keyword arguments for FormField
        """
        super().__init__(*args, **kwargs)
        self.height = height

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create a multi-line text input widget."""
        frame = ttk.Frame(parent)

        # Create widget
        self.widget = tk.Text(
            frame,
            height=self.height,
            width=10,  # Will expand with frame
            wrap=tk.WORD
        )
        self.widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.widget.configure(yscrollcommand=scrollbar.set)

        # Set initial value
        if self.initial_value:
            self.widget.insert(tk.END, str(self.initial_value))

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed
        if self.readonly:
            self.widget.configure(state=tk.DISABLED)

        return frame

    def get_value(self) -> str:
        """Get the text value."""
        return self.widget.get(1.0, tk.END).strip()

    def set_value(self, value: Any):
        """Set the text value."""
        # Clear current content
        self.widget.delete(1.0, tk.END)

        # Insert new content
        if value:
            self.widget.insert(tk.END, str(value))


class ChoiceField(FormField):
    """Dropdown selection field."""

    def __init__(self, *args, choices: List[Union[str, Tuple[str, str]]] = None, **kwargs):
        """
        Initialize a choice field.

        Args:
            choices: List of choices (strings or (value, label) tuples)
            *args: Additional arguments for FormField
            **kwargs: Additional keyword arguments for FormField
        """
        super().__init__(*args, **kwargs)
        self.choices = choices or []

        # Process choices into values and display texts
        self.values = []
        self.display_texts = []

        for choice in self.choices:
            if isinstance(choice, tuple) and len(choice) == 2:
                self.values.append(choice[0])
                self.display_texts.append(choice[1])
            else:
                self.values.append(choice)
                self.display_texts.append(str(choice))

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create a dropdown selection widget."""
        frame = ttk.Frame(parent)

        # Create variable
        self.var = tk.StringVar()

        # Set initial value if provided
        if self.initial_value is not None:
            if self.initial_value in self.values:
                self.var.set(self.initial_value)
            elif str(self.initial_value) in self.values:
                self.var.set(str(self.initial_value))
        elif self.values:
            # Default to first value
            self.var.set(self.values[0])

        # Create widget
        self.widget = ttk.Combobox(
            frame,
            textvariable=self.var,
            values=self.display_texts,
            state="readonly"
        )
        self.widget.pack(side=tk.TOP, fill=tk.X)

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed (combobox is already readonly)

        return frame

    def get_value(self) -> str:
        """Get the selected value."""
        display_text = self.var.get()
        if display_text in self.display_texts:
            index = self.display_texts.index(display_text)
            return self.values[index]
        return display_text

    def set_value(self, value: Any):
        """Set the selected value."""
        if value in self.values:
            index = self.values.index(value)
            self.var.set(self.display_texts[index])
        elif str(value) in self.values:
            index = self.values.index(str(value))
            self.var.set(self.display_texts[index])
        elif value in self.display_texts:
            self.var.set(value)
        elif self.values:
            # Default to first value
            self.var.set(self.display_texts[0])


class DateField(FormField):
    """Date input field."""

    def create_widget(self, parent: tk.Widget) -> tk.Widget:
        """Create a date input widget."""
        frame = ttk.Frame(parent)

        # Try to import DateEntry from tkcalendar
        try:
            from tkcalendar import DateEntry

            # Create widget
            self.widget = DateEntry(
                frame,
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                date_pattern='yyyy-mm-dd'
            )
            self.widget.pack(side=tk.TOP, fill=tk.X)

            # Set initial value
            if self.initial_value:
                try:
                    self.widget.set_date(self.initial_value)
                except:
                    pass

        except ImportError:
            # Fall back to regular entry with validation
            logger.warning("tkcalendar not available, using text entry for date")

            # Create variable
            self.var = tk.StringVar()

            # Set initial value
            if self.initial_value:
                self.var.set(str(self.initial_value))

            # Create validator
            validate_cmd = parent.register(self._validate_date)

            # Create widget
            self.widget = ttk.Entry(
                frame,
                textvariable=self.var,
                validate="key",
                validatecommand=(validate_cmd, '%P')
            )
            self.widget.pack(side=tk.TOP, fill=tk.X)

            # Add hint
            hint = ttk.Label(frame, text="Format: YYYY-MM-DD", font=("", 8), foreground="gray")
            hint.pack(side=tk.TOP, anchor=tk.W)

        # Add error label (hidden by default)
        self._error_label = ttk.Label(frame, foreground="red", font=("", 8))

        # Set readonly if needed
        if self.readonly:
            if hasattr(self.widget, 'state'):
                self.widget.state(['readonly'])
            else:
                self.widget.configure(state=tk.DISABLED)

        return frame

    def _validate_date(self, value: str) -> bool:
        """Validate date format."""
        if value == "":
            return True

        # Check for valid date format (YYYY-MM-DD)
        if re.match(r'^\d{4}-\d{0,2}-\d{0,2}', value):
            return True

        return False

    def get_value(self) -> str:
        """Get the date value."""
        if hasattr(self.widget, 'get_date'):
            return self.widget.get_date()
        else:
            return self.var.get()

    def set_value(self, value: Any):
        """Set the date value."""
        if hasattr(self.widget, 'set_date'):
            try:
                self.widget.set_date(value)
            except:
                pass
        else:
            self.var.set(str(value or ""))


class FormBuilder:
    """
    Dynamic form builder that creates forms from field definitions.

    Features:
    - Support for various field types
    - Validation
    - Field dependencies
    - Layout customization
    """

    # Map field types to field classes
    FIELD_TYPES = {
        'string': StringField,
        'integer': IntegerField,
        'float': FloatField,
        'boolean': BooleanField,
        'text': TextField,
        'choice': ChoiceField,
        'date': DateField,
    }

    def __init__(self, parent: tk.Widget, field_definitions: List[Dict[str, Any]],
                 initial_data: Optional[Dict[str, Any]] = None,
                 on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
                 layout: str = "vertical", columns: int = 1):
        """
        Initialize the form builder.

        Args:
            parent: Parent widget
            field_definitions: List of field definitions
            initial_data: Optional dictionary of initial values
            on_submit: Optional callback for form submission
            layout: Form layout ("vertical", "horizontal", or "grid")
            columns: Number of columns for grid layout
        """
        self.parent = parent
        self.field_definitions = field_definitions
        self.initial_data = initial_data or {}
        self.on_submit = on_submit
        self.layout = layout
        self.columns = columns

        # Dictionary to store field instances
        self.fields = {}

        # Build the form
        self._build_form()

        logger.debug(f"Form builder initialized with {len(field_definitions)} fields")

    def _build_form(self):
        """Build the form based on field definitions."""
        # Create main form frame
        self.form_frame = ttk.Frame(self.parent)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollable content
        self.canvas = tk.Canvas(self.form_frame, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.form_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content_frame = ttk.Frame(self.canvas)

        # Configure scrolling
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)

        # Configure canvas to use scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack widgets
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create fields based on layout
        if self.layout == "horizontal":
            self._build_horizontal_layout()
        elif self.layout == "grid":
            self._build_grid_layout()
        else:  # vertical layout
            self._build_vertical_layout()

        # Add submit button if callback is provided
        if self.on_submit:
            self.button_frame = ttk.Frame(self.form_frame)
            self.button_frame.pack(fill=tk.X, pady=(10, 0))

            self.submit_button = ttk.Button(
                self.button_frame,
                text="Submit",
                command=self._on_submit,
                style="Primary.TButton"
            )
            self.submit_button.pack(side=tk.RIGHT)

    def _on_canvas_resize(self, event):
        """Handle canvas resize event."""
        # Update the width of canvas window to match canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _build_vertical_layout(self):
        """Build form with vertical layout (labels above fields)."""
        for field_def in self.field_definitions:
            # Check required fields
            if "name" not in field_def or "type" not in field_def:
                logger.warning(f"Invalid field definition: {field_def}")
                continue

            name = field_def["name"]
            field_type = field_def["type"]

            # Get field class for this type
            field_class = self.FIELD_TYPES.get(field_type)
            if not field_class:
                logger.warning(f"Unknown field type: {field_type}")
                continue

            # Get initial value if available
            initial_value = self.initial_data.get(name)

            # Create field instance
            field = field_class(
                name=name,
                label=field_def.get("label", name.replace("_", " ").title()),
                required=field_def.get("required", False),
                readonly=field_def.get("readonly", False),
                help_text=field_def.get("help_text", ""),
                validator=field_def.get("validator"),
                initial_value=initial_value,
                **{k: v for k, v in field_def.items() if k not in [
                    "name", "type", "label", "required", "readonly", "help_text", "validator"
                ]}
            )

            # Create field container
            field_container = ttk.Frame(self.content_frame)
            field_container.pack(fill=tk.X, pady=(0, 10))

            # Add label
            label_text = field.label
            if field.required:
                label_text += " *"

            label = ttk.Label(field_container, text=label_text)
            label.pack(fill=tk.X, anchor=tk.W)

            # Create and add the field widget
            field_widget = field.create_widget(field_container)
            field_widget.pack(fill=tk.X, pady=(2, 0))

            # Add help text if provided
            if field.help_text:
                help_label = ttk.Label(
                    field_container,
                    text=field.help_text,
                    foreground="gray",
                    font=("", 8)
                )
                help_label.pack(fill=tk.X, anchor=tk.W, pady=(2, 0))

            # Store the field
            self.fields[name] = field

    def _build_horizontal_layout(self):
        """Build form with horizontal layout (labels beside fields)."""
        for field_def in self.field_definitions:
            # Check required fields
            if "name" not in field_def or "type" not in field_def:
                logger.warning(f"Invalid field definition: {field_def}")
                continue

            name = field_def["name"]
            field_type = field_def["type"]

            # Get field class for this type
            field_class = self.FIELD_TYPES.get(field_type)
            if not field_class:
                logger.warning(f"Unknown field type: {field_type}")
                continue

            # Get initial value if available
            initial_value = self.initial_data.get(name)

            # Create field instance
            field = field_class(
                name=name,
                label=field_def.get("label", name.replace("_", " ").title()),
                required=field_def.get("required", False),
                readonly=field_def.get("readonly", False),
                help_text=field_def.get("help_text", ""),
                validator=field_def.get("validator"),
                initial_value=initial_value,
                **{k: v for k, v in field_def.items() if k not in [
                    "name", "type", "label", "required", "readonly", "help_text", "validator"
                ]}
            )

            # Special case for boolean fields in horizontal layout
            if field_type == "boolean":
                # Create field container
                field_container = ttk.Frame(self.content_frame)
                field_container.pack(fill=tk.X, pady=(0, 10))

                # Boolean fields have the label as part of the checkbox
                field_widget = field.create_widget(field_container)
                field_widget.pack(fill=tk.X)

                # Add help text if provided
                if field.help_text:
                    help_label = ttk.Label(
                        field_container,
                        text=field.help_text,
                        foreground="gray",
                        font=("", 8)
                    )
                    help_label.pack(fill=tk.X, anchor=tk.W, pady=(2, 0), padx=(23, 0))
            else:
                # Create field container
                field_container = ttk.Frame(self.content_frame)
                field_container.pack(fill=tk.X, pady=(0, 10))

                # Configure grid layout
                field_container.columnconfigure(0, weight=0)
                field_container.columnconfigure(1, weight=1)

                # Add label
                label_text = field.label
                if field.required:
                    label_text += " *"

                label = ttk.Label(field_container, text=label_text)
                label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

                # Create and add the field widget
                field_widget = field.create_widget(field_container)
                field_widget.grid(row=0, column=1, sticky=tk.EW)

                # Add help text if provided
                if field.help_text:
                    help_label = ttk.Label(
                        field_container,
                        text=field.help_text,
                        foreground="gray",
                        font=("", 8)
                    )
                    help_label.grid(row=1, column=1, sticky=tk.W, pady=(2, 0))

            # Store the field
            self.fields[name] = field

    def _build_grid_layout(self):
        """Build form with grid layout (multiple columns)."""
        # Create grid container
        grid_frame = ttk.Frame(self.content_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        # Configure columns
        for i in range(self.columns):
            grid_frame.columnconfigure(i * 2, weight=0)  # Label column
            grid_frame.columnconfigure(i * 2 + 1, weight=1)  # Field column

        # Place fields in the grid
        row, col = 0, 0
        for field_def in self.field_definitions:
            # Check required fields
            if "name" not in field_def or "type" not in field_def:
                logger.warning(f"Invalid field definition: {field_def}")
                continue

            name = field_def["name"]
            field_type = field_def["type"]

            # Get field class for this type
            field_class = self.FIELD_TYPES.get(field_type)
            if not field_class:
                logger.warning(f"Unknown field type: {field_type}")
                continue

            # Get initial value if available
            initial_value = self.initial_data.get(name)

            # Create field instance
            field = field_class(
                name=name,
                label=field_def.get("label", name.replace("_", " ").title()),
                required=field_def.get("required", False),
                readonly=field_def.get("readonly", False),
                help_text=field_def.get("help_text", ""),
                validator=field_def.get("validator"),
                initial_value=initial_value,
                **{k: v for k, v in field_def.items() if k not in [
                    "name", "type", "label", "required", "readonly", "help_text", "validator"
                ]}
            )

            # Special case for boolean fields
            if field_type == "boolean":
                # Boolean fields span both label and field columns
                field_widget = field.create_widget(grid_frame)
                field_widget.grid(row=row, column=col * 2, columnspan=2, sticky=tk.W, pady=(0, 10), padx=5)

                # Add help text if provided
                if field.help_text:
                    help_label = ttk.Label(
                        grid_frame,
                        text=field.help_text,
                        foreground="gray",
                        font=("", 8)
                    )
                    row += 1
                    help_label.grid(row=row, column=col * 2, columnspan=2, sticky=tk.W, pady=(0, 10), padx=(23, 5))
            else:
                # Add label
                label_text = field.label
                if field.required:
                    label_text += " *"

                label = ttk.Label(grid_frame, text=label_text)
                label.grid(row=row, column=col * 2, sticky=tk.W, padx=5, pady=(0, 2))

                # Create and add the field widget
                field_widget = field.create_widget(grid_frame)
                field_widget.grid(row=row, column=col * 2 + 1, sticky=tk.EW, padx=5, pady=(0, 2))

                # Add help text if provided
                if field.help_text:
                    help_label = ttk.Label(
                        grid_frame,
                        text=field.help_text,
                        foreground="gray",
                        font=("", 8)
                    )
                    row += 1
                    help_label.grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=5)

            # Store the field
            self.fields[name] = field

            # Move to next column or row
            col += 1
            if col >= self.columns:
                col = 0
                row += 1

    def _on_submit(self):
        """Handle form submission."""
        if self.validate():
            data = self.get_data()
            if self.on_submit:
                self.on_submit(data)

    def validate(self) -> bool:
        """
        Validate all form fields.

        Returns:
            True if all fields are valid, False otherwise
        """
        valid = True
        for field in self.fields.values():
            if not field.validate():
                valid = False

        return valid

    def get_data(self) -> Dict[str, Any]:
        """
        Get the current form data.

        Returns:
            Dictionary of field values
        """
        data = {}
        for name, field in self.fields.items():
            data[name] = field.get_value()

        return data

    def set_data(self, data: Dict[str, Any]):
        """
        Set values for multiple fields.

        Args:
            data: Dictionary of field values
        """
        for name, value in data.items():
            if name in self.fields:
                self.fields[name].set_value(value)

    def set_field_value(self, field_name: str, value: Any):
        """
        Set the value of a specific field.

        Args:
            field_name: Name of the field
            value: Value to set
        """
        if field_name in self.fields:
            self.fields[field_name].set_value(value)

    def get_field_value(self, field_name: str) -> Any:
        """
        Get the value of a specific field.

        Args:
            field_name: Name of the field

        Returns:
            Field value
        """
        if field_name in self.fields:
            return self.fields[field_name].get_value()
        return None

    def set_readonly(self, readonly: bool = True):
        """
        Set all fields to readonly or editable.

        Args:
            readonly: Whether fields should be readonly
        """
        for field in self.fields.values():
            field.readonly = readonly

            # Update widget state
            if hasattr(field.widget, 'state'):
                if readonly:
                    field.widget.state(['readonly'])
                else:
                    field.widget.state(['!readonly'])
            elif hasattr(field.widget, 'configure'):
                if readonly:
                    field.widget.configure(state=tk.DISABLED)
                else:
                    field.widget.configure(state=tk.NORMAL)

    def set_field_readonly(self, field_name: str, readonly: bool = True):
        """
        Set a specific field to readonly or editable.

        Args:
            field_name: Name of the field
            readonly: Whether the field should be readonly
        """
        if field_name in self.fields:
            field = self.fields[field_name]
            field.readonly = readonly

            # Update widget state
            if hasattr(field.widget, 'state'):
                if readonly:
                    field.widget.state(['readonly'])
                else:
                    field.widget.state(['!readonly'])
            elif hasattr(field.widget, 'configure'):
                if readonly:
                    field.widget.configure(state=tk.DISABLED)
                else:
                    field.widget.configure(state=tk.NORMAL)

    def clear(self):
        """Clear all field values."""
        for field in self.fields.values():
            field.set_value(None)

    def focus_field(self, field_name: str):
        """
        Set focus to a specific field.

        Args:
            field_name: Name of the field
        """
        if field_name in self.fields:
            field = self.fields[field_name]
            if field.widget:
                field.widget.focus_set()


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Form Builder Demo")
    root.geometry("600x500")


    def validate_email(value):
        """Validate email format."""
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', value):
            return "Invalid email format"
        return True


    def validate_phone(value):
        """Validate phone number format."""
        if not re.match(r'^\d{3}-\d{3}-\d{4}', value):
            return "Format: 123-456-7890"
        return True


    def handle_submit(data):
        """Handle form submission."""
        print("Form submitted with data:")
        for key, value in data.items():
            print(f"  {key}: {value}")

        tk.messagebox.showinfo("Form Submitted", "Form submitted successfully!")


    # Field definitions
    fields = [
        {
            "name": "first_name",
            "type": "string",
            "label": "First Name",
            "required": True,
            "help_text": "Enter your legal first name"
        },
        {
            "name": "last_name",
            "type": "string",
            "label": "Last Name",
            "required": True
        },
        {
            "name": "email",
            "type": "string",
            "label": "Email",
            "required": True,
            "validator": validate_email,
            "help_text": "Your email address"
        },
        {
            "name": "phone",
            "type": "string",
            "label": "Phone",
            "validator": validate_phone,
            "help_text": "Format: 123-456-7890"
        },
        {
            "name": "age",
            "type": "integer",
            "label": "Age",
            "required": True
        },
        {
            "name": "country",
            "type": "choice",
            "label": "Country",
            "choices": [
                ("us", "United States"),
                ("ca", "Canada"),
                ("mx", "Mexico"),
                ("uk", "United Kingdom")
            ],
            "required": True
        },
        {
            "name": "subscribe",
            "type": "boolean",
            "label": "Subscribe to Newsletter",
            "help_text": "We'll send you updates about our products"
        },
        {
            "name": "birth_date",
            "type": "date",
            "label": "Birth Date"
        },
        {
            "name": "comments",
            "type": "text",
            "label": "Comments",
            "help_text": "Additional comments or feedback",
            "height": 3
        }
    ]

    # Initial data
    initial_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "country": "us",
        "subscribe": True
    }

    # Create form builder with grid layout
    form = FormBuilder(
        root,
        fields,
        initial_data=initial_data,
        on_submit=handle_submit,
        layout="grid",
        columns=2
    )

    root.mainloop()