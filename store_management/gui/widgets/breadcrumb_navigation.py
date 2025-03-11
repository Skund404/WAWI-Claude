# gui/widgets/breadcrumb_navigation.py
"""
Breadcrumb navigation widget for the leatherworking application.

Provides a hierarchical navigation path display for the current view.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional, Dict, Any

from gui.theme import COLORS

logger = logging.getLogger(__name__)


class BreadcrumbNavigation(ttk.Frame):
    """
    A breadcrumb navigation widget showing the current location in the application.

    Displays a hierarchy of views as clickable links, allowing navigation back to
    parent views in the hierarchy.
    """

    def __init__(self, parent, callback=None):
        """
        Initialize the breadcrumb navigation widget.

        Args:
            parent: The parent widget
            callback: Function to call when a breadcrumb is clicked
        """
        super().__init__(parent)

        # Initialize breadcrumb state
        self.breadcrumbs = []
        self.breadcrumb_labels = []
        self.separator_labels = []
        self.callback = callback
        self.logger = logging.getLogger(__name__)

        # Configure style
        self.separator_text = ">"
        self.active_color = COLORS["text"]
        self.inactive_color = COLORS["primary"]
        self.hover_color = COLORS["primary_dark"]
        self.separator_color = COLORS["text_secondary"]

        # Build the widget
        self.build()

    def build(self):
        """Build the breadcrumb navigation widget."""
        # Create main container frame
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.X, expand=True)

    def set_callback(self, callback):
        """
        Set the callback function for breadcrumb clicks.

        Args:
            callback: Function to call when a breadcrumb is clicked
        """
        self.callback = callback

    def update_breadcrumbs(self, breadcrumbs):
        """
        Update the breadcrumb navigation with new breadcrumb data.

        Args:
            breadcrumbs: List of breadcrumb dictionaries with 'title', 'view', and optional 'data'
        """
        # Clear existing breadcrumbs
        self.clear_breadcrumbs()

        # Store new breadcrumbs
        self.breadcrumbs = breadcrumbs

        # Create breadcrumb labels
        for i, crumb in enumerate(breadcrumbs):
            # Add separator if not the first breadcrumb
            if i > 0:
                separator_label = ttk.Label(
                    self.container,
                    text=self.separator_text,
                    foreground=self.separator_color,
                    padding=(5, 0)
                )
                separator_label.pack(side=tk.LEFT)
                self.separator_labels.append(separator_label)

            # Add breadcrumb label
            is_last = i == len(breadcrumbs) - 1

            # Create breadcrumb label
            label = ttk.Label(
                self.container,
                text=crumb["title"],
                foreground=self.active_color if is_last else self.inactive_color,
                cursor="arrow" if is_last else "hand2",
                padding=(0, 0)
            )

            # Bind click event for all except the last breadcrumb
            if not is_last:
                label.bind("<Button-1>", lambda e, idx=i: self._on_breadcrumb_click(idx))
                label.bind("<Enter>", lambda e, l=label: self._on_label_enter(l))
                label.bind("<Leave>", lambda e, l=label: self._on_label_leave(l))

            # Add to container
            label.pack(side=tk.LEFT)
            self.breadcrumb_labels.append(label)

    def add_breadcrumb(self, title, view, data=None):
        """
        Add a new breadcrumb to the navigation path.

        Args:
            title: The display title for the breadcrumb
            view: The view name associated with the breadcrumb
            data: Optional data associated with the breadcrumb
        """
        # Create new breadcrumb
        new_crumb = {
            "title": title,
            "view": view
        }

        if data:
            new_crumb["data"] = data

        # Add to breadcrumbs list
        new_breadcrumbs = self.breadcrumbs + [new_crumb]

        # Update breadcrumbs
        self.update_breadcrumbs(new_breadcrumbs)

    def pop_breadcrumb(self):
        """
        Remove the last breadcrumb from the navigation path.

        Returns:
            The removed breadcrumb or None if the path is empty
        """
        if not self.breadcrumbs:
            return None

        # Remove last breadcrumb
        removed = self.breadcrumbs.pop()

        # Update breadcrumbs
        self.update_breadcrumbs(self.breadcrumbs)

        return removed

    def set_home_breadcrumb(self, title="Dashboard", view="dashboard"):
        """
        Set or reset the navigation to start from the home breadcrumb.

        Args:
            title: The display title for the home breadcrumb
            view: The view name for the home breadcrumb
        """
        self.update_breadcrumbs([{
            "title": title,
            "view": view
        }])

    def clear_breadcrumbs(self):
        """Clear all breadcrumb labels and separators."""
        # Clear breadcrumb labels
        for label in self.breadcrumb_labels:
            label.destroy()
        self.breadcrumb_labels = []

        # Clear separator labels
        for separator in self.separator_labels:
            separator.destroy()
        self.separator_labels = []

    def _on_breadcrumb_click(self, index):
        """
        Handle breadcrumb click event.

        Args:
            index: The index of the clicked breadcrumb
        """
        if index >= len(self.breadcrumbs):
            return

        # Get the clicked breadcrumb
        crumb = self.breadcrumbs[index]

        # Truncate breadcrumbs to the clicked index
        self.breadcrumbs = self.breadcrumbs[:index + 1]
        self.update_breadcrumbs(self.breadcrumbs)

        # Call the callback function
        if self.callback:
            self.callback(crumb["view"], crumb.get("data", None))
        else:
            self.logger.warning("No callback set for breadcrumb navigation")

    def _on_label_enter(self, label):
        """
        Handle mouse enter event on a breadcrumb label.

        Args:
            label: The label widget
        """
        label.configure(foreground=self.hover_color)

    def _on_label_leave(self, label):
        """
        Handle mouse leave event on a breadcrumb label.

        Args:
            label: The label widget
        """
        label.configure(foreground=self.inactive_color)