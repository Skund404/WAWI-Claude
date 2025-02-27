# relative path: store_management/gui/main_window.py
"""
Main Window for the Leatherworking Store Management application.

Provides the primary application interface with tab-based navigation.
"""

import logging
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from typing import Any, Type, Optional

# Import views
from gui.inventory.hardware_inventory import HardwareInventoryView
from gui.inventory.product_inventory import ProductInventoryView
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.pattern_library import PatternLibrary
from gui.order.order_view import OrderView
from gui.product.project_view import ProjectView
from gui.storage.storage_view import StorageView

# Import service interfaces
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService
from services.interfaces.pattern_service import IPatternService


class MainWindow:
    """
    Main application window managing multiple views and service retrieval.

    Provides a notebook-based interface with tabs for different
    functional areas of the leatherworking store management system.

    Attributes:
        root (tk.Tk): Root Tkinter window
        container (Any): Dependency injection container
        notebook (ttk.Notebook): Tabbed interface
    """

    def __init__(self, root: tk.Tk, container: Any):
        """
        Initialize the main window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (Any): Dependency injection container
        """
        self.root = root
        self.container = container

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__module__)

        # Configure window
        self._setup_window()

        # Create notebook for tabs
        self._create_notebook()

        # Create status bar
        self._create_status_bar()

        # Create menu
        self._create_menu()

    def _setup_window(self):
        """
        Configure basic window settings.
        """
        self.root.title("Leatherworking Store Management")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_notebook(self):
        """
        Create a notebook with tabs for different application modules.
        """
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Define views with their configurations
        views = [
            {
                "name": "Leather Inventory",
                "view": LeatherInventoryView,
                "service": IMaterialService
            },
            {
                "name": "Hardware Inventory",
                "view": HardwareInventoryView,
                "service": IMaterialService
            },
            {
                "name": "Product Inventory",
                "view": ProductInventoryView,
                "service": IStorageService
            },
            {
                "name": "Pattern Library",
                "view": PatternLibrary,
                "service": IPatternService
            },
            {
                "name": "Projects",
                "view": ProjectView,
                "service": IProjectService
            },
            {
                "name": "Orders",
                "view": OrderView,
                "service": IOrderService
            },
            {
                "name": "Storage",
                "view": StorageView,
                "service": IStorageService
            }
        ]

        # Create tabs with error handling
        for view_config in views:
            try:
                # Try to retrieve the service
                service = self.get_service(view_config['service'])

                # Create the view
                view = view_config['view'](self.notebook, self)
                self.notebook.add(view, text=view_config['name'])

                self.logger.info(f"{view_config['name']} view initialized")
            except Exception as e:
                self.logger.error(f"Failed to load {view_config['name']} view: {e}")
                # Optionally show a message to the user
                tkinter.messagebox.showwarning(
                    "View Initialization Error",
                    f"Could not load {view_config['name']} view: {e}"
                )

    def _create_status_bar(self):
        """
        Create a status bar at the bottom of the window.
        """
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_menu(self):
        """
        Create the main application menu.
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)

    def get_service(self, service_type: Type[Any]) -> Any:
        """
        Retrieve a service from the dependency injection container.

        Args:
            service_type (Type): The type/interface of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            ValueError: If the service cannot be retrieved
        """
        try:
            # Attempt to get the service using container's get method
            return self.container.get(service_type)
        except Exception as e:
            self.logger.error(f"Error getting service {service_type}: {e}")
            raise ValueError(f"Service {service_type} not available") from e

    def set_status(self, message: str):
        """
        Update the status bar message.

        Args:
            message (str): Status message to display
        """
        self.status_var.set(message)
        self.logger.info(message)

    def _on_new(self):
        """Handle New action."""
        self.logger.info("New action triggered")
        self.set_status("Creating new item...")

    def _on_open(self):
        """Handle Open action."""
        self.logger.info("Open action triggered")
        self.set_status("Opening file...")

    def _on_save(self):
        """Handle Save action."""
        self.logger.info("Save action triggered")
        self.set_status("Saving...")

    def _on_undo(self):
        """Handle Undo action."""
        self.logger.info("Undo action triggered")
        self.set_status("Undoing last action...")

    def _on_redo(self):
        """Handle Redo action."""
        self.logger.info("Redo action triggered")
        self.set_status("Redoing last action...")

    def _on_closing(self):
        """
        Handle application closing.
        Provides confirmation dialog and cleanup.
        """
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.logger.info("Application closing")
            self.root.destroy()

    def mainloop(self):
        """
        Start the main event loop.
        """
        self.logger.info("Starting main event loop...")
        self.root.mainloop()