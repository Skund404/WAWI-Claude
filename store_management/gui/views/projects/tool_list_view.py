# gui/views/projects/tool_list_view.py
"""
Tool list view for managing tool requirements for projects.

This view provides an interface for creating, viewing, and processing
tool lists for tracking tools needed for a project.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import ToolListStatus, ToolCategory
from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge


class ToolListView(BaseView):
    """
    View for displaying and managing tool lists for projects.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the tool list view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                tool_list_id: ID of the tool list to view/edit
                project_id: ID of the project (to create a new tool list)
                readonly: Whether the view should be read-only
        """
        super().__init__(parent)
        self.title = "Tool List"
        self.icon = "🔧"
        self.logger = logging.getLogger(__name__)

        # Store view parameters
        self.tool_list_id = kwargs.get("tool_list_id")
        self.project_id = kwargs.get("project_id")
        self.readonly = kwargs.get("readonly", False)

        if not self.tool_list_id and not self.project_id:
            messagebox.showerror("Error", "Either a tool list ID or project ID is required")
            self.on_back()
            return

        # Initialize services
        self.project_service = get_service("project_service")
        self.tool_list_service = get_service("tool_list_service")
        self.tool_service = get_service("tool_service")

        # Build the view
        self.build()

        # Load data if viewing an existing tool list
        if self.tool_list_id:
            self.load_tool_list()
        elif self.project_id:
            # Create new tool list for the project
            self.create_new_tool_list()

    def build(self):
        """Build the tool list view."""
        super().build()

        # Create main frame
        main_frame = ttk.Frame(self.content_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create info section and item list
        self.create_info_section(main_frame)
        self.create_tool_list(main_frame)
        self.create_actions_section(main_frame)

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        actions_frame = ttk.Frame(self.header)
        actions_frame.pack(side=tk.RIGHT, padx=10)

        if not self.readonly:
            ttk.Button(
                actions_frame,
                text="Save",
                command=self.on_save
            ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Back",
            command=self.on_back
        ).pack(side=tk.RIGHT, padx=5)

        # Add print button
        ttk.Button(
            actions_frame,
            text="Print",
            command=self.on_print
        ).pack(side=tk.RIGHT, padx=5)

    def create_info_section(self, parent):
        """Create the info section with tool list details.

        Args:
            parent: The parent widget
        """
        info_frame = ttk.LabelFrame(parent, text="Tool List Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # Left column with basic info
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Right column with status and assignments
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left column content
        ttk.Label(left_frame, text="Tool List ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.id_label = ttk.Label(left_frame, text="New")
        self.id_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Project:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.project_label = ttk.Label(left_frame, text="")
        self.project_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Created:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.created_label = ttk.Label(left_frame, text="")
        self.created_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Return By:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.return_date_var = tk.StringVar()

        return_date_frame = ttk.Frame(left_frame)
        return_date_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        self.return_date_entry = ttk.Entry(return_date_frame, textvariable=self.return_date_var, width=12)
        self.return_date_entry.pack(side=tk.LEFT)

        if not self.readonly:
            ttk.Button(
                return_date_frame,
                text="...",
                width=2,
                command=lambda: self.show_date_picker(self.return_date_var)
            ).pack(side=tk.LEFT, padx=(5, 0))

        # Right column content
        ttk.Label(right_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        status_frame = ttk.Frame(right_frame)
        status_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        self.status_var = tk.StringVar(value="draft")

        # Only show status combobox if not readonly
        if not self.readonly:
            self.status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, width=15, state="readonly")
            status_values = [s.value.replace("_", " ").title() for s in ToolListStatus]
            self.status_combo["values"] = status_values
            self.status_combo.pack(side=tk.LEFT)
            self.status_combo.bind("<<ComboboxSelected>>", self.on_status_change)

        self.status_badge = StatusBadge(status_frame, "Draft", "draft")
        self.status_badge.pack(side=tk.LEFT, padx=(10 if not self.readonly else 0, 0))

        # Tool keeper
        ttk.Label(right_frame, text="Tool Keeper:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.keeper_var = tk.StringVar()
        self.keeper_entry = ttk.Entry(right_frame, textvariable=self.keeper_var, width=20)
        self.keeper_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.keeper_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

        # Notes
        ttk.Label(right_frame, text="Notes:").grid(row=2, column=0, sticky=tk.NW, padx=5, pady=2)
        self.notes_text = tk.Text(right_frame, width=25, height=3)
        self.notes_text.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.notes_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)

        # Tool location
        ttk.Label(right_frame, text="Tool Location:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(right_frame, textvariable=self.location_var, width=20)
        self.location_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        self.location_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

    def create_tool_list(self, parent):
        """Create the tool list section.

        Args:
            parent: The parent widget
        """
        tools_frame = ttk.LabelFrame(parent, text="Tools Required")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create toolbar for the tool list
        toolbar = ttk.Frame(tools_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        if not self.readonly:
            ttk.Button(
                toolbar,
                text="Add Tool",
                command=self.on_add_tool
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                toolbar,
                text="Remove Tool",
                command=self.on_remove_tool
            ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar,
            text="Check Availability",
            command=self.on_check_availability
        ).pack(side=tk.LEFT, padx=5)

        # Filter options
        ttk.Label(toolbar, text="Category:").pack(side=tk.RIGHT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(toolbar, textvariable=self.filter_var, width=15, state="readonly")

        tool_categories = ["All"] + [c.value.replace("_", " ").title() for c in ToolCategory]
        filter_combo["values"] = tool_categories
        filter_combo.pack(side=tk.RIGHT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        # Create treeview for tools
        columns = (
            "id", "tool", "category", "quantity", "checked_out",
            "returned", "checked_out_by", "condition", "notes"
        )

        self.tools_tree = ttk.Treeview(tools_frame, columns=columns, show="headings", height=10)

        self.tools_tree.heading("id", text="ID")
        self.tools_tree.heading("tool", text="Tool")
        self.tools_tree.heading("category", text="Category")
        self.tools_tree.heading("quantity", text="Quantity")
        self.tools_tree.heading("checked_out", text="Checked Out")
        self.tools_tree.heading("returned", text="Returned")
        self.tools_tree.heading("checked_out_by", text="Checked Out By")
        self.tools_tree.heading("condition", text="Condition")
        self.tools_tree.heading("notes", text="Notes")

        self.tools_tree.column("id", width=50, minwidth=50)
        self.tools_tree.column("tool", width=200, minwidth=150)
        self.tools_tree.column("category", width=100, minwidth=100)
        self.tools_tree.column("quantity", width=80, minwidth=80)
        self.tools_tree.column("checked_out", width=100, minwidth=80)
        self.tools_tree.column("returned", width=80, minwidth=80)
        self.tools_tree.column("checked_out_by", width=120, minwidth=100)
        self.tools_tree.column("condition", width=100, minwidth=80)
        self.tools_tree.column("notes", width=150, minwidth=100)

        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(tools_frame, orient=tk.VERTICAL, command=self.tools_tree.yview)
        self.tools_tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.tools_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)

        # Bind double click to edit checkout status
        self.tools_tree.bind("<Double-1>", self.on_edit_tool)

    def create_actions_section(self, parent):
        """Create the actions section.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        # Create action buttons based on status
        if not self.readonly:
            self.checkout_btn = ttk.Button(
                actions_frame,
                text="Checkout Tools",
                command=self.on_checkout_tools
            )
            self.checkout_btn.pack(side=tk.LEFT, padx=5)

            self.return_btn = ttk.Button(
                actions_frame,
                text="Return Tools",
                command=self.on_return_tools,
                state=tk.DISABLED
            )
            self.return_btn.pack(side=tk.LEFT, padx=5)

            self.cancel_btn = ttk.Button(
                actions_frame,
                text="Cancel Tool List",
                command=self.on_cancel_tool_list
            )
            self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Summary section
        summary_frame = ttk.LabelFrame(parent, text="Summary")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=10, pady=5)

        # Tool counts
        ttk.Label(summary_grid, text="Total Tools:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_tools_label = ttk.Label(summary_grid, text="0")
        self.total_tools_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Checked Out:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.checked_out_label = ttk.Label(summary_grid, text="0")
        self.checked_out_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Returned:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.returned_label = ttk.Label(summary_grid, text="0")
        self.returned_label.grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Unavailable:").grid(row=0, column=6, sticky=tk.W, padx=5, pady=2)
        self.unavailable_label = ttk.Label(summary_grid, text="0")
        self.unavailable_label.grid(row=0, column=7, sticky=tk.W, padx=5, pady=2)

    def load_tool_list(self):
        """Load tool list data from the service."""
        try:
            # Get tool list data from service
            tool_list = self.tool_list_service.get_tool_list(
                self.tool_list_id,
                include_items=True,
                include_project=True
            )

            if not tool_list:
                messagebox.showerror("Error", f"Tool list not found with ID {self.tool_list_id}")
                self.on_back()
                return

            # Update title
            self.title = f"Tool List #{tool_list.id}" + (" (View Only)" if self.readonly else "")
            title_label = self.header.winfo_children()[0]
            if isinstance(title_label, ttk.Label):
                title_label.configure(text=self.title)

            # Update project ID
            self.project_id = tool_list.project_id if hasattr(tool_list, 'project_id') else None

            # Populate info section
            self.id_label.configure(text=str(tool_list.id))

            # Project info
            project_name = "Unknown Project"
            if hasattr(tool_list, 'project') and tool_list.project:
                project = tool_list.project
                project_name = project.name if hasattr(project, 'name') else "Unknown Project"
            self.project_label.configure(text=project_name)

            # Creation date
            created_at = "N/A"
            if hasattr(tool_list, 'created_at') and tool_list.created_at:
                created_at = tool_list.created_at.strftime("%Y-%m-%d %H:%M")
            self.created_label.configure(text=created_at)

            # Return date
            if hasattr(tool_list, 'return_date') and tool_list.return_date:
                self.return_date_var.set(tool_list.return_date.strftime("%Y-%m-%d"))

            # Status
            status_value = "draft"
            if hasattr(tool_list, 'status') and tool_list.status:
                status_value = tool_list.status.value
                status_display = tool_list.status.value.replace("_", " ").title()

                # Update status variable
                self.status_var.set(status_value)

                # Update status badge
                self.status_badge.set_text(status_display, status_value)

            # Tool keeper
            if hasattr(tool_list, 'keeper') and tool_list.keeper:
                self.keeper_var.set(tool_list.keeper)

            # Notes
            if hasattr(tool_list, 'notes') and tool_list.notes:
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", tool_list.notes)

            # Tool location
            if hasattr(tool_list, 'location') and tool_list.location:
                self.location_var.set(tool_list.location)

            # Populate tools
            if hasattr(tool_list, 'items') and tool_list.items:
                self.update_tools_list(tool_list.items)

            # Update action buttons based on status
            self.update_action_buttons(status_value)

        except Exception as e:
            self.logger.error(f"Error loading tool list: {e}")
            messagebox.showerror("Error", f"Failed to load tool list: {str(e)}")

    def create_new_tool_list(self):
        """Create a new tool list for the project."""
        try:
            # Create new tool list
            tool_list = self.tool_list_service.create_tool_list(self.project_id)

            # Update ID
            self.tool_list_id = tool_list.id

            # Load the newly created tool list
            self.load_tool_list()

        except Exception as e:
            self.logger.error(f"Error creating tool list: {e}")
            messagebox.showerror("Error", f"Failed to create tool list: {str(e)}")
            self.on_back()

    def update_tools_list(self, tools):
        """Update the tools list in the treeview.

        Args:
            tools: List of tool list items
        """
        # Clear existing items
        for item in self.tools_tree.get_children():
            self.tools_tree.delete(item)

        # Insert tools
        total_count = 0
        checked_out_count = 0
        returned_count = 0
        unavailable_count = 0

        for tool in tools:
            # Skip if filtered out
            if not self.should_show_tool(tool):
                continue

            # Extract tool values
            item_id = tool.id if hasattr(tool, 'id') else "N/A"

            tool_name = "Unknown Tool"
            if hasattr(tool, 'tool') and tool.tool:
                tool_name = tool.tool.name if hasattr(tool.tool, 'name') else "Unknown Tool"

            tool_category = "Unknown"
            if hasattr(tool, 'tool') and tool.tool and hasattr(tool.tool, 'category') and tool.tool.category:
                tool_category = tool.tool.category.value.replace("_", " ").title()

            quantity = tool.quantity if hasattr(tool, 'quantity') else 1
            checked_out = tool.checked_out if hasattr(tool, 'checked_out') else 0
            returned = tool.returned if hasattr(tool, 'returned') else 0

            checked_out_by = tool.checked_out_by if hasattr(tool, 'checked_out_by') else ""
            condition = tool.condition if hasattr(tool, 'condition') else "Good"
            notes = tool.notes if hasattr(tool, 'notes') else ""

            # Update counts
            if checked_out > 0:
                checked_out_count += 1
            if returned >= checked_out:
                returned_count += 1
            if hasattr(tool, 'available') and not tool.available:
                unavailable_count += 1

            # Insert into treeview
            item_id_str = str(item_id)
            self.tools_tree.insert(
                '', 'end',
                iid=item_id_str,
                values=(
                    item_id,
                    tool_name,
                    tool_category,
                    quantity,
                    checked_out,
                    returned,
                    checked_out_by,
                    condition,
                    notes
                )
            )

            # Apply status styling
            if returned >= checked_out and checked_out > 0:
                self.tools_tree.tag_configure("returned", background=COLORS["success_light"])
                self.tools_tree.item(item_id_str, tags=("returned",))
            elif checked_out > 0:
                self.tools_tree.tag_configure("checked_out", background=COLORS["warning_light"])
                self.tools_tree.item(item_id_str, tags=("checked_out",))
            elif hasattr(tool, 'available') and not tool.available:
                self.tools_tree.tag_configure("unavailable", background=COLORS["error_light"])
                self.tools_tree.item(item_id_str, tags=("unavailable",))

            total_count += 1

        # Update summary
        self.total_tools_label.configure(text=str(total_count))
        self.checked_out_label.configure(text=str(checked_out_count))
        self.returned_label.configure(text=str(returned_count))
        self.unavailable_label.configure(text=str(unavailable_count))

    def should_show_tool(self, tool):
        """Check if a tool should be shown based on the current filter.

        Args:
            tool: The tool to check

        Returns:
            True if the tool should be shown, False otherwise
        """
        filter_value = self.filter_var.get()

        if filter_value == "All":
            return True

        # Check tool category
        tool_category = "Unknown"
        if hasattr(tool, 'tool') and tool.tool and hasattr(tool.tool, 'category') and tool.tool.category:
            tool_category = tool.tool.category.value.replace("_", " ").title()

        return tool_category == filter_value

    def update_action_buttons(self, status):
        """Update action buttons based on the current status.

        Args:
            status: Current tool list status
        """
        if self.readonly:
            return

        # Enable/disable buttons based on status
        if status == "draft":
            self.checkout_btn.configure(state=tk.NORMAL)
            self.return_btn.configure(state=tk.DISABLED)
            self.cancel_btn.configure(state=tk.NORMAL)
        elif status == "in_progress":
            self.checkout_btn.configure(state=tk.DISABLED)
            self.return_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.NORMAL)
        elif status == "in_use":
            self.checkout_btn.configure(state=tk.DISABLED)
            self.return_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.NORMAL)
        elif status in ["completed", "cancelled"]:
            self.checkout_btn.configure(state=tk.DISABLED)
            self.return_btn.configure(state=tk.DISABLED)
            self.cancel_btn.configure(state=tk.DISABLED)
        else:
            self.checkout_btn.configure(state=tk.NORMAL)
            self.return_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.NORMAL)

    def on_status_change(self, event):
        """Handle status change from combobox.

        Args:
            event: Combobox selection event
        """
        status_value = self.status_var.get().lower().replace(" ", "_")
        status_display = self.status_var.get()

        # Update status badge
        self.status_badge.set_text(status_display, status_value)

        # Update action buttons
        self.update_action_buttons(status_value)

    def on_filter_change(self, event):
        """Handle filter change.

        Args:
            event: Combobox selection event
        """
        # Reload tool list with new filter
        self.load_tool_list()

    def on_add_tool(self):
        """Handle add tool button click."""
        # Create add tool dialog
        dialog = tk.Toplevel(self)
        dialog.title("Add Tool to Tool List")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        # Create search frame
        search_frame = ttk.Frame(dialog, padding=5)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Tool category filter
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=(10, 5))
        category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(search_frame, textvariable=category_var, width=15, state="readonly")

        tool_categories = ["All"] + [c.value.replace("_", " ").title() for c in ToolCategory]
        category_combo["values"] = tool_categories
        category_combo.pack(side=tk.LEFT, padx=5)

        def search_tools():
            """Search tools based on criteria."""
            search_text = search_var.get()
            tool_category = None
            if category_var.get() != "All":
                tool_category = category_var.get().lower().replace(" ", "_")

            try:
                # Get tools from service
                tools = self.tool_service.search_tools(
                    search_text=search_text,
                    category=tool_category
                )

                # Clear existing items
                for item in tools_tree.get_children():
                    tools_tree.delete(item)

                # Insert tools
                for tool in tools:
                    tool_id = tool.id if hasattr(tool, 'id') else "N/A"
                    name = tool.name if hasattr(tool, 'name') else "Unnamed"

                    category = "Unknown"
                    if hasattr(tool, 'category') and tool.category:
                        category = tool.category.value.replace("_", " ").title()

                    # Get inventory status
                    availability = "Unknown"
                    if hasattr(tool, 'inventory') and tool.inventory:
                        inventory = tool.inventory
                        if hasattr(inventory, 'status') and inventory.status:
                            if inventory.status.value == "in_use":
                                availability = "In Use"
                            elif inventory.status.value == "available":
                                availability = "Available"
                            else:
                                availability = inventory.status.value.replace("_", " ").title()

                    description = tool.description if hasattr(tool, 'description') else ""

                    tools_tree.insert(
                        '', 'end',
                        iid=tool_id,
                        values=(tool_id, name, category, availability, description)
                    )

            except Exception as e:
                self.logger.error(f"Error searching tools: {e}")
                messagebox.showerror("Search Error", f"Failed to search tools: {str(e)}", parent=dialog)

        ttk.Button(
            search_frame,
            text="Search",
            command=search_tools
        ).pack(side=tk.LEFT, padx=5)

        # Create tools treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "category", "availability", "description")
        tools_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        tools_tree.heading("id", text="ID")
        tools_tree.heading("name", text="Name")
        tools_tree.heading("category", text="Category")
        tools_tree.heading("availability", text="Availability")
        tools_tree.heading("description", text="Description")

        tools_tree.column("id", width=50)
        tools_tree.column("name", width=200)
        tools_tree.column("category", width=100)
        tools_tree.column("availability", width=100)
        tools_tree.column("description", width=250)

        tools_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tools_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tools_tree.configure(yscrollcommand=scrollbar.set)

        # Quantity frame
        quantity_frame = ttk.LabelFrame(dialog, text="Details")
        quantity_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(quantity_frame, text="Quantity:").grid(row=0, column=0, padx=5, pady=5)
        quantity_var = tk.StringVar(value="1")
        quantity_spin = ttk.Spinbox(quantity_frame, from_=1, to=100, textvariable=quantity_var)
        quantity_spin.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(quantity_frame, text="Notes:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)
        notes_text = tk.Text(quantity_frame, width=30, height=3)
        notes_text.grid(row=1, column=1, padx=5, pady=5)

        # Handle tool selection
        def add_selected_tool():
            """Add the selected tool to the tool list."""
            selected_id = tools_tree.focus()
            if not selected_id:
                messagebox.showwarning("No Selection", "Please select a tool to add.", parent=dialog)
                return

            # Get tool data
            tool_data = tools_tree.item(selected_id, "values")
            tool_id = tool_data[0]
            tool_name = tool_data[1]

            # Check if already added
            items = self.tools_tree.get_children()
            for item_id in items:
                item_values = self.tools_tree.item(item_id, "values")
                if item_values[1] == tool_name:
                    messagebox.showwarning(
                        "Already Added",
                        f"Tool '{tool_name}' is already in this tool list.",
                        parent=dialog
                    )
                    return

            # Get quantity
            try:
                quantity = int(quantity_var.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than zero.", parent=dialog)
                    return
            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a number.", parent=dialog)
                return

            # Get notes
            notes = notes_text.get("1.0", tk.END).strip()

            try:
                # Add tool to tool list
                result = self.tool_list_service.add_tool_to_list(
                    self.tool_list_id,
                    tool_id,
                    quantity,
                    notes
                )

                if result:
                    # Reload tool list
                    self.load_tool_list()

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    messagebox.showinfo("Success", f"Tool '{tool_name}' added to tool list.")

            except Exception as e:
                self.logger.error(f"Error adding tool: {e}")
                messagebox.showerror("Error", f"Failed to add tool: {str(e)}", parent=dialog)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Add Tool",
            command=add_selected_tool
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Initial search
        search_tools()

        # Set focus to search entry
        search_entry.focus_set()

    def on_edit_tool(self, event):
        """Handle tool double-click to edit checkout/return status.

        Args:
            event: Double-click event
        """
        if self.readonly:
            return

        # Get the item
        region = self.tools_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Get the clicked item and column
        item_id = self.tools_tree.identify_row(event.y)
        column = self.tools_tree.identify_column(event.x)

        # Only allow editing certain columns
        if column not in ["#5", "#6", "#7", "#8"]:  # checked_out, returned, checked_out_by, condition
            return

        # Get current values
        values = self.tools_tree.item(item_id, "values")
        tool_name = values[1]
        quantity = int(values[3])
        checked_out = int(values[4]) if values[4] else 0
        returned = int(values[5]) if values[5] else 0
        checked_out_by = values[6]
        condition = values[7]

        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Update Tool Status: {tool_name}")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Create form
        ttk.Label(dialog, text="Tool:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=tool_name).grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Total Quantity:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=str(quantity)).grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Checked Out:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        checked_out_var = tk.StringVar(value=str(checked_out))
        checked_out_spin = ttk.Spinbox(
            dialog,
            from_=0,
            to=quantity,
            textvariable=checked_out_var
        )
        checked_out_spin.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Returned:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        returned_var = tk.StringVar(value=str(returned))
        returned_spin = ttk.Spinbox(
            dialog,
            from_=0,
            to=quantity,
            textvariable=returned_var
        )
        returned_spin.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Checked Out By:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        checked_out_by_var = tk.StringVar(value=checked_out_by)
        checked_out_by_entry = ttk.Entry(dialog, textvariable=checked_out_by_var, width=20)
        checked_out_by_entry.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Condition:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        condition_var = tk.StringVar(value=condition)
        condition_combo = ttk.Combobox(dialog, textvariable=condition_var, width=18, state="readonly")
        condition_combo["values"] = ["Excellent", "Good", "Fair", "Poor", "Damaged"]
        condition_combo.grid(row=5, column=1, padx=10, pady=5, sticky=tk.W)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)

        def update_tool_status():
            """Update the tool status."""
            try:
                checked_out_val = int(checked_out_var.get())
                returned_val = int(returned_var.get())

                if checked_out_val < 0 or checked_out_val > quantity:
                    messagebox.showwarning("Invalid Value", f"Checked out must be between 0 and {quantity}.",
                                           parent=dialog)
                    return

                if returned_val < 0 or returned_val > checked_out_val:
                    messagebox.showwarning("Invalid Value", f"Returned must be between 0 and {checked_out_val}.",
                                           parent=dialog)
                    return

                # Update the tool in the service
                result = self.tool_list_service.update_tool_status(
                    self.tool_list_id,
                    int(item_id),
                    {
                        "checked_out": checked_out_val,
                        "returned": returned_val,
                        "checked_out_by": checked_out_by_var.get(),
                        "condition": condition_var.get()
                    }
                )

                if result:
                    # Reload tool list
                    self.load_tool_list()

                    # Close dialog
                    dialog.destroy()

            except ValueError:
                messagebox.showwarning("Invalid Value", "Quantity values must be numbers.", parent=dialog)
            except Exception as e:
                self.logger.error(f"Error updating tool status: {e}")
                messagebox.showerror("Error", f"Failed to update tool status: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Update",
            command=update_tool_status
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Set focus to checked_out spinner
        checked_out_spin.focus_set()

    def on_remove_tool(self):
        """Handle remove tool button click."""
        selected_id = self.tools_tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a tool to remove.")
            return

        # Get tool name
        values = self.tools_tree.item(selected_id, "values")
        tool_name = values[1]

        # Check if tool is checked out
        checked_out = int(values[4]) if values[4] else 0
        returned = int(values[5]) if values[5] else 0

        if checked_out > 0 and returned < checked_out:
            if not messagebox.askyesno(
                    "Warning",
                    f"Tool '{tool_name}' is currently checked out. Are you sure you want to remove it?"
            ):
                return

        # Confirm removal
        if not messagebox.askyesno(
                "Confirm Remove",
                f"Are you sure you want to remove {tool_name} from the tool list?"
        ):
            return

        try:
            # Remove tool from tool list
            result = self.tool_list_service.remove_tool_from_list(
                self.tool_list_id,
                int(selected_id)
            )

            if result:
                # Reload tool list
                self.load_tool_list()

                # Show success message
                messagebox.showinfo("Success", f"Tool '{tool_name}' has been removed from the tool list.")

        except Exception as e:
            self.logger.error(f"Error removing tool: {e}")
            messagebox.showerror("Remove Error", f"Failed to remove tool: {str(e)}")

    def on_check_availability(self):
        """Handle check availability button click."""
        if not self.tools_tree.get_children():
            messagebox.showinfo("No Tools", "There are no tools in this tool list to check.")
            return

        try:
            # Check availability for all tools
            result = self.tool_list_service.check_tools_availability(self.tool_list_id)

            if result:
                # Reload tool list to show updated availability
                self.load_tool_list()

                # Show summary
                available_count = sum(1 for tool in result.values() if tool.get("available"))
                unavailable_count = sum(1 for tool in result.values() if not tool.get("available"))

                message = f"Tool availability checked.\n\n"
                message += f"Available: {available_count}\n"
                message += f"Unavailable: {unavailable_count}"

                if unavailable_count > 0:
                    message += "\n\nSome tools are not available. Consider adjusting your tool list."

                messagebox.showinfo("Availability Check", message)

        except Exception as e:
            self.logger.error(f"Error checking availability: {e}")
            messagebox.showerror("Check Error", f"Failed to check availability: {str(e)}")

    def on_checkout_tools(self):
        """Handle checkout tools button click."""
        if not self.tools_tree.get_children():
            messagebox.showinfo("No Tools", "There are no tools in this tool list to check out.")
            return

        # Check if keeper is set
        if not self.keeper_var.get():
            messagebox.showwarning("Missing Information",
                                   "Please enter a name in the Tool Keeper field before checking out tools.")
            self.keeper_entry.focus_set()
            return

        # Create checkout dialog
        dialog = tk.Toplevel(self)
        dialog.title("Checkout Tools")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

        # Create form
        ttk.Label(dialog, text="Tool Keeper:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        keeper_var = tk.StringVar(value=self.keeper_var.get())
        keeper_entry = ttk.Entry(dialog, textvariable=keeper_var, width=30)
        keeper_entry.grid(row=0, column=1, columnspan=3, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Checkout Date:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        date_frame = ttk.Frame(dialog)
        date_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky=tk.W)

        date_entry = ttk.Entry(date_frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT)

        ttk.Button(
            date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(date_var)
        ).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.NW)
        notes_text = tk.Text(dialog, width=40, height=3)
        notes_text.grid(row=2, column=1, columnspan=3, padx=10, pady=5, sticky=tk.W)

        # Create tool list for checkout
        ttk.Label(dialog, text="Select tools to check out:").grid(row=3, column=0, columnspan=4, padx=10, pady=(15, 5),
                                                                  sticky=tk.W)

        # Create tools treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.grid(row=4, column=0, columnspan=4, padx=10, pady=5, sticky=tk.NSEW)
        dialog.grid_rowconfigure(4, weight=1)
        dialog.grid_columnconfigure(3, weight=1)

        columns = ("tool", "category", "quantity", "checkout")
        checkout_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)

        checkout_tree.heading("tool", text="Tool")
        checkout_tree.heading("category", text="Category")
        checkout_tree.heading("quantity", text="Available")
        checkout_tree.heading("checkout", text="Checkout")

        checkout_tree.column("tool", width=200)
        checkout_tree.column("category", width=120)
        checkout_tree.column("quantity", width=80)
        checkout_tree.column("checkout", width=80)

        checkout_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=checkout_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        checkout_tree.configure(yscrollcommand=scrollbar.set)

        # Add checkout quantities
        checkout_quantities = {}

        # Populate checkout tree
        for item_id in self.tools_tree.get_children():
            values = self.tools_tree.item(item_id, "values")
            tool_name = values[1]
            category = values[2]
            quantity = int(values[3])
            checked_out = int(values[4]) if values[4] else 0

            # Skip already checked out tools
            if checked_out >= quantity:
                continue

            # Add to treeview
            checkout_tree.insert(
                '', 'end',
                iid=item_id,
                values=(tool_name, category, quantity - checked_out, 0)
            )

            # Add to quantities dict
            checkout_quantities[item_id] = 0

        # Update checkout quantity
        def update_checkout_quantity(item_id, direction):
            """Update checkout quantity for a tool.

            Args:
                item_id: Tool item ID
                direction: 1 for increase, -1 for decrease
            """
            values = checkout_tree.item(item_id, "values")
            available = int(values[2])
            current = int(values[3])

            # Calculate new value
            new_value = current + direction
            if new_value < 0 or new_value > available:
                return

            # Update treeview
            checkout_tree.item(
                item_id,
                values=(values[0], values[1], values[2], new_value)
            )

            # Update quantities dict
            checkout_quantities[item_id] = new_value

        # Add buttons for each row
        def create_quantity_buttons():
            """Create plus/minus buttons for each row."""
            # Clear existing buttons
            for widget in button_frames:
                widget.destroy()

            button_frames.clear()

            # Create new buttons
            for item_id in checkout_tree.get_children():
                bbox = checkout_tree.bbox(item_id, column="checkout")
                if not bbox:
                    continue

                # Create frame for buttons
                frame = ttk.Frame(checkout_tree)
                frame.place(x=bbox[0] + bbox[2], y=bbox[1], anchor=tk.NE)
                button_frames.append(frame)

                # Create buttons
                ttk.Button(
                    frame,
                    text="-",
                    width=2,
                    command=lambda id=item_id: update_checkout_quantity(id, -1)
                ).pack(side=tk.LEFT)

                ttk.Button(
                    frame,
                    text="+",
                    width=2,
                    command=lambda id=item_id: update_checkout_quantity(id, 1)
                ).pack(side=tk.LEFT)

        # Keep track of button frames
        button_frames = []

        # Create initial buttons
        checkout_tree.bind("<Map>", lambda e: create_quantity_buttons())

        # Handle checkout
        def perform_checkout():
            """Perform the tool checkout."""
            # Check if any tools are selected
            items_to_checkout = {
                k: v for k, v in checkout_quantities.items() if v > 0
            }

            if not items_to_checkout:
                messagebox.showwarning("No Selection", "Please select tools to check out.", parent=dialog)
                return

            try:
                # Perform checkout
                result = self.tool_list_service.checkout_tools(
                    self.tool_list_id,
                    items_to_checkout,
                    keeper_var.get(),
                    notes_text.get("1.0", tk.END).strip()
                )

                if result:
                    # Update status to in_use
                    self.tool_list_service.update_tool_list_status(
                        self.tool_list_id,
                        "in_use"
                    )

                    # Reload tool list
                    self.load_tool_list()

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    messagebox.showinfo(
                        "Success",
                        f"Tools have been checked out to {keeper_var.get()}."
                    )

            except Exception as e:
                self.logger.error(f"Error checking out tools: {e}")
                messagebox.showerror("Error", f"Failed to check out tools: {str(e)}", parent=dialog)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=4, pady=15)

        ttk.Button(
            button_frame,
            text="Check Out",
            command=perform_checkout
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_return_tools(self):
        """Handle return tools button click."""
        # Check if there are checked out tools
        has_checked_out = False

        for item_id in self.tools_tree.get_children():
            values = self.tools_tree.item(item_id, "values")
            checked_out = int(values[4]) if values[4] else 0
            returned = int(values[5]) if values[5] else 0

            if checked_out > returned:
                has_checked_out = True
                break

        if not has_checked_out:
            messagebox.showinfo("No Tools", "There are no tools to return.")
            return

        # Create return dialog
        dialog = tk.Toplevel(self)
        dialog.title("Return Tools")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

        # Create form
        ttk.Label(dialog, text="Return Date:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        date_frame = ttk.Frame(dialog)
        date_frame.grid(row=0, column=1, columnspan=3, padx=10, pady=5, sticky=tk.W)

        date_entry = ttk.Entry(date_frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT)

        ttk.Button(
            date_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(date_var)
        ).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(dialog, text="Notes:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.NW)
        notes_text = tk.Text(dialog, width=40, height=3)
        notes_text.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky=tk.W)

        # Create tool list for return
        ttk.Label(dialog, text="Select tools to return:").grid(row=2, column=0, columnspan=4, padx=10, pady=(15, 5),
                                                               sticky=tk.W)

        # Create tools treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky=tk.NSEW)
        dialog.grid_rowconfigure(3, weight=1)
        dialog.grid_columnconfigure(3, weight=1)

        columns = ("tool", "category", "checked_out", "returned", "to_return", "condition")
        return_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)

        return_tree.heading("tool", text="Tool")
        return_tree.heading("category", text="Category")
        return_tree.heading("checked_out", text="Checked Out")
        return_tree.heading("returned", text="Returned")
        return_tree.heading("to_return", text="To Return")
        return_tree.heading("condition", text="Condition")

        return_tree.column("tool", width=150)
        return_tree.column("category", width=100)
        return_tree.column("checked_out", width=80)
        return_tree.column("returned", width=80)
        return_tree.column("to_return", width=80)
        return_tree.column("condition", width=100)

        return_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=return_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return_tree.configure(yscrollcommand=scrollbar.set)

        # Add return quantities and conditions
        return_quantities = {}
        return_conditions = {}

        # Populate return tree
        for item_id in self.tools_tree.get_children():
            values = self.tools_tree.item(item_id, "values")
            tool_name = values[1]
            category = values[2]
            checked_out = int(values[4]) if values[4] else 0
            returned = int(values[5]) if values[5] else 0
            current_condition = values[7]

            # Skip tools that are not checked out
            if checked_out <= returned or checked_out == 0:
                continue

            # Add to treeview
            to_return = checked_out - returned
            return_tree.insert(
                '', 'end',
                iid=item_id,
                values=(tool_name, category, checked_out, returned, to_return, current_condition)
            )

            # Add to quantities dict
            return_quantities[item_id] = to_return
            return_conditions[item_id] = current_condition

        # Update return quantity
        def update_return_quantity(item_id, direction):
            """Update return quantity for a tool.

            Args:
                item_id: Tool item ID
                direction: 1 for increase, -1 for decrease
            """
            values = return_tree.item(item_id, "values")
            checked_out = int(values[2])
            returned = int(values[3])
            current = int(values[4])

            # Calculate new value
            new_value = current + direction
            if new_value < 0 or new_value > (checked_out - returned):
                return

            # Update treeview
            return_tree.item(
                item_id,
                values=(values[0], values[1], values[2], values[3], new_value, values[5])
            )

            # Update quantities dict
            return_quantities[item_id] = new_value

        # Update condition
        def update_condition(item_id, condition):
            """Update condition for a tool.

            Args:
                item_id: Tool item ID
                condition: New condition
            """
            values = return_tree.item(item_id, "values")

            # Update treeview
            return_tree.item(
                item_id,
                values=(values[0], values[1], values[2], values[3], values[4], condition)
            )

            # Update conditions dict
            return_conditions[item_id] = condition

        # Add buttons for each row
        def create_row_controls():
            """Create plus/minus buttons and condition combo for each row."""
            # Clear existing controls
            for widget in control_frames:
                widget.destroy()

            control_frames.clear()

            # Create new controls
            for item_id in return_tree.get_children():
                # Get bounding box for to_return column
                to_return_bbox = return_tree.bbox(item_id, column="to_return")
                condition_bbox = return_tree.bbox(item_id, column="condition")
                if not to_return_bbox or not condition_bbox:
                    continue

                # Create frame for quantity buttons
                qty_frame = ttk.Frame(return_tree)
                qty_frame.place(x=to_return_bbox[0] + to_return_bbox[2], y=to_return_bbox[1], anchor=tk.NE)
                control_frames.append(qty_frame)

                # Create buttons
                ttk.Button(
                    qty_frame,
                    text="-",
                    width=2,
                    command=lambda id=item_id: update_return_quantity(id, -1)
                ).pack(side=tk.LEFT)

                ttk.Button(
                    qty_frame,
                    text="+",
                    width=2,
                    command=lambda id=item_id: update_return_quantity(id, 1)
                ).pack(side=tk.LEFT)

                # Create frame for condition combo
                cond_frame = ttk.Frame(return_tree)
                cond_frame.place(x=condition_bbox[0], y=condition_bbox[1])
                control_frames.append(cond_frame)

                # Create combo
                condition_var = tk.StringVar(value=return_conditions[item_id])
                condition_combo = ttk.Combobox(cond_frame, textvariable=condition_var, width=10, state="readonly")
                condition_combo["values"] = ["Excellent", "Good", "Fair", "Poor", "Damaged"]
                condition_combo.pack(side=tk.LEFT)

                # Bind combo selection
                condition_combo.bind(
                    "<<ComboboxSelected>>",
                    lambda e, id=item_id, var=condition_var: update_condition(id, var.get())
                )

        # Keep track of control frames
        control_frames = []

        # Create initial controls
        return_tree.bind("<Map>", lambda e: create_row_controls())

        # Handle return
        def perform_return():
            """Perform the tool return."""
            # Check if any tools are selected for return
            items_to_return = {
                k: {
                    "quantity": v,
                    "condition": return_conditions[k]
                } for k, v in return_quantities.items() if v > 0
            }

            if not items_to_return:
                messagebox.showwarning("No Selection", "Please select tools to return.", parent=dialog)
                return

            try:
                # Perform return
                result = self.tool_list_service.return_tools(
                    self.tool_list_id,
                    items_to_return,
                    notes_text.get("1.0", tk.END).strip()
                )

                if result:
                    # Check if all tools are returned
                    all_returned = True

                    for item_id in self.tools_tree.get_children():
                        values = self.tools_tree.item(item_id, "values")
                        checked_out = int(values[4]) if values[4] else 0
                        returned = int(values[5]) if values[5] else 0
                        to_return = int(return_quantities.get(item_id, 0))

                        if checked_out > (returned + to_return):
                            all_returned = False
                            break

                    # Update status if all tools are returned
                    if all_returned:
                        self.tool_list_service.update_tool_list_status(
                            self.tool_list_id,
                            "completed"
                        )

                    # Reload tool list
                    self.load_tool_list()

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    if all_returned:
                        messagebox.showinfo(
                            "Success",
                            "All tools have been returned. Tool list is now complete."
                        )
                    else:
                        messagebox.showinfo(
                            "Success",
                            "Tools have been returned."
                        )

            except Exception as e:
                self.logger.error(f"Error returning tools: {e}")
                messagebox.showerror("Error", f"Failed to return tools: {str(e)}", parent=dialog)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=4, pady=15)

        ttk.Button(
            button_frame,
            text="Return Tools",
            command=perform_return
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_cancel_tool_list(self):
        """Handle cancel tool list button click."""
        if not messagebox.askyesno(
                "Confirm Cancel",
                "Are you sure you want to cancel this tool list? This action cannot be undone."
        ):
            return

        try:
            # Update status to cancelled
            result = self.tool_list_service.update_tool_list_status(
                self.tool_list_id,
                "cancelled"
            )

            if result:
                # Update status variable and display
                self.status_var.set("cancelled")
                self.status_badge.set_text("Cancelled", "cancelled")

                # Update action buttons
                self.update_action_buttons("cancelled")

                # Show success message
                messagebox.showinfo("Success", "Tool list has been cancelled.")

                # Publish event
                publish("tool_list_cancelled", {
                    "tool_list_id": self.tool_list_id,
                    "project_id": self.project_id
                })

        except Exception as e:
            self.logger.error(f"Error cancelling tool list: {e}")
            messagebox.showerror("Error", f"Failed to cancel tool list: {str(e)}")

    def on_save(self):
        """Handle save button click."""
        try:
            # Collect data
            status = self.status_var.get().lower().replace(" ", "_")
            keeper = self.keeper_var.get()
            notes = self.notes_text.get("1.0", tk.END).strip()
            location = self.location_var.get()
            return_date = None

            if self.return_date_var.get():
                try:
                    return_date = datetime.datetime.strptime(self.return_date_var.get(), "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date", "Return date must be in YYYY-MM-DD format.")
                    return

            # Save tool list
            result = self.tool_list_service.update_tool_list(
                self.tool_list_id,
                {
                    "status": status,
                    "keeper": keeper,
                    "notes": notes,
                    "location": location,
                    "return_date": return_date
                }
            )

            if result:
                # Show success message
                messagebox.showinfo("Success", "Tool list has been saved.")

                # Reload tool list
                self.load_tool_list()

        except Exception as e:
            self.logger.error(f"Error saving tool list: {e}")
            messagebox.showerror("Save Error", f"Failed to save tool list: {str(e)}")

    def on_back(self):
        """Handle back button click."""
        if self.project_id:
            self.parent.master.show_view(
                "project_details",
                view_data={"project_id": self.project_id}
            )
        else:
            self.parent.master.show_view("project_list")

    def on_print(self):
        """Handle print button click."""
        try:
            # Generate and print tool list
            result = self.tool_list_service.print_tool_list(self.tool_list_id)

            if result:
                messagebox.showinfo("Print", "Tool list has been sent to the printer.")

        except Exception as e:
            self.logger.error(f"Error printing tool list: {e}")
            messagebox.showerror("Print Error", f"Failed to print tool list: {str(e)}")

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        current_date = datetime.date.today()

        # Try to parse current value
        if date_var.get():
            try:
                current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Create calendar dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Date")
        dialog.geometry("300x280")
        dialog.transient(self)
        dialog.grab_set()

        # Calendar year and month selection
        cal_header = ttk.Frame(dialog)
        cal_header.pack(fill=tk.X, padx=10, pady=5)

        # Year selection
        ttk.Label(cal_header, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        year_var = tk.StringVar(value=str(current_date.year))
        year_spin = ttk.Spinbox(
            cal_header,
            from_=2000,
            to=2100,
            textvariable=year_var,
            width=5
        )
        year_spin.pack(side=tk.LEFT, padx=5)

        # Month selection
        ttk.Label(cal_header, text="Month:").pack(side=tk.LEFT, padx=(10, 5))
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        month_var = tk.StringVar(value=months[current_date.month - 1])
        month_combo = ttk.Combobox(
            cal_header,
            textvariable=month_var,
            values=months,
            width=10,
            state="readonly"
        )
        month_combo.pack(side=tk.LEFT, padx=5)

        # Calendar frame
        cal_frame = ttk.Frame(dialog, padding=5)
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Day of week headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(
                cal_frame,
                text=day,
                width=3,
                anchor=tk.CENTER,
                font=("TkDefaultFont", 9, "bold")
            ).grid(row=0, column=i, padx=2, pady=2)

        # Day buttons
        day_buttons = []
        for row in range(6):
            for col in range(7):
                btn = ttk.Button(
                    cal_frame,
                    text="",
                    width=3,
                    style="Calendar.TButton"
                )
                btn.grid(row=row + 1, column=col, padx=2, pady=2)
                day_buttons.append(btn)

        # Selected date
        selected_date = None

        # Update calendar when month/year changes
        def update_calendar():
            """Update the calendar display based on selected month and year."""
            nonlocal selected_date

            # Get year and month
            year = int(year_var.get())
            month = months.index(month_var.get()) + 1

            # Get first day of month and number of days
            first_day = datetime.date(year, month, 1)
            if month == 12:
                last_day = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            # Get day of week for first day (0 = Monday, 6 = Sunday)
            first_weekday = first_day.weekday()

            # Clear all buttons
            for btn in day_buttons:
                btn.configure(text="", state=tk.DISABLED)

            # Fill in days
            for day in range(1, last_day.day + 1):
                index = first_weekday + day - 1

                day_buttons[index].configure(
                    text=str(day),
                    state=tk.NORMAL,
                    command=lambda d=day: select_day(d)
                )

                # Highlight current date if it matches
                this_date = datetime.date(year, month, day)

                if this_date == current_date:
                    day_buttons[index].configure(style="Calendar.Accent.TButton")
                else:
                    day_buttons[index].configure(style="Calendar.TButton")

                # Highlight selected date
                if selected_date and this_date == selected_date:
                    day_buttons[index].configure(style="Calendar.Selected.TButton")

        # Select day
        def select_day(day):
            """Select a day in the calendar.

            Args:
                day: The day number to select
            """
            nonlocal selected_date

            # Get year and month
            year = int(year_var.get())
            month = months.index(month_var.get()) + 1

            # Create date object
            selected_date = datetime.date(year, month, day)

            # Update calendar to highlight selected date
            update_calendar()

        # Navigate to previous/next month
        def prev_month():
            """Go to previous month."""
            month_idx = months.index(month_var.get())
            year = int(year_var.get())

            if month_idx == 0:
                # December of previous year
                month_var.set(months[11])
                year_var.set(str(year - 1))
            else:
                # Previous month
                month_var.set(months[month_idx - 1])

            update_calendar()

        def next_month():
            """Go to next month."""
            month_idx = months.index(month_var.get())
            year = int(year_var.get())

            if month_idx == 11:
                # January of next year
                month_var.set(months[0])
                year_var.set(str(year + 1))
            else:
                # Next month
                month_var.set(months[month_idx + 1])

            update_calendar()

        # Navigation buttons
        nav_frame = ttk.Frame(dialog)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            nav_frame,
            text="◀",
            width=3,
            command=prev_month
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame,
            text="▶",
            width=3,
            command=next_month
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame,
            text="Today",
            command=lambda: (
                year_var.set(str(datetime.date.today().year)),
                month_var.set(months[datetime.date.today().month - 1]),
                update_calendar()
            )
        ).pack(side=tk.LEFT, padx=5)

        # OK/Cancel buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_ok():
            """Handle OK button click."""
            if selected_date:
                date_var.set(selected_date.strftime("%Y-%m-%d"))
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="OK",
            command=on_ok
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Bind month and year changes
        month_combo.bind("<<ComboboxSelected>>", lambda e: update_calendar())
        year_spin.bind("<Return>", lambda e: update_calendar())
        year_spin.bind("<FocusOut>", lambda e: update_calendar())

        # Define calendar button styles
        style = ttk.Style()
        style.configure("Calendar.TButton", width=3, padding=1)
        style.configure("Calendar.Accent.TButton", background=COLORS["primary_light"])
        style.configure("Calendar.Selected.TButton", background=COLORS["primary"])

        # Initialize calendar
        update_calendar()

    def refresh(self):
        """Refresh the view."""
        if self.tool_list_id:
            self.load_tool_list()