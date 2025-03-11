# gui/base/base_list_view.py
"""
Base List View class for displaying and managing lists of entities.
Provides common functionality for list views with filtering and pagination.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from gui.base.base_view import BaseView
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.widgets.search_frame import SearchFrame
from gui import theme, config


class BaseListView(BaseView):
    """
    Base class for all list views in the application.
    Includes common functionality for displaying, filtering, and paginating lists of entities.
    """

    def __init__(self, parent):
        """
        Initialize the base list view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "List View"
        self.service_name = None  # Service name to resolve via DI
        self.current_page = 1
        self.page_size = config.DEFAULT_PAGE_SIZE
        self.total_items = 0
        self.filter_criteria = {}
        self.sort_column = "id"
        self.sort_direction = "asc"
        self.columns = []  # List of (id, label, width) tuples
        self.search_fields = []  # List of fields to include in search
        self.selected_item = None
        self.treeview = None
        self.search_frame = None

    def build(self):
        """Build the list view layout."""
        super().build()

        # Create main content frame
        content = ttk.Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add search/filter frame
        self.search_frame = SearchFrame(
            content,
            search_fields=self.search_fields,
            on_search=self.on_search)
        self.search_frame.pack(fill=tk.X, pady=(0, 10))

        # Add list frame with treeview
        list_frame = ttk.Frame(content)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        self.create_treeview(list_frame)

        # Add pagination controls
        self.create_pagination(content)

        # Load initial data
        self.load_data()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Add button
        btn_add = ttk.Button(
            self.action_buttons,
            text="Add New",
            command=self.on_add)
        btn_add.pack(side=tk.LEFT, padx=5)

        # Refresh button
        btn_refresh = ttk.Button(
            self.action_buttons,
            text="Refresh",
            command=self.refresh)
        btn_refresh.pack(side=tk.LEFT, padx=5)

    def create_treeview(self, parent):
        """
        Create the treeview for displaying data.

        Args:
            parent: The parent widget
        """
        # Create a frame for the treeview and scrollbar
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create the enhanced treeview
        self.treeview = EnhancedTreeview(
            frame,
            columns=[col[0] for col in self.columns],
            on_sort=self.on_sort,
            on_select=self.on_select,
            on_double_click=self.on_edit)

        # Configure columns
        for col_id, col_label, col_width in self.columns:
            self.treeview.heading(col_id, text=col_label)
            self.treeview.column(col_id, width=col_width, minwidth=50)

        # Create context menu
        self.create_context_menu()

        # Create item action buttons
        self.create_item_actions(parent)

    def create_context_menu(self):
        """Create the context menu for the treeview."""
        context_menu = tk.Menu(self.treeview, tearoff=0)
        context_menu.add_command(label="View Details", command=self.on_view)
        context_menu.add_command(label="Edit", command=self.on_edit)
        context_menu.add_separator()
        context_menu.add_command(label="Delete", command=self.on_delete)

        # Add any additional context menu items
        self.add_context_menu_items(context_menu)

        # Bind the context menu to right-click
        self.treeview.bind("<Button-3>", lambda e: self.show_context_menu(e, context_menu))

    def add_context_menu_items(self, menu):
        """
        Add additional context menu items.
        Can be overridden by subclasses.

        Args:
            menu: The context menu to add items to
        """
        pass

    def show_context_menu(self, event, menu):
        """
        Show the context menu on right-click.

        Args:
            event: The mouse event
            menu: The context menu to show
        """
        # Select the item under the cursor
        item = self.treeview.identify_row(event.y)
        if item:
            self.treeview.selection_set(item)
            self.on_select()
            menu.post(event.x_root, event.y_root)

    def create_item_actions(self, parent):
        """
        Create action buttons for selected items.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.Frame(parent)

        # View button
        btn_view = ttk.Button(
            actions_frame,
            text="View",
            command=self.on_view,
            state=tk.DISABLED)
        btn_view.pack(side=tk.LEFT, padx=5)
        self.btn_view = btn_view

        # Edit button
        btn_edit = ttk.Button(
            actions_frame,
            text="Edit",
            command=self.on_edit,
            state=tk.DISABLED)
        btn_edit.pack(side=tk.LEFT, padx=5)
        self.btn_edit = btn_edit

        # Delete button
        btn_delete = ttk.Button(
            actions_frame,
            text="Delete",
            command=self.on_delete,
            state=tk.DISABLED)
        btn_delete.pack(side=tk.LEFT, padx=5)
        self.btn_delete = btn_delete

        # Add any additional action buttons
        self.add_item_action_buttons(actions_frame)

        actions_frame.pack(fill=tk.X, pady=5)

    def add_item_action_buttons(self, parent):
        """
        Add additional action buttons.
        Can be overridden by subclasses.

        Args:
            parent: The parent widget
        """
        pass

    def create_pagination(self, parent):
        """
        Create pagination controls.

        Args:
            parent: The parent widget
        """
        pagination_frame = ttk.Frame(parent)

        # Page size selection
        ttk.Label(pagination_frame, text="Items per page:").pack(side=tk.LEFT, padx=5)
        page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_combo = ttk.Combobox(
            pagination_frame,
            textvariable=page_size_var,
            values=config.PAGE_SIZE_OPTIONS,
            width=5,
            state="readonly")
        page_size_combo.pack(side=tk.LEFT, padx=5)
        page_size_combo.bind("<<ComboboxSelected>>", self.on_page_size_change)

        # Navigation buttons
        btn_first = ttk.Button(
            pagination_frame,
            text="<<",
            command=self.go_to_first_page,
            width=3)
        btn_first.pack(side=tk.LEFT, padx=5)

        btn_prev = ttk.Button(
            pagination_frame,
            text="<",
            command=self.go_to_prev_page,
            width=3)
        btn_prev.pack(side=tk.LEFT, padx=5)

        # Page number display
        self.page_info = ttk.Label(pagination_frame, text="Page 1 of 1")
        self.page_info.pack(side=tk.LEFT, padx=10)

        btn_next = ttk.Button(
            pagination_frame,
            text=">",
            command=self.go_to_next_page,
            width=3)
        btn_next.pack(side=tk.LEFT, padx=5)

        btn_last = ttk.Button(
            pagination_frame,
            text=">>",
            command=self.go_to_last_page,
            width=3)
        btn_last.pack(side=tk.LEFT, padx=5)

        # Total items display
        self.total_items_label = ttk.Label(pagination_frame, text="Total: 0 items")
        self.total_items_label.pack(side=tk.RIGHT, padx=10)

        pagination_frame.pack(fill=tk.X, pady=5)

    def load_data(self):
        """Load data into the treeview based on current filters and pagination."""
        if not self.service_name:
            self.logger.error("No service name defined for list view")
            return

        try:
            service = self.get_service(self.service_name)
            if not service:
                return

            # Calculate pagination
            offset = (self.current_page - 1) * self.page_size

            # Get total count first to update pagination
            self.total_items = self.get_total_count(service)
            total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)

            # Adjust current page if needed
            if self.current_page > total_pages:
                self.current_page = total_pages
                offset = (self.current_page - 1) * self.page_size

            # Update pagination display
            self.update_pagination_display(total_pages)

            # Get data for current page
            items = self.get_items(service, offset, self.page_size)

            # Clear existing items
            self.treeview.clear()

            # Add items to treeview
            for item in items:
                values = self.extract_item_values(item)
                item_id = values[0]  # Assuming first column is ID
                self.treeview.insert_item(item_id, values)

        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            self.show_error("Data Load Error", f"Failed to load data: {str(e)}")

    def get_total_count(self, service):
        """
        Get the total count of items.

        Args:
            service: The service to use

        Returns:
            The total count of items
        """
        # Default implementation - override in subclasses
        try:
            return service.get_count(self.filter_criteria)
        except Exception as e:
            self.logger.error(f"Error getting count: {str(e)}")
            return 0

    def get_items(self, service, offset, limit):
        """
        Get items for the current page.

        Args:
            service: The service to use
            offset: Pagination offset
            limit: Page size

        Returns:
            List of items
        """
        # Default implementation - override in subclasses
        try:
            return service.get_all(
                offset=offset,
                limit=limit,
                sort_column=self.sort_column,
                sort_direction=self.sort_direction,
                **self.filter_criteria
            )
        except Exception as e:
            self.logger.error(f"Error getting items: {str(e)}")
            return []

    def extract_item_values(self, item):
        """
        Extract values from an item for display in the treeview.

        Args:
            item: The item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Default implementation - override in subclasses
        if hasattr(item, '__dict__'):
            # For model objects
            return [getattr(item, col[0], "") for col in self.columns]
        elif isinstance(item, dict):
            # For dictionary data
            return [item.get(col[0], "") for col in self.columns]
        else:
            # For other data types
            return [str(item)] + [""] * (len(self.columns) - 1)

    def update_pagination_display(self, total_pages):
        """
        Update the pagination display.

        Args:
            total_pages: The total number of pages
        """
        self.page_info.config(text=f"Page {self.current_page} of {total_pages}")
        self.total_items_label.config(text=f"Total: {self.total_items} items")

    def go_to_first_page(self):
        """Go to the first page."""
        if self.current_page != 1:
            self.current_page = 1
            self.load_data()

    def go_to_prev_page(self):
        """Go to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def go_to_next_page(self):
        """Go to the next page."""
        total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_data()

    def go_to_last_page(self):
        """Go to the last page."""
        total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
        if self.current_page != total_pages:
            self.current_page = total_pages
            self.load_data()

    def on_page_size_change(self, event):
        """
        Handle page size change.

        Args:
            event: The combobox selection event
        """
        combo = event.widget
        self.page_size = int(combo.get())
        self.current_page = 1  # Reset to first page
        self.load_data()

    def on_sort(self, column, direction):
        """
        Handle column sort.

        Args:
            column: The column to sort by
            direction: The sort direction ('asc' or 'desc')
        """
        self.sort_column = column
        self.sort_direction = direction
        self.load_data()

    def on_search(self, criteria):
        """
        Handle search.

        Args:
            criteria: Dictionary of search criteria
        """
        self.filter_criteria = criteria
        self.current_page = 1  # Reset to first page
        self.load_data()

    def on_select(self):
        """Handle item selection."""
        selection = self.treeview.selection()
        if selection:
            self.selected_item = selection[0]
            # Enable action buttons
            self.btn_view.config(state=tk.NORMAL)
            self.btn_edit.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)
        else:
            self.selected_item = None
            # Disable action buttons
            self.btn_view.config(state=tk.DISABLED)
            self.btn_edit.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)

    def on_add(self):
        """Handle add new item action."""
        self.logger.info("Add action not implemented")
        self.show_info("Not Implemented", "Add action not implemented")

    def on_view(self):
        """Handle view item action."""
        if not self.selected_item:
            return

        self.logger.info(f"View action not implemented for item {self.selected_item}")
        self.show_info("Not Implemented", "View action not implemented")

    def on_edit(self):
        """Handle edit item action."""
        if not self.selected_item:
            return

        self.logger.info(f"Edit action not implemented for item {self.selected_item}")
        self.show_info("Not Implemented", "Edit action not implemented")

    def on_delete(self):
        """Handle delete item action."""
        if not self.selected_item:
            return

        if not self.show_confirm("Confirm Delete", "Are you sure you want to delete this item?"):
            return

        try:
            service = self.get_service(self.service_name)
            if not service:
                return

            # Perform delete operation
            service.delete(self.selected_item)

            # Refresh data
            self.refresh()

            self.show_info("Success", "Item deleted successfully")
        except Exception as e:
            self.logger.error(f"Error deleting item: {str(e)}")
            self.show_error("Delete Error", f"Failed to delete item: {str(e)}")

    def refresh(self):
        """Refresh the view."""
        self.load_data()