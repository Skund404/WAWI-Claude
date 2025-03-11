# gui/views/materials/leather_view.py
"""
Leather-specific Material View.
Displays a list of leather materials with specialized filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import LeatherType, LeatherFinish, InventoryStatus
from gui.views.materials.material_list_view import MaterialListView
from gui.views.materials.material_details_dialog import MaterialDetailsDialog
from gui.utils.service_access import get_service


class LeatherView(MaterialListView):
    """View for displaying and managing leather materials."""

    def __init__(self, parent):
        """
        Initialize the leather view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Leather Inventory"
        self.service_name = "ILeatherService"

        # Configure columns with leather-specific fields
        self.columns = [
            ("id", "ID", 60),
            ("name", "Name", 200),
            ("leather_type", "Type", 120),
            ("thickness", "Thickness", 80),
            ("area", "Area", 80),
            ("unit", "Unit", 80),
            ("finish", "Finish", 100),
            ("supplier_name", "Supplier", 150),
            ("inventory_status", "Status", 100),
            ("quantity", "Quantity", 80),
            ("cost", "Cost", 80)
        ]

        # Configure search fields with leather-specific options
        self.search_fields = [
            {"name": "name", "label": "Name", "type": "text", "width": 20},
            {"name": "leather_type", "label": "Type", "type": "select",
             "options": [e.value for e in LeatherType], "width": 15},
            {"name": "finish", "label": "Finish", "type": "select",
             "options": [e.value for e in LeatherFinish], "width": 15},
            {"name": "inventory_status", "label": "Status", "type": "select",
             "options": [e.value for e in InventoryStatus], "width": 15}
        ]

    def extract_item_values(self, item):
        """
        Extract values from a leather item for display in the treeview.

        Args:
            item: The leather item to extract values from

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
                getattr(item, "leather_type", ""),
                getattr(item, "thickness", ""),
                getattr(item, "area", ""),
                getattr(item, "unit", ""),
                getattr(item, "finish", ""),
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
                item.get("leather_type", ""),
                item.get("thickness", ""),
                item.get("area", ""),
                item.get("unit", ""),
                item.get("finish", ""),
                supplier_name,
                inventory_status,
                quantity,
                item.get("cost", 0)
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_add(self):
        """Handle add new leather action."""
        self.logger.info("Opening add leather dialog")

        dialog = MaterialDetailsDialog(self.frame, create_new=True, material_type="LEATHER")
        if dialog.show():
            self.logger.info("Leather created successfully")
            # Refresh data
            self.refresh()

    def on_edit(self):
        """Handle edit leather action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening edit leather dialog for ID {self.selected_item}")

        try:
            leather_id = int(self.selected_item)
            dialog = MaterialDetailsDialog(self.frame, material_id=leather_id, material_type="LEATHER")
            if dialog.show():
                self.logger.info("Leather updated successfully")
                # Refresh data
                self.refresh()
        except Exception as e:
            self.logger.error(f"Error opening leather edit dialog: {str(e)}")
            self.show_error("Error", f"Could not edit leather: {str(e)}")

    def add_context_menu_items(self, menu):
        """
        Add additional context menu items for leather.

        Args:
            menu: The context menu to add items to
        """
        super().add_context_menu_items(menu)
        menu.add_command(label="Calculate Material Usage", command=self.calculate_material_usage)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons for leather.

        Args:
            parent: The parent widget for the buttons
        """
        super().add_item_action_buttons(parent)

        btn_calc_usage = ttk.Button(
            parent,
            text="Calculate Usage",
            command=self.calculate_material_usage,
            state=tk.DISABLED)
        btn_calc_usage.pack(side=tk.LEFT, padx=5)
        self.btn_calc_usage = btn_calc_usage

    def on_select(self):
        """Handle item selection."""
        super().on_select()

        # Enable leather-specific buttons if item is selected
        if self.selected_item:
            self.btn_calc_usage.config(state=tk.NORMAL)
        else:
            self.btn_calc_usage.config(state=tk.DISABLED)

    def calculate_material_usage(self):
        """Calculate material usage for patterns."""
        if not self.selected_item:
            return

        self.logger.info(f"Calculating material usage for leather ID {self.selected_item}")

        try:
            from gui.views.tools.material_calculator import MaterialCalculatorDialog

            leather_id = int(self.selected_item)
            dialog = MaterialCalculatorDialog(self.frame, material_id=leather_id)
            dialog.show()

        except Exception as e:
            self.logger.error(f"Error opening material calculator: {str(e)}")
            self.show_error("Error", f"Could not open material calculator: {str(e)}")