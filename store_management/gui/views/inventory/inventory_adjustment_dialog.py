# gui/views/inventory/inventory_adjustment_dialog.py
"""
Inventory Adjustment Dialog.
Provides a dialog for making inventory adjustments (add/remove stock).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional

from database.models.enums import InventoryStatus, StorageLocationType, TransactionType
from gui.base.base_dialog import BaseDialog
from gui.utils.service_access import get_service


class InventoryAdjustmentDialog(BaseDialog):
    """Dialog for adjusting inventory quantities."""

    def __init__(
            self,
            parent,
            inventory_id: Optional[int] = None,
            item_id: Optional[int] = None,
            item_type: Optional[str] = None
    ):
        """
        Initialize the inventory adjustment dialog.

        Args:
            parent: The parent widget
            inventory_id: Optional ID of existing inventory record
            item_id: Optional ID of item (if creating new inventory)
            item_type: Optional type of item (if creating new inventory)
        """
        title = "Inventory Adjustment"
        super().__init__(parent, title=title, width=500, height=500)

        self.inventory_id = inventory_id
        self.item_id = item_id
        self.item_type = item_type
        self.inventory_data = None
        self.item_data = None

    def create_layout(self):
        """Create the dialog layout."""
        # Main content frame
        content_frame = ttk.Frame(self.dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Load data
        self.load_data()

        # Create the inventory information section
        self.create_inventory_info(content_frame)

        # Create the adjustment section
        self.create_adjustment_section(content_frame)

        # Create button frame
        button_frame = ttk.Frame(self.dialog, padding="10 0 10 10")
        button_frame.pack(fill=tk.X)

        # Create buttons
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Save",
            command=self.on_save
        ).pack(side=tk.RIGHT, padx=5)

    def load_data(self):
        """Load inventory and item data."""
        try:
            service = get_service("IInventoryService")

            if self.inventory_id:
                # Load existing inventory
                self.inventory_data = service.get_by_id(self.inventory_id)
                if not self.inventory_data:
                    raise ValueError(f"Could not find inventory with ID {self.inventory_id}")

                # Extract item information
                self.item_id = getattr(self.inventory_data, "item_id", None)
                self.item_type = getattr(self.inventory_data, "item_type", None)

            if self.item_id and self.item_type:
                # Load item data
                if self.item_type == "material":
                    item_service = get_service("IMaterialService")
                    self.item_data = item_service.get_by_id(self.item_id)
                elif self.item_type == "product":
                    item_service = get_service("IProductService")
                    self.item_data = item_service.get_by_id(self.item_id)
                elif self.item_type == "tool":
                    item_service = get_service("IToolService")
                    self.item_data = item_service.get_by_id(self.item_id)

                if not self.item_data:
                    raise ValueError(f"Could not find {self.item_type} with ID {self.item_id}")

                # If no inventory record yet, check if one exists for this item
                if not self.inventory_id:
                    inventory = service.get_by_item(self.item_id, self.item_type)
                    if inventory:
                        self.inventory_id = getattr(inventory, "id", None)
                        self.inventory_data = inventory

        except Exception as e:
            messagebox.showerror("Error", f"Error loading data: {str(e)}")
            self.close()

    def create_inventory_info(self, parent):
        """
        Create the inventory information section.

        Args:
            parent: The parent widget
        """
        # Create frame
        info_frame = ttk.LabelFrame(parent, text="Item Information", padding=10)
        info_frame.pack(fill=tk.X, pady=10)

        # Create grid layout
        grid = ttk.Frame(info_frame)
        grid.pack(fill=tk.X)

        # Display item information
        item_name = ""
        if self.item_data:
            if hasattr(self.item_data, "name"):
                item_name = self.item_data.name
            elif isinstance(self.item_data, dict) and "name" in self.item_data:
                item_name = self.item_data["name"]

        ttk.Label(grid, text="Item:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(grid, text=item_name).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(grid, text="Type:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(grid, text=self.item_type.capitalize() if self.item_type else "").grid(row=0, column=3, sticky="w",
                                                                                         padx=5, pady=2)

        # Display current inventory information if available
        if self.inventory_data:
            # Current quantity
            ttk.Label(grid, text="Current Quantity:").grid(row=1, column=0, sticky="w", padx=5, pady=2)

            current_qty = getattr(self.inventory_data, "quantity", 0)
            if isinstance(self.inventory_data, dict):
                current_qty = self.inventory_data.get("quantity", 0)

            ttk.Label(grid, text=str(current_qty)).grid(row=1, column=1, sticky="w", padx=5, pady=2)

            # Current status
            ttk.Label(grid, text="Current Status:").grid(row=1, column=2, sticky="w", padx=5, pady=2)

            current_status = getattr(self.inventory_data, "status", "")
            if isinstance(self.inventory_data, dict):
                current_status = self.inventory_data.get("status", "")

            ttk.Label(grid, text=current_status).grid(row=1, column=3, sticky="w", padx=5, pady=2)

            # Current location
            ttk.Label(grid, text="Current Location:").grid(row=2, column=0, sticky="w", padx=5, pady=2)

            current_location = getattr(self.inventory_data, "storage_location", "")
            if isinstance(self.inventory_data, dict):
                current_location = self.inventory_data.get("storage_location", "")

            ttk.Label(grid, text=current_location).grid(row=2, column=1, sticky="w", padx=5, pady=2)

            # Last updated
            ttk.Label(grid, text="Last Updated:").grid(row=2, column=2, sticky="w", padx=5, pady=2)

            last_updated = getattr(self.inventory_data, "last_updated", "")
            if isinstance(self.inventory_data, dict):
                last_updated = self.inventory_data.get("last_updated", "")

            ttk.Label(grid, text=str(last_updated)).grid(row=2, column=3, sticky="w", padx=5, pady=2)

    def create_adjustment_section(self, parent):
        """
        Create the adjustment section.

        Args:
            parent: The parent widget
        """
        # Create frame
        adjustment_frame = ttk.LabelFrame(parent, text="Adjustment Details", padding=10)
        adjustment_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Adjustment type section
        type_frame = ttk.Frame(adjustment_frame)
        type_frame.pack(fill=tk.X, pady=10)

        ttk.Label(type_frame, text="Adjustment Type:").pack(side=tk.LEFT, padx=5)

        self.transaction_type_var = tk.StringVar(value=TransactionType.ADJUSTMENT.value)
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.transaction_type_var,
            values=[
                TransactionType.PURCHASE.value,
                TransactionType.USAGE.value,
                TransactionType.ADJUSTMENT.value,
                TransactionType.RETURN.value,
                TransactionType.WASTE.value,
                TransactionType.TRANSFER.value
            ],
            state="readonly",
            width=15
        )
        type_combo.pack(side=tk.LEFT, padx=5)

        # Quantity section
        qty_frame = ttk.Frame(adjustment_frame)
        qty_frame.pack(fill=tk.X, pady=10)

        ttk.Label(qty_frame, text="Quantity:").pack(side=tk.LEFT, padx=5)

        self.quantity_var = tk.DoubleVar(value=0)
        qty_spinner = ttk.Spinbox(
            qty_frame,
            from_=-10000,
            to=10000,
            increment=1,
            textvariable=self.quantity_var,
            width=10
        )
        qty_spinner.pack(side=tk.LEFT, padx=5)

        # Status section
        status_frame = ttk.Frame(adjustment_frame)
        status_frame.pack(fill=tk.X, pady=10)

        ttk.Label(status_frame, text="New Status:").pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar()
        if self.inventory_data:
            current_status = getattr(self.inventory_data, "status", InventoryStatus.IN_STOCK.value)
            if isinstance(self.inventory_data, dict):
                current_status = self.inventory_data.get("status", InventoryStatus.IN_STOCK.value)
            self.status_var.set(current_status)
        else:
            self.status_var.set(InventoryStatus.IN_STOCK.value)

        status_combo = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=[e.value for e in InventoryStatus],
            state="readonly",
            width=15
        )
        status_combo.pack(side=tk.LEFT, padx=5)

        # Location section
        location_frame = ttk.Frame(adjustment_frame)
        location_frame.pack(fill=tk.X, pady=10)

        ttk.Label(location_frame, text="Storage Location:").pack(side=tk.LEFT, padx=5)

        self.location_var = tk.StringVar()
        if self.inventory_data:
            current_location = getattr(self.inventory_data, "storage_location", "")
            if isinstance(self.inventory_data, dict):
                current_location = self.inventory_data.get("storage_location", "")
            self.location_var.set(current_location)

        # Create combobox with existing locations
        try:
            service = get_service("IInventoryService")
            locations = service.get_storage_locations()
            location_values = [loc.get("location", "") for loc in locations]

            location_combo = ttk.Combobox(
                location_frame,
                textvariable=self.location_var,
                values=location_values,
                width=30
            )
            location_combo.pack(side=tk.LEFT, padx=5)

        except Exception:
            # Fallback to plain entry if location service fails
            location_entry = ttk.Entry(
                location_frame,
                textvariable=self.location_var,
                width=30
            )
            location_entry.pack(side=tk.LEFT, padx=5)

        # Add button to create new location
        new_location_btn = ttk.Button(
            location_frame,
            text="New...",
            command=self.create_new_location,
            width=5
        )
        new_location_btn.pack(side=tk.LEFT, padx=5)

        # Reference section
        reference_frame = ttk.Frame(adjustment_frame)
        reference_frame.pack(fill=tk.X, pady=10)

        ttk.Label(reference_frame, text="Reference:").pack(side=tk.LEFT, padx=5)

        self.reference_var = tk.StringVar()
        reference_entry = ttk.Entry(
            reference_frame,
            textvariable=self.reference_var,
            width=30
        )
        reference_entry.pack(side=tk.LEFT, padx=5)

        # Notes section
        notes_frame = ttk.Frame(adjustment_frame)
        notes_frame.pack(fill=tk.X, pady=10)

        ttk.Label(notes_frame, text="Notes:").pack(anchor="w", padx=5)

        self.notes_text = tk.Text(notes_frame, height=4, width=40)
        self.notes_text.pack(fill=tk.X, padx=5, pady=5)

    def create_new_location(self):
        """Open dialog to create a new storage location."""
        # Create dialog
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Storage Location")
        dialog.geometry("400x250")
        dialog.transient(self.dialog)
        dialog.grab_set()

        # Create content frame
        content = ttk.Frame(dialog, padding=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Create form
        ttk.Label(content, text="Location Type:").pack(anchor="w", pady=(0, 5))

        type_var = tk.StringVar()
        type_combo = ttk.Combobox(
            content,
            textvariable=type_var,
            values=[e.value for e in StorageLocationType],
            state="readonly",
            width=30
        )
        type_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(content, text="Location Identifier:").pack(anchor="w", pady=(0, 5))

        identifier_var = tk.StringVar()
        identifier_entry = ttk.Entry(content, textvariable=identifier_var, width=30)
        identifier_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(content, text="Description:").pack(anchor="w", pady=(0, 5))

        description_var = tk.StringVar()
        description_entry = ttk.Entry(content, textvariable=description_var, width=30)
        description_entry.pack(fill=tk.X, pady=(0, 10))

        # Create buttons
        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        def on_save():
            # Validate input
            location_type = type_var.get()
            identifier = identifier_var.get()

            if not location_type:
                messagebox.showerror("Error", "Please select a location type")
                return

            if not identifier:
                messagebox.showerror("Error", "Please enter a location identifier")
                return

            # Format the location string
            location = f"{location_type}:{identifier}"

            try:
                # Add the location
                service = get_service("IInventoryService")
                result = service.add_storage_location(
                    location=location,
                    description=description_var.get()
                )

                if result:
                    # Update the location variable
                    self.location_var.set(location)

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    messagebox.showinfo("Success", f"Storage location {location} added successfully")
                else:
                    messagebox.showerror("Error", "Failed to add storage location")

            except Exception as e:
                messagebox.showerror("Error", f"Could not add storage location: {str(e)}")

        ttk.Button(
            btn_frame,
            text="Save",
            command=on_save
        ).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')

    def validate_form(self):
        """
        Validate the form input.

        Returns:
            True if valid, False otherwise
        """
        # Check quantity is not zero
        if self.quantity_var.get() == 0:
            messagebox.showerror("Validation Error", "Quantity cannot be zero")
            return False

        # Check location is provided
        if not self.location_var.get():
            messagebox.showerror("Validation Error", "Storage location is required")
            return False

        return True

    def on_save(self):
        """Handle save button click."""
        if not self.validate_form():
            return

        try:
            # Collect form data
            data = {
                "transaction_type": self.transaction_type_var.get(),
                "quantity": self.quantity_var.get(),
                "status": self.status_var.get(),
                "storage_location": self.location_var.get(),
                "reference": self.reference_var.get(),
                "notes": self.notes_text.get("1.0", tk.END).strip()
            }

            # If item_id and item_type are provided, add them
            if self.item_id and self.item_type:
                data["item_id"] = self.item_id
                data["item_type"] = self.item_type

            # Process adjustment
            service = get_service("IInventoryService")

            if self.inventory_id:
                # Adjust existing inventory
                result = service.adjust_inventory(self.inventory_id, **data)
            else:
                # Create new inventory
                result = service.create_inventory(**data)

            if result:
                messagebox.showinfo("Success", "Inventory adjustment completed successfully")
                self.result = True
                self.close()
            else:
                messagebox.showerror("Error", "Failed to complete inventory adjustment")

        except Exception as e:
            messagebox.showerror("Error", f"Error saving inventory adjustment: {str(e)}")