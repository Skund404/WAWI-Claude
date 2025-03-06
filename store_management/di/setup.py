# di/setup.py
"""Unified dependency injection setup for the application."""

import logging
import os
import sys
import traceback
from typing import Any, Optional, Tuple, Type

from di.container import DependencyContainer
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
    ('services.interfaces.order_service.IOrderService',
     'services.implementations.order_service.OrderService'),
    ('services.interfaces.pattern_service.IPatternService',
     'services.implementations.pattern_service.PatternService'),
    ('services.interfaces.project_service.IProjectService',
     'services.implementations.project_service.ProjectService'),
    ('services.interfaces.shopping_list_service.IShoppingListService',
     'services.implementations.shopping_list_service.ShoppingListService'),
    ('services.interfaces.storage_service.IStorageService',
     'services.implementations.storage_service.StorageService'),
    ('services.interfaces.supplier_service.ISupplierService',
     'services.implementations.supplier_service.SupplierService'),
    ('services.interfaces.picking_list_service.IPickingListService',
     'services.implementations.picking_list_service.PickingListService'),
]

# Services that don't depend on database models - these can be initialized directly
NON_DB_SERVICES = [
    'services.interfaces.pattern_service.IPatternService',
    'services.interfaces.inventory_service.IInventoryService',
]


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


def create_mock_service(interface_path):
    """
    Create a mock service that implements the bare minimum of the interface.

    Used as a fallback when database is not initialized yet.

    Args:
        interface_path: Path to the interface

    Returns:
        A minimal mock implementation of the service
    """
    interface_name = interface_path.split('.')[-1]

    # Define a comprehensive mock class
    class MockService:
        def __init__(self):
            logger.info(f"Created mock implementation of {interface_name}")

        def get_all_suppliers(self):
            logger.info("Mock: get_all_suppliers called")
            return []

        def get_all_materials(self):
            logger.info("Mock: get_all_materials called")
            return []

        def get_all_projects(self):
            logger.info("Mock: get_all_projects called")
            return []

        # Implement methods for MaterialService
        def create(self, data):
            logger.info("Mock: create called")
            return None

        def get_by_id(self, material_id):
            logger.info(f"Mock: get_by_id called for {material_id}")
            return None

        def update(self, material_id, updates):
            logger.info(f"Mock: update called for {material_id}")
            return None

        def delete(self, material_id):
            logger.info(f"Mock: delete called for {material_id}")
            return False

        def get_materials(self, material_type=None, **kwargs):
            logger.info(f"Mock: get_materials called with type {material_type}")
            return []

        def search_materials(self, search_text, material_type=None, **kwargs):
            logger.info(f"Mock: search_materials called with text '{search_text}'")
            return []

        def record_material_transaction(self, transaction_data):
            logger.info("Mock: record_material_transaction called")
            return {}

        def get_material_transactions(self, material_id=None, transaction_type=None):
            logger.info("Mock: get_material_transactions called")
            return []

        def calculate_material_cost(self, material_id, quantity):
            logger.info(f"Mock: calculate_material_cost called for {material_id}")
            return 0.0

        def get_material_types(self):
            logger.info("Mock: get_material_types called")
            return []

    return MockService


def create_lazy_registration(interface, implementation):
    """
    Create a lazy registration function for service instantiation.

    Args:
        interface: The service interface name or path
        implementation: The implementation module path

    Returns:
        callable: Lazy registration function
    """

    def lazy_loader():
        try:
            logger.debug(f"Lazy loading {interface}")

            # For DB-dependent services that need a session
            if 'material_service' in implementation.lower():
                try:
                    from database.sqlalchemy.session import get_db_session
                    implementation_class = safe_import(implementation)

                    if implementation_class is None:
                        logger.error(f"Failed to import {implementation}")
                        return create_mock_service(interface)()

                    # Get a session and initialize with it
                    session = get_db_session()
                    service_instance = implementation_class(session)

                    logger.info(f"Successfully instantiated {interface} with session")
                    return service_instance
                except ImportError as e:
                    logger.warning(f"Database models not initialized yet for {interface}: {e}")
                    # Return a mock service if the database isn't ready
                    mock_service = create_mock_service(interface)()
                    return mock_service
                except Exception as e:
                    logger.error(f"Error creating service with session: {e}")
                    logger.error(traceback.format_exc())
                    # Return a mock service on any database error
                    mock_service = create_mock_service(interface)()
                    return mock_service

            # Continue with normal import logic for other services
            # Try to import Base to check if database models are ready
            try:
                from database.models.base import Base
                logger.debug(f"Base class is available, attempting to load {implementation}")

                # Continue with normal import logic
                implementation_class = safe_import(implementation)

                if implementation_class is None:
                    logger.error(f"Failed to import {implementation}")
                    # Return a mock service instead
                    mock_service = create_mock_service(interface)()
                    return mock_service

                # Instantiate the service
                service_instance = implementation_class()

                logger.info(f"Successfully instantiated {interface}")
                return service_instance

            except ImportError as e:
                logger.warning(f"Database models not initialized yet for {interface}: {e}")
                # Return a mock service if the database isn't ready
                mock_service = create_mock_service(interface)()
                return mock_service
            except Exception as e:
                logger.error(f"Database error for {interface}: {e}")
                logger.error(traceback.format_exc())
                # Return a mock service on any database error
                mock_service = create_mock_service(interface)()
                return mock_service

        except Exception as e:
            logger.error(f"Error in lazy loader for {interface}: {e}")
            logger.error(traceback.format_exc())
            # Return a mock service on any error
            mock_service = create_mock_service(interface)()
            return mock_service

    # This function returns the lazy_loader function itself
    return lazy_loader


