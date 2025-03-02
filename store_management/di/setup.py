# di/setup.py
"""Setup dependency injection container with service registrations."""

import logging
import os
import sys
import traceback
from typing import Any, Optional, Tuple, Type

from .container import DependencyContainer
from utils.circular_import_resolver import CircularImportResolver, register_lazy_import

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Define service interface-implementation pairs
SERVICE_MAPPINGS = [
    ('services.interfaces.hardware_service.IHardwareService',
     'services.implementations.hardware_service.HardwareService'),
    ('services.interfaces.inventory_service.IInventoryService',
     'services.implementations.inventory_service.InventoryService'),
    ('services.interfaces.material_service.IMaterialService',
     'services.implementations.material_service.MaterialService'),
    ('services.interfaces.order_service.IOrderService', 'services.implementations.order_service.OrderService'),
    ('services.interfaces.pattern_service.IPatternService', 'services.implementations.pattern_service.PatternService'),
    ('services.interfaces.project_service.IProjectService', 'services.implementations.project_service.ProjectService'),
    ('services.interfaces.shopping_list_service.IShoppingListService',
     'services.implementations.shopping_list_service.ShoppingListService'),
    ('services.interfaces.storage_service.IStorageService', 'services.implementations.storage_service.StorageService'),
    ('services.interfaces.supplier_service.ISupplierService',
     'services.implementations.supplier_service.SupplierService'),

    ('services.interfaces.picking_list_service.IPickingListService',
     'services.implementations.picking_list_service.PickingListService'),]


def safe_import(path):
    """
    Safely import a module with comprehensive error tracking.

    Args:
        path (str): Full import path

    Returns:
        Imported module or None
    """
    try:
        logger.debug(f"Attempting to import: {path}")
        module_name, class_name = path.rsplit('.', 1)
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except ImportError as e:
        logger.error(f"Import error for {path}: {e}")
        logger.error(traceback.format_exc())
    except AttributeError as e:
        logger.error(f"Attribute error importing {path}: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error importing {path}: {e}")
        logger.error(traceback.format_exc())
    return None


def setup_dependency_injection():
    """
    Set up dependency injection container with comprehensive service registration.
    """
    logger.info("Starting dependency injection setup")

    # Log system and environment information
    logger.debug(f"Python Version: {sys.version}")
    logger.debug(f"Python Executable: {sys.executable}")
    logger.debug(f"Python Path: {sys.path}")

    try:
        container = DependencyContainer()

        # Register services with extensive error handling
        for interface_path, implementation_path in SERVICE_MAPPINGS:
            try:
                logger.info(f"Attempting to register service: {interface_path}")

                # Register by full path
                container.register(interface_path, create_lazy_registration(interface_path, implementation_path))

                # Also register by class name for convenience
                interface_name = interface_path.split('.')[-1]
                container.register(interface_name, create_lazy_registration(interface_path, implementation_path))

                logger.info(f"Registered service: {interface_path}")

            except Exception as service_reg_error:
                logger.error(f"Failed to register {interface_path}: {service_reg_error}")
                logger.error(traceback.format_exc())

        # Add direct registration for problematic services
        try:
            logger.info("Adding direct registration for SupplierService")
            from services.implementations.supplier_service import SupplierService
            from services.interfaces.supplier_service import ISupplierService

            supplier_service = SupplierService()
            container.register(ISupplierService, supplier_service)
            container.register("ISupplierService", supplier_service)
            logger.info("Successfully registered SupplierService directly")
        except Exception as e:
            logger.error(f"Failed to directly register SupplierService: {e}")
            logger.error(traceback.format_exc())

        logger.info("Dependency injection setup completed successfully")
        return container

    except Exception as e:
        logger.error(f"Critical error in dependency injection setup: {e}")
        logger.error(traceback.format_exc())
        raise


def create_lazy_registration(interface, implementation):
    """Create a lazy registration function for service instantiation."""

    def lazy_loader():
        try:
            logger.debug(f"Lazy loading {interface}")

            # Import the implementation class
            implementation_class = safe_import(implementation)

            if implementation_class is None:
                logger.error(f"Failed to import {implementation}")
                raise ImportError(f"Could not import {implementation}")

            # Instantiate the service
            service_instance = implementation_class()

            logger.info(f"Successfully instantiated {interface}")
            return service_instance

        except Exception as inner_e:
            logger.error(f"Error in lazy loader for {interface}: {inner_e}")
            logger.error(traceback.format_exc())
            raise

    return lazy_loader


def verify_container(container):
    """
    Verify that all services can be resolved from the container.

    Args:
        container: Dependency injection container to verify
    """
    logger.info("Starting container verification")

    for interface_path, _ in SERVICE_MAPPINGS:
        try:
            # Attempt to resolve the service
            logger.debug(f"Attempting to resolve: {interface_path}")
            service = container.get(interface_path)

            # Log successful resolution
            logger.info(f"Successfully resolved {interface_path}: {service.__class__.__name__}")

        except Exception as e:
            logger.error(f"Failed to retrieve {interface_path}: {str(e)}")
            logger.error(traceback.format_exc())

            # Try with just the class name
            try:
                interface_name = interface_path.split('.')[-1]
                logger.debug(f"Attempting to resolve by class name: {interface_name}")
                service = container.get(interface_name)
                logger.info(f"Successfully resolved {interface_name}: {service.__class__.__name__}")
            except Exception as inner_e:
                logger.error(f"Failed to retrieve {interface_name}: {str(inner_e)}")

    logger.info("Container verification completed")


def main():
    """
    Main function for testing dependency injection setup.
    """
    try:
        logger.info("Starting dependency injection test")

        # Set up the container
        container = setup_dependency_injection()

        # Verify the container
        verify_container(container)

        # Attempt to retrieve and test the Supplier Service
        try:
            # Try using different ways to access the service
            logger.info("Testing supplier service resolution...")

            # Method 1: By interface path
            try:
                supplier_service = container.get("services.interfaces.supplier_service.ISupplierService")
                suppliers = supplier_service.get_all_suppliers()
                logger.info(f"Method 1: Retrieved {len(suppliers)} suppliers")
            except Exception as e:
                logger.error(f"Method 1 failed: {e}")

            # Method 2: By interface class
            try:
                from services.interfaces.supplier_service import ISupplierService
                supplier_service = container.get(ISupplierService)
                suppliers = supplier_service.get_all_suppliers()
                logger.info(f"Method 2: Retrieved {len(suppliers)} suppliers")
            except Exception as e:
                logger.error(f"Method 2 failed: {e}")

            # Method 3: By interface name
            try:
                supplier_service = container.get("ISupplierService")
                suppliers = supplier_service.get_all_suppliers()
                logger.info(f"Method 3: Retrieved {len(suppliers)} suppliers")
            except Exception as e:
                logger.error(f"Method 3 failed: {e}")

            # Method 4: Direct instantiation
            try:
                from services.implementations.supplier_service import SupplierService
                supplier_service = SupplierService()
                suppliers = supplier_service.get_all_suppliers()
                logger.info(f"Method 4: Retrieved {len(suppliers)} suppliers from direct instantiation")
            except Exception as e:
                logger.error(f"Method 4 failed: {e}")

        except Exception as service_test_error:
            logger.error(f"Error testing Supplier Service: {service_test_error}")
            logger.error(traceback.format_exc())

        logger.info("Dependency injection testing completed")

    except Exception as e:
        logger.error(f"Critical error during dependency injection testing: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()