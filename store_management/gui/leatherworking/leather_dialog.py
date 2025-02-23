# Path: gui/leatherworking/leather_dialog.py
"""
Leather Details Dialog for Leatherworking Project

Provides a comprehensive dialog for adding and editing leather items
with validation and detailed input fields.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable


class LeatherDetailsDialog(tk.Toplevel):
    """
    A dialog for capturing and editing detailed leather information.

    Supports:
    - Adding new leather items
    - Editing existing leather items
    - Comprehensive input validation
    """

    def __init__(
        self,
        parent,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        initial_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Leather Details Dialog.

        Args:
            parent (tk.Widget): Parent widget
            callback (Optional[Callable]): Function to call with leather data
            initial_data (Optional[Dict]): Existing leather data for editing
        """
        super().__init__(parent)
        self.title("Leather Details")
        self.geometry("500x600")
        self.resizable(False, False)

        # Callback and initial data
        self.callback = callback
        self.initial_data = initial_data or {}

        # Validation variables
        self.validation_errors = []

        # Setup UI
        self._create_main_frame()
        self._create_input_fields()
        self._create_buttons()

        # Load initial data if editing
        if initial_data:
            self._load_initial_data()

    def _create_main_frame(self):
        """
        Create the main frame for the dialog.
        """
        self.main_frame = ttk.Frame(self, padding="20 10 20 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(1, weight=1)

    def _create_input_fields(self):
        """
        Create comprehensive input fields for leather details.
        """
        # Leather Identification
        ttk.Label(self.main_frame, text="Leather ID:").grid(row=0, column=0, sticky="w", pady=5)
        self.id_var = tk.StringVar(value=self.initial_data.get("id", ""))
        self.id_entry = ttk.Entry(self.main_frame, textvariable=self.id_var, state="readonly")
        self.id_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Leather Type
        ttk.Label(self.main_frame, text="Leather Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.type_var = tk.StringVar(value=self.initial_data.get("type", ""))
        leather_types = ["Full Grain", "Top Grain", "Genuine Leather", "Suede", "Nubuck", "Other"]
        self.type_combo = ttk.Combobox(
            self.main_frame, textvariable=self.type_var, values=leather_types
        )
        self.type_combo.grid(row=1, column=1, sticky="ew", pady=5)

        # Color
        ttk.Label(self.main_frame, text="Color:").grid(row=2, column=0, sticky="w", pady=5)
        self.color_var = tk.StringVar(value=self.initial_data.get("color", ""))
        self.color_entry = ttk.Entry(self.main_frame, textvariable=self.color_var)
        self.color_entry.grid(row=2, column=1, sticky="ew", pady=5)

        # Area
        ttk.Label(self.main_frame, text="Area (sq units):").grid(row=3, column=0, sticky="w", pady=5)
        self.area_var = tk.StringVar(value=str(self.initial_data.get("area", "")))
        self.area_entry = ttk.Entry(self.main_frame, textvariable=self.area_var)
        self.area_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # Quality
        ttk.Label(self.main_frame, text="Quality Grade:").grid(row=4, column=0, sticky="w", pady=5)
        self.quality_var = tk.StringVar(value=self.initial_data.get("quality", ""))
        quality_grades = ["Premium", "High", "Standard", "Low", "Reject"]
        self.quality_combo = ttk.Combobox(
            self.main_frame, textvariable=self.quality_var, values=quality_grades
        )
        self.quality_combo.grid(row=4, column=1, sticky="ew", pady=5)

        # Status
        ttk.Label(self.main_frame, text="Status:").grid(row=5, column=0, sticky="w", pady=5)
        self.status_var = tk.StringVar(value=self.initial_data.get("status", "Available"))
        status_options = ["Available", "Reserved", "In Use", "Damaged"]
        self.status_combo = ttk.Combobox(
            self.main_frame, textvariable=self.status_var, values=status_options
        )
        self.status_combo.grid(row=5, column=1, sticky="ew", pady=5)

        # Origin/Supplier
        ttk.Label(self.main_frame, text="Supplier:").grid(row=6, column=0, sticky="w", pady=5)
        self.supplier_var = tk.StringVar(value=self.initial_data.get("supplier", ""))
        self.supplier_entry = ttk.Entry(self.main_frame, textvariable=self.supplier_var)
        self.supplier_entry.grid(row=6, column=1, sticky="ew", pady=5)

        # Additional Notes
        ttk.Label(self.main_frame, text="Notes:").grid(row=7, column=0, sticky="nw", pady=5)
        self.notes_text = tk.Text(self.main_frame, height=4, width=40)
        self.notes_text.grid(row=7, column=1, sticky="ew", pady=5)
        self.notes_text.insert(tk.END, self.initial_data.get("notes", ""))

    def _create_buttons(self):
        """
        Create action buttons for the dialog.
        """
        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10)

        # Save button
        save_btn = ttk.Button(button_frame, text="Save", command=self._on_save)
        save_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def _load_initial_data(self):
        """
        Populate fields with existing leather data when editing.
        """
        # If editing an existing item, potentially disable ID field
        if self.initial_data.get("id"):
            self.id_entry.config(state="normal")

    def _validate_input(self) -> bool:
        """
        Validate input fields.

        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        # Reset validation errors
        self.validation_errors = []

        # Validate leather type
        if not self.type_var.get():
            self.validation_errors.append("Leather Type is required")

        # Validate area (must be a positive number)
        try:
            area = float(self.area_var.get())
            if area <= 0:
                self.validation_errors.append("Area must be a positive number")
        except ValueError:
            self.validation_errors.append("Invalid area. Please enter a number")

        # Validate color
        if not self.color_var.get():
            self.validation_errors.append("Color is required")

        # Validate quality
        if not self.quality_var.get():
            self.validation_errors.append("Quality Grade is required")

        # Display validation errors if any
        if self.validation_errors:
            error_message = "Please correct the following errors:\n" + "\n".join(
                f"- {error}" for error in self.validation_errors
            )
            messagebox.showerror("Validation Error", error_message)
            return False

        return True

    def _on_save(self):
        """
        Handle save action, validate and return leather data.
        """
        # Validate inputs
        if not self._validate_input():
            return

        # Prepare leather data
        leather_data = {
            "id": self.id_var.get() or f"LTH-{int(tk.datetime.now().timestamp())}",
            "type": self.type_var.get(),
            "color": self.color_var.get(),
            "area": self.area_var.get(),
            "quality": self.quality_var.get(),
            "status": self.status_var.get(),
            "supplier": self.supplier_var.get(),
            "notes": self.notes_text.get("1.0", tk.END).strip(),
        }

        # Call callback if provided
        if self.callback:
            self.callback(leather_data)

        # Close dialog
        self.destroy()


def main():
    """
    Standalone test for LeatherDetailsDialog.
    """
    root = tk.Tk()
    root.title("Leather Details Test")

    def print_leather_data(data):
        """
        Print leather data for testing.

        Args:
            data (dict): Leather item details
        """
        print("Leather Data:")
        for key, value in data.items():
            print(f"{key}: {value}")

    # Button to open dialog for new leather
    def open_new_leather_dialog():
        """Open dialog for adding new leather."""
        LeatherDetailsDialog(root, callback=print_leather_data)

    # Button to open dialog for editing existing leather
    def open_edit_leather_dialog():
        """Open dialog for editing existing leather."""
        existing_leather = {
            "id": "LTH-001",
            "type": "Full Grain",
            "color": "Brown",
            "area": "5.5",
            "quality": "Premium",
            "status": "Available",
            "supplier": "Local Tannery",
            "notes": "High-quality leather for premium products",
        }
        LeatherDetailsDialog(root, callback=print_leather_data, initial_data=existing_leather)

    # Create test buttons
    new_btn = ttk.Button(root, text="Add New Leather", command=open_new_leather_dialog)
    new_btn.pack(pady=10)

    edit_btn = ttk.Button(root, text="Edit Existing Leather", command=open_edit_leather_dialog)
    edit_btn.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
