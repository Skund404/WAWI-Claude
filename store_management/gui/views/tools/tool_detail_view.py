# gui/views/tools/tool_detail_view.py
"""
Tool detail view for adding, editing, and viewing tool information in the leatherworking ERP system.

This view provides a form interface for managing tool data, including basic information,
supplier details, inventory status, and other tool-specific properties.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Type

from gui.base.base_form_view import BaseFormView, FormField
from gui.widgets.enum_combobox import EnumCombobox
from gui.theme import COLORS
from utils.service_access import with_service

from database.models.enums import ToolCategory, InventoryStatus, SupplierStatus, MeasurementUnit


class ToolDetailView(BaseFormView):
    """Tool detail view for adding, editing, and viewing tool information."""

    def __init__(self, parent, tool_id=None, readonly=False):
        """Initialize the tool detail view.

        Args:
            parent: The parent widget
            tool_id: ID of the tool to edit (None for new tools)
            readonly: Whether the view should be read-only
        """
        self.readonly = readonly
        self.logger = logging.getLogger(__name__)

        # Set view title based on mode
        self.title = "View Tool" if readonly else "Edit Tool" if tool_id else "Add New Tool"
        self.icon = "🔧"  # Tool icon

        super().__init__(parent, tool_id)

    def on_view_maintenance(self):
        """View maintenance history for the current tool."""
        if not self.item_id:
            return

        self.logger.info(f"Opening maintenance history for tool ID: {self.item_id}")

        # Open maintenance view for this tool
        from gui.views.tools.tool_maintenance_view import ToolMaintenanceView
        maintenance_view = ToolMaintenanceView(self.parent, tool_id=self.item_id)

    def build(self):
        """Build the tool detail view layout."""
        super().build()

        # Update header with appropriate subtitle
        action = "Viewing" if self.readonly else "Editing" if self.item_id else "Adding new"
        self.header_subtitle.config(text=f"{action} tool information")

        # Define form fields
        self.form_fields = [
            # Basic Tool Information
            FormField("name", "Tool Name", "text", required=True, max_length=100),
            FormField("description", "Description", "text_area", height=3),
            FormField("tool_category", "Tool Category", "enum", enum_class=ToolCategory, required=True),

            # Supplier Information
            FormField("supplier_id", "Supplier", "combobox", required=False,
                      options=self.get_supplier_options),

            # Cost Information
            FormField("purchase_price", "Purchase Price", "decimal", required=False),
            FormField("purchase_date", "Purchase Date", "date", required=False),

            # Technical Specifications
            FormField("specifications", "Specifications", "text_area", height=3, required=False),
            FormField("brand", "Brand/Manufacturer", "text", required=False),
            FormField("model", "Model/Part Number", "text", required=False),
            FormField("serial_number", "Serial Number", "text", required=False),

            # Inventory Information
            FormField("status", "Status", "enum", enum_class=InventoryStatus, required=True),
            FormField("quantity", "Quantity", "integer", required=True, default=1),
            FormField("min_stock_level", "Minimum Stock Level", "integer", required=False),
            FormField("storage_location", "Storage Location", "text", required=False),

            # Maintenance Information
            FormField("maintenance_interval", "Maintenance Interval (Days)", "integer", required=False),
            FormField("last_maintenance_date", "Last Maintenance Date", "date", required=False),
            FormField("next_maintenance_date", "Next Maintenance Date", "date", required=False,
                      editable=False, help_text="Calculated automatically"),

            # Notes
            FormField("notes", "Notes", "text_area", height=3, required=False),
        ]

        # Create form fields
        self.create_form_fields()

        # Create form buttons
        self.create_form_buttons(self.form_frame)

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        super()._add_default_action_buttons()

        # Add tool-specific action buttons when viewing existing tool
        if self.item_id and self.readonly:
            ttk.Button(
                self.header_actions,
                text="Edit",
                style="Accent.TButton",
                command=self.on_edit
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                self.header_actions,
                text="View Maintenance",
                command=self.on_view_maintenance
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                self.header_actions,
                text="Check Out/In",
                command=self.on_checkout
            ).pack(side=tk.RIGHT, padx=5)

    @with_service("supplier_service")
    def get_supplier_options(self, service) -> List[Dict[str, Any]]:
        """Get a list of suppliers for the supplier dropdown.

        Args:
            service: The supplier service injected by the decorator

        Returns:
            List of supplier options with id and display text
        """
        try:
            # Get active suppliers
            suppliers = service.get_suppliers(
                criteria={"status": SupplierStatus.ACTIVE},
                limit=100
            )

            # Format for dropdown
            return [
                {"value": supplier.id, "text": supplier.name}
                for supplier in suppliers
            ]
        except Exception as e:
            self.logger.error(f"Error loading suppliers: {e}")
            return []

    @with_service("tool_service")
    def load_item_data(self, service):
        """Load tool data for editing.

        Args:
            service: The tool service injected by the decorator
        """
        if not self.item_id:
            return

        try:
            # Load tool with related data
            self.item = service.get_tool_by_id(
                self.item_id,
                include_inventory=True,
                include_supplier=True,
                include_usage=True
            )

            if not self.item:
                messagebox.showerror("Error", f"Tool with ID {self.item_id} not found")
                self.on_cancel()
                return

            # Convert to dictionary for form population
            self.item_data = self.item_to_dict(self.item)

            # Populate form fields
            self.populate_fields()

            # Make fields read-only if in view mode
            if self.readonly:
                for field_name, field_info in self.field_widgets.items():
                    widget = field_info["widget"]
                    if hasattr(widget, "config"):
                        widget.config(state="readonly" if widget.winfo_class() != "Text" else "disabled")
                    elif hasattr(widget, "configure"):
                        widget.configure(state="readonly" if widget.winfo_class() != "Text" else "disabled")

        except Exception as e:
            self.logger.error(f"Error loading tool data: {e}")
            messagebox.showerror("Error", f"Failed to load tool data: {str(e)}")
            self.on_cancel()

    def item_to_dict(self, item) -> Dict[str, Any]:
        """Convert a tool model to a dictionary.

        Args:
            item: The tool model to convert

        Returns:
            Dictionary representation of the tool
        """
        data = {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "tool_category": item.tool_category,
            "supplier_id": item.supplier_id if hasattr(item, "supplier_id") else None,
            "brand": getattr(item, "brand", ""),
            "model": getattr(item, "model", ""),
            "serial_number": getattr(item, "serial_number", ""),
            "specifications": getattr(item, "specifications", ""),
            "purchase_price": getattr(item, "purchase_price", 0.0),
            "purchase_date": getattr(item, "purchase_date", None),
            "notes": getattr(item, "notes", ""),
            "maintenance_interval": getattr(item, "maintenance_interval", 0),
            "last_maintenance_date": getattr(item, "last_maintenance_date", None),
            "next_maintenance_date": getattr(item, "next_maintenance_date", None),
        }

        # Extract inventory information if available
        if hasattr(item, 'inventory') and item.inventory:
            for inv in item.inventory:
                data.update({
                    "status": inv.status,
                    "quantity": inv.quantity,
                    "min_stock_level": getattr(inv, "min_stock_level", 0),
                    "storage_location": inv.storage_location if hasattr(inv, "storage_location") else ""
                })
                break  # We only need the first inventory entry

        return data

    def validate_form(self) -> bool:
        """Validate form data.

        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        is_valid = super().validate_form()

        if not is_valid:
            return False

        # Additional custom validation
        data = self.collect_form_data()
        errors = {}

        # Validate quantity > 0
        if data.get("quantity", 0) <= 0:
            errors["quantity"] = "Quantity must be greater than 0"

        # Validate purchase price
        if data.get("purchase_price") and data.get("purchase_price") < 0:
            errors["purchase_price"] = "Purchase price cannot be negative"

        # Validate maintenance interval
        if data.get("maintenance_interval") and data.get("maintenance_interval") < 0:
            errors["maintenance_interval"] = "Maintenance interval cannot be negative"

        # If there are validation errors, display them and return False
        if errors:
            for field, error in errors.items():
                self.validation_errors[field] = error
            self.display_validation_errors()
            return False

        return True

    def process_data_before_save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process form data before saving.

        Args:
            data: The form data to process

        Returns:
            Processed data ready for saving
        """
        # Remove empty strings and convert to None
        for key, value in data.items():
            if value == "":
                data[key] = None

        # Handle inventory-specific data
        inventory_data = {
            "status": data.pop("status", None),
            "quantity": data.pop("quantity", 1),
            "min_stock_level": data.pop("min_stock_level", None),
            "storage_location": data.pop("storage_location", None)
        }

        # Add inventory data back in a structure expected by the service
        data["inventory"] = inventory_data

        return data

    @with_service("tool_service")
    def on_save(self, service):
        """Handle form save action.

        Args:
            service: The tool service injected by the decorator
        """
        if not self.validate_form():
            return

        try:
            # Collect and process form data
            data = self.collect_form_data()
            processed_data = self.process_data_before_save(data)

            # Save the tool
            if self.item_id:
                # Update existing tool
                result = service.update_tool(self.item_id, processed_data)
                messagebox.showinfo("Success", "Tool updated successfully")
            else:
                # Create new tool
                result = service.create_tool(processed_data)
                messagebox.showinfo("Success", "Tool created successfully")

            # Handle successful save
            self.on_save_success(result)

        except Exception as e:
            self.logger.error(f"Error saving tool: {e}")
            messagebox.showerror("Error", f"Failed to save tool: {str(e)}")

    def on_edit(self):
        """Switch from view mode to edit mode."""
        if not self.readonly:
            return

        # Create a new instance of the form in edit mode
        edit_view = ToolDetailView(self.parent, self.item_id, readonly=False)

        # Close the current view
        self.destroy()

    def on_view_maintenance(self):
        """View maintenance history for the current tool."""
        if not self.item_id:
            return

        # This would be implemented in Phase 2
        messagebox.showinfo("Coming Soon", "Tool maintenance history will be available in a future update")

    def on_checkout(self):
        """Check out or check in the current tool."""
        if not self.item_id:
            return

        # This would be implemented in Phase 3
        messagebox.showinfo("Coming Soon", "Tool checkout functionality will be available in a future update")