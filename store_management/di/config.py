# Path: store_management\store_management\di\config.py
from typing import Dict, Any, Type, TypeVar

from store_management.di.container import DependencyContainer
from store_management.database.sqlalchemy.session import get_db_session
from store_management.database.sqlalchemy.core.base_manager import BaseManager
from store_management.database.sqlalchemy.core.manager_factory import get_manager
from store_management.services.interfaces.storage_service import IStorageService
from store_management.services.implementations.storage_service import StorageService
from store_management.services.interfaces.order_service import IOrderService
from store_management.services.implementations.order_service import OrderService
from store_management.services.interfaces.recipe_service import IRecipeService
from store_management.services.implementations.recipe_service import RecipeService
from store_management.services.interfaces.shopping_list_service import IShoppingListService
from store_management.services.implementations.shopping_list_service import ShoppingListService
from store_management.services.interfaces.supplier_service import ISupplierService
from store_management.services.implementations.supplier_service import SupplierService

# Import all necessary managers
from store_management.database.sqlalchemy.core.specialized.storage_manager import StorageManager
from store_management.database.sqlalchemy.core.specialized.order_manager import OrderManager
from store_management.database.sqlalchemy.core.specialized.recipe_manager import RecipeManager
from store_management.database.sqlalchemy.core.specialized.shopping_list_manager import ShoppingListManager
from store_management.database.sqlalchemy.core.specialized.supplier_manager import SupplierManager

# Convenience type variable
T = TypeVar('T')


class ApplicationConfig:
    """
    Dependency Injection Configuration for the Store Management Application.

    Responsible for:
    - Configuring the dependency injection container
    - Registering services and their dependencies
    - Providing a centralized configuration mechanism
    """

    @classmethod
    def configure_container(cls) -> DependencyContainer:
        """
        Configure the dependency injection container.

        This method sets up the entire dependency graph for the application.

        Returns:
            Configured DependencyContainer instance
        """
        container = DependencyContainer()

        # Register services
        cls._register_services(container)

        return container

    @classmethod
    def _register_services(cls, container: DependencyContainer) -> None:
        """
        Register all application services in the dependency container.

        Args:
            container: Dependency container to register services in
        """
        # Register Storage Manager
        container.register(
            StorageManager,
            lambda: get_manager(StorageManager),
            singleton=True
        )

        # Register Order Manager
        container.register(
            OrderManager,
            lambda: get_manager(OrderManager),
            singleton=True
        )

        # Register Recipe Manager
        container.register(
            RecipeManager,
            lambda: get_manager(RecipeManager),
            singleton=True
        )

        # Register Shopping List Manager
        container.register(
            ShoppingListManager,
            lambda: get_manager(ShoppingListManager),
            singleton=True
        )

        # Register Supplier Manager
        container.register(
            SupplierManager,
            lambda: get_manager(SupplierManager),
            singleton=True
        )

        # Register storage service
        container.register(
            IStorageService,
            lambda: StorageService(container),
            singleton=True
        )

        # Register order service
        container.register(
            IOrderService,
            lambda: OrderService(container),
            singleton=True
        )

        # Register recipe service
        container.register(
            IRecipeService,
            lambda: RecipeService(container),
            singleton=True
        )

        # Register shopping list service
        container.register(
            IShoppingListService,
            lambda: ShoppingListService(container),
            singleton=True
        )

        # Register supplier service
        container.register(
            ISupplierService,
            lambda: SupplierService(container),
            singleton=True
        )

    @classmethod
    def get_service(cls, container: DependencyContainer, service_type: Type[T]) -> T:
        """
        Retrieve a service from the dependency container.

        Args:
            container: Dependency container
            service_type: Type of service to retrieve

        Returns:
            Resolved service instance
        """
        return container.resolve(service_type)