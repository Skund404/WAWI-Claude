# gui/views/materials/supplies_view.py
"""
Supplies-specific Material View.
Displays a list of supplies materials with specialized filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import MaterialType, InventoryStatus
from gui.views.materials.material_list_view import MaterialListView
from gui.views.materials.material_details_dialog import MaterialDetailsDialog
from gui.utils.service_access import get_service


class SuppliesView(MaterialListView):
    """View for displaying and managing supplies materials (thread, adhesives, etc.)."""

    def __init__(self, parent):
        """
        Initialize the supplies view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Supplies Inventory"
        self.service_name = "ISuppliesService"

        # Configure columns with supplies-specific fields
        self.columns = [
            ("id", "ID", 60),
            ("name", "Name", 200),
            ("supplies_type", "Type", 120),
            ("color", "Color", 100),
            ("thickness", "Thickness", 80),
            ("material_composition", "Composition", 150),
            ("supplier_name", "Supplier", 150),
            ("inventory_status", "Status", 100),
            ("quantity", "Quantity", 80),
            ("cost", "Cost", 80)
        ]

        # Configure search fields with supplies-specific options
        self.search_fields = [
            {"name": "name", "label": "Name", "type": "text", "width": 20},
            {"name": "supplies_type", "label": "Type", "type": "select",
             "options": ["thread", "adhesive", "dye", "finish", "edge_paint", "wax"], "width": 15},
            {"name": "color", "label": "Color", "type": "text", "width": 15},
            {"name": "inventory_status", "label": "Status", "type": "select",
             "options": [e.value for e in InventoryStatus], "width": 15}
        ]

    def extract_item_values(self, item):
        """
        Extract values from a supplies item for display in the treeview.

        Args:
            item: The supplies item to extract values from

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

            # Get the specific supplies type
            supplies_type = getattr(item, "supplies_type", "")
            if not supplies_type and hasattr(item, "material_type"):
                # Fall back to material_type if supplies_type not available
                supplies_type = item.material_type

            return [
                item.id,
                item.name,
                supplies_type,
                getattr(item, "color", ""),
                getattr(item, "thickness", ""),
                getattr(item, "material_composition", ""),
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

            # Get the specific supplies type
            supplies_type = item.get("supplies_type", "")
            if not supplies_type and "material_type" in item:
                # Fall back to material_type if supplies_type not available
                supplies_type = item["material_type"]

            return [
                item.get("id", ""),
                item.get("name", ""),
                supplies_type,
                item.get("color", ""),
                item.get("thickness", ""),
                item.get("material_composition", ""),
                supplier_name,
                inventory_status,
                quantity,
                item.get("cost", 0)
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_add(self):
        """Handle add new supplies action."""
        self.logger.info("Opening add supplies dialog")

        dialog = MaterialDetailsDialog(self.frame, create_new=True, material_type="SUPPLIES")
        if dialog.show():
            self.logger.info("Supplies created successfully")
            # Refresh data
            self.refresh()

    def on_edit(self):
        """Handle edit supplies action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening edit supplies dialog for ID {self.selected_item}")

        try:
            supplies_id = int(self.selected_item)
            dialog = MaterialDetailsDialog(self.frame, material_id=supplies_id, material_type="SUPPLIES")
            if dialog.show():
                self.logger.info("Supplies updated successfully")
                # Refresh data
                self.refresh()
        except Exception as e:
            self.logger.error(f"Error opening supplies edit dialog: {str(e)}")
            self.show_error("Error", f"Could not edit supplies: {str(e)}")

    def add_context_menu_items(self, menu):
        """
        Add additional context menu items for supplies.

        Args:
            menu: The context menu to add items to
        """
        super().add_context_menu_items(menu)
        menu.add_command(label="Order More", command=self.order_supplies)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons for supplies.

        Args:
            parent: The parent widget for the buttons
        """
        super().add_item_action_buttons(parent)

        btn_order = ttk.Button(
            parent,
            text="Order More",
            command=self.order_supplies,
            state=tk.DISABLED)
        btn_order.pack(side=tk.LEFT, padx=5)
        self.btn_order = btn_order

    def on_select(self):
        """Handle item selection."""
        super().on_select()

        # Enable supplies-specific buttons if item is selected
        if self.selected_item:
            self.btn_order.config(state=tk.NORMAL)
        else:
            self.btn_order.config(state=tk.DISABLED)

    def order_supplies(self):
        """Create a purchase order for the selected supplies."""
        if not self.selected_item:
            return

        self.logger.info(f"Creating purchase order for supplies ID {self.selected_item}")

        try:
            supplies_id = int(self.selected_item)

            # Get the supplies details
            service = self.get_service(self.service_name)
            supplies = service.get_by_id(supplies_id)

            if not supplies:
                self.show_error("Error", f"Could not retrieve supplies with ID {supplies_id}")
                return

            # Get supplier information
            supplier_id = None
            supplier_name = ""

            if hasattr(supplies, "supplier_id"):
                supplier_id = supplies.supplier_id
            elif hasattr(supplies, "supplier") and supplies.supplier:
                supplier_id = supplies.supplier.id
                supplier_name = supplies.supplier.name

            if not supplier_id:
                self.show_error("Error", "No supplier information available for this item")
                return

            # Open purchase order dialog
            from gui.views.purchases.purchase_details_view import PurchaseDetailsView

            # Create initial purchase data with this supplies item
            purchase_data = {
                "supplier_id": supplier_id,
                "items": [
                    {
                        "item_id": supplies_id,
                        "item_type": "material",
                        "name": getattr(supplies, "name", f"Supplies {supplies_id}"),
                        "quantity": 1,
                        "price": getattr(supplies, "cost", 0)
                    }
                ]
            }

            # Show purchase dialog
            purchase_view = PurchaseDetailsView(self.frame, create_new=True, initial_data=purchase_data)
            purchase_view.show()

        except Exception as e:
            self.logger.error(f"Error creating purchase order: {str(e)}")
            self.show_error("Error", f"Could not create purchase order: {str(e)}")