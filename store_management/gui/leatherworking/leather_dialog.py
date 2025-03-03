# gui/leatherworking/leather_dialog.py
"""
Dialog for adding or editing leather details in the leatherworking application.
"""
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional

# Import enums safely
from enum import Enum

class LeatherType(Enum):
    """Enum for leather types, mirroring database model"""
    FULL_GRAIN = "full_grain"
    TOP_GRAIN = "top_grain"
    CORRECTED_GRAIN = "corrected_grain"
    SPLIT = "split"
    NUBUCK = "nubuck"
    SUEDE = "suede"
    EXOTIC = "exotic"
    VEGETABLE_TANNED = "vegetable_tanned"
    CHROME_TANNED = "chrome_tanned"

class MaterialQualityGrade(Enum):
    """Enum for material quality grades, mirroring database model"""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    SECONDS = "seconds"
    SCRAP = "scrap"

class InventoryStatus(Enum):
    """Enum for inventory status, mirroring database model"""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    ON_ORDER = "on_order"


class LeatherDetailsDialog:
    """Dialog for capturing leather material details."""

    def __init__(self, parent: tk.Widget, title: str, leather_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the leather details dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            leather_data: Optional existing leather data for editing
        """
        self.parent = parent
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create a frame to hold all content
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create form fields
        row = 0

        # Basic Info
        ttk.Label(main_frame, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        ttk.Label(main_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.description_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.description_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E,
                                                                                pady=2)
        row += 1

        # Leather Type
        ttk.Label(main_frame, text="Leather Type:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.leather_type_var = tk.StringVar()
        leather_types = [lt.value for lt in LeatherType]
        ttk.Combobox(main_frame, textvariable=self.leather_type_var, values=leather_types, state="readonly").grid(
            row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Quality Grade
        ttk.Label(main_frame, text="Quality Grade:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.grade_var = tk.StringVar()
        grades = [g.value for g in MaterialQualityGrade]
        ttk.Combobox(main_frame, textvariable=self.grade_var, values=grades, state="readonly").grid(
            row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Color
        ttk.Label(main_frame, text="Color:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.color_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.color_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Thickness
        ttk.Label(main_frame, text="Thickness (mm):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.thickness_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.thickness_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E,
                                                                              pady=2)
        row += 1

        # Size
        ttk.Label(main_frame, text="Size (sq ft):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.size_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.size_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Unit Price
        ttk.Label(main_frame, text="Unit Price ($):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.price_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.price_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Quantity
        ttk.Label(main_frame, text="Quantity:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.quantity_var = tk.StringVar(value="1")
        ttk.Entry(main_frame, textvariable=self.quantity_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E,
                                                                             pady=2)
        row += 1

        # Status
        ttk.Label(main_frame, text="Status:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.status_var = tk.StringVar()
        status_values = [s.value for s in InventoryStatus]
        ttk.Combobox(main_frame, textvariable=self.status_var, values=status_values, state="readonly").grid(
            row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Location
        ttk.Label(main_frame, text="Storage Location:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.location_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.location_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E,
                                                                             pady=2)
        row += 1

        # Notes
        ttk.Label(main_frame, text="Notes:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.notes_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.notes_var, width=30).grid(row=row, column=1, sticky=tk.W + tk.E, pady=2)
        row += 1

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky=tk.E, pady=(10, 0))

        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=self._on_save).pack(side=tk.RIGHT, padx=5)

        # If editing, populate with existing data
        if leather_data:
            self._populate_form(leather_data)
        else:
            # Set defaults for new item
            self.status_var.set(InventoryStatus.IN_STOCK.value)

        # Set reasonable size for dialog
        self.dialog.update_idletasks()
        width = min(400, parent.winfo_width() - 50)
        height = min(500, parent.winfo_height() - 50)
        x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        # Wait for dialog to close
        self.dialog.wait_window()

    def _populate_form(self, leather_data: Dict[str, Any]):
        """Populate form fields with existing leather data.

        Args:
            leather_data: Dictionary containing leather details
        """
        # Basic Info
        self.name_var.set(leather_data.get('name', ''))
        self.description_var.set(leather_data.get('description', ''))

        # Handle leather type
        leather_type = leather_data.get('leather_type') or leather_data.get('type')
        if isinstance(leather_type, str):
            # Attempt to find a matching enum value
            try:
                leather_type = next(lt.value for lt in LeatherType if lt.value == leather_type)
                self.leather_type_var.set(leather_type)
            except StopIteration:
                pass

        # Handle grade
        grade = leather_data.get('grade') or leather_data.get('quality_grade')
        if isinstance(grade, str):
            # Attempt to find a matching enum value
            try:
                grade = next(g.value for g in MaterialQualityGrade if g.value == grade)
                self.grade_var.set(grade)
            except StopIteration:
                pass

        self.color_var.set(leather_data.get('color', ''))

        # Handle thickness (could be either 'thickness' or 'thickness_mm')
        thickness = leather_data.get('thickness_mm') or leather_data.get('thickness', '')
        self.thickness_var.set(str(thickness) if thickness else '')

        self.size_var.set(str(leather_data.get('size_sqft', '')) if leather_data.get('size_sqft') is not None else '')

        # Handle price
        price = leather_data.get('unit_price', '') or leather_data.get('cost_per_sqft', '')
        self.price_var.set(str(price) if price else '')

        self.quantity_var.set(str(leather_data.get('quantity', 1)))

        # Handle status
        status = leather_data.get('status', InventoryStatus.IN_STOCK.value)
        if isinstance(status, str):
            try:
                status = next(s.value for s in InventoryStatus if s.value == status)
                self.status_var.set(status)
            except StopIteration:
                # Fallback to default
                self.status_var.set(InventoryStatus.IN_STOCK.value)

            self.location_var.set(leather_data.get('location', ''))
            self.notes_var.set(leather_data.get('notes', ''))

    def _validate_form(self) -> bool:
        """Validate form inputs.

        Returns:
            bool: True if validation passes, False otherwise
        """
        # Required fields
        if not self.name_var.get().strip():
            messagebox.showerror("Validation Error", "Name is required", parent=self.dialog)
            return False

        if not self.leather_type_var.get():
            messagebox.showerror("Validation Error", "Leather Type is required", parent=self.dialog)
            return False

        if not self.grade_var.get():
            messagebox.showerror("Validation Error", "Quality Grade is required", parent=self.dialog)
            return False

        # Numeric field validation
        try:
            if self.thickness_var.get().strip():
                thickness = float(self.thickness_var.get())
                if thickness <= 0:
                    messagebox.showerror("Validation Error", "Thickness must be a positive number",
                                         parent=self.dialog)
                    return False
        except ValueError:
            messagebox.showerror("Validation Error", "Thickness must be a valid number", parent=self.dialog)
            return False

        try:
            if self.size_var.get().strip():
                size = float(self.size_var.get())
                if size <= 0:
                    messagebox.showerror("Validation Error", "Size must be a positive number", parent=self.dialog)
                    return False
        except ValueError:
            messagebox.showerror("Validation Error", "Size must be a valid number", parent=self.dialog)
            return False

        try:
            if self.price_var.get().strip():
                price = float(self.price_var.get())
                if price < 0:
                    messagebox.showerror("Validation Error", "Price cannot be negative", parent=self.dialog)
                    return False
        except ValueError:
            messagebox.showerror("Validation Error", "Price must be a valid number", parent=self.dialog)
            return False

        try:
            if self.quantity_var.get().strip():
                quantity = int(self.quantity_var.get())
                if quantity < 0:
                    messagebox.showerror("Validation Error", "Quantity cannot be negative", parent=self.dialog)
                    return False
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a valid integer", parent=self.dialog)
            return False

        return True

    def _on_save(self):
        """Handle save button click."""
        if not self._validate_form():
            return

        # Create result dictionary
        self.result = {
            'name': self.name_var.get().strip(),
            'description': self.description_var.get().strip(),
            'type': 'leather',  # Set material type for compatibility with IMaterialService
            'leather_type': self.leather_type_var.get(),
            'quality_grade': self.grade_var.get(),
            'color': self.color_var.get().strip(),
            'notes': self.notes_var.get().strip(),
            'location': self.location_var.get().strip(),
            'status': self.status_var.get()
        }

        # Add numeric fields if they have values
        if self.thickness_var.get().strip():
            self.result['thickness'] = float(self.thickness_var.get())

        if self.size_var.get().strip():
            self.result['size_sqft'] = float(self.size_var.get())

        if self.price_var.get().strip():
            price = float(self.price_var.get())
            self.result['unit_price'] = price
            self.result['cost_per_sqft'] = price  # Set both for compatibility

        if self.quantity_var.get().strip():
            self.result['quantity'] = int(self.quantity_var.get())

        # Close dialog
        self.dialog.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.dialog.destroy()

def main():
    """Standalone testing of the LeatherDetailsDialog"""
    import tkinter as tk

    root = tk.Tk()
    root.title("Leather Details Test")

    def open_dialog():
        dialog = LeatherDetailsDialog(root, "Add Leather Material")
        if dialog.result:
            print("Dialog Result:", dialog.result)

    tk.Button(root, text="Open Dialog", command=open_dialog).pack(padx=20, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()