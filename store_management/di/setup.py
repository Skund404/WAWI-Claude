# Path: di/setup.py
"""
Dependency Injection Setup for the Leatherworking Store Management Application.

Configures service implementations for various interfaces.
"""

import os
import sys
import logging
from typing import Any, Optional, Tuple, Type

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from di.container import DependencyContainer

# Standard direct import method
def direct_import(module_path: str) -> Any:
    """
    Standard direct import method.

    Args:
        module_path: Dot-separated path including module and class

    Returns:
        The imported class or None if import fails
    """
    try:
        module_name, class_name = module_path.rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logging.error(f"Failed to import {module_path}: {e}")
        return None

# Service Interface Import Paths
SERVICE_INTERFACES = [
    'services.interfaces.material_service.IMaterialService',
    'services.interfaces.order_service.IOrderService',
    'services.interfaces.project_service.IProjectService',
    'services.interfaces.inventory_service.IInventoryService',
    'services.interfaces.storage_service.IStorageService',
    'services.interfaces.pattern_service.IPatternService',
    'services.interfaces.hardware_service.IHardwareService',
    'services.interfaces.supplier_service.ISupplierService',
    'services.interfaces.shopping_list_service.IShoppingListService'
]

# Service Implementation Import Paths
SERVICE_IMPLEMENTATIONS = [
    'services.implementations.material_service.MaterialService',
    'services.implementations.order_service.OrderService',
    'services.implementations.project_service.ProjectService',
    'services.implementations.inventory_service.InventoryService',
    'services.implementations.storage_service.StorageService',
    'services.implementations.pattern_service.PatternService',
    'services.implementations.hardware_service.HardwareService',
    'services.implementations.supplier_service.SupplierService',
    'services.implementations.shopping_list_service.ShoppingListService'
]


def setup_dependency_injection(container: Optional[DependencyContainer] = None) -> DependencyContainer:
    """
    Set up dependency injection by registering service implementations.

    Args:
        container (Optional[DependencyContainer]): Dependency injection container

    Returns:
        DependencyContainer: The configured container
    """
    try:
        logging.info("Setting up dependency injection...")

        # Use existing container or create a new one
        di_container = container or DependencyContainer()

        # Import and register services one by one
        for interface_path, implementation_path in zip(SERVICE_INTERFACES, SERVICE_IMPLEMENTATIONS):
            try:
                # Import interface
                interface = direct_import(interface_path)
                if interface is None:
                    logging.warning(f"Skipping registration for {interface_path}: Interface not found")
                    continue

                # Import implementation
                implementation = direct_import(implementation_path)
                if implementation is None:
                    logging.warning(f"Skipping registration for {interface_path}: Implementation not found")
                    continue

                # Create instance if possible
                try:
                    instance = implementation()
                    # Register the instance directly
                    di_container.register(interface, instance)
                    logging.info(f"Registered service: {interface.__name__}")
                except Exception as e:
                    # If instantiation fails, register the implementation class
                    logging.error(f"Failed to create service {implementation.__name__}: {e}")
                    di_container.register(interface, implementation)
                    logging.info(f"Registered service with lazy initialization: {interface.__name__}")
            except Exception as e:
                logging.error(f"Error registering {implementation_path}: {e}")

        logging.info("Dependency injection setup completed successfully")
        return di_container

    except Exception as e:
        logging.error(f"Dependency injection setup failed: {e}")
        # Return the container even if incomplete to avoid None errors
        return container or DependencyContainer()


def verify_dependency_injection(container: Optional[DependencyContainer] = None) -> None:
    """
    Verify that dependency injection is working correctly.

    Attempts to retrieve each registered service and logs the results.

    Args:
        container (Optional[DependencyContainer]): Container to verify
    """
    try:
        logging.info("Verifying dependency injection...")
        di_container = container or DependencyContainer()

        # Dynamically import and verify service interfaces
        service_interfaces = []
        for interface_path in SERVICE_INTERFACES:
            interface = direct_import(interface_path)
            if interface is not None:
                service_interfaces.append(interface)

        # Attempt to retrieve each service
        for service_type in service_interfaces:
            try:
                service = di_container.get(service_type)
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
        # Setup dependency injection
        container = setup_dependency_injection()

        # Verify dependency injection
        verify_dependency_injection(container)

    except Exception as e:
        logging.error(f"Dependency injection test failed: {e}")


if __name__ == "__main__":
    main()