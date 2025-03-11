# gui/utils/view_history_manager.py
"""
View history manager for the leatherworking application.

Manages navigation history for implementing back/forward navigation.
"""

import logging
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)


class ViewHistoryManager:
    """
    Manages view navigation history to support back/forward navigation.

    Maintains a history stack of visited views and provides methods to
    navigate through the history.
    """

    def __init__(self, max_history=50):
        """
        Initialize the view history manager.

        Args:
            max_history: Maximum number of views to keep in history
        """
        self.history = []
        self.current_index = -1
        self.max_history = max_history
        self.navigation_callback = None
        self.logger = logging.getLogger(__name__)

    def set_navigation_callback(self, callback):
        """
        Set the callback function for navigation.

        Args:
            callback: Function to call when navigating to a view
        """
        self.navigation_callback = callback

    def add_view(self, view_name, view_data=None):
        """
        Add a view to the history.

        Args:
            view_name: The name of the view
            view_data: Optional data associated with the view
        """
        # Create view entry
        view_entry = {
            "view_name": view_name,
            "view_data": view_data or {}
        }

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

    def can_go_back(self):
        """
        Check if we can navigate back in history.

        Returns:
            True if we can go back, False otherwise
        """
        return self.current_index > 0

    def can_go_forward(self):
        """
        Check if we can navigate forward in history.

        Returns:
            True if we can go forward, False otherwise
        """
        return self.current_index < len(self.history) - 1

    def go_back(self):
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

    def go_forward(self):
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

    def get_current_view(self):
        """
        Get the current view entry.

        Returns:
            The current view entry or None if history is empty
        """
        if self.current_index < 0 or self.current_index >= len(self.history):
            return None

        return self.history[self.current_index]

    def clear_history(self):
        """Clear the view history."""
        self.history = []
        self.current_index = -1
        self.logger.debug("View history cleared")