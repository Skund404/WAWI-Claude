import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable, Optional
import uuid


class AddDialog(tk.Toplevel):
    def __init__(self, parent, save_callback: Callable[[Dict], bool], fields: list):
        """
        Initialize add dialog

        Args:
            parent: Parent window
            save_callback: Function to call with form data on save
            fields: List of tuples (field_name, display_name, required, field_type)
                   field_type can be 'string', 'float', or 'text'
        """
        super().__init__(parent)
        self.title("Add New Item")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()

        self.save_callback = save_callback
        self.fields = fields
        self.entries = {}

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI components"""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entry fields
        for i, (field_name, display_name, required, field_type) in enumerate(self.fields):
            # Label
            ttk.Label(main_frame, text=f"{display_name}:").grid(
                row=i, column=0, sticky='w', padx=5, pady=2
            )

            # Entry or Text widget based on field type
            if field_type == 'text':
                entry = tk.Text(main_frame, width=40, height=4)
                entry.grid(row=i, column=1, sticky='ew', padx=5, pady=2)
            else:
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=i, column=1, sticky='ew', padx=5, pady=2)

            self.entries[field_name] = entry

            # Required field indicator
            if required:
                ttk.Label(main_frame, text="*", foreground="red").grid(
                    row=i, column=2, sticky='w'
                )

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(self.fields), column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Required fields note
        ttk.Label(
            main_frame,
            text="* Required fields",
            foreground="red"
        ).grid(row=len(self.fields) + 1, column=0, columnspan=3, sticky='w', pady=(5, 0))

        # Set focus to first entry
        first_entry = next(iter(self.entries.values()))
        first_entry.focus_set()

    def get_field_values(self) -> Dict:
        """Get all field values from entries"""
        values = {}
        for field_name, display_name, _, field_type in self.fields:
            widget = self.entries[field_name]
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", tk.END).strip()
            else:
                value = widget.get().strip()

            # Convert types if needed
            if field_type == 'float' and value:
                try:
                    value = float(value)
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        f"{display_name} must be a valid number"
                    )
                    return None

            values[field_name] = value

        return values

    def validate_required_fields(self) -> bool:
        """Validate that all required fields have values"""
        required_fields = [(name, display) for name, display, req, _ in self.fields if req]

        for field_name, display_name in required_fields:
            widget = self.entries[field_name]
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", tk.END).strip()
            else:
                value = widget.get().strip()

            if not value:
                messagebox.showerror(
                    "Error",
                    f"{display_name} is required"
                )
                widget.focus_set()
                return False
        return True

    def save(self):
        """Validate and save the form data"""
        if not self.validate_required_fields():
            return

        values = self.get_field_values()
        if values is None:  # Validation failed
            return

        try:
            if self.save_callback(values):
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save item")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")