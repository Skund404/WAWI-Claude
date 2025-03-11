# gui/views/tools/tool_checkout_view.py
"""
Tool checkout view for managing tool checkouts and returns.

This view provides an interface for checking tools in and out,
tracking who has tools, and managing the checkout/return workflow.
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


class ToolCheckoutView(BaseListView):
    """Tool checkout view for managing tool checkouts and returns."""

    def __init__(self, parent, tool_id=None):
        """Initialize the tool checkout view.

        Args:
            parent: The parent widget
            tool_id: Optional tool ID to filter checkouts for a specific tool
        """
        super().__init__(parent)
        self.tool_id = tool_id
        self.title = "Tool Checkout" if not tool_id else "Tool Checkout History"
        self.icon = "🧰"  # Toolbox icon
        self.logger = logging.getLogger(__name__)
        self.build()

    def build(self):
        """Build the tool checkout view layout."""
        super().build()

        # Update header with appropriate subtitle
        if self.tool_id:
            with self.get_service("tool_service") as service:
                tool = service.get_tool_by_id(self.tool_id)
                if tool:
                    self.header_subtitle.config(text=f"Checkout records for: {tool.name}")
                else:
                    self.header_subtitle.config(text="Checkout records for selected tool")
        else:
            self.header_subtitle.config(text="Manage tool checkouts and returns")

        # Create search fields
        self.search_fields = [
            SearchField("tool_name", "Tool Name", "text"),
            SearchField("status", "Status", "combobox",
                        options=[
                            {"value": "checked_out", "text": "Checked Out"},
                            {"value": "returned", "text": "Returned"},
                            {"value": "overdue", "text": "Overdue"},
                            {"value": "lost", "text": "Lost"},
                            {"value": "damaged", "text": "Damaged"}
                        ]),
            SearchField("checked_out_by", "Checked Out By", "text"),
            SearchField("checked_out_from", "Checked Out From", "date"),
            SearchField("checked_out_to", "Checked Out To", "date"),
            SearchField("due_from", "Due From", "date"),
            SearchField("due_to", "Due To", "date"),
        ]

        # Create search frame
        self.search_frame = SearchFrame(
            self.content_frame,
            title="Search Checkouts",
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
            "id", "tool_name", "checked_out_by", "checked_out_date",
            "due_date", "status", "returned_date", "project"
        )

        # Column widths
        column_widths = {
            "id": 60,
            "tool_name": 200,
            "checked_out_by": 150,
            "checked_out_date": 120,
            "due_date": 120,
            "status": 100,
            "returned_date": 120,
            "project": 150
        }

        # Column headings
        self.column_headings = {
            "id": "ID",
            "tool_name": "Tool",
            "checked_out_by": "User",
            "checked_out_date": "Checked Out",
            "due_date": "Due Date",
            "status": "Status",
            "returned_date": "Returned",
            "project": "Project"
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

        # Add checkout-specific action buttons
        ttk.Button(
            self.header_actions,
            text="Check Out Tool",
            style="Accent.TButton",
            command=self.on_checkout
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.header_actions,
            text="Check In Tool",
            command=self.on_checkin
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.header_actions,
            text="View Overdue",
            command=self.on_view_overdue
        ).pack(side=tk.RIGHT, padx=5)

        # Add back to tool button if we're viewing a specific tool
        if self.tool_id:
            ttk.Button(
                self.header_actions,
                text="Back to Tool",
                command=self.on_back_to_tool
            ).pack(side=tk.RIGHT, padx=5)

    def add_context_menu_items(self, menu):
        """Add checkout-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        super().add_context_menu_items(menu)

        menu.add_separator()
        menu.add_command(label="Check In", command=self.on_checkin_selected)
        menu.add_command(label="Extend Due Date", command=self.on_extend_due_date)
        menu.add_command(label="Report Lost/Damaged", command=self.on_report_problem)
        menu.add_command(label="View Tool", command=self.on_view_tool)

    def add_item_action_buttons(self, parent):
        """Add checkout-specific action buttons.

        Args:
            parent: The parent widget
        """
        super().add_item_action_buttons(parent)

        ttk.Button(
            parent,
            text="Check In",
            command=self.on_checkin_selected
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            parent,
            text="Extend Due Date",
            command=self.on_extend_due_date
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            parent,
            text="Report Problem",
            command=self.on_report_problem
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def create_stats_frame(self, parent):
        """Create a frame for displaying checkout statistics.

        Args:
            parent: The parent widget
        """
        # Create a frame for statistics
        stats_frame = ttk.LabelFrame(parent, text="Checkout Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=5, anchor=tk.W)

        # Create a grid layout for statistics
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        # Add statistics labels
        self.stats_labels = {}

        # Currently checked out
        ttk.Label(stats_frame, text="Currently Checked Out:").grid(
            row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["total_active"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["total_active"].grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        # Overdue
        ttk.Label(stats_frame, text="Overdue Tools:").grid(
            row=0, column=2, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["overdue"] = ttk.Label(stats_frame, text="0", foreground=COLORS["danger"])
        self.stats_labels["overdue"].grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)

        # Checked out today
        ttk.Label(stats_frame, text="Checked Out Today:").grid(
            row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["checkout_count_today"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["checkout_count_today"].grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        # Returned today
        ttk.Label(stats_frame, text="Returned Today:").grid(
            row=1, column=2, padx=10, pady=5, sticky=tk.W)
        self.stats_labels["return_count_today"] = ttk.Label(stats_frame, text="0")
        self.stats_labels["return_count_today"].grid(row=1, column=3, padx=10, pady=5, sticky=tk.W)

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

    @with_service("tool_checkout_service")
    def get_total_count(self, service=None):
        """Get the total count of checkout records.

        Args:
            service: The tool checkout service injected by the decorator

        Returns:
            The total count of checkout records
        """
        criteria = self.search_criteria if hasattr(self, 'search_criteria') else {}

        # If tool_id is provided, filter by tool
        if self.tool_id and "tool_id" not in criteria:
            criteria["tool_id"] = self.tool_id

        try:
            return service.count_checkouts(criteria)
        except Exception as e:
            self.logger.error(f"Error counting checkout records: {e}")
            return 0

    @with_service("tool_checkout_service")
    def get_items(self, service, offset, limit):
        """Get checkout records for the current page.

        Args:
            service: The tool checkout service injected by the decorator
            offset: Pagination offset
            limit: Page size

        Returns:
            List of checkout records
        """
        criteria = self.search_criteria if hasattr(self, 'search_criteria') else {}
        sort_field = self.sort_column if hasattr(self, 'sort_column') else "checked_out_date"
        sort_dir = self.sort_direction if hasattr(self, 'sort_direction') else "desc"

        # If tool_id is provided, filter by tool
        if self.tool_id and "tool_id" not in criteria:
            criteria["tool_id"] = self.tool_id

        try:
            return service.get_checkouts(
                criteria=criteria,
                offset=offset,
                limit=limit,
                sort_by=sort_field,
                sort_dir=sort_dir,
                include_tool=True,
                include_project=True
            )
        except Exception as e:
            self.logger.error(f"Error getting checkout records: {e}")
            return []

    def extract_item_values(self, item):
        """Extract values from a checkout record for display in the treeview.

        Args:
            item: The checkout record to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Format dates
        checked_out_date = item.checked_out_date.strftime("%Y-%m-%d") if item.checked_out_date else "N/A"
        due_date = item.due_date.strftime("%Y-%m-%d") if item.due_date else ""
        returned_date = item.returned_date.strftime("%Y-%m-%d") if item.returned_date else ""

        # Get tool name
        tool_name = item.tool["name"] if hasattr(item, "tool") and item.tool else "Unknown Tool"

        # Get project name
        project_name = item.project["name"] if hasattr(item, "project") and item.project else ""

        # Format status for display
        status_display = {
            "checked_out": "Checked Out",
            "returned": "Returned",
            "overdue": "Overdue",
            "lost": "Lost",
            "damaged": "Damaged"
        }
        status = status_display.get(item.status, item.status)

        # Return values in order of columns
        return [
            item.id,
            tool_name,
            item.checked_out_by,
            checked_out_date,
            due_date,
            status,
            returned_date,
            project_name
        ]

    @with_service("tool_checkout_service")
    def update_stats(self, service=None):
        """Update the checkout statistics display.

        Args:
            service: The tool checkout service injected by the decorator
        """
        try:
            # Get statistics from the service
            stats = service.get_checkout_statistics()

            # Update the statistics display
            self.stats_labels["total_active"].config(text=str(stats.get("total_active", 0)))
            self.stats_labels["overdue"].config(text=str(stats.get("overdue", 0)))
            self.stats_labels["checkout_count_today"].config(text=str(stats.get("checkout_count_today", 0)))
            self.stats_labels["return_count_today"].config(text=str(stats.get("return_count_today", 0)))

            # Highlight overdue count in red if there are any
            if stats.get("overdue", 0) > 0:
                self.stats_labels["overdue"].config(foreground=COLORS["danger"])
            else:
                self.stats_labels["overdue"].config(foreground=COLORS["success"])

        except Exception as e:
            self.logger.error(f"Error updating checkout statistics: {e}")

    def refresh(self):
        """Refresh the checkout records and statistics."""
        super().refresh()
        self.update_stats()

    def on_checkout(self):
        """Handle checking out a tool."""
        self.logger.info("Opening check out tool dialog")

        # Open dialog to check out a tool
        from gui.views.tools.tool_checkout_dialog import ToolCheckoutDialog
        dialog = ToolCheckoutDialog(self.parent, tool_id=self.tool_id)

        if dialog.result:
            self.refresh()

    def on_checkin(self):
        """Handle checking in a tool."""
        self.logger.info("Opening check in tool dialog")

        # Open dialog to check in a tool
        from gui.views.tools.tool_checkin_dialog import ToolCheckinDialog
        dialog = ToolCheckinDialog(self.parent)

        if dialog.result:
            self.refresh()

    def on_checkin_selected(self):
        """Handle checking in the selected tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a checkout record to check in")
            return

        self.logger.info(f"Checking in checkout record ID: {selected_id}")

        # Open dialog to check in the selected checkout
        from gui.views.tools.tool_checkin_dialog import ToolCheckinDialog
        dialog = ToolCheckinDialog(self.parent, checkout_id=selected_id)

        if dialog.result:
            self.refresh()

    def on_extend_due_date(self):
        """Handle extending the due date for a checked out tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a checkout record to extend")
            return

        # Get the selected checkout record
        with self.get_service("tool_checkout_service") as service:
            try:
                checkout = service.get_checkout_by_id(selected_id)

                # Check if the tool is already returned
                if checkout.status == "returned":
                    messagebox.showwarning("Already Returned", "This tool has already been returned")
                    return

                # Show a date picker dialog to select the new due date
                from tkcalendar import DateEntry

                # Create a top-level window for the date picker
                top = tk.Toplevel(self.parent)
                top.title("Extend Due Date")
                top.transient(self.parent)
                top.grab_set()

                # Center the dialog
                top.geometry(f"+{self.parent.winfo_rootx() + 50}+{self.parent.winfo_rooty() + 50}")

                # Create a frame for the content
                frame = ttk.Frame(top)
                frame.pack(padx=20, pady=10)

                # Show the current due date
                current_due = "None" if not checkout.due_date else checkout.due_date.strftime("%Y-%m-%d")
                ttk.Label(frame, text=f"Current Due Date: {current_due}").pack(pady=5)

                # Create the date entry widget
                ttk.Label(frame, text="New Due Date:").pack(pady=5)

                # Default to current due date + 7 days, or today + 7 days if no current due date
                default_date = datetime.now() + timedelta(days=7)
                if checkout.due_date:
                    default_date = checkout.due_date + timedelta(days=7)

                cal = DateEntry(frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2,
                                year=default_date.year, month=default_date.month, day=default_date.day)
                cal.pack(pady=5)

                # Function to update the due date
                def update_due_date():
                    try:
                        new_due_date = cal.get_date()

                        # Update the checkout record
                        service.update_checkout_record(selected_id, {"due_date": new_due_date})

                        messagebox.showinfo("Success", "Due date extended successfully")
                        self.refresh()
                        top.destroy()
                    except Exception as e:
                        self.logger.error(f"Error extending due date: {e}")
                        messagebox.showerror("Error", f"Failed to extend due date: {str(e)}")

                # Add buttons
                button_frame = ttk.Frame(frame)
                button_frame.pack(pady=10)

                ttk.Button(button_frame, text="Cancel", command=top.destroy).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Update", command=update_due_date).pack(side=tk.RIGHT, padx=5)

            except Exception as e:
                self.logger.error(f"Error extending due date: {e}")
                messagebox.showerror("Error", f"Failed to extend due date: {str(e)}")

    def on_report_problem(self):
        """Handle reporting a problem with a checked out tool."""
        selected_id = self.treeview.get_selected_id()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a checkout record to report a problem")
            return

        # Get the selected checkout record
        with self.get_service("tool_checkout_service") as service:
            try:
                checkout = service.get_checkout_by_id(selected_id, include_tool=True)

                # Check if the tool is already returned
                if checkout.status == "returned":
                    messagebox.showwarning("Already Returned", "This tool has already been returned")
                    return

                # Show a dialog to report the problem
                top = tk.Toplevel(self.parent)
                top.title("Report Tool Problem")
                top.transient(self.parent)
                top.grab_set()

                # Center the dialog
                top.geometry(f"+{self.parent.winfo_rootx() + 50}+{self.parent.winfo_rooty() + 50}")

                # Create a frame for the content
                frame = ttk.Frame(top)
                frame.pack(padx=20, pady=10)

                # Show the tool information
                tool_name = checkout.tool["name"] if checkout.tool else "Unknown Tool"
                ttk.Label(frame, text=f"Tool: {tool_name}").pack(pady=5)
                ttk.Label(frame, text=f"Checked Out By: {checkout.checked_out_by}").pack(pady=5)

                # Problem type selection
                ttk.Label(frame, text="Problem Type:").pack(pady=5)

                problem_type = tk.StringVar(value="damaged")

                problem_frame = ttk.Frame(frame)
                problem_frame.pack(fill=tk.X, pady=5)

                ttk.Radiobutton(problem_frame, text="Damaged", value="damaged",
                                variable=problem_type).pack(side=tk.LEFT, padx=10)
                ttk.Radiobutton(problem_frame, text="Lost", value="lost",
                                variable=problem_type).pack(side=tk.LEFT, padx=10)

                # Notes
                ttk.Label(frame, text="Notes:").pack(pady=5)

                notes_text = tk.Text(frame, height=5, width=40)
                notes_text.pack(fill=tk.X, pady=5)

                # Function to report the problem
                def report_problem():
                    try:
                        notes = notes_text.get("1.0", tk.END).strip()

                        if not notes:
                            messagebox.showwarning("Missing Information", "Please enter notes about the problem")
                            return

                        # Report the problem
                        service.report_tool_problem(selected_id, problem_type.get(), notes)

                        messagebox.showinfo("Success", "Problem reported successfully")
                        self.refresh()
                        top.destroy()
                    except Exception as e:
                        self.logger.error(f"Error reporting problem: {e}")
                        messagebox.showerror("Error", f"Failed to report problem: {str(e)}")

                # Add buttons
                button_frame = ttk.Frame(frame)
                button_frame.pack(pady=10)

                ttk.Button(button_frame, text="Cancel", command=top.destroy).pack(side=tk.RIGHT, padx=5)
                ttk.Button(button_frame, text="Report", command=report_problem).pack(side=tk.RIGHT, padx=5)

            except Exception as e:
                self.logger.error(f"Error reporting problem: {e}")
                messagebox.showerror("Error", f"Failed to report problem: {str(e)}")

    def on_view_tool(self):
        """View the tool associated with the selected checkout record."""
        selected_values = self.treeview.get_selected_item_values()
        if not selected_values:
            messagebox.showwarning("No Selection", "Please select a checkout record to view the associated tool")
            return

        # Get the tool ID from the checkout record
        try:
            with self.get_service("tool_checkout_service") as service:
                checkout = service.get_checkout_by_id(selected_values[0], include_tool=True)

                if checkout and checkout.tool:
                    # Open the tool detail view
                    from gui.views.tools.tool_detail_view import ToolDetailView
                    view = ToolDetailView(self.parent, tool_id=checkout.tool_id, readonly=True)
                else:
                    messagebox.showwarning("Tool Not Found",
                                           "The tool associated with this checkout record could not be found")
        except Exception as e:
            self.logger.error(f"Error viewing tool: {e}")
            messagebox.showerror("Error", f"Failed to view tool: {str(e)}")

    def on_view_overdue(self):
        """Filter the view to show only overdue tools."""
        self.search_criteria = {"status": "overdue"}
        self.refresh()

        # Update the search frame to show the filter
        self.search_frame.set_field_value("status", "overdue")

    def on_back_to_tool(self):
        """Navigate back to the tool detail view."""
        if not self.tool_id:
            return

        # Open the tool detail view
        from gui.views.tools.tool_detail_view import ToolDetailView
        view = ToolDetailView(self.parent, tool_id=self.tool_id, readonly=True)

        # Close this view
        self.destroy()