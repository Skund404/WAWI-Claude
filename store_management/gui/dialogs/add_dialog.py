# relative/path/add_dialog.py
"""
Dynamic Add Dialog module for flexible entry creation in the application.

Provides a configurable dialog for adding new entries with dynamic field generation,
validation, and type-specific input handling.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import uuid
from typing import List, Tuple, Dict, Union, Callable, Any, Optional

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from utils.logging import get_logger
from base_dialog import BaseDialog

logger = get_logger(__name__)


class AddDialog(BaseDialog):
    """
    A flexible dialog for adding new entries with dynamic field generation.

    Supports different field types and provides validation mechanisms.

    Attributes:
        _parent (tk.Tk): Parent window
        _save_callback (Callable): Function to call when save is triggered
        _fields (List[Tuple]): List of field configurations
        _entries (Dict): Dictionary to store entry widgets
    """

    @inject(MaterialService)
    def __init__(
            self,
            parent: tk.Tk,
            save_callback: Callable[[Dict[str, Any]], None],
            fields: List[Tuple[str, str, bool, str]] = [],
            title: str = 'Add Entry'
    ):
        """
        Initialize the add dialog.

        Args:
            parent: Parent window
            save_callback: Function called with form data on save
            fields: List of field tuples (field_name, display_name, required, field_type)
            title: Dialog title

        Field Types:
        - 'string': Text entry
        - 'text': Multiline text entry
        - 'float': Numeric entry (floating-point)
        - 'int': Integer entry
        - 'boolean': Checkbox
        """
        try:
            # Use parent's width for consistent sizing
            parent_width = parent.winfo_width() or 500
            dialog_width = min(max(400, parent_width), 600)

            super().__init__(
                parent,
                title=title,
                size=(dialog_width, 500),
                modal=True
            )

            self._parent = parent
            self._save_callback = save_callback
            self._fields = fields
            self._entries: Dict[str, Union[tk.Entry, tk.Text, tk.BooleanVar, ttk.Checkbutton]] = {}

            # Override OK button with custom save method
            self.add_ok_cancel_buttons(
                ok_text='Save',
                ok_command=self._on_save
            )

            # Create dynamic UI
            self._create_ui()

        except Exception as e:
            logger.error(f"Error initializing AddDialog: {e}")
            messagebox.showerror("Initialization Error", str(e))
            self.destroy()

    def _create_ui(self) -> None:
        """
        Create dialog user interface with dynamic fields.
        """
        try:
            # Main frame for field entries
            main_frame = ttk.Frame(self.main_frame, padding='10 10 10 10')
            main_frame.pack(fill=tk.BOTH, expand=True)
            main_frame.columnconfigure(1, weight=1)

            # Dynamically create fields based on configuration
            for i, (field_name, display_name, required, field_type) in enumerate(self._fields):
                # Create label
                label = ttk.Label(main_frame, text=f'{display_name}:')
                label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)

                # Create appropriate input widget based on field type
                entry = self._create_field_entry(
                    main_frame,
                    field_type,
                    row=i,
                    required=required
                )
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)

                # Store reference to the entry
                self._entries[field_name] = entry

        except Exception as e:
            logger.error(f"Error creating dialog UI: {e}")
            messagebox.showerror("UI Creation Error", str(e))

    def _create_field_entry(
            self,
            parent: tk.Widget,
            field_type: str,
            row: int,
            required: bool = False
    ) -> Union[tk.Entry, tk.Text, tk.BooleanVar]:
        """
        Create an appropriate entry widget based on field type.

        Args:
            parent: Parent widget
            field_type: Type of field to create
            row: Grid row for validation styling
            required: Whether the field is required

        Returns:
            Appropriate entry widget
        """
        try:
            if field_type == 'string':
                entry = ttk.Entry(parent, width=40)
            elif field_type == 'text':
                entry = tk.Text(parent, height=4, width=40)
            elif field_type in ['float', 'int']:
                entry = ttk.Entry(parent, width=40)
            elif field_type == 'boolean':
                var = tk.BooleanVar()
                entry = ttk.Checkbutton(parent, variable=var)
            else:
                raise ValueError(f"Unsupported field type: {field_type}")

            # Add validation for required numeric fields
            if field_type in ['float', 'int']:
                entry.configure(validate='key')
                if field_type == 'float':
                    vcmd = (parent.register(self._validate_float), '%P')
                else:
                    vcmd = (parent.register(self._validate_int), '%P')
                entry.configure(validatecommand=vcmd)

            return entry

        except Exception as e:
            logger.error(f"Error creating field entry: {e}")
            messagebox.showerror("Field Creation Error", str(e))
            raise

    def _validate_float(self, value: str) -> bool:
        """
        Validate float input.

        Args:
            value: Input value to validate

        Returns:
            True if valid float, False otherwise
        """
        if value == "" or value == "-":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _validate_int(self, value: str) -> bool:
        """
        Validate integer input.

        Args:
            value: Input value to validate

        Returns:
            True if valid integer, False otherwise
        """
        if value == "" or value == "-":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _on_save(self) -> None:
        """
        Handle save action, validate and process form data.
        """
        try:
            # Collect and validate form data
            form_data: Dict[str, Any] = {}

            for field_name, _, required, field_type in self._fields:
                entry = self._entries[field_name]

                # Extract value based on field type
                if field_type == 'string':
                    value = entry.get()
                elif field_type == 'text':
                    value = entry.get('1.0', tk.END).strip()
                elif field_type == 'float':
                    try:
                        value = float(entry.get())
                    except ValueError:
                        messagebox.showerror(
                            'Invalid Input',
                            f'Invalid float value for {field_name}'
                        )
                        return
                elif field_type == 'int':
                    try:
                        value = int(entry.get())
                    except ValueError:
                        messagebox.showerror(
                            'Invalid Input',
                            f'Invalid integer value for {field_name}'
                        )
                        return
                elif field_type == 'boolean':
                    value = entry.get()

                # Validate required fields
                if required and not value:
                    messagebox.showerror(
                        'Missing Input',
                        f'{field_name} is required'
                    )
                    return

                form_data[field_name] = value

            # Generate ID if not provided
            if 'id' not in form_data:
                form_data['id'] = str(uuid.uuid4())

            # Call save callback
            try:
                self._save_callback(form_data)
                self.destroy()
            except Exception as e:
                logger.error(f"Save callback error: {e}")
                messagebox.showerror('Save Error', str(e))

        except Exception as e:
            logger.error(f"Unexpected error during save: {e}")
            messagebox.showerror('Unexpected Error', str(e))


# Optional: Add module-level testing if imported directly
if __name__ == '__main__':
    def dummy_save_callback(data: Dict[str, Any]) -> None:
        """
        Dummy save callback for testing dialog.

        Args:
            data: Collected form data
        """
        print("Saving data:", data)


    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Example field configurations
    test_fields = [
        ('name', 'Name', True, 'string'),
        ('description', 'Description', False, 'text'),
        ('quantity', 'Quantity', True, 'int'),
        ('price', 'Price', True, 'float'),
        ('active', 'Active', False, 'boolean')
    ]

    dialog = AddDialog(
        root,
        save_callback=dummy_save_callback,
        fields=test_fields,
        title='Add Test Item'
    )
    root.mainloop()