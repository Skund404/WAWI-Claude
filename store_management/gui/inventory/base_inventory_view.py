# relative path: store_management/gui/inventory/base_inventory_view.py
"""
Base Inventory View for the Leatherworking Store Management application.

Provides a standardized base class for all inventory-related views.
"""

import logging
import tkinter as tk
import tkinter.ttk as ttk
from typing import Any, Optional, List, Dict

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.storage_service import IStorageService


class BaseInventoryView(BaseView):
    """
    Base class for inventory views with common functionality.

    Provides standard methods for loading, displaying, and managing
    inventory items across different inventory types.

    Attributes:
        parent (tk.Widget): Parent widget
        app (Any): Application instance
        material_service (IMaterialService): Service for material operations
        _items (List[Dict]): List of inventory items
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the base inventory view.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance
        """
        super().__init__(parent, app)

        # Setup logging
        self._logger = logging.getLogger(self.__class__.__module__)

        # Initialize services
        self._material_service: Optional[IMaterialService] = None
        self._storage_service: Optional[IStorageService] = None

        # Items storage
        self._items: List[Dict] = []

        # UI Components
        self._tree: Optional[ttk.Treeview] = None

        # Setup the view
        self._setup_view()

    def _setup_view(self):
        """
        Set up the basic view structure.
        To be overridden by specific inventory views.
        """
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Create toolbar
        self.toolbar = self.create_toolbar(self.main_frame)

        # Create search box
        self.search_box = self.create_search_box(
            self.main_frame,
            search_callback=self._on_search
        )

        # Create treeview for displaying items
        self._create_treeview()

    def _create_treeview(self):
        """
        Create a standard treeview for displaying inventory items.
        To be customized by specific inventory views.
        """
        # Create treeview frame
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(expand=True, fill=tk.BOTH)

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self._tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        self._tree.pack(expand=True, fill=tk.BOTH)

        # Configure scrollbars
        tree_scroll_y.config(command=self._tree.yview)
        tree_scroll_x.config(command=self._tree.xview)

    def _load_data(self):
        """
        Load inventory data.
        To be implemented by specific inventory views.
        """
        raise NotImplementedError("Subclasses must implement _load_data method")

    def _on_search(self, query: str = ""):
        """
        Handle search functionality.

        Args:
            query (str, optional): Search query. Defaults to "".
        """
        try:
            # Filter items based on query
            filtered_items = self._filter_items(query)

            # Clear existing items
            for item in self._tree.get_children():
                self._tree.delete(item)

            # Populate treeview with filtered items
            for item in filtered_items:
                self._tree.insert("", tk.END, values=self._get_item_values(item))

            # Update status
            self.set_status(f"Found {len(filtered_items)} items matching '{query}'")
        except Exception as e:
            self.show_error("Search Error", str(e))

    def _filter_items(self, query: str) -> List[Dict]:
        """
        Filter items based on search query.

        Args:
            query (str): Search query

        Returns:
            List of filtered items
        """
        if not query:
            return self._items

        # Default implementation: case-insensitive search across all fields
        query = query.lower()
        return [
            item for item in self._items
            if any(query in str(value).lower() for value in item.values())
        ]

    def _get_item_values(self, item: Dict) -> Tuple:
        """
        Convert item dictionary to treeview values.
        To be implemented by specific inventory views.

        Args:
            item (Dict): Item dictionary

        Returns:
            Tuple of values for treeview
        """
        raise NotImplementedError("Subclasses must implement _get_item_values method")

    def on_new(self):
        """
        Handle creating a new inventory item.
        """
        try:
            # Open dialog for adding new item
            self._open_add_item_dialog()
        except Exception as e:
            self.show_error("New Item Error", str(e))

    def on_edit(self):
        """
        Handle editing an existing inventory item.
        """
        try:
            # Get selected item
            selected_item = self._tree.selection()
            if not selected_item:
                self.show_error("Edit Error", "Please select an item to edit")
                return

            # Open dialog for editing
            self._open_edit_item_dialog(selected_item[0])
        except Exception as e:
            self.show_error("Edit Item Error", str(e))

    def on_delete(self):
        """
        Handle deleting an inventory item.
        """
        try:
            # Get selected item
            selected_item = self._tree.selection()
            if not selected_item:
                self.show_error("Delete Error", "Please select an item to delete")
                return

            # Confirm deletion
            confirm = self.show_message(
                "Are you sure you want to delete the selected item?",
                message_type="question"
            )

            if confirm:
                self._delete_item(selected_item[0])
        except Exception as e:
            self.show_error("Delete Item Error", str(e))

    def _open_add_item_dialog(self):
        """
        Open dialog for adding a new item.
        To be implemented by specific inventory views.
        """
        raise NotImplementedError("Subclasses must implement _open_add_item_dialog method")

    def _open_edit_item_dialog(self, item_id):
        """
        Open dialog for editing an existing item.
        To be implemented by specific inventory views.

        Args:
            item_id: Identifier of the item to edit
        """
        raise NotImplementedError("Subclasses must implement _open_edit_item_dialog method")

    def _delete_item(self, item_id):
        """
        Delete an item from the inventory.
        To be implemented by specific inventory views.

        Args:
            item_id: Identifier of the item to delete
        """
        raise NotImplementedError("Subclasses must implement _delete_item method")

    def on_refresh(self):
        """
        Refresh the inventory view.
        """
        try:
            self._load_data()
            self.set_status("Inventory refreshed")
        except Exception as e:
            self.show_error("Refresh Error", str(e))