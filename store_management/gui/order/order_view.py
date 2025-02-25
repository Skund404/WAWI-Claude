# order_view.py
import tkinter
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Tuple
import logging

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService

logger = logging.getLogger(__name__)


class BaseView(tkinter.Frame):
    """Base class for all views in the application."""

    def __init__(self, parent, app):
        """Initialize the base view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.pack(fill=tkinter.BOTH, expand=True)

    def get_service(self, service_interface):
        """Get a service from the dependency injection container.

        Args:
            service_interface: Interface class of the service

        Returns:
            Instance of the requested service
        """
        # This is a placeholder assuming the app has a get_service method
        return self.app.get_service(service_interface)

    def show_error(self, title: str, message: str):
        """Show an error message dialog.

        Args:
            title: Error dialog title
            message: Error message to display
        """
        messagebox.showerror(title, message)
        logger.error(f"{title}: {message}")


class SearchDialog(tkinter.Toplevel):
    """Dialog for searching data."""

    def __init__(self, parent, columns: List[str], search_callback: callable):
        """Initialize the search dialog.

        Args:
            parent: Parent widget
            columns: List of column names to search in
            search_callback: Function to call with search parameters
        """
        super().__init__(parent)
        self.title("Search")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()

        self.columns = columns
        self.search_callback = search_callback

        self._create_widgets()

    def _create_widgets(self):
        """Create the dialog widgets."""
        # Search term entry
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tkinter.BOTH, expand=True)

        ttk.Label(frame, text="Search term:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.search_var = tkinter.StringVar()
        ttk.Entry(frame, textvariable=self.search_var, width=30).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Column selection
        ttk.Label(frame, text="Search in:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.column_vars = []
        col_frame = ttk.Frame(frame)
        col_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        for i, col in enumerate(self.columns):
            var = tkinter.BooleanVar(value=True)
            self.column_vars.append(var)
            ttk.Checkbutton(col_frame, text=col, variable=var).grid(row=i // 2, column=i % 2, sticky="w")

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Button(button_frame, text="Search", command=self._perform_search).pack(side=tkinter.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tkinter.LEFT, padx=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

    def _perform_search(self):
        """Perform the search operation."""
        search_term = self.search_var.get()
        selected_columns = [col for col, var in zip(self.columns, self.column_vars) if var.get()]

        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term")
            return

        if not selected_columns:
            messagebox.showwarning("Warning", "Please select at least one column to search in")
            return

        self.search_callback(search_term, selected_columns)
        self.destroy()


class OrderView(BaseView):
    """View for managing orders in the application.

    Provides functionality for:
    - Viewing order list
    - Creating new orders
    - Updating existing orders
    - Deleting orders
    - Filtering and searching orders
    """
    # Interface definition used for dependency injection
    IOrderService = OrderService

    @inject(MaterialService)
    def __init__(self, parent, app):
        """Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.setup_ui()

    @inject(MaterialService)
    def setup_ui(self):
        """Set up the user interface components."""
        self._setup_treeview()
        self.load_data()
        self.tree.bind('<Double-1>', self.on_double_click)

    @inject(MaterialService)
    def _get_columns(self):
        """Get the column definitions for the treeview."""
        return ('Order Number', 'Customer Name', 'Status', 'Payment Status', 'Total Amount', 'Notes')

    @inject(MaterialService)
    def _setup_treeview(self):
        """Configure the treeview columns and headings."""
        columns = self._get_columns()
        self.tree = tkinter.ttk.Treeview(self, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self._sort_column(_col))
            self.tree.column(col, minwidth=100)

        # Add scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Make the treeview expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)