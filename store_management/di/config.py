# di/config.py
import importlib
import logging
from typing import Any, Callable

from di.container import DependencyContainer

from services.interfaces.inventory_service import IInventoryService
from services.interfaces.order_service import IOrderService
from services.interfaces.recipe_service import IRecipeService
from services.interfaces.shopping_list_service import IShoppingListService
from services.interfaces.storage_service import IStorageService
from services.interfaces.supplier_service import ISupplierService


class ApplicationConfig:
    """
    Configuration class for dependency injection and service registration.

    Handles the initialization and registration of services
    in the dependency injection container.
    """

    @classmethod
    def configure_container(cls) -> DependencyContainer:
        """
        Configure and set up the dependency injection container.

        Returns:
            DependencyContainer: Configured container with registered services.
        """
        logger = logging.getLogger(__name__)
        try:
            container = DependencyContainer()

            # Register services
            cls._register_services(container)

            logger.info("Dependency container configured successfully")
            return container
        except Exception as e:
            logger.error(f"Error configuring dependency container: {e}")
            raise

    @classmethod
    def _register_services(cls, container
                           ):
        """
        Register services in the dependency injection container.

        Args:
            container (DependencyContainer): Container to register services in.
        """
        logger = logging.getLogger(__name__)

        # Service implementations to register
        service_mappings = [
            (IInventoryService, 'services.implementations.inventory_service.InventoryService'),
            (IOrderService, 'services.implementations.order_service.OrderService'),
            (IRecipeService, 'services.implementations.recipe_service.RecipeService'),
            (IShoppingListService, 'services.implementations.shopping_list_service.ShoppingListService'),
            (IStorageService, 'services.implementations.storage_service.StorageService'),
            (ISupplierService, 'services.implementations.supplier_service.SupplierService')
        ]

        # Register each service
        for interface, implementation_path in service_mappings:
            try:
                # Dynamically import the implementation
                module_path, class_name = implementation_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                implementation_class = getattr(module, class_name)

                # Only register if not already registered
                if not container.is_registered(interface):
                    container.register(
                        interface_type=interface,
                        implementation_factory=lambda cont, impl=implementation_class: impl(cont),
                        singleton=True
                    )
                    logger.info(f"Registered {implementation_path} for {interface.__name__}")
            except ImportError as e:
                logger.warning(f"Could not import {implementation_path}: {e}")
            except Exception as e:
                logger.error(f"Error registering {implementation_path}: {e}")

    @classmethod
    def get_service(cls, container: DependencyContainer, service_type: type) -> Any:
        """
        Retrieve a service from the container.

        Args:
            container (DependencyContainer): Dependency injection container.
            service_type (type): Interface type of the service to retrieve.

        Returns:
            The requested service implementation.

        Raises:
            ValueError: If no implementation is registered for the service type.
        """
        logger = logging.getLogger(__name__)
        try:
            return container.resolve(service_type)
        except Exception as e:
            logger.error(f"Error retrieving service {service_type}: {e}")
            raise ValueError(f"No implementation registered for {service_type}")

    # Configure logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)