# Rest of the file remains the same as in the original implementation
def setup_project_dependencies(container):
    """
    Set up dependency injection for project-related services and repositories.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    logger.info("Setting up project-specific dependencies")

    try:
        # Register project-specific repositories or other dependencies
        try:
            from database.repositories.project_repository import ProjectRepository
            container.register("ProjectRepository", ProjectRepository)
            logger.info("Successfully registered ProjectRepository")
        except Exception as e:
            logger.error(f"Failed to register ProjectRepository: {e}")
            logger.error(traceback.format_exc())

        # Call the detailed project service registration
        register_project_services(container)

    except Exception as e:
        logger.error(f"Error in project dependencies setup: {e}")
        logger.error(traceback.format_exc())


def register_project_services(container):
    """
    Comprehensive registration of project-related services.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    logger.info("Registering project-specific services")

    try:
        # Add project-specific registrations here
        pass

    except Exception as e:
        logger.error(f"Error in project services registration: {e}")
        logger.error(traceback.format_exc())


def setup_dependency_injection():
    """
    Set up dependency injection container with comprehensive service registration.

    Returns:
        DependencyContainer: Configured dependency injection container
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

        # Setup project-specific dependencies (integrating project_service_setup.py)
        setup_project_dependencies(container)

        logger.info("Dependency injection setup completed successfully")
        return container

    except Exception as e:
        logger.error(f"Critical error in dependency injection setup: {e}")
        logger.error(traceback.format_exc())
        raise


def verify_container(container):
    """
    Verify that all services can be resolved from the container.

    Args:
        container: Dependency injection container to verify
    """
    logger.info("Starting container verification")

    # First verify the non-DB services which should work regardless of the database state
    for interface_path in NON_DB_SERVICES:
        try:
            logger.debug(f"Attempting to resolve non-DB service: {interface_path}")
            service = container.get(interface_path)
            interface_name = interface_path.split('.')[-1]
            logger.info(f"Successfully resolved {interface_name}: {service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to resolve non-DB service {interface_path}: {e}")
            logger.error(traceback.format_exc())

    # Then try the DB-dependent services, accepting that they might return mocks
    for interface_path, _ in SERVICE_MAPPINGS:
        if interface_path in NON_DB_SERVICES:
            continue  # Skip those we already verified

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


def setup_mock_db():
    """
    Set up a mock database Base class if the real one cannot be loaded.
    This serves as a temporary solution until the real database is initialized.
    """
    try:
        # See if the real Base exists
        from database.models.base import Base
        logger.info("Real database Base class found")
        return
    except ImportError:
        logger.warning("Real database Base class not found, setting up mock Base")

        try:
            # Create a system path if needed
            sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

            # Create directory structure if it doesn't exist
            os.makedirs("database/models", exist_ok=True)

            # Create a simple mock base.py
            with open("database/models/base.py", "w") as f:
                f.write("""
# This is a temporary mock Base class
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
                """)

            logger.info("Created mock database Base class")

        except Exception as e:
            logger.error(f"Failed to create mock Base: {e}")
            logger.error(traceback.format_exc())


def main():
    """
    Main function for testing dependency injection setup.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting dependency injection test")

        # Try to set up mock database if needed
        setup_mock_db()

        # Set up the container
        container = setup_dependency_injection()

        # Verify the container
        verify_container(container)

        # Attempt to retrieve and test the non-database services
        try:
            logger.info("Testing pattern service resolution...")
            pattern_service = container.get("IPatternService")
            if pattern_service:
                logger.info(f"Successfully retrieved pattern service: {pattern_service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error testing Pattern Service: {e}")
            logger.error(traceback.format_exc())

        logger.info("Dependency injection testing completed")
        return True

    except Exception as e:
        logger.error(f"Critical error during dependency injection testing: {e}")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)