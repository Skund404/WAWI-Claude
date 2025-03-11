# gui/views/materials/hardware_view.py
"""
Hardware-specific Material View.
Displays a list of hardware materials with specialized filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import HardwareType, HardwareMaterial, HardwareFinish, InventoryStatus
from gui.views.materials.material_list_view import MaterialListView
from gui.views.materials.material_details_dialog import MaterialDetailsDialog
from gui.utils.service_access import get_service


class HardwareView(MaterialListView):
    """View for displaying and managing hardware materials."""

    def __init__(self, parent):
        """
        Initialize the hardware view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Hardware Inventory"
        self.service_name = "IHardwareService"

        # Configure columns with hardware-specific fields
        self.columns = [
            ("id", "ID", 60),
            ("name", "Name", 200),
            ("hardware_type", "Type", 120),
            ("hardware_material", "Material", 120),
            ("finish", "Finish", 100),
            ("size", "Size", 80),
            ("supplier_name", "Supplier", 150),
            ("inventory_status", "Status", 100),
            ("quantity", "Quantity", 80),
            ("cost", "Cost", 80)
        ]

        # Configure search fields with hardware-specific options
        self.search_fields = [
            {"name": "name", "label": "Name", "type": "text", "width": 20},
            {"name": "hardware_type", "label": "Type", "type": "select",
             "options": [e.value for e in HardwareType], "width": 15},
            {"name": "hardware_material", "label": "Material", "type": "select",
             "options": [e.value for e in HardwareMaterial], "width": 15},
            {"name": "finish", "label": "Finish", "type": "select",
             "options": [e.value for e in HardwareFinish], "width": 15},
            {"name": "inventory_status", "label": "Status", "type": "select",
             "options": [e.value for e in InventoryStatus], "width": 15}
        ]

    def extract_item_values(self, item):
        """
        Extract values from a hardware item for display in the treeview.

        Args:
            item: The hardware item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # For DTO objects
        if hasattr(item, "id"):
            # Get inventory status from inventory data if available
            inventory_status = "UNKNOWN"
            quantity = 0

            if hasattr(item, "inventory") and item.inventory:
                if isinstance(item.inventory, list) and len(item.inventory) > 0:
                    inventory_status = item.inventory[0].status
                    quantity = item.inventory[0].quantity
                elif hasattr(item.inventory, "status"):
                    inventory_status = item.inventory.status
                    quantity = item.inventory.quantity

            # Get supplier name if available
            supplier_name = ""
            if hasattr(item, "supplier") and item.supplier:
                supplier_name = item.supplier.name
            elif hasattr(item, "supplier_name"):
                supplier_name = item.supplier_name

            return [
                item.id,
                item.name,
                getattr(item, "hardware_type", ""),
                getattr(item, "hardware_material", ""),
                getattr(item, "finish", ""),
                getattr(item, "size", ""),
                supplier_name,
                inventory_status,
                quantity,
                getattr(item, "cost", 0)
            ]

        # For dictionary data
        elif isinstance(item, dict):
            inventory_status = item.get("inventory_status", "UNKNOWN")
            quantity = item.get("quantity", 0)

            # Get inventory data if available
            if "inventory" in item and item["inventory"]:
                if isinstance(item["inventory"], list) and len(item["inventory"]) > 0:
                    inventory_status = item["inventory"][0].get("status", "UNKNOWN")
                    quantity = item["inventory"][0].get("quantity", 0)
                elif isinstance(item["inventory"], dict):
                    inventory_status = item["inventory"].get("status", "UNKNOWN")
                    quantity = item["inventory"].get("quantity", 0)

            # Get supplier name if available
            supplier_name = ""
            if "supplier" in item and item["supplier"]:
                supplier_name = item["supplier"].get("name", "")
            elif "supplier_name" in item:
                supplier_name = item["supplier_name"]

            return [
                item.get("id", ""),
                item.get("name", ""),
                item.get("hardware_type", ""),
                item.get("hardware_material", ""),
                item.get("finish", ""),
                item.get("size", ""),
                supplier_name,
                inventory_status,
                quantity,
                item.get("cost", 0)
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_add(self):
        """Handle add new hardware action."""
        self.logger.info("Opening add hardware dialog")

        dialog = MaterialDetailsDialog(self.frame, create_new=True, material_type="HARDWARE")
        if dialog.show():
            self.logger.info("Hardware created successfully")
            # Refresh data
            self.refresh()

    def on_edit(self):
        """Handle edit hardware action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening edit hardware dialog for ID {self.selected_item}")

        try:
            hardware_id = int(self.selected_item)
            dialog = MaterialDetailsDialog(self.frame, material_id=hardware_id, material_type="HARDWARE")
            if dialog.show():
                self.logger.info("Hardware updated successfully")
                # Refresh data
                self.refresh()
        except Exception as e:
            self.logger.error(f"Error opening hardware edit dialog: {str(e)}")
            self.show_error("Error", f"Could not edit hardware: {str(e)}")

    def add_context_menu_items(self, menu):
        """
        Add additional context menu items for hardware.

        Args:
            menu: The context menu to add items to
        """
        super().add_context_menu_items(menu)
        menu.add_command(label="Similar Hardware", command=self.find_similar_hardware)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons for hardware.

        Args:
            parent: The parent widget for the buttons
        """
        super().add_item_action_buttons(parent)

        btn_similar = ttk.Button(
            parent,
            text="Similar Items",
            command=self.find_similar_hardware,
            state=tk.DISABLED)
        btn_similar.pack(side=tk.LEFT, padx=5)
        self.btn_similar = btn_similar

    def on_select(self):
        """Handle item selection."""
        super().on_select()

        # Enable hardware-specific buttons if item is selected
        if self.selected_item:
            self.btn_similar.config(state=tk.NORMAL)
        else:
            self.btn_similar.config(state=tk.DISABLED)

    def find_similar_hardware(self):
        """Find similar hardware items."""
        if not self.selected_item:
            return

        self.logger.info(f"Finding similar hardware for ID {self.selected_item}")

        try:
            hardware_id = int(self.selected_item)
            service = self.get_service(self.service_name)

            # Get the selected hardware item
            hardware = service.get_by_id(hardware_id)
            if not hardware:
                self.show_error("Error", "Could not retrieve hardware details")
                return

            # Find similar hardware by type
            similar_items = []
            if hasattr(hardware, "hardware_type"):
                hardware_type = hardware.hardware_type
                similar_items = service.find_by_type(hardware_type)
            elif isinstance(hardware, dict) and "hardware_type" in hardware:
                hardware_type = hardware["hardware_type"]
                similar_items = service.find_by_type(hardware_type)

            # Remove the selected item from results
            similar_items = [item for item in similar_items if getattr(item, "id", 0) != hardware_id]

            # Display the results
            if not similar_items:
                self.show_info("Similar Hardware", "No similar hardware items found")
                return

            # Create dialog to display similar items
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Similar Hardware to {getattr(hardware, 'name', hardware_id)}")
            dialog.geometry("800x400")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create a treeview to display the items
            tree_frame = ttk.Frame(dialog, padding=10)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            tree = ttk.Treeview(
                tree_frame,
                columns=("id", "name", "type", "material", "finish", "size", "quantity"),
                show="headings"
            )

            # Configure columns
            tree.heading("id", text="ID")
            tree.heading("name", text="Name")
            tree.heading("type", text="Type")
            tree.heading("material", text="Material")
            tree.heading("finish", text="Finish")
            tree.heading("size", text="Size")
            tree.heading("quantity", text="Quantity")

            tree.column("id", width=50)
            tree.column("name", width=200)
            tree.column("type", width=100)
            tree.column("material", width=100)
            tree.column("finish", width=100)
            tree.column("size", width=80)
            tree.column("quantity", width=80)

            # Add scrollbar
            sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)

            # Add close button
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT)

            # Add similar items to the treeview
            for item in similar_items:
                # Get inventory quantity
                quantity = 0
                if hasattr(item, "inventory") and item.inventory:
                    if isinstance(item.inventory, list) and len(item.inventory) > 0:
                        quantity = item.inventory[0].quantity
                    elif hasattr(item.inventory, "quantity"):
                        quantity = item.inventory.quantity

                tree.insert("", "end", values=(
                    getattr(item, "id", ""),
                    getattr(item, "name", ""),
                    getattr(item, "hardware_type", ""),
                    getattr(item, "hardware_material", ""),
                    getattr(item, "finish", ""),
                    getattr(item, "size", ""),
                    quantity
                ))

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error finding similar hardware: {str(e)}")
            self.show_error("Error", f"Could not find similar hardware: {str(e)}")