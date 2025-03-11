# gui/widgets/enhanced_treeview.py
"""
Enhanced Treeview widget with sorting, filtering, and improved interaction.
Extends the standard ttk.Treeview with additional functionality.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

from gui import theme, config


class EnhancedTreeview(ttk.Treeview):
    """
    Enhanced Treeview widget with additional functionality:
    - Column sorting
    - Row highlighting
    - Selection tracking
    - Double-click handling
    - Status-based styling
    """

    def __init__(
            self,
            parent,
            columns: List[str],
            on_sort: Optional[Callable[[str, str], None]] = None,
            on_select: Optional[Callable[[], None]] = None,
            on_double_click: Optional[Callable[[], None]] = None,
            status_column: Optional[str] = None,
            **kwargs
    ):
        """
        Initialize the enhanced treeview.

        Args:
            parent: The parent widget
            columns: List of column identifiers
            on_sort: Callback when a column is sorted (column_id, direction)
            on_select: Callback when an item is selected
            on_double_click: Callback when an item is double-clicked
            status_column: Column containing status values for styling
            **kwargs: Additional arguments for ttk.Treeview
        """
        super().__init__(parent, columns=columns, **kwargs)

        # Store parameters
        self.on_sort_callback = on_sort
        self.on_select_callback = on_select
        self.on_double_click_callback = on_double_click
        self.status_column = status_column
        self.columns = columns

        # Create scrollbars
        self._create_scrollbars(parent)

        # Set up sorting
        self.sort_column = None
        self.sort_direction = "asc"
        self._setup_sorting()

        # Set up selection handling
        self.bind("<<TreeviewSelect>>", self._on_select)
        self.bind("<Double-1>", self._on_double_click)

        # Configure tag styles for status values
        self._setup_tags()

        # Set alternating row colors
        self.tag_configure("odd_row", background=theme.COLORS["bg_light"])
        self.tag_configure("even_row", background="#ffffff")

    def _create_scrollbars(self, parent):
        """
        Create scrollbars for the treeview.

        Args:
            parent: The parent widget
        """
        # Create vertical scrollbar
        scrollbar_y = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.configure(yscrollcommand=scrollbar_y.set)

        # Create horizontal scrollbar
        scrollbar_x = ttk.Scrollbar(parent, orient="horizontal", command=self.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.configure(xscrollcommand=scrollbar_x.set)

        # Pack the treeview
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _setup_sorting(self):
        """Set up column sorting."""
        # Bind click event to column headers
        for col in self.columns:
            self.heading(
                col,
                command=lambda c=col: self._on_column_click(c)
            )

    def _setup_tags(self):
        """Set up tag styles for status values."""
        # Create standard status tags based on themes
        for status, style in theme.STATUS_BADGE_STYLES.items():
            self.tag_configure(
                f"status_{status.lower()}",
                background=style["bg"],
                foreground=style["fg"]
            )

    def _on_column_click(self, column):
        """
        Handle column header click for sorting.

        Args:
            column: The column identifier
        """
        if self.sort_column == column:
            # Toggle direction
            self.sort_direction = "desc" if self.sort_direction == "asc" else "asc"
        else:
            # New column, default to ascending
            self.sort_column = column
            self.sort_direction = "asc"

        # Update column headers to show sort direction
        self._update_sort_indicators()

        # Call sort callback if provided
        if self.on_sort_callback:
            self.on_sort_callback(column, self.sort_direction)

    def _update_sort_indicators(self):
        """Update column headers to show sort indicators."""
        for col in self.columns:
            if col == self.sort_column:
                # Add sort indicator to header text
                indicator = " ▲" if self.sort_direction == "asc" else " ▼"
                self.heading(col, text=f"{self.heading(col)['text'].split(' ')[0]}{indicator}")
            else:
                # Remove any existing indicators
                text = self.heading(col)["text"]
                if " ▲" in text or " ▼" in text:
                    self.heading(col, text=text.split(" ")[0])

    def _on_select(self, event):
        """
        Handle item selection.

        Args:
            event: The TreeviewSelect event
        """
        if self.on_select_callback:
            self.on_select_callback()

    def _on_double_click(self, event):
        """
        Handle item double-click.

        Args:
            event: The Double-1 event
        """
        # Only trigger if clicking on an item (not header or empty space)
        region = self.identify_region(event.x, event.y)
        if region == "cell" or region == "tree":
            if self.on_double_click_callback:
                self.on_double_click_callback()

    def insert_item(self, item_id, values):
        """
        Insert an item into the treeview with proper styling.

        Args:
            item_id: The item identifier
            values: List of values for the item

        Returns:
            The item identifier
        """
        # Determine row tags (for alternating colors)
        row_count = len(self.get_children())
        row_tag = "even_row" if row_count % 2 == 0 else "odd_row"

        # Determine status tag if applicable
        tags = [row_tag]
        if self.status_column and self.status_column in self.columns:
            status_index = self.columns.index(self.status_column)
            if status_index < len(values):
                status_value = str(values[status_index]).lower()
                status_tag = f"status_{status_value}"
                tags.append(status_tag)

        # Insert the item
        return self.insert("", "end", iid=str(item_id), values=values, tags=tags)

    def clear(self):
        """Clear all items from the treeview."""
        for item in self.get_children():
            self.delete(item)

    def set_column_widths(self, widths):
        """
        Set the width of columns.

        Args:
            widths: Dictionary of column_id -> width
        """
        for col, width in widths.items():
            if col in self.columns:
                self.column(col, width=width)

    def get_selected_item_values(self):
        """
        Get the values of the selected item.

        Returns:
            List of values for the selected item, or None if no selection
        """
        selection = self.selection()
        if not selection:
            return None

        return self.item(selection[0], "values")

    def get_selected_id(self):
        """
        Get the ID of the selected item.

        Returns:
            The ID of the selected item, or None if no selection
        """
        selection = self.selection()
        if not selection:
            return None

        return selection[0]