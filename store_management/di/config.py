"""
File: di/config.py
Configuration for dependency injection container.
Registers service implementations with their interfaces.
"""
import logging
from typing import Type, Any, TypeVar

T = TypeVar('T')


class ApplicationConfig:
    """
    Configures and manages the dependency injection container.
    Handles registration of services and their implementations.
    """

    @classmethod
    def configure_container(cls):
        """
        Creates and configures the dependency injection container.

        Returns:
            DependencyContainer: The configured dependency container
        """
        from di.container import DependencyContainer
        container = DependencyContainer()
        cls._register_services(container)
        return container

    @classmethod
    def _register_services(cls, container):
        """
        Registers all service implementations with their corresponding interfaces.

        Args:
            container: The dependency container to register services with
        """
        try:
            # Import interfaces
            from services.interfaces.inventory_service import IInventoryService
            from services.interfaces.order_service import IOrderService
            from services.interfaces.recipe_service import IRecipeService
            from services.interfaces.shopping_list_service import IShoppingListService
            from services.interfaces.storage_service import IStorageService
            from services.interfaces.supplier_service import ISupplierService

            # Import implementations
            from services.implementations.inventory_service import InventoryService
            from services.implementations.order_service import OrderService
            from services.implementations.recipe_service import RecipeService
            from services.implementations.shopping_list_service import ShoppingListService
            from services.implementations.storage_service import StorageService
            from services.implementations.supplier_service import SupplierService

            # Register each service with its implementation
            container.register(IInventoryService, lambda c: InventoryService(c), singleton=True)
            container.register(IOrderService, lambda c: OrderService(c), singleton=True)
            container.register(IRecipeService, lambda c: RecipeService(c), singleton=True)
            container.register(IShoppingListService, lambda c: ShoppingListService(c), singleton=True)
            container.register(IStorageService, lambda c: StorageService(c), singleton=True)
            container.register(ISupplierService, lambda c: SupplierService(c), singleton=True)

            logging.info("All services registered successfully")
        except Exception as e:
            logging.error(f"Error registering services: {str(e)}")
            raise

        return container

    @classmethod
    def get_service(cls, container, service_type: Type[T]) -> T:
        """
        Resolves and returns a service from the container.

        Args:
            container: The dependency container
            service_type: The type of service to retrieve

        Returns:
            An instance of the requested service type

        Raises:
            ValueError: If no implementation is registered for the service type
        """
        return container.get_service(service_type)