# gui/utils/view_history_manager.py
"""
View history manager for the leatherworking application.

Manages navigation history for implementing back/forward navigation.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Union, TypeVar

logger = logging.getLogger(__name__)

# Type variables for view entry typing
ViewData = TypeVar('ViewData', Dict[str, Any], None)


class ViewHistoryManager:
    """
    Manages view navigation history to support back/forward navigation.

    Maintains a history stack of visited views and provides methods to
    navigate through the history.
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize the view history manager.

        Args:
            max_history: Maximum number of views to keep in history
        """
        self.history: List[Dict[str, Any]] = []
        self.current_index: int = -1
        self.max_history: int = max_history
        self.navigation_callback: Optional[Callable[[str, Any], None]] = None
        self.logger = logging.getLogger(__name__)

    def set_navigation_callback(self, callback: Callable[[str, Any], None]) -> None:
        """
        Set the callback function for navigation.

        Args:
            callback: Function to call when navigating to a view
        """
        self.navigation_callback = callback

    def add_view(self, view_name: str, view_data: Optional[Union[Dict[str, Any], Any]] = None) -> None:
        """
        Add a view to the history.

        Args:
            view_name: The name of the view
            view_data: Optional data associated with the view
        """
        # Normalize view data to be a dictionary
        if view_data is None:
            view_data = {}
        elif not isinstance(view_data, dict):
            view_data = {"data": view_data}

        # Create view entry
        view_entry = {
            "view_name": view_name,
            "view_data": view_data
        }

        # Check if this is the same as the current view (avoid duplicates)
        if (self.current_index >= 0 and
                self.history[self.current_index]["view_name"] == view_name and
                self._are_view_params_equal(self.history[self.current_index]["view_data"], view_data)):
            # Same view and parameters, don't add to history
            return

        # Check if we're not at the end of history
        if self.current_index < len(self.history) - 1:
            # Remove forward history
            self.history = self.history[:self.current_index + 1]

        # Add the view to history
        self.history.append(view_entry)
        self.current_index = len(self.history) - 1

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1

        # Log navigation
        self.logger.debug(f"Added view to history: {view_name}")

    def _are_view_params_equal(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> bool:
        """
        Compare two view parameter dictionaries to determine if they represent the same view state.

        Args:
            params1: First parameter dictionary
            params2: Second parameter dictionary

        Returns:
            bool: True if parameters are considered equal, False otherwise
        """
        # Handle entity ID comparison specially (most common case)
        if 'entity_id' in params1 and 'entity_id' in params2:
            if params1['entity_id'] != params2['entity_id']:
                return False

        # For simple cases, direct equality is sufficient
        if len(params1) == len(params2):
            # Skip comparison of certain UI state parameters that don't affect view identity
            keys_to_skip = {'scroll_position', 'selected_index', 'last_updated'}

            for key in params1:
                if key in keys_to_skip:
                    continue
                if key not in params2 or params1[key] != params2[key]:
                    return False
            return True

        return False

    def can_go_back(self) -> bool:
        """
        Check if we can navigate back in history.

        Returns:
            True if we can go back, False otherwise
        """
        return self.current_index > 0

    def can_go_forward(self) -> bool:
        """
        Check if we can navigate forward in history.

        Returns:
            True if we can go forward, False otherwise
        """
        return self.current_index < len(self.history) - 1

    def go_back(self) -> bool:
        """
        Navigate back in history.

        Returns:
            True if navigation was successful, False otherwise
        """
        if not self.can_go_back():
            return False

        # Move back in history
        self.current_index -= 1
        view_entry = self.history[self.current_index]

        # Navigate to the view
        if self.navigation_callback:
            self.navigation_callback(
                view_entry["view_name"],
                view_entry["view_data"]
            )
            self.logger.debug(f"Navigated back to: {view_entry['view_name']}")
            return True
        else:
            self.logger.warning("No navigation callback set")
            return False

    def go_forward(self) -> bool:
        """
        Navigate forward in history.

        Returns:
            True if navigation was successful, False otherwise
        """
        if not self.can_go_forward():
            return False

        # Move forward in history
        self.current_index += 1
        view_entry = self.history[self.current_index]

        # Navigate to the view
        if self.navigation_callback:
            self.navigation_callback(
                view_entry["view_name"],
                view_entry["view_data"]
            )
            self.logger.debug(f"Navigated forward to: {view_entry['view_name']}")
            return True
        else:
            self.logger.warning("No navigation callback set")
            return False

    def get_current_view(self) -> Optional[Dict[str, Any]]:
        """
        Get the current view entry.

        Returns:
            The current view entry or None if history is empty
        """
        if self.current_index < 0 or self.current_index >= len(self.history):
            return None

        return self.history[self.current_index]

    def get_previous_view(self) -> Optional[Dict[str, Any]]:
        """
        Get the previous view entry.

        Returns:
            The previous view entry or None if no previous view exists
        """
        if self.current_index <= 0 or self.current_index >= len(self.history):
            return None

        return self.history[self.current_index - 1]

    def clear_history(self) -> None:
        """Clear the view history."""
        self.history = []
        self.current_index = -1
        self.logger.debug("View history cleared")

    def contains_view(self, view_name: str, view_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if the history contains a specific view.

        Args:
            view_name: The name of the view to check
            view_data: Optional data to match with the view

        Returns:
            bool: True if the view is in history, False otherwise
        """
        if not self.history:
            return False

        for entry in self.history:
            if entry["view_name"] == view_name:
                if view_data is None:
                    return True

                if self._are_view_params_equal(entry["view_data"], view_data):
                    return True

        return False

    def replace_current_view(self, view_name: str, view_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Replace the current view in history without adding a new entry.
        Useful for updating the current view's parameters.

        Args:
            view_name: The name of the view
            view_data: Optional data associated with the view
        """
        if self.current_index < 0:
            # No current view to replace, just add
            self.add_view(view_name, view_data)
            return

        # Normalize view data
        if view_data is None:
            view_data = {}

        # Replace the current entry
        self.history[self.current_index] = {
            "view_name": view_name,
            "view_data": view_data
        }

        self.logger.debug(f"Replaced current view in history: {view_name}")