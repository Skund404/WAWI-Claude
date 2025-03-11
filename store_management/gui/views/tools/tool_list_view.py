# gui/views/tools/tool_list_view.py
"""
Tool list view for displaying and managing tools in the leatherworking ERP system.

This view provides an interface for viewing, filtering, and managing tools,
including adding new tools, editing existing ones, and performing various
tool-related operations.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type

from gui.base.base_list_view import BaseListView
from gui.widgets.search_frame import SearchField, SearchFrame
from gui.theme import COLORS
from gui.config import Config
from utils.service_access import with_service

from database.models.enums import ToolCategory, InventoryStatus


class ToolListView(BaseListView):
    """Tool list view for managing tools in the leatherworking ERP."""

    def __init__(self, parent):
        """Initialize the tool list view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Tool Management"
        self.icon = "🔧"  # Tool icon
        self.logger = logging.getLogger(__name__)
        self.build()

    def build(self):
        """Build the tool list view layout."""
        super().build()

        # Update header with tool-specific information
        self.header_subtitle.config(text="Manage your tools and equipment")

        # Create search fields specific to tools
        self.search_fields = [
            SearchField("name", "Tool Name", "text"),
            SearchField("tool_category", "Category", "enum", enum_class=ToolCategory),
            SearchField("status", "Status", "enum", enum_class=InventoryStatus),
            SearchField("supplier_name", "Supplier", "text"),
        ]

        # Create search frame with the defined fields
        self.search_frame = SearchFrame(
            self.content_frame,
            title="Search Tools",
            fields=self.search_fields,
            on_search=self.on_search,
            on_reset=self.refresh
        )
        self.search_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create tool list with appropriate columns
        columns = (
            "id", "name", "tool_category", "supplier_name",
            "status", "quantity", "location"
        )
        column_widths = {
            "id": 80,
            "name": 250,
            "tool_category": 150,
            "supplier_name": 180,
            "status": 120,
            "quantity": 80,
            "location": 150
        }

        # Define column headings
        self.column_headings = {
            "id": "ID",
            "name": "Tool Name",
            "tool_category": "Category",
            "supplier_name": "Supplier",
            "status": "Status",
            "quantity": "Quantity",
            "location": "Location"
        }

        # Create treeview with the defined columns
        self.create_treeview(self.content_frame)
        self.treeview.configure(columns=columns)

        # Set column headings
        for col in columns:
            self.treeview.heading(col, text=self.column_headings.get(col, col.capitalize()))

        # Set column widths
        self.treeview.set_column_widths(column_widths)

        # Create item actions (buttons)
        self.create_item_actions(self.content_frame)

        # Create pagination controls
        self.create_pagination(self.content_frame)

        # Context menu for right-click actions
        self.create_context_menu()

        # Load initial data
        self.refresh()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        super()._add_default_action_buttons()

        # Add tool-specific action buttons
        ttk.Button(
            self.header_actions,
            text="Add New Tool",
            style="Accent.TButton",
            command=self.on_add
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.header_actions,
            text="Maintenance",
            command=self.on_maintenance
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.header_actions,
            text="Export",
            command=self.on_export
        ).pack(side=tk.RIGHT, padx=5)

    def add_context_menu_items(self, menu):
        """Add tool-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        super().add_context_menu_items(menu)

        menu.add_separator()
        menu.add_command(label="View Maintenance History", command=self.on_view_maintenance)
        menu.add_command(label="Schedule Maintenance", command=self.on_schedule_maintenance)
        menu.add_command(label="Check Out Tool", command=self.on_checkout)
        menu.add_command(label="Check In Tool", command=self.on_checkin)

    def on_maintenance(self):
        """Open the tool maintenance management view."""
        self.logger.info("Opening tool maintenance management view")

        # Open the maintenance management view
        from gui.views.tools.tool_maintenance_view import ToolMaintenanceView
        maintenance_view = ToolMaintenanceView(self.parent)

    def on_view_maintenance(self):
        """View maintenance history for the selected tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to view maintenance history")
            return

        self.logger.info(f"Opening maintenance history for tool ID: {selected_id}")

        # Open maintenance view for this tool
        from gui.views.tools.tool_maintenance_view import ToolMaintenanceView
        maintenance_view = ToolMaintenanceView(self.parent, tool_id=selected_id)

    def add_item_action_buttons(self, parent):
        """Add tool-specific action buttons.

        Args:
            parent: The parent widget
        """
        super().add_item_action_buttons(parent)

        ttk.Button(
            parent,
            text="View Maintenance",
            command=self.on_view_maintenance
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            parent,
            text="Check Out/In",
            command=self.on_checkout
        ).pack(side=tk.LEFT, padx=5, pady=5)

    @with_service("tool_service")
    def get_total_count(self, service) -> int:
        """Get the total count of tools.

        Args:
            service: The tool service injected by the decorator

        Returns:
            The total count of tools
        """
        criteria = self.search_criteria if hasattr(self, 'search_criteria') else {}
        return service.count_tools(criteria)

    @with_service("tool_service")
    def get_items(self, service, offset: int, limit: int) -> List[Any]:
        """Get tools for the current page.

        Args:
            service: The tool service injected by the decorator
            offset: Pagination offset
            limit: Page size

        Returns:
            List of tools
        """
        criteria = self.search_criteria if hasattr(self, 'search_criteria') else {}
        sort_field = self.sort_column if hasattr(self, 'sort_column') else "name"
        sort_dir = self.sort_direction if hasattr(self, 'sort_direction') else "asc"

        return service.get_tools(
            criteria=criteria,
            offset=offset,
            limit=limit,
            sort_by=sort_field,
            sort_dir=sort_dir,
            include_inventory=True,
            include_supplier=True
        )

    def extract_item_values(self, item) -> List[Any]:
        """Extract values from a tool for display in the treeview.

        Args:
            item: The tool to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Extract inventory info if available
        inventory_info = {}
        if hasattr(item, 'inventory') and item.inventory:
            for inv in item.inventory:
                inventory_info = {
                    'status': inv.status.value if inv.status else "Unknown",
                    'quantity': inv.quantity if hasattr(inv, 'quantity') else 0,
                    'location': inv.storage_location if hasattr(inv, 'storage_location') else "Unknown"
                }

        # Extract supplier info if available
        supplier_name = "N/A"
        if hasattr(item, 'supplier') and item.supplier:
            supplier_name = item.supplier.name

        # Return values in order of columns
        return [
            item.id,
            item.name,
            item.tool_category.value if item.tool_category else "N/A",
            supplier_name,
            inventory_info.get('status', "Unknown"),
            inventory_info.get('quantity', 0),
            inventory_info.get('location', "Unknown")
        ]

    def on_add(self):
        """Handle adding a new tool."""
        self.logger.info("Opening add tool dialog")
        from gui.views.tools.tool_detail_view import ToolDetailView

        # Open tool detail view in add mode (no tool_id)
        view = ToolDetailView(self.parent)

        # Refresh the list after adding
        self.app.navigation.add_callback(self.refresh)

    def on_edit(self):
        """Handle editing an existing tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to edit")
            return

        self.logger.info(f"Opening edit dialog for tool ID: {selected_id}")
        from gui.views.tools.tool_detail_view import ToolDetailView

        # Open tool detail view in edit mode with the selected tool ID
        view = ToolDetailView(self.parent, tool_id=selected_id)

        # Refresh the list after editing
        self.app.navigation.add_callback(self.refresh)

    def on_delete(self):
        """Handle deleting an existing tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to delete")
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            "Are you sure you want to delete this tool? This action cannot be undone."
        )

        if not confirm:
            return

        self.logger.info(f"Deleting tool ID: {selected_id}")

        # Delete the tool using the tool service
        try:
            with self.get_service("tool_service") as service:
                service.delete_tool(selected_id)

            messagebox.showinfo("Success", "Tool deleted successfully")
            self.refresh()
        except Exception as e:
            self.logger.error(f"Error deleting tool: {e}")
            messagebox.showerror("Error", f"Failed to delete tool: {str(e)}")

    def on_view(self):
        """Handle viewing tool details."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to view")
            return

        self.logger.info(f"Opening view dialog for tool ID: {selected_id}")
        from gui.views.tools.tool_detail_view import ToolDetailView

        # Open tool detail view in view mode (read-only)
        view = ToolDetailView(self.parent, tool_id=selected_id, readonly=True)

    def on_maintenance(self):
        """Open the tool maintenance management view."""
        # This would be implemented in Phase 2
        messagebox.showinfo("Coming Soon", "Tool maintenance management will be available in a future update")

    def on_view_maintenance(self):
        """View maintenance history for the selected tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to view maintenance history")
            return

        # This would be implemented in Phase 2
        messagebox.showinfo("Coming Soon", "Tool maintenance history will be available in a future update")

    def on_schedule_maintenance(self):
        """Schedule maintenance for the selected tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to schedule maintenance")
            return

        # This would be implemented in Phase 2
        messagebox.showinfo("Coming Soon", "Maintenance scheduling will be available in a future update")

    def on_checkout(self):
        """Check out the selected tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to check out")
            return

        # This would be implemented in Phase 3
        messagebox.showinfo("Coming Soon", "Tool checkout functionality will be available in a future update")

    def on_checkin(self):
        """Check in the selected tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to check in")
            return

        # This would be implemented in Phase 3
        messagebox.showinfo("Coming Soon", "Tool check-in functionality will be available in a future update")

    def on_export(self):
        """Export tool list to a file."""
        # Basic implementation of export functionality
        messagebox.showinfo("Coming Soon", "Export functionality will be available in a future update")