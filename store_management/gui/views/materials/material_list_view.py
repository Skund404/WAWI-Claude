# gui/views/materials/material_list_view.py
"""
Generic Material List View.
Displays a list of all materials with filtering and sorting capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import MaterialType, InventoryStatus
from gui.base.base_list_view import BaseListView
from gui.views.materials.material_details_dialog import MaterialDetailsDialog
from gui.widgets.status_badge import StatusBadge
from gui.utils.service_access import get_service
from gui.utils.event_bus import subscribe, unsubscribe, publish


class MaterialListView(BaseListView):
    """View for displaying and managing a list of materials."""

    def __init__(self, parent):
        """
        Initialize the material list view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Materials"
        self.service_name = "IMaterialService"

        # Configure columns
        self.columns = [
            ("id", "ID", 60),
            ("name", "Name", 200),
            ("material_type", "Type", 120),
            ("unit", "Unit", 80),
            ("supplier_name", "Supplier", 150),
            ("quality", "Quality", 100),
            ("inventory_status", "Status", 100),
            ("quantity", "Quantity", 80),
            ("cost", "Cost", 80)
        ]

        # Configure search fields
        self.search_fields = [
            {"name": "name", "label": "Name", "type": "text", "width": 20},
            {"name": "material_type", "label": "Type", "type": "select",
             "options": [e.value for e in MaterialType], "width": 15},
            {"name": "supplier_name", "label": "Supplier", "type": "text", "width": 15},
            {"name": "inventory_status", "label": "Status", "type": "select",
             "options": [e.value for e in InventoryStatus], "width": 15}
        ]

        # Status column for styling
        self.status_column = "inventory_status"

        # Subscribe to material update events
        subscribe("material_updated", self.on_material_updated)

    def build(self):
        """Build the material list view."""
        super().build()

        # Customize the treeview
        self.treeview.set_column_widths({
            "name": 200,
            "material_type": 120,
            "supplier_name": 150
        })

    def extract_item_values(self, item):
        """
        Extract values from a material item for display in the treeview.

        Args:
            item: The material item to extract values from

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
                item.material_type,
                getattr(item, "unit", ""),
                supplier_name,
                getattr(item, "quality", ""),
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
                item.get("material_type", ""),
                item.get("unit", ""),
                supplier_name,
                item.get("quality", ""),
                inventory_status,
                quantity,
                item.get("cost", 0)
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_add(self):
        """Handle add new material action."""
        self.logger.info("Opening add material dialog")

        dialog = MaterialDetailsDialog(self.frame, create_new=True)
        if dialog.show():
            self.logger.info("Material created successfully")
            # Refresh data
            self.refresh()

    def on_view(self):
        """Handle view material action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening view material dialog for ID {self.selected_item}")

        try:
            material_id = int(self.selected_item)
            dialog = MaterialDetailsDialog(self.frame, material_id=material_id, readonly=True)
            dialog.show()
        except Exception as e:
            self.logger.error(f"Error opening material details: {str(e)}")
            self.show_error("Error", f"Could not open material details: {str(e)}")

    def on_edit(self):
        """Handle edit material action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening edit material dialog for ID {self.selected_item}")

        try:
            material_id = int(self.selected_item)
            dialog = MaterialDetailsDialog(self.frame, material_id=material_id)
            if dialog.show():
                self.logger.info("Material updated successfully")
                # Refresh data
                self.refresh()
        except Exception as e:
            self.logger.error(f"Error opening material edit dialog: {str(e)}")
            self.show_error("Error", f"Could not edit material: {str(e)}")

    def add_context_menu_items(self, menu):
        """
        Add additional context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_separator()
        menu.add_command(label="Adjust Inventory", command=self.adjust_inventory)
        menu.add_command(label="View Transactions", command=self.view_transactions)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons.

        Args:
            parent: The parent widget for the buttons
        """
        btn_adjust = ttk.Button(
            parent,
            text="Adjust Inventory",
            command=self.adjust_inventory,
            state=tk.DISABLED)
        btn_adjust.pack(side=tk.LEFT, padx=5)
        self.btn_adjust = btn_adjust

        btn_transactions = ttk.Button(
            parent,
            text="Transactions",
            command=self.view_transactions,
            state=tk.DISABLED)
        btn_transactions.pack(side=tk.LEFT, padx=5)
        self.btn_transactions = btn_transactions

    def on_select(self):
        """Handle item selection."""
        super().on_select()

        # Enable additional buttons if item is selected
        if self.selected_item:
            self.btn_adjust.config(state=tk.NORMAL)
            self.btn_transactions.config(state=tk.NORMAL)
        else:
            self.btn_adjust.config(state=tk.DISABLED)
            self.btn_transactions.config(state=tk.DISABLED)

    def adjust_inventory(self):
        """Open inventory adjustment dialog."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening inventory adjustment dialog for material ID {self.selected_item}")

        try:
            from gui.views.inventory.inventory_adjustment_dialog import InventoryAdjustmentDialog

            material_id = int(self.selected_item)
            dialog = InventoryAdjustmentDialog(
                self.frame,
                item_id=material_id,
                item_type="material"
            )

            if dialog.show():
                self.logger.info("Inventory adjustment completed")
                # Refresh data
                self.refresh()
                # Publish inventory update event
                publish("inventory_updated", {"item_id": material_id, "item_type": "material"})
        except Exception as e:
            self.logger.error(f"Error opening inventory adjustment dialog: {str(e)}")
            self.show_error("Error", f"Could not open inventory adjustment: {str(e)}")

    def view_transactions(self):
        """View inventory transactions for the selected material."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening transactions view for material ID {self.selected_item}")

        try:
            from gui.views.inventory.inventory_transaction_view import InventoryTransactionView

            material_id = int(self.selected_item)

            # Open dialog with transactions for this material
            dialog = tk.Toplevel(self.frame)
            dialog.title("Material Transactions")
            dialog.geometry("800x600")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create transactions view with filter for this material
            transaction_view = InventoryTransactionView(
                dialog,
                item_id=material_id,
                item_type="material"
            )
            transaction_view.build()

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

            # Wait for dialog to close
            self.frame.wait_window(dialog)

        except Exception as e:
            self.logger.error(f"Error opening transactions view: {str(e)}")
            self.show_error("Error", f"Could not open transactions view: {str(e)}")

    def on_material_updated(self, data):
        """
        Handle material updated event.

        Args:
            data: Event data
        """
        self.logger.info(f"Received material updated event: {data}")
        self.refresh()

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("material_updated", self.on_material_updated)
        super().destroy()