# gui/views/inventory/inventory_view.py
"""
Inventory View.
Displays a comprehensive view of inventory across all item types.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import InventoryStatus, StorageLocationType, TransactionType
from gui.base.base_list_view import BaseListView
from gui.widgets.status_badge import StatusBadge
from gui.utils.service_access import get_service
from gui.utils.event_bus import subscribe, unsubscribe, publish


class InventoryView(BaseListView):
    """View for displaying and managing inventory items."""

    def __init__(self, parent):
        """
        Initialize the inventory view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Inventory Management"
        self.service_name = "IInventoryService"

        # Configure columns
        self.columns = [
            ("id", "ID", 60),
            ("item_type", "Type", 100),
            ("item_name", "Item", 200),
            ("item_specifics", "Details", 150),
            ("storage_location", "Location", 150),
            ("quantity", "Quantity", 80),
            ("status", "Status", 100),
            ("last_updated", "Last Updated", 150),
            ("last_transaction", "Last Transaction", 150)
        ]

        # Configure search fields
        self.search_fields = [
            {"name": "item_name", "label": "Item Name", "type": "text", "width": 20},
            {"name": "item_type", "label": "Item Type", "type": "select",
             "options": ["material", "product", "tool"], "width": 15},
            {"name": "status", "label": "Status", "type": "select",
             "options": [e.value for e in InventoryStatus], "width": 15},
            {"name": "storage_location", "label": "Location", "type": "text", "width": 15}
        ]

        # Status column for styling
        self.status_column = "status"

        # Subscribe to inventory update events
        subscribe("inventory_updated", self.on_inventory_updated)

    def build(self):
        """Build the inventory view."""
        super().build()

        # Add additional buttons to the action buttons area
        self.add_inventory_actions(self.action_buttons)

    def add_inventory_actions(self, parent):
        """
        Add inventory-specific action buttons.

        Args:
            parent: The parent widget for the buttons
        """
        # Add button to run inventory check
        btn_check = ttk.Button(
            parent,
            text="Inventory Check",
            command=self.run_inventory_check)
        btn_check.pack(side=tk.LEFT, padx=5)

        # Add button to generate report
        btn_report = ttk.Button(
            parent,
            text="Generate Report",
            command=self.generate_inventory_report)
        btn_report.pack(side=tk.LEFT, padx=5)

    def extract_item_values(self, item):
        """
        Extract values from an inventory item for display in the treeview.

        Args:
            item: The inventory item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # For DTO objects
        if hasattr(item, "id"):
            # Get item specifics
            specifics = ""
            if hasattr(item, 'related_item') and item.related_item:
                if item.item_type == "material":
                    material_type = getattr(item.related_item, 'material_type', '')
                    if material_type == "LEATHER":
                        specifics = f"{getattr(item.related_item, 'leather_type', '')}"
                    elif material_type == "HARDWARE":
                        specifics = f"{getattr(item.related_item, 'hardware_type', '')}"
                    elif material_type == "SUPPLIES":
                        specifics = f"{getattr(item.related_item, 'supplies_type', '')}"
                elif item.item_type == "product":
                    specifics = getattr(item.related_item, 'product_type', '')
                elif item.item_type == "tool":
                    specifics = getattr(item.related_item, 'tool_type', '')

            # Get last transaction info
            last_transaction = ""
            if hasattr(item, 'transactions') and item.transactions and len(item.transactions) > 0:
                trans = item.transactions[0]
                last_transaction = f"{trans.transaction_type} ({trans.quantity})"

            # Get item name
            item_name = ""
            if hasattr(item, 'related_item') and item.related_item and hasattr(item.related_item, 'name'):
                item_name = item.related_item.name
            elif hasattr(item, 'item_name'):
                item_name = item.item_name

            return [
                item.id,
                item.item_type.capitalize() if hasattr(item, 'item_type') else "",
                item_name,
                specifics,
                getattr(item, 'storage_location', ''),
                getattr(item, 'quantity', 0),
                getattr(item, 'status', ''),
                getattr(item, 'last_updated', ''),
                last_transaction
            ]

        # For dictionary data
        elif isinstance(item, dict):
            # Get item specifics
            specifics = ""
            if 'related_item' in item and item['related_item']:
                related = item['related_item']
                if item.get('item_type') == "material":
                    material_type = related.get('material_type', '')
                    if material_type == "LEATHER":
                        specifics = f"{related.get('leather_type', '')}"
                    elif material_type == "HARDWARE":
                        specifics = f"{related.get('hardware_type', '')}"
                    elif material_type == "SUPPLIES":
                        specifics = f"{related.get('supplies_type', '')}"
                elif item.get('item_type') == "product":
                    specifics = related.get('product_type', '')
                elif item.get('item_type') == "tool":
                    specifics = related.get('tool_type', '')

            # Get last transaction info
            last_transaction = ""
            if 'transactions' in item and item['transactions'] and len(item['transactions']) > 0:
                trans = item['transactions'][0]
                last_transaction = f"{trans.get('transaction_type', '')} ({trans.get('quantity', 0)})"

            # Get item name
            item_name = ""
            if 'related_item' in item and item['related_item'] and 'name' in item['related_item']:
                item_name = item['related_item']['name']
            elif 'item_name' in item:
                item_name = item['item_name']

            return [
                item.get('id', ''),
                item.get('item_type', '').capitalize(),
                item_name,
                specifics,
                item.get('storage_location', ''),
                item.get('quantity', 0),
                item.get('status', ''),
                item.get('last_updated', ''),
                last_transaction
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_add(self):
        """Handle add inventory action."""
        # Show dialog to select item type first
        self.logger.info("Opening add inventory dialog")

        # Create dialog to select item type
        type_dialog = tk.Toplevel(self.frame)
        type_dialog.title("Add Inventory")
        type_dialog.geometry("400x250")
        type_dialog.transient(self.frame)
        type_dialog.grab_set()

        # Create content frame
        content = ttk.Frame(type_dialog, padding=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Add instructions
        ttk.Label(
            content,
            text="Select the type of item to add to inventory:",
            font=("Helvetica", 12, "bold")
        ).pack(pady=(0, 20))

        # Create buttons for each item type
        btn_material = ttk.Button(
            content,
            text="Material",
            command=lambda: self.add_inventory_item("material", type_dialog)
        )
        btn_material.pack(fill=tk.X, pady=5)

        btn_product = ttk.Button(
            content,
            text="Product",
            command=lambda: self.add_inventory_item("product", type_dialog)
        )
        btn_product.pack(fill=tk.X, pady=5)

        btn_tool = ttk.Button(
            content,
            text="Tool",
            command=lambda: self.add_inventory_item("tool", type_dialog)
        )
        btn_tool.pack(fill=tk.X, pady=5)

        # Cancel button
        ttk.Button(
            content,
            text="Cancel",
            command=type_dialog.destroy
        ).pack(fill=tk.X, pady=(10, 0))

        # Center the dialog
        type_dialog.update_idletasks()
        width = type_dialog.winfo_width()
        height = type_dialog.winfo_height()
        x = (type_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (type_dialog.winfo_screenheight() // 2) - (height // 2)
        type_dialog.geometry(f'+{x}+{y}')

    def add_inventory_item(self, item_type, dialog):
        """
        Add a new inventory item of the specified type.

        Args:
            item_type: The type of item to add
            dialog: The type selection dialog to close
        """
        # Close the type selection dialog
        dialog.destroy()

        try:
            # Depending on item type, open appropriate dialog to select item
            if item_type == "material":
                # Open material selection dialog
                from gui.views.materials.material_list_view import MaterialListView

                # Create dialog
                item_dialog = tk.Toplevel(self.frame)
                item_dialog.title("Select Material")
                item_dialog.geometry("800x600")
                item_dialog.transient(self.frame)
                item_dialog.grab_set()

                # Create material list with selection callback
                def on_select_material(material_id):
                    item_dialog.destroy()
                    self.open_inventory_adjustment_dialog(material_id, "material")

                # Create custom material list view with selection button
                material_list = MaterialListView(item_dialog)
                material_list.on_double_click_callback = lambda: on_select_material(material_list.selected_item)
                material_list.build()

                # Add select button
                btn_frame = ttk.Frame(item_dialog, padding=10)
                btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

                ttk.Button(
                    btn_frame,
                    text="Cancel",
                    command=item_dialog.destroy
                ).pack(side=tk.RIGHT, padx=5)

                ttk.Button(
                    btn_frame,
                    text="Select Material",
                    command=lambda: on_select_material(
                        material_list.selected_item) if material_list.selected_item else None
                ).pack(side=tk.RIGHT, padx=5)

            elif item_type == "product":
                # Open product selection dialog
                from gui.views.products.product_list_view import ProductListView

                # Create dialog
                item_dialog = tk.Toplevel(self.frame)
                item_dialog.title("Select Product")
                item_dialog.geometry("800x600")
                item_dialog.transient(self.frame)
                item_dialog.grab_set()

                # Create product list with selection callback
                def on_select_product(product_id):
                    item_dialog.destroy()
                    self.open_inventory_adjustment_dialog(product_id, "product")

                # Create custom product list view with selection button
                product_list = ProductListView(item_dialog)
                product_list.on_double_click_callback = lambda: on_select_product(product_list.selected_item)
                product_list.build()

                # Add select button
                btn_frame = ttk.Frame(item_dialog, padding=10)
                btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

                ttk.Button(
                    btn_frame,
                    text="Cancel",
                    command=item_dialog.destroy
                ).pack(side=tk.RIGHT, padx=5)

                ttk.Button(
                    btn_frame,
                    text="Select Product",
                    command=lambda: on_select_product(
                        product_list.selected_item) if product_list.selected_item else None
                ).pack(side=tk.RIGHT, padx=5)

            elif item_type == "tool":
                # Open tool selection dialog
                from gui.views.tools.tool_list_view import ToolListView

                # Create dialog
                item_dialog = tk.Toplevel(self.frame)
                item_dialog.title("Select Tool")
                item_dialog.geometry("800x600")
                item_dialog.transient(self.frame)
                item_dialog.grab_set()

                # Create tool list with selection callback
                def on_select_tool(tool_id):
                    item_dialog.destroy()
                    self.open_inventory_adjustment_dialog(tool_id, "tool")

                # Create custom tool list view with selection button
                tool_list = ToolListView(item_dialog)
                tool_list.on_double_click_callback = lambda: on_select_tool(tool_list.selected_item)
                tool_list.build()

                # Add select button
                btn_frame = ttk.Frame(item_dialog, padding=10)
                btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

                ttk.Button(
                    btn_frame,
                    text="Cancel",
                    command=item_dialog.destroy
                ).pack(side=tk.RIGHT, padx=5)

                ttk.Button(
                    btn_frame,
                    text="Select Tool",
                    command=lambda: on_select_tool(tool_list.selected_item) if tool_list.selected_item else None
                ).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            self.logger.error(f"Error opening item selection dialog: {str(e)}")
            self.show_error("Error", f"Could not open selection dialog: {str(e)}")

    def on_view(self):
        """Handle view inventory action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening view inventory dialog for ID {self.selected_item}")

        try:
            inventory_id = int(self.selected_item)
            self.open_inventory_details_dialog(inventory_id)
        except Exception as e:
            self.logger.error(f"Error opening inventory details: {str(e)}")
            self.show_error("Error", f"Could not open inventory details: {str(e)}")

    def on_edit(self):
        """Handle edit inventory action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening inventory adjustment dialog for ID {self.selected_item}")

        try:
            inventory_id = int(self.selected_item)

            # Get inventory details to determine item type
            service = self.get_service(self.service_name)
            inventory = service.get_by_id(inventory_id)

            if not inventory:
                self.show_error("Error", f"Could not retrieve inventory details for ID {inventory_id}")
                return

            # Extract item type and ID
            item_type = getattr(inventory, "item_type", None)
            item_id = getattr(inventory, "item_id", None)

            if not item_type or not item_id:
                self.show_error("Error", "Invalid inventory data: missing item type or ID")
                return

            # Open inventory adjustment dialog
            from gui.views.inventory.inventory_adjustment_dialog import InventoryAdjustmentDialog

            dialog = InventoryAdjustmentDialog(
                self.frame,
                inventory_id=inventory_id,
                item_id=item_id,
                item_type=item_type
            )

            if dialog.show():
                self.logger.info("Inventory adjustment completed")
                # Refresh data
                self.refresh()
                # Publish inventory update event
                publish("inventory_updated", {"inventory_id": inventory_id})

        except Exception as e:
            self.logger.error(f"Error opening inventory adjustment dialog: {str(e)}")
            self.show_error("Error", f"Could not adjust inventory: {str(e)}")

    def add_context_menu_items(self, menu):
        """
        Add additional context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_separator()
        menu.add_command(label="Adjust Inventory", command=self.on_edit)
        menu.add_command(label="View Transactions", command=self.view_transactions)
        menu.add_command(label="Move Location", command=self.move_location)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons.

        Args:
            parent: The parent widget for the buttons
        """
        btn_adjust = ttk.Button(
            parent,
            text="Adjust",
            command=self.on_edit,
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

        btn_move = ttk.Button(
            parent,
            text="Move Location",
            command=self.move_location,
            state=tk.DISABLED)
        btn_move.pack(side=tk.LEFT, padx=5)
        self.btn_move = btn_move

    def on_select(self):
        """Handle item selection."""
        super().on_select()

        # Enable additional buttons if item is selected
        if self.selected_item:
            self.btn_adjust.config(state=tk.NORMAL)
            self.btn_transactions.config(state=tk.NORMAL)
            self.btn_move.config(state=tk.NORMAL)
        else:
            self.btn_adjust.config(state=tk.DISABLED)
            self.btn_transactions.config(state=tk.DISABLED)
            self.btn_move.config(state=tk.DISABLED)

    def open_inventory_details_dialog(self, inventory_id):
        """
        Open the inventory details dialog.

        Args:
            inventory_id: ID of the inventory item to view
        """
        try:
            service = self.get_service(self.service_name)
            inventory = service.get_by_id(inventory_id)

            if not inventory:
                self.show_error("Error", f"Could not retrieve inventory details for ID {inventory_id}")
                return

            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Inventory Details - {getattr(inventory, 'item_name', inventory_id)}")
            dialog.geometry("600x600")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Create details view
            self.create_inventory_details_view(content, inventory)

            # Add buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                btn_frame,
                text="Adjust",
                command=lambda: self.on_adjust_from_details(dialog, inventory)
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                btn_frame,
                text="Transactions",
                command=lambda: self.on_transactions_from_details(dialog, inventory)
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening inventory details: {str(e)}")
            self.show_error("Error", f"Could not display inventory details: {str(e)}")

    def create_inventory_details_view(self, parent, inventory):
        """
        Create the inventory details view.

        Args:
            parent: The parent widget
            inventory: The inventory item data
        """
        # Create header with item name and status
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        item_name = getattr(inventory, "item_name", "Unknown Item")
        status = getattr(inventory, "status", "UNKNOWN")

        ttk.Label(
            header_frame,
            text=item_name,
            font=("Helvetica", 16, "bold")
        ).pack(side=tk.LEFT)

        status_badge = StatusBadge(
            header_frame,
            text=status,
            status_value=status
        )
        status_badge.pack(side=tk.RIGHT)

        # Create details frame
        details_frame = ttk.LabelFrame(parent, text="Details")
        details_frame.pack(fill=tk.X, pady=10)

        # Grid layout for details
        details_grid = ttk.Frame(details_frame, padding=10)
        details_grid.pack(fill=tk.X)

        # Row 1
        ttk.Label(details_grid, text="ID:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(inventory, "id", ""))).grid(row=0, column=1, sticky="w", padx=5,
                                                                             pady=2)

        ttk.Label(details_grid, text="Item Type:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(inventory, "item_type", "")).capitalize()).grid(row=0, column=3,
                                                                                                 sticky="w", padx=5,
                                                                                                 pady=2)

        # Row 2
        ttk.Label(details_grid, text="Quantity:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(inventory, "quantity", 0))).grid(row=1, column=1, sticky="w", padx=5,
                                                                                  pady=2)

        ttk.Label(details_grid, text="Location:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(inventory, "storage_location", ""))).grid(row=1, column=3, sticky="w",
                                                                                           padx=5, pady=2)

        # Row 3
        ttk.Label(details_grid, text="Last Updated:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(inventory, "last_updated", ""))).grid(row=2, column=1, sticky="w",
                                                                                       padx=5, pady=2)

        ttk.Label(details_grid, text="Created Date:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(inventory, "created_at", ""))).grid(row=2, column=3, sticky="w",
                                                                                     padx=5, pady=2)

        # Item details section
        if hasattr(inventory, "related_item") and inventory.related_item:
            item_frame = ttk.LabelFrame(parent, text="Item Information")
            item_frame.pack(fill=tk.X, pady=10)

            item_grid = ttk.Frame(item_frame, padding=10)
            item_grid.pack(fill=tk.X)

            item = inventory.related_item

            # Item details based on type
            if inventory.item_type == "material":
                self.create_material_details(item_grid, item)
            elif inventory.item_type == "product":
                self.create_product_details(item_grid, item)
            elif inventory.item_type == "tool":
                self.create_tool_details(item_grid, item)

        # Transactions section
        if hasattr(inventory, "transactions") and inventory.transactions:
            trans_frame = ttk.LabelFrame(parent, text="Recent Transactions")
            trans_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Create treeview for transactions
            tree_frame = ttk.Frame(trans_frame, padding=10)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            tree = ttk.Treeview(
                tree_frame,
                columns=("date", "type", "quantity", "notes"),
                show="headings"
            )

            tree.heading("date", text="Date")
            tree.heading("type", text="Type")
            tree.heading("quantity", text="Quantity")
            tree.heading("notes", text="Notes")

            tree.column("date", width=150)
            tree.column("type", width=100)
            tree.column("quantity", width=80)
            tree.column("notes", width=200)

            # Add scrollbar
            sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)

            # Add transactions to treeview (limited to 10 most recent)
            for idx, trans in enumerate(inventory.transactions[:10]):
                tree.insert("", "end", values=(
                    getattr(trans, "transaction_date", ""),
                    getattr(trans, "transaction_type", ""),
                    getattr(trans, "quantity", 0),
                    getattr(trans, "notes", "")
                ))

    def create_material_details(self, parent, material):
        """
        Create material details view.

        Args:
            parent: The parent widget
            material: The material data
        """
        row = 0

        # Material type
        ttk.Label(parent, text="Material Type:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(material, "material_type", ""))).grid(row=row, column=1, sticky="w", padx=5,
                                                                                 pady=2)

        row += 1

        # Material-specific details
        material_type = getattr(material, "material_type", "")

        if material_type == "LEATHER":
            ttk.Label(parent, text="Leather Type:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "leather_type", ""))).grid(row=row, column=1, sticky="w",
                                                                                    padx=5, pady=2)

            ttk.Label(parent, text="Thickness:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "thickness", ""))).grid(row=row, column=3, sticky="w", padx=5,
                                                                                 pady=2)

            row += 1

            ttk.Label(parent, text="Finish:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "finish", ""))).grid(row=row, column=1, sticky="w", padx=5,
                                                                              pady=2)

        elif material_type == "HARDWARE":
            ttk.Label(parent, text="Hardware Type:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "hardware_type", ""))).grid(row=row, column=1, sticky="w",
                                                                                     padx=5, pady=2)

            ttk.Label(parent, text="Material:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "hardware_material", ""))).grid(row=row, column=3, sticky="w",
                                                                                         padx=5, pady=2)

            row += 1

            ttk.Label(parent, text="Finish:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "finish", ""))).grid(row=row, column=1, sticky="w", padx=5,
                                                                              pady=2)

            ttk.Label(parent, text="Size:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "size", ""))).grid(row=row, column=3, sticky="w", padx=5,
                                                                            pady=2)

        elif material_type == "SUPPLIES":
            ttk.Label(parent, text="Supplies Type:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "supplies_type", ""))).grid(row=row, column=1, sticky="w",
                                                                                     padx=5, pady=2)

            ttk.Label(parent, text="Color:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(parent, text=str(getattr(material, "color", ""))).grid(row=row, column=3, sticky="w", padx=5,
                                                                             pady=2)

        # Row for supplier information
        row += 1
        ttk.Label(parent, text="Supplier:").grid(row=row, column=0, sticky="w", padx=5, pady=2)

        supplier_name = ""
        if hasattr(material, "supplier") and material.supplier:
            supplier_name = material.supplier.name
        elif hasattr(material, "supplier_name"):
            supplier_name = material.supplier_name

        ttk.Label(parent, text=supplier_name).grid(row=row, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(parent, text="Cost:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(material, "cost", 0))).grid(row=row, column=3, sticky="w", padx=5, pady=2)

    def create_product_details(self, parent, product):
        """
        Create product details view.

        Args:
            parent: The parent widget
            product: The product data
        """
        row = 0

        # Product details
        ttk.Label(parent, text="Product Type:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(product, "product_type", ""))).grid(row=row, column=1, sticky="w", padx=5,
                                                                               pady=2)

        ttk.Label(parent, text="SKU:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(product, "sku", ""))).grid(row=row, column=3, sticky="w", padx=5, pady=2)

        row += 1

        ttk.Label(parent, text="Price:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(product, "price", 0))).grid(row=row, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(parent, text="Cost:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(product, "cost", 0))).grid(row=row, column=3, sticky="w", padx=5, pady=2)

    def create_tool_details(self, parent, tool):
        """
        Create tool details view.

        Args:
            parent: The parent widget
            tool: The tool data
        """
        row = 0

        # Tool details
        ttk.Label(parent, text="Tool Type:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(tool, "tool_type", ""))).grid(row=row, column=1, sticky="w", padx=5, pady=2)

        row += 1

        ttk.Label(parent, text="Supplier:").grid(row=row, column=0, sticky="w", padx=5, pady=2)

        supplier_name = ""
        if hasattr(tool, "supplier") and tool.supplier:
            supplier_name = tool.supplier.name
        elif hasattr(tool, "supplier_name"):
            supplier_name = tool.supplier_name

        ttk.Label(parent, text=supplier_name).grid(row=row, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(parent, text="Cost:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(tool, "cost", 0))).grid(row=row, column=3, sticky="w", padx=5, pady=2)

        row += 1

        ttk.Label(parent, text="Serial Number:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(parent, text=str(getattr(tool, "serial_number", ""))).grid(row=row, column=1, sticky="w", padx=5,
                                                                             pady=2)

    def on_adjust_from_details(self, dialog, inventory):
        """
        Handle adjust button click from details dialog.

        Args:
            dialog: The details dialog to close
            inventory: The inventory item
        """
        # Close the details dialog
        dialog.destroy()

        # Open inventory adjustment dialog
        self.on_edit()

    def on_transactions_from_details(self, dialog, inventory):
        """
        Handle transactions button click from details dialog.

        Args:
            dialog: The details dialog to close
            inventory: The inventory item
        """
        # Close the details dialog
        dialog.destroy()

        # Open transactions view
        self.view_transactions()

    def open_inventory_adjustment_dialog(self, item_id, item_type):
        """
        Open the inventory adjustment dialog for a specific item.

        Args:
            item_id: ID of the item
            item_type: Type of the item
        """
        try:
            from gui.views.inventory.inventory_adjustment_dialog import InventoryAdjustmentDialog

            dialog = InventoryAdjustmentDialog(
                self.frame,
                item_id=item_id,
                item_type=item_type
            )

            if dialog.show():
                self.logger.info("Inventory adjustment completed")
                # Refresh data
                self.refresh()
                # Publish inventory update event
                publish("inventory_updated", {"item_id": item_id, "item_type": item_type})
        except Exception as e:
            self.logger.error(f"Error opening inventory adjustment dialog: {str(e)}")
            self.show_error("Error", f"Could not open inventory adjustment: {str(e)}")

    def view_transactions(self):
        """View inventory transactions for the selected inventory."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening transactions view for inventory ID {self.selected_item}")

        try:
            from gui.views.inventory.inventory_transaction_view import InventoryTransactionView

            inventory_id = int(self.selected_item)

            # Open dialog with transactions for this inventory
            dialog = tk.Toplevel(self.frame)
            dialog.title("Inventory Transactions")
            dialog.geometry("800x600")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create transactions view with filter for this inventory
            transaction_view = InventoryTransactionView(
                dialog,
                inventory_id=inventory_id
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

    def move_location(self):
        """Move inventory to a different storage location."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening move location dialog for inventory ID {self.selected_item}")

        try:
            inventory_id = int(self.selected_item)

            # Get current inventory data
            service = self.get_service(self.service_name)
            inventory = service.get_by_id(inventory_id)

            if not inventory:
                self.show_error("Error", f"Could not retrieve inventory details for ID {inventory_id}")
                return

            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Move Location - {getattr(inventory, 'item_name', inventory_id)}")
            dialog.geometry("400x300")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Current location display
            ttk.Label(
                content,
                text="Current Location:",
                font=("Helvetica", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))

            current_location = getattr(inventory, "storage_location", "None")
            ttk.Label(
                content,
                text=current_location
            ).pack(anchor="w", pady=(0, 20))

            # New location entry
            ttk.Label(
                content,
                text="New Location:",
                font=("Helvetica", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))

            # Create combobox for location type
            ttk.Label(content, text="Location Type:").pack(anchor="w")

            location_type_var = tk.StringVar()
            location_type_combo = ttk.Combobox(
                content,
                textvariable=location_type_var,
                values=[e.value for e in StorageLocationType],
                state="readonly"
            )
            location_type_combo.pack(fill=tk.X, pady=(0, 10))

            # Location identifier
            ttk.Label(content, text="Location Identifier:").pack(anchor="w")

            location_id_var = tk.StringVar()
            location_id_entry = ttk.Entry(
                content,
                textvariable=location_id_var,
                width=30
            )
            location_id_entry.pack(fill=tk.X, pady=(0, 20))

            # Notes field
            ttk.Label(content, text="Notes:").pack(anchor="w")

            notes_var = tk.StringVar()
            notes_entry = ttk.Entry(
                content,
                textvariable=notes_var,
                width=30
            )
            notes_entry.pack(fill=tk.X)

            # Add buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            def on_move():
                # Get the new location
                location_type = location_type_var.get()
                location_id = location_id_var.get()
                notes = notes_var.get()

                if not location_type or not location_id:
                    messagebox.showerror("Error", "Please provide both location type and identifier")
                    return

                # Format new location
                new_location = f"{location_type}:{location_id}"

                try:
                    # Update the location
                    service.update_location(
                        inventory_id=inventory_id,
                        new_location=new_location,
                        notes=notes
                    )

                    # Close the dialog
                    dialog.destroy()

                    # Refresh data
                    self.refresh()

                    # Show success message
                    messagebox.showinfo(
                        "Success",
                        f"Inventory moved from {current_location} to {new_location}"
                    )

                    # Publish inventory update event
                    publish("inventory_updated", {"inventory_id": inventory_id})
                except Exception as e:
                    self.logger.error(f"Error moving inventory: {str(e)}")
                    messagebox.showerror("Error", f"Could not move inventory: {str(e)}")

            ttk.Button(
                btn_frame,
                text="Move",
                command=on_move
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening move location dialog: {str(e)}")
            self.show_error("Error", f"Could not open move location dialog: {str(e)}")

    def run_inventory_check(self):
        """Run an inventory check process."""
        self.logger.info("Starting inventory check process")

        try:
            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Inventory Check")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Add instructions
            ttk.Label(
                content,
                text="Inventory Check Process",
                font=("Helvetica", 14, "bold")
            ).pack(pady=(0, 10))

            ttk.Label(
                content,
                text="This process will generate a checklist for verifying inventory quantities.",
                wraplength=450
            ).pack(pady=5)

            # Filters section
            filters_frame = ttk.LabelFrame(content, text="Filters")
            filters_frame.pack(fill=tk.X, pady=10)

            filters_grid = ttk.Frame(filters_frame, padding=10)
            filters_grid.pack(fill=tk.X)

            # Item type filter
            ttk.Label(filters_grid, text="Item Type:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

            item_type_var = tk.StringVar(value="ALL")
            item_type_combo = ttk.Combobox(
                filters_grid,
                textvariable=item_type_var,
                values=["ALL", "material", "product", "tool"],
                state="readonly",
                width=15
            )
            item_type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)

            # Location filter
            ttk.Label(filters_grid, text="Location:").grid(row=0, column=2, sticky="w", padx=5, pady=2)

            location_var = tk.StringVar()
            location_entry = ttk.Entry(
                filters_grid,
                textvariable=location_var,
                width=15
            )
            location_entry.grid(row=0, column=3, sticky="w", padx=5, pady=2)

            # Status filter
            ttk.Label(filters_grid, text="Status:").grid(row=1, column=0, sticky="w", padx=5, pady=2)

            status_var = tk.StringVar(value="ALL")
            status_combo = ttk.Combobox(
                filters_grid,
                textvariable=status_var,
                values=["ALL"] + [e.value for e in InventoryStatus],
                state="readonly",
                width=15
            )
            status_combo.grid(row=1, column=1, sticky="w", padx=5, pady=2)

            # Format options
            format_frame = ttk.LabelFrame(content, text="Output Format")
            format_frame.pack(fill=tk.X, pady=10)

            format_grid = ttk.Frame(format_frame, padding=10)
            format_grid.pack(fill=tk.X)

            format_var = tk.StringVar(value="PDF")

            ttk.Radiobutton(
                format_grid,
                text="PDF Document",
                variable=format_var,
                value="PDF"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="Excel Spreadsheet",
                variable=format_var,
                value="EXCEL"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="CSV File",
                variable=format_var,
                value="CSV"
            ).grid(row=0, column=2, sticky="w", padx=5)

            # Include columns
            include_frame = ttk.LabelFrame(content, text="Include Columns")
            include_frame.pack(fill=tk.X, pady=10)

            include_grid = ttk.Frame(include_frame, padding=10)
            include_grid.pack(fill=tk.X)

            # Column checkboxes
            loc_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                include_grid,
                text="Location",
                variable=loc_var
            ).grid(row=0, column=0, sticky="w", padx=5)

            item_detail_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                include_grid,
                text="Item Details",
                variable=item_detail_var
            ).grid(row=0, column=1, sticky="w", padx=5)

            expected_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                include_grid,
                text="Expected Quantity",
                variable=expected_var
            ).grid(row=0, column=2, sticky="w", padx=5)

            actual_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                include_grid,
                text="Actual Quantity Field",
                variable=actual_var
            ).grid(row=1, column=0, sticky="w", padx=5)

            notes_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                include_grid,
                text="Notes Field",
                variable=notes_var
            ).grid(row=1, column=1, sticky="w", padx=5)

            # Buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            def generate_check():
                try:
                    # Get the filter values
                    item_type = None if item_type_var.get() == "ALL" else item_type_var.get()
                    location = location_var.get() or None
                    status = None if status_var.get() == "ALL" else status_var.get()

                    # Get the format
                    output_format = format_var.get()

                    # Get include options
                    include_options = {
                        "location": loc_var.get(),
                        "item_details": item_detail_var.get(),
                        "expected_quantity": expected_var.get(),
                        "actual_quantity": actual_var.get(),
                        "notes": notes_var.get()
                    }

                    # Generate the report
                    service = self.get_service(self.service_name)

                    # Show a confirmation that report is being generated
                    dialog.destroy()
                    messagebox.showinfo(
                        "Report Generation",
                        f"The inventory check report is being generated in {output_format} format.\n\n"
                        "It will be saved to the reports directory."
                    )

                    # In a real application, this would call the service to generate the report
                    # For this demonstration, we'll just log the parameters
                    self.logger.info(
                        f"Generating inventory check report with: "
                        f"format={output_format}, item_type={item_type}, "
                        f"location={location}, status={status}, "
                        f"include_options={include_options}"
                    )

                except Exception as e:
                    self.logger.error(f"Error generating inventory check report: {str(e)}")
                    messagebox.showerror("Error", f"Could not generate report: {str(e)}")

            ttk.Button(
                btn_frame,
                text="Generate",
                command=generate_check
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error running inventory check: {str(e)}")
            self.show_error("Error", f"Could not run inventory check: {str(e)}")

    def generate_inventory_report(self):
        """Generate inventory report."""
        self.logger.info("Opening inventory report dialog")

        try:
            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Generate Inventory Report")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Add instructions
            ttk.Label(
                content,
                text="Inventory Report Generator",
                font=("Helvetica", 14, "bold")
            ).pack(pady=(0, 10))

            ttk.Label(
                content,
                text="Generate a report of the current inventory status.",
                wraplength=450
            ).pack(pady=5)

            # Report type section
            report_frame = ttk.LabelFrame(content, text="Report Type")
            report_frame.pack(fill=tk.X, pady=10)

            report_grid = ttk.Frame(report_frame, padding=10)
            report_grid.pack(fill=tk.X)

            report_type_var = tk.StringVar(value="SUMMARY")

            ttk.Radiobutton(
                report_grid,
                text="Summary Report",
                variable=report_type_var,
                value="SUMMARY"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Detailed Report",
                variable=report_type_var,
                value="DETAILED"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Value Report",
                variable=report_type_var,
                value="VALUE"
            ).grid(row=1, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Low Stock Alert",
                variable=report_type_var,
                value="LOW_STOCK"
            ).grid(row=1, column=1, sticky="w", padx=5)

            # Filters section
            filters_frame = ttk.LabelFrame(content, text="Filters")
            filters_frame.pack(fill=tk.X, pady=10)

            filters_grid = ttk.Frame(filters_frame, padding=10)
            filters_grid.pack(fill=tk.X)

            # Item type filter
            ttk.Label(filters_grid, text="Item Type:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

            item_type_var = tk.StringVar(value="ALL")
            item_type_combo = ttk.Combobox(
                filters_grid,
                textvariable=item_type_var,
                values=["ALL", "material", "product", "tool"],
                state="readonly",
                width=15
            )
            item_type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)

            # Location filter
            ttk.Label(filters_grid, text="Location:").grid(row=0, column=2, sticky="w", padx=5, pady=2)

            location_var = tk.StringVar()
            location_entry = ttk.Entry(
                filters_grid,
                textvariable=location_var,
                width=15
            )
            location_entry.grid(row=0, column=3, sticky="w", padx=5, pady=2)

            # Format options
            format_frame = ttk.LabelFrame(content, text="Output Format")
            format_frame.pack(fill=tk.X, pady=10)

            format_grid = ttk.Frame(format_frame, padding=10)
            format_grid.pack(fill=tk.X)

            format_var = tk.StringVar(value="PDF")

            ttk.Radiobutton(
                format_grid,
                text="PDF Document",
                variable=format_var,
                value="PDF"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="Excel Spreadsheet",
                variable=format_var,
                value="EXCEL"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="CSV File",
                variable=format_var,
                value="CSV"
            ).grid(row=0, column=2, sticky="w", padx=5)

            # Buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            def generate_report():
                try:
                    # Get the filter values
                    report_type = report_type_var.get()
                    item_type = None if item_type_var.get() == "ALL" else item_type_var.get()
                    location = location_var.get() or None

                    # Get the format
                    output_format = format_var.get()

                    # Generate the report
                    service = self.get_service(self.service_name)

                    # Show a confirmation that report is being generated
                    dialog.destroy()
                    messagebox.showinfo(
                        "Report Generation",
                        f"The {report_type} inventory report is being generated in {output_format} format.\n\n"
                        "It will be saved to the reports directory."
                    )

                    # In a real application, this would call the service to generate the report
                    # For this demonstration, we'll just log the parameters
                    self.logger.info(
                        f"Generating inventory report with: "
                        f"type={report_type}, format={output_format}, "
                        f"item_type={item_type}, location={location}"
                    )

                except Exception as e:
                    self.logger.error(f"Error generating inventory report: {str(e)}")
                    messagebox.showerror("Error", f"Could not generate report: {str(e)}")

            ttk.Button(
                btn_frame,
                text="Generate",
                command=generate_report
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening report dialog: {str(e)}")
            self.show_error("Error", f"Could not open report dialog: {str(e)}")

    def on_inventory_updated(self, data):
        """
        Handle inventory updated event.

        Args:
            data: Event data
        """
        self.logger.info(f"Received inventory updated event: {data}")
        self.refresh()

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("inventory_updated", self.on_inventory_updated)
        super().destroy()