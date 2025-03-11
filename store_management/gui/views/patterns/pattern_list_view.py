# gui/views/patterns/pattern_list_view.py
"""
Pattern list view for displaying and managing patterns.

Displays a list of patterns with filtering, sorting and actions for creating,
editing, duplicating, and deleting patterns.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional, Tuple

from database.models.enums import SkillLevel, ProjectType
from gui.base.base_list_view import BaseListView
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge
from gui.theme import COLORS, get_status_style

logger = logging.getLogger(__name__)


class PatternListView(BaseListView):
    """
    View for displaying and managing patterns in a list format.
    """

    def __init__(self, parent):
        """
        Initialize the pattern list view.

        Args:
            parent: The parent widget
        """
        self.title = "Patterns"
        self.description = "Manage your leatherworking patterns"

        # Define columns for the treeview
        self.columns = [
            {"id": "name", "text": "Pattern Name", "width": 200},
            {"id": "skill_level", "text": "Skill Level", "width": 100},
            {"id": "num_components", "text": "Components", "width": 90},
            {"id": "project_type", "text": "Project Type", "width": 120},
            {"id": "created_at", "text": "Created", "width": 100},
            {"id": "updated_at", "text": "Updated", "width": 100},
        ]

        # Define search fields
        self.search_fields = [
            {"name": "name", "label": "Name", "type": "text"},
            {"name": "skill_level", "label": "Skill Level", "type": "enum", "enum_type": SkillLevel},
            {"name": "project_type", "label": "Project Type", "type": "enum", "enum_type": ProjectType},
        ]

        # Call parent constructor
        super().__init__(parent)

    def build(self):
        """Build the pattern list view."""
        # Set up the view header
        self.create_header()

        # Create search frame
        search_frame = self.create_search_frame()
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create treeview with scrollbars
        self.treeview_frame = ttk.Frame(self)
        self.treeview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.create_treeview(self.treeview_frame)

        # Set column widths
        column_widths = {col["id"]: col["width"] for col in self.columns}
        self.treeview.set_column_widths(column_widths)

        # Create actions frame
        self.actions_frame = ttk.Frame(self)
        self.actions_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create item actions
        self.create_item_actions(self.actions_frame)

        # Add pagination
        self.create_pagination(self.actions_frame)

        # Create context menu
        self.create_context_menu()

        # Load initial data
        self.load_data()

    def add_item_action_buttons(self, parent):
        """
        Add pattern-specific action buttons.

        Args:
            parent: The parent widget for buttons
        """
        # Duplicate pattern button
        self.duplicate_btn = ttk.Button(
            parent,
            text="Duplicate",
            command=self.on_duplicate,
            state=tk.DISABLED
        )
        self.duplicate_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Export pattern button
        self.export_btn = ttk.Button(
            parent,
            text="Export",
            command=self.on_export,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Print pattern button
        self.print_btn = ttk.Button(
            parent,
            text="Print",
            command=self.on_print,
            state=tk.DISABLED
        )
        self.print_btn.pack(side=tk.LEFT, padx=(0, 5))

    def add_context_menu_items(self, menu):
        """
        Add pattern-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_separator()

        # Duplicate pattern
        menu.add_command(
            label="Duplicate Pattern",
            command=self.on_duplicate
        )

        # Export pattern
        menu.add_command(
            label="Export Pattern",
            command=self.on_export
        )

        # Print pattern
        menu.add_command(
            label="Print Pattern",
            command=self.on_print
        )

    def extract_item_values(self, item):
        """
        Extract values from a pattern item for display in the treeview.

        Args:
            item: The pattern item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Format skill level
        skill_level = item.get("skill_level", "")
        if isinstance(skill_level, str):
            skill_level = skill_level.replace("_", " ").title()

        # Format project type
        project_type = item.get("project_type", "")
        if isinstance(project_type, str):
            project_type = project_type.replace("_", " ").title()

        # Format dates
        created_at = item.get("created_at", "")
        if created_at:
            if isinstance(created_at, str):
                created_at = created_at[:10]  # Extract date part
            else:
                created_at = created_at.strftime("%Y-%m-%d")

        updated_at = item.get("updated_at", "")
        if updated_at:
            if isinstance(updated_at, str):
                updated_at = updated_at[:10]  # Extract date part
            else:
                updated_at = updated_at.strftime("%Y-%m-%d")

        # Count components
        num_components = len(item.get("components", []))

        return [
            item.get("name", ""),
            skill_level,
            num_components,
            project_type,
            created_at,
            updated_at,
        ]

    def get_items(self, service, offset, limit):
        """
        Get patterns for the current page.

        Args:
            service: The service to use
            offset: Pagination offset
            limit: Page size

        Returns:
            List of patterns
        """
        # Build query params from search criteria
        params = self.search_criteria.copy() if self.search_criteria else {}

        # Add pagination params
        params["offset"] = offset
        params["limit"] = limit

        # Add sorting
        if self.sort_column and self.sort_direction:
            params["sort_by"] = self.sort_column
            params["sort_dir"] = self.sort_direction

        try:
            # Get patterns from service
            patterns = service.get_patterns(**params)
            return patterns
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            self.show_error("Error", f"Failed to load patterns: {e}")
            return []

    def get_total_count(self, service):
        """
        Get the total count of patterns.

        Args:
            service: The service to use

        Returns:
            The total count of patterns
        """
        # Build query params from search criteria
        params = self.search_criteria.copy() if self.search_criteria else {}

        try:
            # Get count from service
            return service.get_pattern_count(**params)
        except Exception as e:
            logger.error(f"Error getting pattern count: {e}")
            self.show_error("Error", f"Failed to get pattern count: {e}")
            return 0

    def load_data(self):
        """Load pattern data into the treeview."""
        try:
            # Get the pattern service
            service = get_service("IPatternService")

            # Calculate pagination
            offset = (self.current_page - 1) * self.page_size
            limit = self.page_size

            # Get total count for pagination
            total_count = self.get_total_count(service)
            total_pages = (total_count + self.page_size - 1) // self.page_size

            # Update pagination display
            self.update_pagination_display(total_pages)

            # Clear current items
            self.treeview.clear()

            # Get items for current page
            items = self.get_items(service, offset, limit)

            # Insert items into treeview
            for i, item in enumerate(items):
                item_id = item.get("id")
                values = self.extract_item_values(item)
                self.treeview.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=values,
                    tags=[str(item_id)]
                )

            # Update message if no results
            if not items:
                empty_message = "No patterns found"
                if self.search_criteria:
                    empty_message = "No patterns match your search criteria"

                self.treeview.insert(
                    "",
                    "end",
                    iid="empty",
                    values=(empty_message, "", "", "", "", ""),
                    tags=["empty"]
                )
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            self.show_error("Error", f"Failed to load patterns: {e}")

    def on_select(self):
        """Handle item selection."""
        # Get the selected item
        selected = self.treeview.selection()
        if not selected:
            # Disable action buttons when no selection
            self.view_btn.configure(state=tk.DISABLED)
            self.edit_btn.configure(state=tk.DISABLED)
            self.delete_btn.configure(state=tk.DISABLED)
            self.duplicate_btn.configure(state=tk.DISABLED)
            self.export_btn.configure(state=tk.DISABLED)
            self.print_btn.configure(state=tk.DISABLED)
            return

        # Check if "empty" placeholder is selected
        if "empty" in self.treeview.item(selected[0], "tags"):
            return

        # Enable action buttons
        self.view_btn.configure(state=tk.NORMAL)
        self.edit_btn.configure(state=tk.NORMAL)
        self.delete_btn.configure(state=tk.NORMAL)
        self.duplicate_btn.configure(state=tk.NORMAL)
        self.export_btn.configure(state=tk.NORMAL)
        self.print_btn.configure(state=tk.NORMAL)

    def on_add(self):
        """Handle add new pattern action."""
        try:
            # Open pattern details view for new pattern
            from gui.views.patterns.pattern_detail_view import PatternDetailView

            # Replace content with pattern detail view
            detail_view = PatternDetailView(self.parent, create_new=True)
            detail_view.pack(fill=tk.BOTH, expand=True)

            # Hide current view
            self.pack_forget()
        except Exception as e:
            logger.error(f"Error adding pattern: {e}")
            self.show_error("Error", f"Failed to add pattern: {e}")

    def on_view(self):
        """Handle view pattern action."""
        # Get selected pattern ID
        pattern_id = self.get_selected_id()
        if not pattern_id:
            return

        try:
            # Open pattern details view
            from gui.views.patterns.pattern_detail_view import PatternDetailView

            # Replace content with pattern detail view
            detail_view = PatternDetailView(self.parent, pattern_id=pattern_id, readonly=True)
            detail_view.pack(fill=tk.BOTH, expand=True)

            # Hide current view
            self.pack_forget()
        except Exception as e:
            logger.error(f"Error viewing pattern: {e}")
            self.show_error("Error", f"Failed to view pattern: {e}")

    def on_edit(self):
        """Handle edit pattern action."""
        # Get selected pattern ID
        pattern_id = self.get_selected_id()
        if not pattern_id:
            return

        try:
            # Open pattern details view for editing
            from gui.views.patterns.pattern_detail_view import PatternDetailView

            # Replace content with pattern detail view
            detail_view = PatternDetailView(self.parent, pattern_id=pattern_id)
            detail_view.pack(fill=tk.BOTH, expand=True)

            # Hide current view
            self.pack_forget()
        except Exception as e:
            logger.error(f"Error editing pattern: {e}")
            self.show_error("Error", f"Failed to edit pattern: {e}")

    def on_delete(self):
        """Handle delete pattern action."""
        # Get selected pattern ID
        pattern_id = self.get_selected_id()
        if not pattern_id:
            return

        # Get pattern name
        selected = self.treeview.selection()
        if not selected:
            return

        values = self.treeview.item(selected[0], "values")
        pattern_name = values[0]

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the pattern '{pattern_name}'?\n\n"
                "This action cannot be undone."
        ):
            return

        try:
            # Get pattern service
            service = get_service("IPatternService")

            # Delete pattern
            result = service.delete_pattern(pattern_id)

            if result:
                messagebox.showinfo("Success", f"Pattern '{pattern_name}' deleted successfully.")
                self.refresh()
            else:
                self.show_error("Error", f"Failed to delete pattern '{pattern_name}'.")
        except Exception as e:
            logger.error(f"Error deleting pattern: {e}")
            self.show_error("Error", f"Failed to delete pattern: {e}")

    def get_selected_id(self):
        """
        Get the ID of the selected pattern.

        Returns:
            The ID of the selected pattern, or None if no selection
        """
        selected = self.treeview.selection()
        if not selected:
            return None

        # Get tags which contain the ID
        tags = self.treeview.item(selected[0], "tags")
        if not tags or "empty" in tags:
            return None

        # Extract ID from tags
        try:
            return int(tags[0])
        except (ValueError, IndexError):
            return None

    def on_duplicate(self):
        """Handle duplicate pattern action."""
        # Get selected pattern ID
        pattern_id = self.get_selected_id()
        if not pattern_id:
            return

        # Get pattern name
        selected = self.treeview.selection()
        if not selected:
            return

        values = self.treeview.item(selected[0], "values")
        pattern_name = values[0]

        # Ask for new name
        from tkinter import simpledialog
        new_name = simpledialog.askstring(
            "Duplicate Pattern",
            "Enter a name for the duplicated pattern:",
            initialvalue=f"Copy of {pattern_name}"
        )

        if not new_name:
            return

        try:
            # Get pattern service
            service = get_service("IPatternService")

            # Duplicate pattern
            result = service.duplicate_pattern(pattern_id, new_name)

            if result:
                messagebox.showinfo("Success", f"Pattern duplicated successfully as '{new_name}'.")
                self.refresh()

                # Select the new pattern
                self.select_pattern_by_name(new_name)
            else:
                self.show_error("Error", f"Failed to duplicate pattern.")
        except Exception as e:
            logger.error(f"Error duplicating pattern: {e}")
            self.show_error("Error", f"Failed to duplicate pattern: {e}")

    def on_export(self):
        """Handle export pattern action."""
        # Get selected pattern ID
        pattern_id = self.get_selected_id()
        if not pattern_id:
            return

        try:
            # Open export dialog
            from gui.views.patterns.pattern_export_dialog import PatternExportDialog

            # Create and show dialog
            dialog = PatternExportDialog(self, pattern_id)
            result = dialog.show()

            # Refresh if needed based on dialog result
            if result == "ok":
                self.refresh()
        except Exception as e:
            logger.error(f"Error exporting pattern: {e}")
            self.show_error("Error", f"Failed to export pattern: {e}")

    def on_print(self):
        """Handle print pattern action."""
        # Get selected pattern ID
        pattern_id = self.get_selected_id()
        if not pattern_id:
            return

        try:
            # Open print dialog
            from gui.views.patterns.print_dialog import PrintDialog

            # Create and show dialog
            dialog = PrintDialog(self, pattern_id)
            dialog.show()
        except Exception as e:
            logger.error(f"Error printing pattern: {e}")
            self.show_error("Error", f"Failed to print pattern: {e}")

    def select_pattern_by_name(self, name):
        """
        Select a pattern in the treeview by name.

        Args:
            name: The name of the pattern to select
        """
        # Find the pattern by name
        for item_id in self.treeview.get_children():
            values = self.treeview.item(item_id, "values")
            if values[0] == name:
                # Select the item
                self.treeview.selection_set(item_id)
                self.treeview.see(item_id)
                self.on_select()
                break