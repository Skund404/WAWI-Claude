# gui/views/tools/tool_dashboard_widget.py
"""
Tool dashboard widget for the leatherworking ERP system.

This widget provides a summary view of tool-related information
for display on the main dashboard.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta

from gui.theme import COLORS
from utils.service_access import with_service


class ToolDashboardWidget(ttk.Frame):
    """Dashboard widget showing tool statistics and information."""

    def __init__(self, parent, navigation_callback=None):
        """Initialize the tool dashboard widget.

        Args:
            parent: The parent widget
            navigation_callback: Callback function for navigation
        """
        super().__init__(parent, style="Card.TFrame")
        self.parent = parent
        self.navigation_callback = navigation_callback
        self.logger = logging.getLogger(__name__)

        # Build the widget
        self.build()

        # Refresh data
        self.refresh()

    def build(self):
        """Build the dashboard widget layout."""
        # Set padding and styling
        self.configure(padding=(15, 10))

        # Create header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Add title
        title_label = ttk.Label(header_frame, text="Tool Management", style="DashboardWidgetTitle.TLabel")
        title_label.pack(side=tk.LEFT)

        # Add refresh button
        refresh_btn = ttk.Button(header_frame, text="↻", width=3, command=self.refresh)
        refresh_btn.pack(side=tk.RIGHT)

        # Create content sections
        self.create_stats_section()
        self.create_alerts_section()

        # Add button to view all tools
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        view_all_btn = ttk.Button(btn_frame, text="View All Tools",
                                  command=self.on_view_all_tools)
        view_all_btn.pack(side=tk.LEFT, padx=5)

        view_checkouts_btn = ttk.Button(btn_frame, text="View Checkouts",
                                        command=self.on_view_checkouts)
        view_checkouts_btn.pack(side=tk.LEFT, padx=5)

        view_maintenance_btn = ttk.Button(btn_frame, text="View Maintenance",
                                          command=self.on_view_maintenance)
        view_maintenance_btn.pack(side=tk.LEFT, padx=5)

    def create_stats_section(self):
        """Create the section for displaying tool statistics."""
        # Create frame for statistics
        stats_frame = ttk.LabelFrame(self, text="Tool Statistics")
        stats_frame.pack(fill=tk.X, pady=5)

        # Create grid for statistics
        for i in range(3):
            stats_frame.columnconfigure(i, weight=1)

        # Create statistic labels
        self.stats_labels = {}

        # Row 1: Tool counts
        ttk.Label(stats_frame, text="Total Tools:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.stats_labels["total_tools"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["total_tools"].grid(row=0, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(stats_frame, text="In Stock:").grid(row=0, column=2, padx=5, pady=3, sticky=tk.W)
        self.stats_labels["in_stock"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["in_stock"].grid(row=0, column=3, padx=5, pady=3, sticky=tk.W)

        ttk.Label(stats_frame, text="Checked Out:").grid(row=0, column=4, padx=5, pady=3, sticky=tk.W)
        self.stats_labels["checked_out"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["checked_out"].grid(row=0, column=5, padx=5, pady=3, sticky=tk.W)

        # Row 2: Maintenance and status
        ttk.Label(stats_frame, text="Maintenance Due:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.stats_labels["maintenance_due"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["maintenance_due"].grid(row=1, column=1, padx=5, pady=3, sticky=tk.W)

        ttk.Label(stats_frame, text="Out of Service:").grid(row=1, column=2, padx=5, pady=3, sticky=tk.W)
        self.stats_labels["out_of_service"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["out_of_service"].grid(row=1, column=3, padx=5, pady=3, sticky=tk.W)

        ttk.Label(stats_frame, text="Overdue Returns:").grid(row=1, column=4, padx=5, pady=3, sticky=tk.W)
        self.stats_labels["overdue"] = ttk.Label(stats_frame, text="0", foreground=COLORS["danger"])
        self.stats_labels["overdue"].grid(row=1, column=5, padx=5, pady=3, sticky=tk.W)

    def create_alerts_section(self):
        """Create the section for displaying tool alerts."""
        # Create frame for alerts
        alerts_frame = ttk.LabelFrame(self, text="Recent Activity & Alerts")
        alerts_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create list for alerts
        self.alerts_listbox = tk.Listbox(alerts_frame, height=5, activestyle="none")
        self.alerts_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.alerts_listbox, orient=tk.VERTICAL, command=self.alerts_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.alerts_listbox.configure(yscrollcommand=scrollbar.set)

        # Bind double-click to view details
        self.alerts_listbox.bind("<Double-1>", self.on_alert_double_click)

        # Store alert data
        self.alerts_data = []

    @with_service("tool_service")
    @with_service("tool_checkout_service")
    @with_service("tool_maintenance_service")
    def refresh(self, tool_service=None, tool_checkout_service=None, tool_maintenance_service=None):
        """Refresh the widget with the latest data.

        Args:
            tool_service: The tool service injected by the decorator
            tool_checkout_service: The tool checkout service injected by the decorator
            tool_maintenance_service: The tool maintenance service injected by the decorator
        """
        try:
            # Get tool statistics
            tool_stats = self.get_tool_statistics(tool_service)

            # Update tool count statistics
            self.stats_labels["total_tools"].config(text=str(tool_stats.get("total", 0)))
            self.stats_labels["in_stock"].config(text=str(tool_stats.get("in_stock", 0)))
            self.stats_labels["checked_out"].config(text=str(tool_stats.get("checked_out", 0)))
            self.stats_labels["out_of_service"].config(text=str(tool_stats.get("out_of_service", 0)))

            # Get checkout statistics
            checkout_stats = tool_checkout_service.get_checkout_statistics()

            # Update checkout statistics
            overdue_count = checkout_stats.get("overdue", 0)
            self.stats_labels["overdue"].config(text=str(overdue_count))

            # Set color based on whether there are overdue items
            if overdue_count > 0:
                self.stats_labels["overdue"].config(foreground=COLORS["danger"])
            else:
                self.stats_labels["overdue"].config(foreground=COLORS["success"])

            # Get maintenance statistics
            maintenance_stats = tool_maintenance_service.get_maintenance_statistics()

            # Update maintenance statistics
            self.stats_labels["maintenance_due"].config(text=str(maintenance_stats.get("upcoming", 0) +
                                                                 maintenance_stats.get("overdue", 0)))

            # Combine alerts
            self.update_alerts(tool_service, tool_checkout_service, tool_maintenance_service)

        except Exception as e:
            self.logger.error(f"Error refreshing tool dashboard widget: {e}")

    def get_tool_statistics(self, tool_service):
        """Get tool statistics from the tool service.

        Args:
            tool_service: The tool service

        Returns:
            Dictionary of tool statistics
        """
        try:
            # Get total count
            total = tool_service.count_tools()

            # Get counts by status
            in_stock = tool_service.count_tools(criteria={"status": "IN_STOCK"})
            checked_out = tool_service.count_tools(criteria={"status": "CHECKED_OUT"})
            out_of_service = tool_service.count_tools(
                criteria={"status__in": ["DAMAGED", "LOST", "MAINTENANCE"]}
            )

            return {
                "total": total,
                "in_stock": in_stock,
                "checked_out": checked_out,
                "out_of_service": out_of_service
            }
        except Exception as e:
            self.logger.error(f"Error getting tool statistics: {e}")
            return {
                "total": 0,
                "in_stock": 0,
                "checked_out": 0,
                "out_of_service": 0
            }

    def update_alerts(self, tool_service, tool_checkout_service, tool_maintenance_service):
        """Update alerts list with recent activity and important alerts.

        Args:
            tool_service: The tool service
            tool_checkout_service: The tool checkout service
            tool_maintenance_service: The tool maintenance service
        """
        try:
            # Clear existing alerts
            self.alerts_listbox.delete(0, tk.END)
            self.alerts_data = []

            # Get overdue tools
            checkouts = tool_checkout_service.get_checkouts(
                criteria={"status": "overdue"},
                limit=5,
                include_tool=True
            )

            for checkout in checkouts:
                tool_name = checkout.tool["name"] if checkout.tool else "Unknown Tool"
                self.alerts_listbox.insert(tk.END, f"⚠️ Overdue: {tool_name} - {checkout.checked_out_by}")
                self.alerts_data.append({
                    "type": "checkout",
                    "id": checkout.id,
                    "message": f"Overdue: {tool_name} - {checkout.checked_out_by}"
                })

            # Get maintenance due tools
            now = datetime.now()
            maintenance_records = tool_maintenance_service.get_maintenance_records(
                criteria={
                    "next_maintenance_date__lte": now + timedelta(days=7),
                    "status__not": "completed"
                },
                limit=5,
                include_tool=True
            )

            for record in maintenance_records:
                tool_name = record.tool["name"] if hasattr(record, "tool") and record.tool else "Unknown Tool"
                due_date = record.next_maintenance_date.strftime(
                    "%Y-%m-%d") if record.next_maintenance_date else "Unknown"

                if record.next_maintenance_date and record.next_maintenance_date < now:
                    # Overdue maintenance
                    self.alerts_listbox.insert(tk.END, f"🔧 Maintenance Overdue: {tool_name} (Due: {due_date})")
                else:
                    # Upcoming maintenance
                    self.alerts_listbox.insert(tk.END, f"🔧 Maintenance Due: {tool_name} (Due: {due_date})")

                self.alerts_data.append({
                    "type": "maintenance",
                    "id": record.id,
                    "message": f"Maintenance Due: {tool_name} (Due: {due_date})"
                })

            # Get recently checked out tools
            recent_checkouts = tool_checkout_service.get_checkouts(
                criteria={"status": "checked_out"},
                limit=5,
                sort_by="checked_out_date",
                sort_dir="desc",
                include_tool=True
            )

            for checkout in recent_checkouts:
                tool_name = checkout.tool["name"] if checkout.tool else "Unknown Tool"
                date = checkout.checked_out_date.strftime("%Y-%m-%d") if checkout.checked_out_date else "Unknown"
                self.alerts_listbox.insert(tk.END, f"📤 Checked Out: {tool_name} - {checkout.checked_out_by} ({date})")
                self.alerts_data.append({
                    "type": "checkout",
                    "id": checkout.id,
                    "message": f"Checked Out: {tool_name} - {checkout.checked_out_by} ({date})"
                })

            # Get recently added tools
            recent_tools = tool_service.get_tools(
                limit=5,
                sort_by="created_at",
                sort_dir="desc"
            )

            for tool in recent_tools:
                date = tool.created_at.strftime("%Y-%m-%d") if tool.created_at else "Unknown"
                self.alerts_listbox.insert(tk.END, f"🆕 New Tool: {tool.name} ({date})")
                self.alerts_data.append({
                    "type": "tool",
                    "id": tool.id,
                    "message": f"New Tool: {tool.name} ({date})"
                })

            # Get recently completed maintenance
            completed_maintenance = tool_maintenance_service.get_maintenance_records(
                criteria={"status": "Completed"},
                limit=5,
                sort_by="maintenance_date",
                sort_dir="desc",
                include_tool=True
            )

            for record in completed_maintenance:
                tool_name = record.tool["name"] if hasattr(record, "tool") and record.tool else "Unknown Tool"
                date = record.maintenance_date.strftime("%Y-%m-%d") if record.maintenance_date else "Unknown"
                self.alerts_listbox.insert(tk.END, f"✅ Maintenance Completed: {tool_name} ({date})")
                self.alerts_data.append({
                    "type": "maintenance",
                    "id": record.id,
                    "message": f"Maintenance Completed: {tool_name} ({date})"
                })

        except Exception as e:
            self.logger.error(f"Error updating alerts: {e}")
            self.alerts_listbox.insert(tk.END, "Error loading alerts")

    def on_alert_double_click(self, event):
        """Handle double-click on an alert.

        Args:
            event: The mouse event
        """
        # Get the selected item index
        selection = self.alerts_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if 0 <= index < len(self.alerts_data):
            alert = self.alerts_data[index]

            # Navigate based on alert type
            if alert["type"] == "tool":
                self.navigate_to_tool_details(alert["id"])
            elif alert["type"] == "checkout":
                self.navigate_to_checkout_details(alert["id"])
            elif alert["type"] == "maintenance":
                self.navigate_to_maintenance_details(alert["id"])

    def navigate_to_tool_details(self, tool_id):
        """Navigate to the tool details view.

        Args:
            tool_id: The ID of the tool to view
        """
        if self.navigation_callback:
            self.navigation_callback("tool_detail", {"tool_id": tool_id})
        else:
            # Fallback if no navigation callback is provided
            from gui.views.tools.tool_detail_view import ToolDetailView
            ToolDetailView(self.parent, tool_id=tool_id, readonly=True)

    def navigate_to_checkout_details(self, checkout_id):
        """Navigate to the checkout details view.

        Args:
            checkout_id: The ID of the checkout to view
        """
        if self.navigation_callback:
            self.navigation_callback("tool_checkout", {"checkout_id": checkout_id})
        else:
            # Fallback if no navigation callback is provided
            from gui.views.tools.tool_checkout_view import ToolCheckoutView
            ToolCheckoutView(self.parent)

    def navigate_to_maintenance_details(self, maintenance_id):
        """Navigate to the maintenance details view.

        Args:
            maintenance_id: The ID of the maintenance record to view
        """
        if self.navigation_callback:
            self.navigation_callback("tool_maintenance", {"maintenance_id": maintenance_id})
        else:
            # Fallback if no navigation callback is provided
            from gui.views.tools.tool_maintenance_view import ToolMaintenanceView
            ToolMaintenanceView(self.parent)

    def on_view_all_tools(self):
        """Navigate to the full tool list view."""
        if self.navigation_callback:
            self.navigation_callback("tools")
        else:
            # Fallback if no navigation callback is provided
            from gui.views.tools.tool_list_view import ToolListView
            ToolListView(self.parent)

    def on_view_checkouts(self):
        """Navigate to the tool checkout view."""
        if self.navigation_callback:
            self.navigation_callback("tool_checkouts")
        else:
            # Fallback if no navigation callback is provided
            from gui.views.tools.tool_checkout_view import ToolCheckoutView
            ToolCheckoutView(self.parent)

    def on_view_maintenance(self):
        """Navigate to the tool maintenance view."""
        if self.navigation_callback:
            self.navigation_callback("tool_maintenance")
        else:
            # Fallback if no navigation callback is provided
            from gui.views.tools.tool_maintenance_view import ToolMaintenanceView
            ToolMaintenanceView(self.parent)