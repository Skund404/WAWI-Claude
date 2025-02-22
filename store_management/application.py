# Path: application.py
"""
Main application class that orchestrates the components of the system.
"""
import tkinter as tk
import logging
from typing import Any, Type

from di.container import DependencyContainer
from services.interfaces.storage_service import IStorageService
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.order_service import IOrderService
from services.interfaces.recipe_service import IRecipeService
from services.interfaces.shopping_list_service import IShoppingListService
from services.interfaces.supplier_service import ISupplierService

from services.implementations.storage_service import StorageService
from services.implementations.inventory_service import InventoryService
from services.implementations.order_service import OrderService
from services.implementations.recipe_service import RecipeService
from services.implementations.shopping_list_service import ShoppingListService
from services.implementations.supplier_service import SupplierService

logger = logging.getLogger(__name__)

class Application:
    """
    Main application class responsible for running the application.
    """

    def __init__(self):
        """Initialize the application."""
        self.container = DependencyContainer()
        self.root = None
        self.main_window = None
        self._register_services()
        logger.info("Application initialized")

    def _register_services(self):
        """Register all services in the dependency container."""
        try:
            # Register all services
            self.container.register(IStorageService, lambda c: StorageService(c), True)
            self.container.register(IInventoryService, lambda c: InventoryService(c), True)
            self.container.register(IOrderService, lambda c: OrderService(c), True)
            self.container.register(IRecipeService, lambda c: RecipeService(c), True)
            self.container.register(IShoppingListService, lambda c: ShoppingListService(c), True)
            self.container.register(ISupplierService, lambda c: SupplierService(c), True)

            logger.info("Services registered successfully")
        except Exception as e:
            logger.error(f"Error registering services: {str(e)}", exc_info=True)
            raise

    def get_service(self, service_type: Type):
        """
        Get a service from the container.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance
        """
        if service_type is None:
            logger.warning("Attempted to get service with None service_type")
            return None

        try:
            service = self.container.resolve(service_type)
            logger.debug(f"Got service: {service_type.__name__}")
            return service
        except Exception as e:
            logger.error(f"Error getting service {service_type}: {str(e)}")
            return None

    def run(self):
        """Run the application."""
        try:
            # Create the main window
            self.root = tk.Tk()

            # Import here to avoid circular import
            from gui.main_window import MainWindow
            self.main_window = MainWindow(self.root, self)

            # Start the main loop
            logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error running application: {str(e)}", exc_info=True)
            raise

    def quit(self):
        """Quit the application."""
        try:
            # Perform cleanup
            if self.root:
                self.root.destroy()
            logger.info("Application terminated")
        except Exception as e:
            logger.error(f"Error quitting application: {str(e)}", exc_info=True)
            raise