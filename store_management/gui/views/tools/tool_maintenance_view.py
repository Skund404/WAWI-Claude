# gui/views/tools/tool_maintenance_view.py
"""
Tool maintenance view for managing tool maintenance activities and schedules.

This view provides an interface for viewing maintenance history, scheduling
new maintenance activities, and tracking maintenance status for tools.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from gui.base.base_list_view import BaseListView
from gui.widgets.search_frame import SearchField, SearchFrame
from gui.theme import COLORS
from gui.config import Config
from utils.service_access import with_service

from database.models.enums import ToolCategory


class ToolMaintenanceView(BaseListView):
    """Tool maintenance view for managing tool maintenance activities."""

    def __init__(self, parent, tool_id=None):
        """Initialize the tool maintenance view.

        Args:
            parent: The parent widget
            tool_id: Optional tool ID to filter maintenance records for a specific tool
        """
        super().__init__(parent)
        self.tool_id = tool_id
        self.title = f"Tool Maintenance" if not tool_id else "Tool Maintenance History"
        self.icon = "🧰"  # Toolbox icon
        self.logger = logging.getLogger(__name__)
        self.build()

    def build(self):
        """Build the tool maintenance view layout."""
        super().build()

        # Update header with appropriate subtitle
        if self.tool_id:
            with self.get_service("tool_service") as service:
                tool = service.get_tool_by_id(self.tool_id)
                if tool:
                    self.header_subtitle.config(text=f"Maintenance records for: {tool.name}")
                else:
                    self.header_subtitle.config(text="Maintenance records for selected tool")
        else:
            self.header_subtitle.config(text="View and manage tool maintenance activities")

        # Create search fields
        self.search_fields = [
            SearchField("tool_name", "Tool Name", "text"),
            SearchField("maintenance_type", "Maintenance Type", "combobox",
                        options=[
                            {"value": "routine", "text": "Routine"},
                            {"value": "repair", "text": "Repair"},
                            {"value": "calibration", "text": "Calibration"},
                            {"value": "inspection", "text": "Inspection"},
                            {"value": "replacement", "text": "Part Replacement"},
                            {"value": "other", "text": "Other"}
                        ]),
            SearchField("date_from", "Date From", "date"),
            SearchField("date_to", "Date To", "date"),
            SearchField("technician", "Technician", "text"),
        ]

        # Create search frame
        self.search_frame = SearchFrame(
            self.content_frame,
            title="Search Maintenance Records",
            fields=self.search_fields,
            on_search=self.on_search,
            on_reset=self.refresh
        )
        self.search_frame.pack(fill=tk.X, padx=10, pady=5)

        # If tool_id is provided, pre-fill the tool name search
        if self.tool_id:
            self.search_frame.set_field_value("tool_name", self.get_tool_name(self.tool_id))

        # Create columns for the treeview
        columns = (
            "id", "tool_name", "maintenance_date", "maintenance_type",
            "performed_by", "cost", "status", "next_date"
        )

        # Column widths
        column_widths = {
            "id": 80,
            "tool_name": 200,
            "maintenance_date": 120,
            "maintenance_type": 150,
            "performed_by": 150,
            "cost": 80,
            "status": 100,
            "next_date": 120
        }

        # Column headings
        self.column_headings = {
            "id": "ID",
            "tool_name": "Tool Name",
            "maintenance_date": "Date",
            "maintenance_type": "Type",
            "performed_by": "Performed By",
            "cost": "Cost",
            "status": "Status",
            "next_date": "Next Due"
        }

        # Create treeview with the defined columns
        self.create_treeview(self.content_frame)
        self.treeview.configure(columns=columns)

        # Set column headings
        for col in columns:
            self.treeview.heading(col, text=self.column_headings.get(col, col.capitalize()))

        # Set column widths
        self.treeview.set_column_widths(column_widths)

        # Create item actions frame
        self.create_item_actions(self.content_frame)

        # Create pagination controls
        self.create_pagination(self.content_frame)

        # Create context menu
        self.create_context_menu()

        # Create stats frame
        self.create_stats_frame(self.content_frame)

        # Load initial data
        self.refresh()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        super()._add_default_action_buttons()

        # Add maintenance-specific action buttons
        ttk.Button(
            self.header_actions,
            text="Add Maintenance Record",
            style="Accent.TButton",
            command=self.on_add
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.header_actions,
            text="Generate Report",
            command=self.on_generate_report
        ).pack(side=tk.RIGHT, padx=5)

        # Add back to tool button if we're viewing a specific tool
        if self.tool_id:
            ttk.Button(
                self.header_actions,
                text="Back to Tool",
                command=self.on_back_to_tool
            ).pack(side=tk.RIGHT, padx=5)

    def add_context_menu_items(self, menu):
        """Add maintenance-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        super().add_context_menu_items(menu)

        menu.add_separator()
        menu.add_command(label="Complete Maintenance", command=self.on_complete_maintenance)
        menu.add_command(label="Print Record", command=self.on_print_record)

    def add_item_action_buttons(self, parent):
        """Add maintenance-specific action buttons.

        Args:
            parent: The parent widget
        """
        super().add_item_action_buttons(parent)

        ttk.Button(
            parent,
            text="Complete",
            command=self.on_complete_maintenance
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            parent,
            text="View Tool",
            command=self.on_view_tool
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def create_stats_frame(self, parent):
        """Create a frame for displaying maintenance statistics.

        Args:
            parent: The parent widget
        """
        # Create a frame for statistics
        stats_frame = ttk.LabelFrame(parent, text="Maintenance Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=5, anchor=tk.W)

        # Create a grid layout for statistics
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        # Add statistics labels
        self.stats_labels = {}

        # Upcoming maintenance
        ttk.Label(stats_frame, text="Upcoming Maintenance:").grid(
            row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["upcoming"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["upcoming"].grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        # Overdue maintenance
        ttk.Label(stats_frame, text="Overdue Maintenance:").grid(
            row=0, column=2, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["overdue"] = ttk.Label(stats_frame, text="0", foreground=COLORS["danger"])
        self.stats_labels["overdue"].grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)

        # Maintenance this month
        ttk.Label(stats_frame, text="This Month:").grid(
            row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["this_month"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["this_month"].grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        # Total maintenance cost
        ttk.Label(stats_frame, text="Total Cost:").grid(
            row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["total_cost"] = ttk.Label(stats_frame, text="$0.00")
        self.stats_labels["total_cost"].grid(row=1, column=3, padx=10, pady=5, sticky=tk.W)

    @with_service("tool_service")
    def get_tool_name(self, tool_id, service=None):
        """Get the name of a tool by ID.

        Args:
            tool_id: The ID of the tool
            service: The tool service injected by the decorator

        Returns:
            The tool name or empty string if not found
        """
        try:
            tool = service.get_tool_by_id(tool_id)
            return tool.name if tool else ""
        except Exception as e:
            self.logger.error(f"Error getting tool name: {e}")
            return ""

    @with_service("tool_maintenance_service")
    def get_total_count(self, service=None):
        """Get the total count of maintenance records.

        Args:
            service: The tool maintenance service injected by the decorator

        Returns:
            The total count of maintenance records
        """
        criteria = self.search_criteria if hasattr(self, 'search_criteria') else {}

        # If tool_id is provided, filter by tool
        if self.tool_id and "tool_id" not in criteria:
            criteria["tool_id"] = self.tool_id

        try:
            return service.count_maintenance_records(criteria)
        except Exception as e:
            self.logger.error(f"Error counting maintenance records: {e}")
            return 0

    @with_service("tool_maintenance_service")
    def get_items(self, service, offset, limit):
        """Get maintenance records for the current page.

        Args:
            service: The tool maintenance service injected by the decorator
            offset: Pagination offset
            limit: Page size

        Returns:
            List of maintenance records
        """
        criteria = self.search_criteria if hasattr(self, 'search_criteria') else {}
        sort_field = self.sort_column if hasattr(self, 'sort_column') else "maintenance_date"
        sort_dir = self.sort_direction if hasattr(self, 'sort_direction') else "desc"

        # If tool_id is provided, filter by tool
        if self.tool_id and "tool_id" not in criteria:
            criteria["tool_id"] = self.tool_id

        try:
            return service.get_maintenance_records(
                criteria=criteria,
                offset=offset,
                limit=limit,
                sort_by=sort_field,
                sort_dir=sort_dir,
                include_tool=True
            )
        except Exception as e:
            self.logger.error(f"Error getting maintenance records: {e}")
            return []

    def extract_item_values(self, item):
        """Extract values from a maintenance record for display in the treeview.

        Args:
            item: The maintenance record to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Format dates
        maintenance_date = item.maintenance_date.strftime("%Y-%m-%d") if item.maintenance_date else "N/A"
        next_date = item.next_maintenance_date.strftime("%Y-%m-%d") if hasattr(item,
                                                                               "next_maintenance_date") and item.next_maintenance_date else "N/A"

        # Format cost
        cost = f"${item.cost:.2f}" if hasattr(item, "cost") and item.cost is not None else "N/A"

        # Get tool name
        tool_name = item.tool.name if hasattr(item, "tool") and item.tool else "Unknown Tool"

        # Return values in order of columns
        return [
            item.id,
            tool_name,
            maintenance_date,
            item.maintenance_type if hasattr(item, "maintenance_type") else "Unknown",
            item.performed_by if hasattr(item, "performed_by") else "N/A",
            cost,
            item.status if hasattr(item, "status") else "Completed",
            next_date
        ]

    @with_service("tool_maintenance_service")
    def update_stats(self, service=None):
        """Update the maintenance statistics display.

        Args:
            service: The tool maintenance service injected by the decorator
        """
        try:
            # Get statistics from the service
            stats = service.get_maintenance_statistics(tool_id=self.tool_id)

            # Update the statistics display
            self.stats_labels["upcoming"].config(text=str(stats.get("upcoming", 0)))
            self.stats_labels["overdue"].config(text=str(stats.get("overdue", 0)))
            self.stats_labels["this_month"].config(text=str(stats.get("this_month", 0)))
            self.stats_labels["total_cost"].config(text=f"${stats.get('total_cost', 0):.2f}")

            # Highlight overdue maintenance in red if there are any
            if stats.get("overdue", 0) > 0:
                self.stats_labels["overdue"].config(foreground=COLORS["danger"])
            else:
                self.stats_labels["overdue"].config(foreground=COLORS["success"])

        except Exception as e:
            self.logger.error(f"Error updating maintenance statistics: {e}")

    def refresh(self):
        """Refresh the maintenance records and statistics."""
        super().refresh()
        self.update_stats()

    def on_add(self):
        """Handle adding a new maintenance record."""
        self.logger.info("Opening add maintenance record dialog")

        # Open dialog to add a new maintenance record
        from gui.views.tools.tool_maintenance_dialog import ToolMaintenanceDialog
        dialog = ToolMaintenanceDialog(self.parent, tool_id=self.tool_id)

        if dialog.result:
            self.refresh()

    def on_edit(self):
        """Handle editing an existing maintenance record."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a maintenance record to edit")
            return

        self.logger.info(f"Opening edit dialog for maintenance record ID: {selected_id}")

        # Open dialog to edit the selected maintenance record
        from gui.views.tools.tool_maintenance_dialog import ToolMaintenanceDialog
        dialog = ToolMaintenanceDialog(self.parent, maintenance_id=selected_id)

        if dialog.result:
            self.refresh()

    def on_delete(self):
        """Handle deleting an existing maintenance record."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a maintenance record to delete")
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            "Are you sure you want to delete this maintenance record? This action cannot be undone."
        )

        if not confirm:
            return

        self.logger.info(f"Deleting maintenance record ID: {selected_id}")

        # Delete the maintenance record
        try:
            with self.get_service("tool_maintenance_service") as service:
                service.delete_maintenance_record(selected_id)

            messagebox.showinfo("Success", "Maintenance record deleted successfully")
            self.refresh()
        except Exception as e:
            self.logger.error(f"Error deleting maintenance record: {e}")
            messagebox.showerror("Error", f"Failed to delete maintenance record: {str(e)}")

    def on_view(self):
        """Handle viewing maintenance record details."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a maintenance record to view")
            return

        self.logger.info(f"Opening view dialog for maintenance record ID: {selected_id}")

        # Open dialog to view the selected maintenance record
        from gui.views.tools.tool_maintenance_dialog import ToolMaintenanceDialog
        dialog = ToolMaintenanceDialog(self.parent, maintenance_id=selected_id, readonly=True)

    def on_complete_maintenance(self):
        """Handle completing a maintenance task."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a maintenance record to complete")
            return

        self.logger.info(f"Completing maintenance record ID: {selected_id}")

        # Mark the maintenance record as completed
        try:
            with self.get_service("tool_maintenance_service") as service:
                service.complete_maintenance(selected_id)

            messagebox.showinfo("Success", "Maintenance record marked as completed")
            self.refresh()
        except Exception as e:
            self.logger.error(f"Error completing maintenance record: {e}")
            messagebox.showerror("Error", f"Failed to complete maintenance record: {str(e)}")

    def on_view_tool(self):
        """View the tool associated with the selected maintenance record."""
        selected_values = self.treeview.get_selected_item_values()
        if not selected_values:
            messagebox.showwarning("No Selection", "Please select a maintenance record to view the associated tool")
            return

        # Get the tool ID from the maintenance record
        try:
            with self.get_service("tool_maintenance_service") as service:
                maintenance = service.get_maintenance_record_by_id(selected_values[0], include_tool=True)

                if maintenance and hasattr(maintenance, "tool_id"):
                    # Open the tool detail view
                    from gui.views.tools.tool_detail_view import ToolDetailView
                    view = ToolDetailView(self.parent, tool_id=maintenance.tool_id, readonly=True)
                else:
                    messagebox.showwarning("Tool Not Found",
                                           "The tool associated with this maintenance record could not be found")
        except Exception as e:
            self.logger.error(f"Error viewing tool: {e}")
            messagebox.showerror("Error", f"Failed to view tool: {str(e)}")

    def on_generate_report(self):
        """Generate a maintenance report."""
        # This would be implemented as part of advanced functionality
        messagebox.showinfo("Coming Soon", "Report generation will be available in a future update")

    def on_print_record(self):
        """Print the selected maintenance record."""
        # This would be implemented as part of advanced functionality
        messagebox.showinfo("Coming Soon", "Printing functionality will be available in a future update")

    def on_back_to_tool(self):
        """Navigate back to the tool detail view."""
        if not self.tool_id:
            return

        # Open the tool detail view
        from gui.views.tools.tool_detail_view import ToolDetailView
        view = ToolDetailView(self.parent, tool_id=self.tool_id, readonly=True)

        # Close this view
        self.destroy()