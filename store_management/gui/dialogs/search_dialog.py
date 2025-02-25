# relative/path/search_dialog.py
"""
Search Dialog module for flexible item searching in the application.

This module provides a SearchDialog class for creating a dynamic search interface
that allows users to search across different columns with configurable options.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Dict, Optional

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from utils.logging import get_logger

logger = get_logger(__name__)


class SearchDialog(tk.Toplevel):
    """
    A dialog window for performing advanced searches across multiple columns.

    Attributes:
        parent (tk.Tk): The parent window
        columns (List[str]): List of searchable columns
        search_callback (Callable[[Dict], None]): Callback function for search results
    """

    @inject(MaterialService)
    def __init__(
            self,
            parent: tk.Tk,
            columns: List[str],
            search_callback: Callable[[Dict[str, str]], None]
    ):
        """
        Initialize the search dialog.

        Args:
            parent (tk.Tk): Parent window
            columns (List[str]): List of columns to search in
            search_callback (Callable[[Dict[str, str]], None]): Callback to process search
        """
        try:
            super().__init__(parent)

            # Configure dialog properties
            self.title('Search Items')
            self.geometry('400x250')
            self.transient(parent)
            self.grab_set()

            # Prepare searchable columns
            self.columns = ['All'] + columns
            self.search_callback = search_callback

            # Setup user interface
            self._setup_ui()
        except Exception as e:
            logger.error(f"Error initializing SearchDialog: {e}")
            tk.messagebox.showerror("Initialization Error", str(e))
            self.destroy()

    def _setup_ui(self) -> None:
        """
        Setup the dialog user interface components.
        Creates search input, column selection, and action buttons.
        """
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Column Selection
        ttk.Label(main_frame, text='Search in:').grid(
            row=0, column=0, sticky='w', padx=5, pady=2
        )
        self.column_var = tk.StringVar(value='All')
        column_combo = ttk.Combobox(
            main_frame,
            textvariable=self.column_var,
            values=[col.replace('_', ' ').title() for col in self.columns]
        )
        column_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        column_combo.state(['readonly'])

        # Search Entry
        ttk.Label(main_frame, text='Search for:').grid(
            row=1, column=0, sticky='w', padx=5, pady=2
        )
        self.search_entry = ttk.Entry(main_frame)
        self.search_entry.grid(
            row=1, column=1, sticky='ew', padx=5, pady=2
        )

        # Case Sensitivity Option
        self.match_case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text='Match case',
            variable=self.match_case_var
        ).grid(row=2, column=1, sticky='w', padx=5, pady=2)

        # Partial/Exact Match Option
        self.exact_match_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text='Exact match',
            variable=self.exact_match_var
        ).grid(row=3, column=1, sticky='w', padx=5, pady=2)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame,
            text='Search',
            command=self._search
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text='Cancel',
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Focus and bind return key
        self.search_entry.focus_set()
        self.search_entry.bind('<Return>', lambda e: self._search())

    def _search(self) -> None:
        """
        Execute the search based on user-specified parameters.
        Validates input and calls the search callback with parameters.
        """
        try:
            # Determine search column
            column_display = self.column_var.get()
            column = (
                self.columns[0] if column_display == 'All'
                else '_'.join(column_display.lower().split())
            )

            # Prepare search parameters
            search_params: Dict[str, str] = {
                'column': column,
                'text': self.search_entry.get().strip(),
                'match_case': str(self.match_case_var.get()),
                'exact_match': str(self.exact_match_var.get())
            }

            # Validate search text
            if not search_params['text']:
                tk.messagebox.showwarning(
                    'Empty Search',
                    'Please enter a search term.'
                )
                return

            # Call search callback
            self.search_callback(search_params)
            self.destroy()

        except Exception as e:
            logger.error(f"Search execution error: {e}")
            tk.messagebox.showerror("Search Error", str(e))


# Optional: Add module-level validation if imported directly
if __name__ == '__main__':
    def dummy_search(params: Dict[str, str]) -> None:
        """Dummy search callback for testing."""
        print(f"Search Parameters: {params}")


    root = tk.Tk()
    root.withdraw()  # Hide the main window

    dialog = SearchDialog(
        root,
        columns=['name', 'description', 'category'],
        search_callback=dummy_search
    )
    root.mainloop()