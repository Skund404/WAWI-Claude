# application.py

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Dict, Type

from gui.main_window import MainWindow
from gui.storage.storage_view import StorageView
from gui.order.order_view import OrderView
from gui.recipe.project_view import RecipeView
from gui.shopping_list.shopping_list_view import ShoppingListView
from gui.leatherworking.project_view import LeatherworkingProjectView

from di.container import DependencyContainer
from di.config import ApplicationConfig

logger = logging.getLogger('application')


class Application:
    """
    Main application class that handles window management and view initialization.
    """

    def __init__(self) -> None:
        """Initialize the application components."""
        self.root: Optional[tk.Tk] = None
        self.main_window: Optional[MainWindow] = None
        self.container = DependencyContainer()
        self._setup_application()

    def _setup_application(self) -> None:
        """Setup the application components and register services."""
        logger.info("Initializing application...")

        # Create and configure root window
        self.root = tk.Tk()
        self.root.withdraw()  # Hide root window initially

        # Register services
        self._register_services()
        logger.info("Services registered successfully")

        # Create main window
        self.main_window = MainWindow(self.root, self)

        # Register views
        self._register_views()

        # Show the main window
        self.root.deiconify()
        logger.info("Application initialized successfully")

    def _register_services(self) -> None:
        """Register all required services in the dependency container."""
        ApplicationConfig.configure_container()
        self.container = ApplicationConfig.get_container()

    def _register_views(self) -> None:
        """Register and initialize all application views."""
        if not self.main_window:
            logger.error("Main window not initialized")
            return

        try:
            self._main_window.add_view("Storage", StorageView(self._main_window, self))
            logger.debug("Registered view: Storage")
        except Exception as e:
            logger.error(f"Failed to register view Storage: {str(e)}")

        try:
            self._main_window.add_view("Orders", OrderView(self._main_window, self))
            logger.debug("Registered view: Orders")
        except Exception as e:
            logger.error(f"Failed to register view Orders: {str(e)}")

        try:
            self._main_window.add_view("Recipes", RecipeView(self._main_window, self))
            logger.debug("Registered view: Recipes")
        except Exception as e:
            logger.error(f"Failed to register view Recipes: {str(e)}")

        try:
            self._main_window.add_view("Shopping Lists", ShoppingListView(self._main_window, self))
            logger.debug("Registered view: Shopping Lists")
        except Exception as e:
            logger.error(f"Failed to register view Shopping Lists: {str(e)}")

        try:
            self._main_window.add_view("Leatherworking", LeatherworkingProjectView(self._main_window, self))
            logger.debug("Registered view: Leatherworking")
        except Exception as e:
            logger.error(f"Failed to register view Leatherworking: {str(e)}")

    def get_service(self, service_type: Type) -> any:
        """
        Get a service instance from the dependency container.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance
        """
        return self.container.resolve(service_type)

    def run(self) -> None:
        """Start the application main loop."""
        if self.root:
            logger.info("Application started")
            self.root.mainloop()

    def quit(self) -> None:
        """Clean up and shut down the application."""
        if self.root:
            self.root.quit()