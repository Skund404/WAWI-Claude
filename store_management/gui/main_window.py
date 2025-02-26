# gui/main_window.py - Updated with new inventory views
"""
Main window for the leatherworking store management system.
Sets up the UI framework and loads different view components.
"""

import logging
import tkinter as tk
from tkinter import ttk

from di.container import DependencyContainer
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.pattern_library import PatternLibrary
from gui.leatherworking.project_dashboard import ProjectDashboard
from gui.order.order_view import OrderView
from gui.shopping_list.shopping_list_view import ShoppingListView
from gui.inventory.hardware_inventory import HardwareInventoryView
from gui.inventory.product_inventory import ProductInventoryView
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


class MainWindow:
    """
    Main application window class.

    Sets up the main UI layout, menu, and manages the different views
    of the application using a notebook with tabs.
    """

    def __init__(self, root: tk.Tk, container: DependencyContainer):
        """
        Initialize the main application window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (DependencyContainer): Dependency injection container
        """
        self.root = root
        self.container = container

        # Setup window properties
        self._setup_window()

        # Create main components
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()

        logger.info("Main window initialized successfully")

    def _setup_window(self):
        """Configure basic window settings."""
        self.root.title("Leatherworking Store Management")

        # Set window size and position
        width, height = 1200, 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _create_menu(self):
        """Create the main application menu."""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh", command=lambda: self.set_status("Refreshing data..."))
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help", command=lambda: self.set_status("Help would be shown here"))
        help_menu.add_command(label="About", command=lambda: self.set_status("About information would be shown here"))
        menubar.add_cascade(label="Help", menu=help_menu)

        # Set the menu
        self.root.config(menu=menubar)

    def _create_notebook(self):
        """Create a notebook with different application views."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Add tabs for each view
        try:
            # Material Inventory
            inventory_frame = ttk.Frame(self.notebook)
            LeatherInventoryView(inventory_frame, self)
            self.notebook.add(inventory_frame, text="Leather Inventory")

            # Hardware Inventory (NEW)
            hardware_frame = ttk.Frame(self.notebook)
            HardwareInventoryView(hardware_frame, self)
            self.notebook.add(hardware_frame, text="Hardware Inventory")

            # Product Inventory (RENAMED from Storage)
            product_frame = ttk.Frame(self.notebook)
            ProductInventoryView(product_frame, self)
            self.notebook.add(product_frame, text="Product Inventory")

            # Pattern Library
            patterns_frame = ttk.Frame(self.notebook)
            PatternLibrary(patterns_frame, self)
            self.notebook.add(patterns_frame, text="Pattern Library")

            # Project Dashboard
            projects_frame = ttk.Frame(self.notebook)
            ProjectDashboard(projects_frame, self)
            self.notebook.add(projects_frame, text="Projects")

            # Orders
            orders_frame = ttk.Frame(self.notebook)
            OrderView(orders_frame, self)
            self.notebook.add(orders_frame, text="Orders")

            # Shopping List
            shopping_frame = ttk.Frame(self.notebook)
            ShoppingListView(shopping_frame, self)
            self.notebook.add(shopping_frame, text="Shopping List")

        except Exception as e:
            logger.error(f"Error creating views: {str(e)}", exc_info=True)

    def _create_status_bar(self):
        """Create a status bar at the bottom of the window."""
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky="ew")

        self.status_var.set("Ready")

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
        return self.container.get_service(service_type)

    def _on_new(self):
        """Handle New action in the menu."""
        self.set_status("New action selected")

    def _on_open(self):
        """Handle Open action in the menu."""
        self.set_status("Open action selected")

    def _on_save(self):
        """Handle Save action in the menu."""
        self.set_status("Save action selected")

    def _on_undo(self):
        """Handle Undo action in the menu."""
        self.set_status("Undo action selected")

    def _on_redo(self):
        """Handle Redo action in the menu."""
        self.set_status("Redo action selected")

    def quit(self):
        """Close the application."""
        logger.info("Closing application")
        self.root.quit()