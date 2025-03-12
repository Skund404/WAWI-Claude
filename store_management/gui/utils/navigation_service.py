# gui/utils/navigation_service.py
"""
Navigation service for the leatherworking application.

Provides centralized navigation functionality with standardized patterns
for navigating between views and handling view parameters.
"""

import logging
import sys
import os
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional, Union, Callable, TypeVar, Type

# Import using lazy imports to avoid circular dependencies
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from utils.circular_import_resolver import register_lazy_import, resolve_lazy_import

# Register lazy imports for views
register_lazy_import("gui.views.dashboard.main_dashboard", "DashboardView")
register_lazy_import("gui.utils.view_history_manager", "ViewHistoryManager")

# Type variables for generic typing
T = TypeVar('T')

logger = logging.getLogger(__name__)


class NavigationService:
    """
    Centralized navigation service with standardized patterns.

    Provides methods for navigating between views, handling view parameters,
    and maintaining navigation history.
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls) -> 'NavigationService':
        """
        Get the singleton instance of the navigation service.

        Returns:
            NavigationService: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the navigation service."""
        self.main_window = None
        self.view_history_manager = None
        self.logger = logging.getLogger(__name__)

    def initialize(self, main_window: Any, view_history_manager: Any) -> None:
        """
        Initialize the navigation service with main window and history manager.

        Args:
            main_window: The main window instance
            view_history_manager: The view history manager instance
        """
        self.main_window = main_window
        self.view_history_manager = view_history_manager
        self.logger.info("Navigation service initialized")

    @staticmethod
    def navigate_to_view(parent_window: Any, view_name: str, view_params: Optional[Dict[str, Any]] = None,
                         add_to_history: bool = True) -> Any:
        """
        Navigate to a specific view with parameters.

        Args:
            parent_window: The parent window containing the main window instance
            view_name: The name of the view to navigate to
            view_params: Optional parameters to pass to the view
            add_to_history: Whether to add this navigation to history

        Returns:
            Any: The view instance if successfully navigated, None otherwise
        """
        logger.info(f"Navigating to view: {view_name}")

        # Find the main window instance
        main_window = _find_main_window(parent_window)
        if not main_window:
            logger.error("Cannot navigate: Main window not found")
            return None

        try:
            # Special handling for dashboard
            if view_name == "dashboard":
                return main_window.show_dashboard(add_to_history=add_to_history)

            # For all other views
            return main_window.show_view(
                view_name=view_name,
                add_to_history=add_to_history,
                view_data=view_params
            )
        except Exception as e:
            logger.error(f"Error navigating to view {view_name}: {str(e)}")
            messagebox.showerror("Navigation Error", f"Failed to navigate to {view_name}: {str(e)}")
            return None

    @staticmethod
    def navigate_to_entity_details(parent_window: Any, entity_type: str, entity_id: Union[int, str],
                                   readonly: bool = False) -> Any:
        """
        Navigate to entity details view with standardized parameters.

        Args:
            parent_window: The parent window containing the main window instance
            entity_type: The type of entity (e.g., 'material', 'product', 'inventory')
            entity_id: The ID of the entity to view
            readonly: Whether to open the details in readonly mode

        Returns:
            Any: The view instance if successfully navigated, None otherwise
        """
        # Map entity types to their corresponding view names
        entity_view_mapping = {
            "material": "materials",
            "leather": "leather",
            "hardware": "hardware",
            "supplies": "supplies",
            "product": "products",
            "inventory": "inventory",
            "storage_location": "storage",
            "project": "projects",
            "pattern": "patterns",
            "component": "components",
            "customer": "customers",
            "supplier": "suppliers",
            "sale": "sales",
            "purchase": "purchases",
            "tool": "tools"
        }

        # If entity type not in mapping, use the entity type as the view name
        view_name = entity_view_mapping.get(entity_type, entity_type)

        # Prepare view parameters
        view_params = {
            "entity_id": entity_id,
            "readonly": readonly,
            "details_mode": True
        }

        logger.info(f"Navigating to {entity_type} details, ID: {entity_id}")
        return NavigationService.navigate_to_view(parent_window, view_name, view_params)

    @staticmethod
    def navigate_back(parent_window: Any) -> bool:
        """
        Navigate back in history.

        Args:
            parent_window: The parent window containing the main window instance

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        main_window = _find_main_window(parent_window)
        if not main_window:
            logger.error("Cannot navigate back: Main window not found")
            return False

        return main_window.navigate_back()

    @staticmethod
    def navigate_forward(parent_window: Any) -> bool:
        """
        Navigate forward in history.

        Args:
            parent_window: The parent window containing the main window instance

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        main_window = _find_main_window(parent_window)
        if not main_window:
            logger.error("Cannot navigate forward: Main window not found")
            return False

        return main_window.navigate_forward()

    @staticmethod
    def can_go_back(parent_window: Any) -> bool:
        """
        Check if navigation back is possible.

        Args:
            parent_window: The parent window containing the main window instance

        Returns:
            bool: True if navigation back is possible, False otherwise
        """
        main_window = _find_main_window(parent_window)
        if not main_window:
            return False

        return main_window.view_history.can_go_back()

    @staticmethod
    def can_go_forward(parent_window: Any) -> bool:
        """
        Check if navigation forward is possible.

        Args:
            parent_window: The parent window containing the main window instance

        Returns:
            bool: True if navigation forward is possible, False otherwise
        """
        main_window = _find_main_window(parent_window)
        if not main_window:
            return False

        return main_window.view_history.can_go_forward()

    @staticmethod
    def open_dialog(parent_window: Any, dialog_class: Type[T], **kwargs) -> Optional[T]:
        """
        Open a dialog with standardized handling.

        Args:
            parent_window: The parent window for the dialog
            dialog_class: The dialog class to instantiate
            **kwargs: Additional keyword arguments to pass to the dialog constructor

        Returns:
            Optional[T]: The dialog instance or None if failed
        """
        try:
            dialog = dialog_class(parent_window, **kwargs)
            return dialog.show()
        except Exception as e:
            logger.error(f"Error opening dialog {dialog_class.__name__}: {str(e)}")
            messagebox.showerror("Dialog Error", f"Failed to open dialog: {str(e)}")
            return None


def _find_main_window(widget: Any) -> Optional[Any]:
    """
    Find the main window instance from any widget in the application.

    Args:
        widget: Any widget in the application

    Returns:
        Optional[Any]: The main window instance or None if not found
    """
    # If widget is None, we can't find the main window
    if widget is None:
        return None

    # If widget has 'main_window' attribute, return it
    if hasattr(widget, 'main_window'):
        return widget.main_window

    # If widget is the main window itself
    if hasattr(widget, 'show_view') and hasattr(widget, 'show_dashboard'):
        return widget

    # Check if we can find the main window in the widget's attributes
    for attr_name in dir(widget):
        if attr_name.startswith('_'):
            continue

        try:
            attr = getattr(widget, attr_name)
            if hasattr(attr, 'show_view') and hasattr(attr, 'show_dashboard'):
                return attr
        except (AttributeError, TypeError):
            pass

    # Traverse up the widget tree
    if hasattr(widget, 'master') and widget.master is not None:
        return _find_main_window(widget.master)

    # If we reach the root widget and still haven't found the main window
    if hasattr(widget, 'winfo_toplevel'):
        top_level = widget.winfo_toplevel()
        if top_level != widget:
            return _find_main_window(top_level)

    return None