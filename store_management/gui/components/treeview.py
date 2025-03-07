"""
Enhanced treeview component with sorting, filtering, and pagination.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class EnhancedTreeview(ttk.Treeview):
    """
    Enhanced treeview widget with additional functionality.

    Features:
    - Automatic column sorting
    - Filtering capability
    - Pagination for large datasets
    - Export functionality
    - Context menu support
    - Alternating row colors
    """

    def __init__(self, parent: tk.Widget, columns: List[str],
                 column_widths: Optional[Dict[str, int]] = None,
                 headings: Optional[Dict[str, str]] = None,
                 sortable: bool = True,
                 filterable: bool = True,
                 paginated: bool = False,
                 items_per_page: int = 50,
                 alternate_row_colors: bool = True,
                 **kwargs):
        """
        Initialize the enhanced treeview.

        Args:
            parent: Parent widget
            columns: List of column IDs
            column_widths: Optional dictionary mapping column IDs to widths
            headings: Optional dictionary mapping column IDs to display names
            sortable: Whether the treeview should support column sorting
            filterable: Whether the treeview should support filtering
            paginated: Whether the treeview should support pagination
            items_per_page: Number of items to show per page when paginated
            alternate_row_colors: Whether to use alternating row colors
            **kwargs: Additional arguments to pass to the ttk.Treeview constructor
        """
        # Initialize the parent ttk.Treeview
        super().__init__(
            parent,
            columns=columns,
            show="headings",  # Don't show the first empty column
            **kwargs
        )

        # Store configuration
        self.parent = parent
        self.treeview_columns = columns
        self.sortable = sortable
        self.filterable = filterable
        self.paginated = paginated
        self.items_per_page = items_per_page
        self.alternate_row_colors = alternate_row_colors

        # Set up column widths and headings
        self._configure_columns(columns, column_widths, headings)

        # Initialize state variables
        self.sort_column = None
        self.sort_reverse = False
        self.current_filter = None
        self.current_page = 0
        self.total_pages = 0

        # Set up sorting if enabled
        if sortable:
            self._setup_sorting()

        # Set up alternating row colors if enabled
        if alternate_row_colors:
            self._setup_alternating_colors()

        # Set up right-click context menu functionality
        self.context_menu = None
        self.bind("<Button-3>", self._on_right_click)

        # Set up pagination if enabled
        if paginated:
            self._setup_pagination()

        logger.debug("Enhanced treeview initialized")

    def _configure_columns(self, columns: List[str],
                           column_widths: Optional[Dict[str, int]],
                           headings: Optional[Dict[str, str]]):
        """
        Configure column properties.

        Args:
            columns: List of column IDs
            column_widths: Optional dictionary mapping column IDs to widths
            headings: Optional dictionary mapping column IDs to display names
        """
        # Use default values if not provided
        if column_widths is None:
            column_widths = {}

        if headings is None:
            headings = {col: col.replace('_', ' ').title() for col in columns}

        # Configure columns
        for col in columns:
            width = column_widths.get(col, 100)
            heading = headings.get(col, col.replace('_', ' ').title())

            self.column(col, width=width, anchor="w")
            self.heading(col, text=heading)

    def _setup_sorting(self):
        """Set up column sorting functionality."""
        # Add click handlers to column headings
        for col in self.treeview_columns:
            self.heading(
                col,
                command=lambda _col=col: self.sort_by_column(_col)
            )

    def _setup_alternating_colors(self):
        """Set up alternating row colors."""
        # Bind virtual events that are triggered when items are added
        self.bind("<<TreeviewOpen>>", self._update_row_colors)
        self.bind("<<TreeviewClose>>", self._update_row_colors)

        # Create a tag for odd-numbered rows
        self.tag_configure("odd_row", background="#f5f5f5")

    def _update_row_colors(self, event=None):
        """Update the row colors to create an alternating pattern."""
        if not self.alternate_row_colors:
            return

        # Remove existing tags
        for item in self.get_children():
            self.item(item, tags=())

        # Apply tags to odd rows
        for i, item in enumerate(self.get_children()):
            if i % 2 == 1:
                self.item(item, tags=("odd_row",))

    def _setup_pagination(self):
        """Set up pagination controls."""
        # Create a frame for pagination controls at the bottom of the parent
        self.pagination_frame = ttk.Frame(self.parent)
        self.pagination_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        # Create pagination controls
        self.prev_button = ttk.Button(
            self.pagination_frame,
            text="Previous",
            command=self.previous_page,
            state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.page_label = ttk.Label(
            self.pagination_frame,
            text="Page 1 of 1"
        )
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(
            self.pagination_frame,
            text="Next",
            command=self.next_page,
            state=tk.DISABLED
        )
        self.next_button.pack(side=tk.LEFT, padx=5)

        # Add items per page selector
        ttk.Label(self.pagination_frame, text="Items per page:").pack(side=tk.RIGHT, padx=5)

        self.page_size_var = tk.StringVar(value=str(self.items_per_page))
        page_size_combo = ttk.Combobox(
            self.pagination_frame,
            textvariable=self.page_size_var,
            values=["10", "25", "50", "100", "All"],
            width=5,
            state="readonly"
        )
        page_size_combo.pack(side=tk.RIGHT, padx=5)

        # Bind change event
        page_size_combo.bind("<<ComboboxSelected>>", self._on_page_size_change)

    def _on_page_size_change(self, event):
        """Handle change in items per page."""
        value = self.page_size_var.get()
        if value == "All":
            self.items_per_page = 0  # Show all items
        else:
            try:
                self.items_per_page = int(value)
            except ValueError:
                self.items_per_page = 50  # Default

        # Reset to first page and refresh
        self.current_page = 0
        self.refresh()

    def next_page(self):
        """Go to the next page of results."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.refresh()

    def previous_page(self):
        """Go to the previous page of results."""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def _update_pagination_controls(self):
        """Update pagination controls state and labels."""
        if not self.paginated:
            return

        # Update page label
        self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")

        # Update button states
        self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)

    def sort_by_column(self, column: str):
        """
        Sort the treeview by the specified column.

        Args:
            column: Column ID to sort by
        """
        if not self.sortable:
            return

        logger.debug(f"Sorting by column: {column}")

        # Toggle sort direction if sorting the same column again
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Get all items
        items = [(self.set(k, column), k) for k in self.get_children('')]

        # Sort items
        try:
            # Try to convert to number if possible
            items.sort(
                key=lambda x: self._convert_value(x[0]),
                reverse=self.sort_reverse
            )
        except Exception as e:
            logger.error(f"Error sorting column {column}: {e}")
            # Fall back to string sort
            items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)

        # Rearrange items
        for index, (_, item) in enumerate(items):
            self.move(item, '', index)

        # Update column headings
        self._update_sort_indicators()

    def _update_sort_indicators(self):
        """Update column headings to show sort indicators."""
        for col in self.treeview_columns:
            # Remove sorting indicator from all columns
            current_text = self.heading(col, "text")
            new_text = current_text.replace(' ↑', '').replace(' ↓', '')
            self.heading(col, text=new_text)

        # Add sorting indicator to the sorted column
        if self.sort_column:
            current_text = self.heading(self.sort_column, "text")
            new_text = f"{current_text} {'↓' if self.sort_reverse else '↑'}"
            self.heading(self.sort_column, text=new_text)

    def _convert_value(self, value: str) -> Any:
        """
        Convert a value for sorting.

        Args:
            value: The value to convert

        Returns:
            Converted value appropriate for sorting
        """
        if value == '':
            return ''

        # Try to convert to numeric types
        try:
            # Try integer first
            return int(value)
        except (ValueError, TypeError):
            try:
                # Then try float
                return float(value)
            except (ValueError, TypeError):
                # If not numeric, return lowercase string for case-insensitive sort
                return str(value).lower()

    def set_context_menu(self, menu: tk.Menu):
        """
        Set the context menu for the treeview.

        Args:
            menu: The menu to show on right-click
        """
        self.context_menu = menu

    def _on_right_click(self, event):
        """Handle right-click events to show the context menu."""
        if not self.context_menu:
            return

        # Select the item under the cursor
        item_id = self.identify_row(event.y)
        if item_id:
            # If clicking on an item, select it
            self.selection_set(item_id)

            # Show the context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def set_filter(self, filter_func: Callable[[Dict[str, str]], bool]):
        """
        Set a filter function for the treeview.

        Args:
            filter_func: Function that takes a row (as a dict) and returns True if it should be shown
        """
        if not self.filterable:
            return

        self.current_filter = filter_func
        self.refresh()

    def clear_filter(self):
        """Clear the current filter."""
        self.current_filter = None
        self.refresh()

    def load_data(self, data: List[Dict[str, Any]]):
        """
        Load data into the treeview.

        Args:
            data: List of dictionaries where keys are column IDs
        """
        # Clear existing items
        for item in self.get_children():
            self.delete(item)

        # Store all data for filtering/pagination
        self._all_data = data

        # Apply filter if set
        filtered_data = data
        if self.filterable and self.current_filter:
            filtered_data = [item for item in data if self.current_filter(item)]

        # Calculate pagination if enabled
        if self.paginated and self.items_per_page > 0:
            self.total_pages = (len(filtered_data) + self.items_per_page - 1) // self.items_per_page

            # Adjust current page if needed
            if self.total_pages == 0:
                self.total_pages = 1

            if self.current_page >= self.total_pages:
                self.current_page = self.total_pages - 1

            # Get page of data
            start = self.current_page * self.items_per_page
            end = start + self.items_per_page
            page_data = filtered_data[start:end]
        else:
            # No pagination, use all filtered data
            page_data = filtered_data
            self.total_pages = 1
            self.current_page = 0

        # Insert items
        for item in page_data:
            values = []
            for col in self.treeview_columns:
                values.append(item.get(col, ""))

            self.insert("", tk.END, values=values)

        # Update row colors
        self._update_row_colors()

        # Update pagination controls if enabled
        if self.paginated:
            self._update_pagination_controls()

    def get_selected_items(self) -> List[Dict[str, str]]:
        """
        Get the currently selected items.

        Returns:
            List of dictionaries representing the selected rows
        """
        selected = []
        for item_id in self.selection():
            item = {}
            for col in self.treeview_columns:
                item[col] = self.set(item_id, col)
            selected.append(item)

        return selected

    def refresh(self):
        """Refresh the treeview display."""
        # Reapply current data and filtering
        if hasattr(self, '_all_data'):
            self.load_data(self._all_data)

    def export_data(self, format_type: str = "csv") -> str:
        """
        Export the treeview data to the specified format.

        Args:
            format_type: Export format ("csv", "json", "excel")

        Returns:
            A string containing the exported data or path to file
        """
        # Get all visible data (respecting current filter)
        data = []
        for item_id in self.get_children():
            row = {}
            for col in self.treeview_columns:
                row[col] = self.set(item_id, col)
            data.append(row)

        # Export based on format
        if format_type == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=self.treeview_columns)
            writer.writeheader()
            writer.writerows(data)

            return output.getvalue()

        elif format_type == "json":
            import json
            return json.dumps(data, indent=2)

        elif format_type == "excel":
            try:
                import pandas as pd
                import tempfile

                # Convert to DataFrame
                df = pd.DataFrame(data)

                # Write to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                df.to_excel(temp_file.name, index=False)

                return temp_file.name

            except ImportError:
                logger.error("pandas is required for Excel export")
                raise ValueError("pandas is required for Excel export")

        else:
            raise ValueError(f"Unsupported export format: {format_type}")


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Enhanced Treeview Demo")
    root.geometry("800x600")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    # Create the enhanced treeview
    treeview = EnhancedTreeview(
        frame,
        columns=["id", "name", "type", "quantity", "price"],
        column_widths={"id": 50, "price": 80},
        paginated=True,
        items_per_page=10
    )
    treeview.pack(fill=tk.BOTH, expand=True)

    # Load sample data
    sample_data = []
    for i in range(100):
        sample_data.append({
            "id": i,
            "name": f"Item {i}",
            "type": f"Type {i % 5}",
            "quantity": i * 10,
            "price": f"${i * 5.99:.2f}"
        })

    treeview.load_data(sample_data)

    # Create a context menu
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="View Item", command=lambda: print("View item"))
    context_menu.add_command(label="Edit Item", command=lambda: print("Edit item"))
    context_menu.add_command(label="Delete Item", command=lambda: print("Delete item"))

    treeview.set_context_menu(context_menu)

    root.mainloop()