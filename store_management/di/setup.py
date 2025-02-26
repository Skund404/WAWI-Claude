# store_management/di/setup.py
"""
Dependency Injection Setup for the Leatherworking Store Management Application.

Configures service implementations for various interfaces.
"""

import logging
from typing import Any, Optional

from di.container import DependencyContainer

# Service Interfaces
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.storage_service import IStorageService
from services.interfaces.pattern_service import IPatternService
from services.interfaces.hardware_service import IHardwareService
from services.interfaces.supplier_service import ISupplierService
from services.interfaces.shopping_list_service import IShoppingListService

# Service Implementations
from services.implementations.material_service import MaterialService
from services.implementations.order_service import OrderService
from services.implementations.project_service import ProjectService
from services.implementations.inventory_service import InventoryService
from services.implementations.storage_service import StorageService
from services.implementations.pattern_service import PatternService
from services.implementations.hardware_service import HardwareService
from services.implementations.supplier_service import SupplierService
from services.implementations.shopping_list_service import ShoppingListService


def create_service(service_class: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Create a service instance with optional arguments.

    Args:
        service_class (type): Service class to instantiate
        *args: Positional arguments for service instantiation
        **kwargs: Keyword arguments for service instantiation

    Returns:
        Any: Instantiated service
    """
    return service_class(*args, **kwargs)


def setup_dependency_injection(container: Optional[DependencyContainer] = None) -> None:
    """
    Set up dependency injection by registering service implementations.

    Args:
        container (Optional[DependencyContainer]): Dependency injection container
    """
    try:
        logging.info("Setting up dependency injection...")

        # Use existing container or create a new one
        di_container = container or DependencyContainer()

        # Define service mappings
        service_mappings = [
            (IMaterialService, MaterialService),
            (IOrderService, OrderService),
            (IProjectService, ProjectService),
            (IInventoryService, InventoryService),
            (IStorageService, StorageService),
            (IPatternService, PatternService),
            (IHardwareService, HardwareService),
            (ISupplierService, SupplierService),
            (IShoppingListService, ShoppingListService)
        ]

        # Register services
        for interface, implementation in service_mappings:
            di_container.register(
                interface,
                lambda impl=implementation: create_service(impl)
            )

        logging.info("Dependency injection setup completed successfully")

    except Exception as e:
        logging.error(f"Dependency injection setup failed: {e}")
        raise


def verify_dependency_injection() -> None:
    """
    Verify that dependency injection is working correctly.

    Attempts to retrieve each registered service and logs the results.
    """
    try:
        logging.info("Verifying dependency injection...")
        container = DependencyContainer()

        # List of service interfaces to verify
        service_interfaces = [
            IMaterialService,
            IOrderService,
            IProjectService,
            IInventoryService,
            IStorageService,
            IPatternService,
            IHardwareService,
            ISupplierService,
            IShoppingListService
        ]

        # Attempt to retrieve each service
        for service_type in service_interfaces:
            try:
                service = container.get(service_type)
                logging.info(f"Successfully retrieved {service_type.__name__}: {service}")
            except Exception as service_error:
                logging.warning(f"Failed to retrieve {service_type.__name__}: {service_error}")

        logging.info("Dependency injection verification completed")

    except Exception as e:
        logging.error(f"Dependency injection verification failed: {e}")


def main():
    """
    Main function for testing dependency injection setup.

    Useful for manual testing and verification of the DI configuration.
    """
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Setup and verify dependency injection
        setup_dependency_injection()
        verify_dependency_injection()

    except Exception as e:
        logging.error(f"Dependency injection test failed: {e}")


if __name__ == "__main__":
    main()