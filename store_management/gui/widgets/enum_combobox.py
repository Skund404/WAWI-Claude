# gui/widgets/enum_combobox.py
"""
EnumCombobox widget for displaying and selecting enum values.
Specialized combobox for working with Python Enum types.
"""

import tkinter as tk
from tkinter import ttk
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union


class EnumCombobox(ttk.Combobox):
    """
    Combobox widget specialized for working with enum values.
    Provides a user-friendly way to display and select enum values.
    """

    def __init__(
            self,
            parent,
            enum_class: Type[Enum],
            textvariable: Optional[tk.StringVar] = None,
            display_formatter: Optional[callable] = None,
            **kwargs
    ):
        """
        Initialize the enum combobox.

        Args:
            parent: The parent widget
            enum_class: The enum class to use
            textvariable: Optional StringVar to track the selected value
            display_formatter: Optional function to format enum values for display
            **kwargs: Additional arguments for ttk.Combobox
        """
        self.enum_class = enum_class
        self.enum_values = list(enum_class)
        self.enum_by_name = {e.name: e for e in self.enum_values}
        self.enum_by_value = {str(e.value): e for e in self.enum_values}

        # Create a new StringVar if not provided
        if textvariable is None:
            textvariable = tk.StringVar()
        self.textvariable = textvariable

        # Define formatter for display values
        self.display_formatter = display_formatter or self._default_formatter

        # Create display values
        self.display_values = [self.display_formatter(e) for e in self.enum_values]

        # Create mapping from display values to enum values
        self.display_to_enum = {self.display_formatter(e): e for e in self.enum_values}

        # Initialize combobox with display values
        super().__init__(parent, textvariable=textvariable, values=self.display_values, **kwargs)

        # Set up change tracking
        self.bind("<<ComboboxSelected>>", self._on_select)

        # Initialize the display value
        self._update_display_from_var()

        # Track original variable's set method for custom setting
        self._original_var_set = self.textvariable.set
        self.textvariable.set = self._custom_var_set

    def _default_formatter(self, enum_value: Enum) -> str:
        """
        Default formatter for enum values.
        Converts enum values to display strings.

        Args:
            enum_value: The enum value to format

        Returns:
            Formatted string for display
        """
        # Use enum value, replacing underscores with spaces and capitalizing words
        if hasattr(enum_value, 'value'):
            # For Enum types that use string values
            if isinstance(enum_value.value, str):
                return enum_value.value.replace('_', ' ').title()
            # For other value types
            return str(enum_value.value)

        # Fallback to name
        return enum_value.name.replace('_', ' ').title()

    def _on_select(self, event):
        """
        Handle combobox selection change.

        Args:
            event: The ComboboxSelected event
        """
        # Get the selected display value
        display_value = self.get()

        # Convert to enum value
        enum_value = self.display_to_enum.get(display_value)

        # Store the enum value (as string) in the variable
        if enum_value:
            self._original_var_set(str(enum_value.value))

    def _custom_var_set(self, value):
        """
        Custom set method for the textvariable.
        Converts enum values or strings to display values.

        Args:
            value: The value to set (enum value, enum name, or string)
        """
        # Convert value to enum if it's not already
        enum_value = self._convert_to_enum(value)

        if enum_value:
            # Set the display value in the combobox
            display_value = self.display_formatter(enum_value)
            super().set(display_value)

            # Store the actual enum value (as string) in the variable
            self._original_var_set(str(enum_value.value))
        else:
            # If value can't be converted to enum, just set it directly
            super().set(str(value))
            self._original_var_set(str(value))

    def _update_display_from_var(self):
        """Update the display value based on the current variable value."""
        value = self.textvariable.get()
        self._custom_var_set(value)

    def _convert_to_enum(self, value) -> Optional[Enum]:
        """
        Convert a value to an enum instance.

        Args:
            value: Value to convert (enum instance, enum name, or string)

        Returns:
            Enum instance or None if conversion fails
        """
        if value is None or value == "":
            return None

        # Already an enum instance
        if isinstance(value, self.enum_class):
            return value

        # Try by name (for string enum names)
        if isinstance(value, str) and value in self.enum_by_name:
            return self.enum_by_name[value]

        # Try by value (converted to string for comparison)
        if str(value) in self.enum_by_value:
            return self.enum_by_value[str(value)]

        # Check if value matches a display value
        if value in self.display_to_enum:
            return self.display_to_enum[value]

        # No match found
        return None

    def get_enum(self) -> Optional[Enum]:
        """
        Get the selected enum value.

        Returns:
            Selected enum value or None if none selected
        """
        value = self.textvariable.get()
        return self._convert_to_enum(value)

    def set_enum(self, enum_value: Union[Enum, str, Any]):
        """
        Set the selected enum value.

        Args:
            enum_value: Enum value to select (can be instance, name, or value)
        """
        self._custom_var_set(enum_value)