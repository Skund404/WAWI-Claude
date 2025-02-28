# di/setup.py
"""Setup dependency injection container with service registrations."""

import logging
import os
import sys
from typing import Any, Optional, Tuple, Type

from di.container import DependencyContainer
from utils.circular_import_resolver import CircularImportResolver, register_lazy_import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define service interface-implementation pairs
SERVICE_MAPPINGS = [
    ('services.interfaces.hardware_service.IHardwareService', 'services.implementations.hardware_service.HardwareService'),
    ('services.interfaces.inventory_service.IInventoryService', 'services.implementations.inventory_service.InventoryService'),
    ('services.interfaces.material_service.IMaterialService', 'services.implementations.material_service.MaterialService'),
    ('services.interfaces.order_service.IOrderService', 'services.implementations.order_service.OrderService'),
    ('services.interfaces.pattern_service.IPatternService', 'services.implementations.pattern_service.PatternService'),
    ('services.interfaces.project_service.IProjectService', 'services.implementations.project_service.ProjectService'),
    ('services.interfaces.shopping_list_service.IShoppingListService', 'services.implementations.shopping_list_service.ShoppingListService'),
    ('services.interfaces.storage_service.IStorageService', 'services.implementations.storage_service.StorageService'),
    ('services.interfaces.supplier_service.ISupplierService', 'services.implementations.supplier_service.SupplierService'),
]


def setup_dependency_injection():
    """Set up dependency injection container with all services."""
    logger.info("Setting up dependency injection...")

    # Initialize container
    container = DependencyContainer()

    # Register each service implementation with its interface
    for interface_path, implementation_path in SERVICE_MAPPINGS:
        try:
            # Register the full interface path with the container
            # to ensure correct service resolution by type
            implementation_module = '.'.join(implementation_path.split('.')[:-1])
            implementation_class = implementation_path.split('.')[-1]

            # Register with the container using the full interface path
            container.register_lazy(interface_path, implementation_module, implementation_class)
            logger.info(f"Registered service with lazy resolution: {interface_path}")
        except Exception as e:
            logger.error(f"Error registering {implementation_path} for {interface_path}: {str(e)}")

    logger.info("Dependency injection setup completed successfully")
    return container


def verify_container(container):
    """Verify that all services can be resolved from the container."""
    logger.info("Verifying dependency injection...")

    for interface_path, _ in SERVICE_MAPPINGS:
        try:
            # Try to resolve the service using the full interface path
            service = container.get(interface_path)
            logger.info(f"Successfully resolved {interface_path}: {service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to retrieve {interface_path}: {str(e)}")

    logger.info("Dependency injection verification completed")


def main():
    """Main function for testing dependency injection setup."""
    container = setup_dependency_injection()
    verify_container(container)


if __name__ == "__main__":
    main()