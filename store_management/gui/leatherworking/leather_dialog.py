# gui/leatherworking/leather_dialog.py
"""
Dialog for adding and editing leather material details.
"""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import logging
from typing import Any, Dict, Optional

from services.interfaces.material_service import MaterialType

# Configure logger
logger = logging.getLogger(__name__)


class LeatherDetailsDialog(tk.Toplevel):
    """Dialog for adding or editing leather material details."""

    def __init__(self, parent: tk.Widget, title: str, leather_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the leather details dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            leather_data: Optional existing leather data for editing
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Store references
        self.parent = parent
        self.leather_data = leather_data or {}
        self.result = None

        # Create UI components
        self._create_widgets()

        # Fill in existing data if editing
        if leather_data:
            self._populate_fields()

        # Center the dialog
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Set focus
        self.name_entry.focus_set()

        logger.debug(f"Opened {title} dialog for leather: {leather_data.get('id', 'New')}")

    def _populate_fields(self) -> None:
        """Populate form fields with existing leather data."""
        if not self.leather_data:
            return

        # Set form values from leather data
        self.name_var.set(self.leather_data.get('name', ''))
        self.type_var.set(self.leather_data.get('leather_type', ''))
        self.color_var.set(self.leather_data.get('color', ''))
        self.thickness_var.set(str(self.leather_data.get('thickness', '')))
        self.size_var.set(str(self.leather_data.get('size', '')))
        self.quantity_var.set(str(self.leather_data.get('quantity', 0)))
        self.cost_var.set(str(self.leather_data.get('cost_per_unit', 0)))
        self.supplier_var.set(self.leather_data.get('supplier_code', ''))
        self.grade_var.set(self.leather_data.get('quality_grade', ''))

        # Set text widgets
        desc = self.leather_data.get('description', '')
        self.description_text.delete('1.0', tk.END)
        if desc:
            self.description_text.insert('1.0', desc)

        notes = self.leather_data.get('notes', '')
        self.notes_text.delete('1.0', tk.END)
        if notes:
            self.notes_text.insert('1.0', notes)

        # Set image path if exists
        self.image_path_var.set(self.leather_data.get('image_path', 'No image selected'))

    def _select_image(self) -> None:
        """Open file dialog to select an image."""
        file_types = [
            ('Image files', '*.jpg;*.jpeg;*.png;*.gif'),
            ('All files', '*.*')
        ]

        file_path = filedialog.askopenfilename(
            title="Select Leather Image",
            filetypes=file_types
        )

        if file_path:
            self.image_path_var.set(file_path)

    def _save_leather(self) -> None:
        """Save leather information."""
        # Validate required fields
        if not self.name_var.get().strip():
            messagebox.showerror("Validation Error", "Name is required")
            self.name_entry.focus_set()
            return

        # Collect data from form
        leather_data = {
            'name': self.name_var.get().strip(),
            'material_type': MaterialType.LEATHER.value,
            'leather_type': self.type_var.get(),
            'color': self.color_var.get().strip(),
            'description': self.description_text.get('1.0', tk.END).strip(),
            'notes': self.notes_text.get('1.0', tk.END).strip(),
            'quality_grade': self.grade_var.get(),
            'supplier_code': self.supplier_var.get().strip(),
            'image_path': self.image_path_var.get()
        }

        # Convert numeric fields
        try:
            if self.thickness_var.get().strip():
                leather_data['thickness'] = float(self.thickness_var.get())

            if self.size_var.get().strip():
                leather_data['size'] = float(self.size_var.get())

            if self.quantity_var.get().strip():
                leather_data['quantity'] = float(self.quantity_var.get())

            if self.cost_var.get().strip():
                leather_data['cost_per_unit'] = float(self.cost_var.get())
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid numeric value")
            return

        # Add ID if editing
        if self.leather_data and 'id' in self.leather_data:
            leather_data['id'] = self.leather_data['id']

        # Save the data
        try:
            # Pass data back to parent
            self.result = leather_data

            # Get material service from parent
            if hasattr(self.parent, 'material_service') and self.parent.material_service:
                material_service = self.parent.material_service

                if 'id' in leather_data:
                    # Update existing
                    material_service.update_material(leather_data['id'], leather_data)
                    logger.info(f"Updated leather item: {leather_data['id']} - {leather_data['name']}")
                else:
                    # Create new
                    result = material_service.create_material(leather_data)
                    logger.info(f"Created new leather item: {result.get('id')} - {result.get('name')}")

                messagebox.showinfo("Success", "Leather information saved successfully")
                self.destroy()
            else:
                logger.warning("Material service not available in parent")
                messagebox.showinfo("Demo Mode", "Changes would be saved (Demo Mode)")
                self.destroy()

        except Exception as e:
            logger.error(f"Error saving leather information: {str(e)}")
            messagebox.showerror("Save Error", f"Could not save leather information: {str(e)}")

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create form fields
        row = 0

        # Name field
        ttk.Label(main_frame, text="Name:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=row, column=1, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5)
        row += 1

        # Type field
        ttk.Label(main_frame, text="Leather Type:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar()
        leather_types = ["FULL_GRAIN", "TOP_GRAIN", "CORRECTED_GRAIN", "SPLIT", "NUBUCK", "SUEDE", "EXOTIC", "OTHER"]
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=leather_types, width=15)
        self.type_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Color field
        ttk.Label(main_frame, text="Color:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.color_var = tk.StringVar()
        self.color_entry = ttk.Entry(main_frame, textvariable=self.color_var, width=15)
        self.color_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Thickness field
        ttk.Label(main_frame, text="Thickness (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.thickness_var = tk.StringVar()
        self.thickness_entry = ttk.Entry(main_frame, textvariable=self.thickness_var, width=10)
        self.thickness_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Size field
        ttk.Label(main_frame, text="Size (sq.ft):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.size_var = tk.StringVar()
        self.size_entry = ttk.Entry(main_frame, textvariable=self.size_var, width=10)
        self.size_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Quantity field
        ttk.Label(main_frame, text="Quantity:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.quantity_var = tk.StringVar()
        self.quantity_entry = ttk.Entry(main_frame, textvariable=self.quantity_var, width=10)
        self.quantity_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Cost field
        ttk.Label(main_frame, text="Cost (per sq.ft):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.cost_var = tk.StringVar()
        self.cost_entry = ttk.Entry(main_frame, textvariable=self.cost_var, width=10)
        self.cost_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Supplier field
        ttk.Label(main_frame, text="Supplier:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.supplier_var = tk.StringVar()
        self.supplier_entry = ttk.Entry(main_frame, textvariable=self.supplier_var, width=20)
        self.supplier_entry.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Quality grade field
        ttk.Label(main_frame, text="Quality Grade:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.grade_var = tk.StringVar()
        grade_types = ["PREMIUM", "STANDARD", "ECONOMY", "SECONDS", "SCRAP"]
        self.grade_combo = ttk.Combobox(main_frame, textvariable=self.grade_var, values=grade_types, width=15)
        self.grade_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Description field
        ttk.Label(main_frame, text="Description:").grid(row=row, column=0, sticky=tk.W + tk.N, padx=5, pady=5)
        self.description_var = tk.StringVar()
        self.description_text = tk.Text(main_frame, width=30, height=5)
        self.description_text.grid(row=row, column=1, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5)
        row += 1

        # Notes field
        ttk.Label(main_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W + tk.N, padx=5, pady=5)
        self.notes_text = tk.Text(main_frame, width=30, height=3)
        self.notes_text.grid(row=row, column=1, columnspan=2, sticky=tk.W + tk.E, padx=5, pady=5)
        row += 1

        # Image placeholder (to be implemented)
        ttk.Label(main_frame, text="Image:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Button(main_frame, text="Select Image", command=self._select_image).grid(row=row, column=1, sticky=tk.W,
                                                                                     padx=5, pady=5)
        self.image_path_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.image_path_var).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        row += 1

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=15)

        ttk.Button(button_frame, text="Save", command=self._save_leather, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy, width=10).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)