# Path: gui/main_window.py

"""
Main Window for the Leatherworking Store Management Application.

Provides the primary application interface with navigation and core functionality.
"""

import logging
import tkinter as tk
from tkinter import ttk

# Import views
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.pattern_library import PatternLibrary
from gui.leatherworking.project_dashboard import ProjectDashboard
from gui.order.order_view import OrderView
from gui.shopping_list.shopping_list_view import ShoppingListView
from gui.storage.storage_view import StorageView

# Import services
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService

# Import dependency injection
from di.container import DependencyContainer

# Configure logging
logger = logging.getLogger(__name__)


class MainWindow:
    """
    Main application window managing different views and service interactions.

    Provides a tabbed interface for various application functionalities.

    Attributes:
        root (tk.Tk): The main application window
        container (DependencyContainer): Dependency injection container
        notebook (ttk.Notebook): Tabbed interface for different views
    """

    def __init__(self, root: tk.Tk, container: DependencyContainer):
        """
        Initialize the main application window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (DependencyContainer): Dependency injection container
        """
        # Store references
        self.root = root
        self.container = container

        # Configure window
        self._setup_window()

        # Create notebook (tabbed interface)
        self._create_notebook()

        # Create menu
        self._create_menu()

        # Create status bar
        self._create_status_bar()

        logger.info("Main window initialized successfully")

    def _setup_window(self):
        """
        Configure basic window settings.
        """
        # Set window size and position
        window_width = 1200
        window_height = 800

        # Calculate screen center
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Set window geometry
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

        # Configure window icon (if available)
        # self.root.iconbitmap('path/to/icon.ico')

    def _create_notebook(self):
        """
        Create a notebook with different application views.
        """
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Create views
        views = [
            ("Leather Inventory", LeatherInventoryView),
            ("Pattern Library", PatternLibrary),
            ("Projects", ProjectDashboard),
            ("Orders", OrderView),
            ("Shopping List", ShoppingListView),
            ("Storage", StorageView)
        ]

        # Add views to notebook
        for title, view_class in views:
            try:
                # Create view with container
                view = view_class(self.notebook, self)
                self.notebook.add(view, text=title)
            except Exception as e:
                logger.error(f"Failed to create {title} view: {e}")

    def _create_menu(self):
        """
        Create the main application menu.
        """
        # Create main menu
        main_menu = tk.Menu(self.root)
        self.root.config(menu=main_menu)

        # File menu
        file_menu = tk.Menu(main_menu, tearoff=0)
        main_menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(main_menu, tearoff=0)
        main_menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)

    def _create_status_bar(self):
        """
        Create a status bar at the bottom of the window.
        """
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message: str):
        """
        Update the status bar message.

        Args:
            message (str): Status message to display
        """
        self.status_var.set(message)

    def get_service(self, service_type):
        """
        Retrieve a service from the dependency injection container.

        Args:
            service_type (type): Service interface to retrieve

        Returns:
            Service implementation
        """
        try:
            return self.container.get(service_type)
        except Exception as e:
            logger.error(f"Failed to retrieve service {service_type}: {e}")
            raise

    def _on_new(self):
        """
        Handle New action in the menu.
        """
        logger.info("New action triggered")
        # Placeholder for new action

    def _on_open(self):
        """
        Handle Open action in the menu.
        """
        logger.info("Open action triggered")
        # Placeholder for open action

    def _on_undo(self):
        """
        Handle Undo action in the menu.
        """
        logger.info("Undo action triggered")
        # Placeholder for undo action

    def _on_redo(self):
        """
        Handle Redo action in the menu.
        """
        logger.info("Redo action triggered")
        # Placeholder for redo action