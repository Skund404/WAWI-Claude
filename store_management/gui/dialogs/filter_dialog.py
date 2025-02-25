# relative/path/filter_dialog.py
"""
Filter Dialog module for advanced filtering of application data.

Provides a dynamic, scrollable interface for creating complex filter conditions
across multiple columns with various operators.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Callable, Optional

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from utils.logging import get_logger
from base_dialog import BaseDialog

logger = get_logger(__name__)


class FilterDialog(BaseDialog):
    """
    Advanced filtering dialog with dynamic filter condition creation.

    Allows users to:
    - Add multiple filter conditions
    - Remove individual filter conditions
    - Apply filters across different columns
    - Validate numeric filters

    Attributes:
        columns (List[str]): List of filterable columns
        filter_callback (Callable): Function to process filter conditions
    """

    @inject(MaterialService)
    def __init__(
            self,
            parent: tk.Tk,
            columns: List[str],
            filter_callback: Callable[[List[Dict]], None]
    ):
        """
        Initialize filter dialog.

        Args:
            parent: Parent window
            columns: List of column names to filter on
            filter_callback: Function to call with filter conditions
        """
        try:
            # Determine dialog size based on parent
            parent_width = parent.winfo_width() or 500
            dialog_width = min(max(500, parent_width), 800)

            super().__init__(
                parent,
                title='Filter Items',
                size=(dialog_width, 400),
                modal=True
            )

            # Dialog configuration
            self.columns = columns
            self.filter_callback = filter_callback
            self.filter_frames: List[Dict[str, Union[tk.Frame, tk.StringVar, ttk.Entry]]] = []

            # Configure buttons
            self.add_ok_cancel_buttons(
                ok_text='Apply Filters',
                ok_command=self.apply_filters,
                cancel_text='Cancel'
            )

            # Add custom buttons
            self.add_button(
                text='Add Filter',
                command=self.add_filter,
                side=tk.LEFT
            )
            self.add_button(
                text='Clear Filters',
                command=self.clear_filters,
                side=tk.LEFT
            )

            # Setup UI
            self._setup_ui()

        except Exception as e:
            logger.error(f"Error initializing FilterDialog: {e}")
            messagebox.showerror("Initialization Error", str(e))
            self.destroy()

    def _setup_ui(self) -> None:
        """
        Setup the dialog UI components with scrollable filter area.
        """
        try:
            # Main frame with padding
            main_frame = ttk.Frame(self.main_frame, padding='10')
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Scrollable container for filters
            container_frame = ttk.Frame(main_frame)
            container_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Canvas and scrollbar
            canvas = tk.Canvas(container_frame)
            scrollbar = ttk.Scrollbar(
                container_frame,
                orient='vertical',
                command=canvas.yview
            )

            # Filters frame inside canvas
            self.filters_frame = ttk.Frame(canvas)
            self.filters_frame.bind(
                '<Configure>',
                lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
            )

            # Create scrollable window
            canvas.create_window((0, 0), window=self.filters_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)

            # Pack canvas and scrollbar
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

            # Add initial filter
            self.add_filter()

        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            messagebox.showerror("UI Setup Error", str(e))

    def add_filter(self) -> None:
        """
        Add a new filter row to the dialog.
        """
        try:
            # Create filter frame
            filter_frame = ttk.Frame(self.filters_frame)
            filter_frame.pack(fill=tk.X, pady=2)

            # Column selection
            column_var = tk.StringVar()
            column_combo = ttk.Combobox(
                filter_frame,
                textvariable=column_var,
                width=20
            )
            column_combo['values'] = [
                col.replace('_', ' ').title() for col in self.columns
            ]
            column_combo.pack(side=tk.LEFT, padx=2)
            column_combo.state(['readonly'])

            # Operator selection
            operator_var = tk.StringVar()
            operator_combo = ttk.Combobox(
                filter_frame,
                textvariable=operator_var,
                width=15
            )
            operator_combo['values'] = [
                'equals', 'contains', 'greater than', 'less than'
            ]
            operator_combo.pack(side=tk.LEFT, padx=2)
            operator_combo.state(['readonly'])

            # Value entry
            value_entry = ttk.Entry(filter_frame)
            value_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

            # Remove filter button
            remove_btn = ttk.Button(
                filter_frame,
                text='✕',
                width=3,
                command=lambda f=filter_frame: self.remove_filter(f)
            )
            remove_btn.pack(side=tk.LEFT, padx=2)

            # Store filter components
            filter_components = {
                'frame': filter_frame,
                'column': column_var,
                'operator': operator_var,
                'value': value_entry
            }
            self.filter_frames.append(filter_components)

            # Set default values if columns exist
            if self.columns:
                column_combo.set(self.columns[0].replace('_', ' ').title())
                operator_combo.set('equals')

        except Exception as e:
            logger.error(f"Error adding filter: {e}")
            messagebox.showerror("Filter Addition Error", str(e))

    def remove_filter(self, filter_frame: tk.Frame) -> None:
        """
        Remove a specific filter row.

        Args:
            filter_frame: Frame to remove
        """
        try:
            # Remove from tracked filters
            self.filter_frames = [
                f for f in self.filter_frames if f['frame'] != filter_frame
            ]

            # Destroy frame
            filter_frame.destroy()

        except Exception as e:
            logger.error(f"Error removing filter: {e}")
            messagebox.showerror("Filter Removal Error", str(e))

    def get_filter_conditions(self) -> List[Dict[str, str]]:
        """
        Compile all filter conditions from the dialog.

        Returns:
            List of filter condition dictionaries
        """
        conditions = []
        for filter_comp in self.filter_frames:
            # Extract values
            column_display = filter_comp['column'].get()
            column = '_'.join(column_display.lower().split())
            operator = filter_comp['operator'].get()
            value = filter_comp['value'].get().strip()

            # Only add non-empty conditions
            if column and operator and value:
                conditions.append({
                    'column': column,
                    'operator': operator,
                    'value': value
                })

        return conditions

    def apply_filters(self) -> None:
        """
        Apply all filter conditions after validation.
        """
        try:
            # Get filter conditions
            conditions = self.get_filter_conditions()

            # Handle empty conditions
            if not conditions:
                response = messagebox.askyesno(
                    'Warning',
                    'No filter conditions specified. This will show all items. Continue?'
                )
                if not response:
                    return

            # Validate numeric filters
            for condition in conditions:
                if not self._validate_numeric_filter(
                        condition['value'],
                        condition['column']
                ):
                    return

            # Call filter callback
            self.filter_callback(conditions)
            self.destroy()

        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            messagebox.showerror("Filter Application Error", str(e))

    def _validate_numeric_filter(self, value: str, column: str) -> bool:
        """
        Validate numeric filters for specific columns.

        Args:
            value: Input value to validate
            column: Column being filtered

        Returns:
            True if valid, False otherwise
        """
        numeric_columns = ['thickness', 'size_ft', 'area_sqft']

        if column in numeric_columns:
            try:
                float(value)
                return True
            except ValueError:
                messagebox.showerror(
                    'Error',
                    f"{column.replace('_', ' ').title()} must be a number"
                )
                return False

        return True

    def clear_filters(self) -> None:
        """
        Clear all filter conditions.
        """
        try:
            # Destroy all existing filter frames
            for filter_frame in self.filter_frames:
                filter_frame['frame'].destroy()

            # Reset filter frames list
            self.filter_frames.clear()

            # Add a new default filter
            self.add_filter()

        except Exception as e:
            logger.error(f"Error clearing filters: {e}")
            messagebox.showerror("Filter Clearing Error", str(e))


# Optional: Add module-level testing if imported directly
if __name__ == '__main__':
    def dummy_filter_callback(conditions: List[Dict]) -> None:
        """
        Dummy filter callback for testing.

        Args:
            conditions: List of filter conditions
        """
        print("Filter Conditions:")
        for condition in conditions:
            print(condition)


    root = tk.Tk()
    root.withdraw()  # Hide the main window

    test_columns = [
        'name', 'description', 'thickness',
        'size_ft', 'color', 'type'
    ]

    dialog = FilterDialog(
        root,
        columns=test_columns,
        filter_callback=dummy_filter_callback
    )
    root.mainloop()