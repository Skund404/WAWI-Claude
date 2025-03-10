"""
Dependency Injection Setup.

Configures and initializes the DI container with all required services.
"""

import importlib
import inspect
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Type, Union

# Configure logging
logger = logging.getLogger(__name__)

# Add project root to sys.path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from di.container import Container, Lifetime, create_container, get_container
from di.config import SERVICE_MAPPINGS, REPOSITORY_MAPPINGS, DATABASE_SESSION_CONFIG


def safe_import(import_path: str) -> Optional[Any]:
    """
    Safely import a module or class.

    Args:
        import_path: Dotted path to the module or class

    Returns:
        Imported module/class or None if import fails
    """
    try:
        if '.' in import_path:
            # If path contains a dot, it might be a module.class reference
            module_path, class_name = import_path.rsplit('.', 1)

            # First try to import the module
            module = importlib.import_module(module_path)

            # Then try to get the class/attribute if specified
            if hasattr(module, class_name):
                return getattr(module, class_name)
            return module
        else:
            # It's just a module
            return importlib.import_module(import_path)
    except (ImportError, AttributeError) as e:
        logger.warning(f"Failed to import {import_path}: {str(e)}")
        return None


def register_database_session(container: Container) -> Container:
    """
    Register the database session factory.

    Args:
        container: DI container

    Returns:
        Updated container
    """
    try:
        module_name = DATABASE_SESSION_CONFIG['module']

        # Import the session module
        module = safe_import(module_name)
        if not module:
            logger.error(f"Failed to import database session module: {module_name}")
            logger.info("Registering a dummy session factory for testing")
            # Register a dummy factory for testing
            container.register_factory("Session", lambda c: None)
            return container

        # Register a dummy session factory for now
        logger.info("Registering a dummy session factory for testing")
        container.register_factory("Session", lambda c: None)
        return container

    except Exception as e:
        logger.error(f"Error registering database session: {str(e)}")
        traceback.print_exc()
        # Register a dummy factory for testing
        container.register_factory("Session", lambda c: None)
        return container


def register_repositories(container: Container) -> Container:
    """
    Register all repositories with the container.

    Args:
        container: DI container

    Returns:
        Updated container
    """
    registered_count = 0

    for repo_path in REPOSITORY_MAPPINGS:
        try:
            # For repositories, we register the class by name and use the path for lazy loading
            module_path, class_name = repo_path.rsplit('.', 1)

            # Check if already registered
            if container.is_registered(class_name):
                continue

            # Register with scoped lifetime
            container.register(class_name, repo_path, Lifetime.SCOPED)
            registered_count += 1

        except Exception as e:
            logger.warning(f"Failed to register repository {repo_path}: {str(e)}")

    logger.info(f"Registered {registered_count} repositories")
    return container


def register_services(container: Container) -> Container:
    """
    Register all services with the container.

    Args:
        container: DI container

    Returns:
        Updated container
    """
    registered_count = 0

    # First try to register real services from SERVICE_MAPPINGS
    for interface_name, implementation_path in SERVICE_MAPPINGS.items():
        try:
            # Skip if already registered
            if container.is_registered(interface_name):
                continue

            # Register any real services that exist
            if implementation_path and implementation_path != 'mock_implementations':
                container.register(interface_name, implementation_path)
                registered_count += 1
                logger.info(f"Registered service: {interface_name} -> {implementation_path}")

        except Exception as e:
            logger.warning(f"Failed to register service {interface_name}: {str(e)}")

    # Now register mock implementations for testing where needed
    try:
        # Import the mock implementations package
        from di.tests.mock_implementations import MOCK_SERVICES

        # Register mock implementations for interfaces without real implementations
        for interface_name, mock_class in MOCK_SERVICES.items():
            if not container.is_registered(interface_name):
                # Create an instance of the mock
                mock_instance = mock_class()

                # Register the mock instance
                container.register_instance(interface_name, mock_instance)
                registered_count += 1
                logger.info(f"Registered mock implementation for {interface_name}")

    except Exception as e:
        logger.error(f"Failed to register mock implementations: {str(e)}")
        traceback.print_exc()

    logger.info(f"Registered {registered_count} services")
    return container


def initialize() -> Container:
    """
    Initialize the DI system for the application.

    Returns:
        Initialized container
    """
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('di_setup.log', encoding='utf-8', mode='a')
            ]
        )

        logger.info("Initializing DI container")

        # Create container
        container = create_container()

        # Register components
        register_database_session(container)
        register_repositories(container)
        register_services(container)

        logger.info("DI container initialized successfully")
        return container

    except Exception as e:
        logger.error(f"Failed to initialize DI container: {str(e)}")
        traceback.print_exc()
        raise


def verify_container() -> bool:
    """
    Verify that critical services can be resolved from the container.

    Returns:
        True if all verifications pass, False otherwise
    """
    try:
        container = get_container()
        verification_results = []

        # Critical services to verify
        critical_services = [
            'ICustomerService',
            'IMaterialService',
            'IProjectService',
            'IInventoryService',
            'ISalesService',
            'ISupplierService',
            'IPatternService',
            'IToolListService'
        ]

        logger.info("Verifying container service resolution")

        for service in critical_services:
            try:
                instance = container.resolve(service)
                logger.info(f"✓ Successfully resolved {service}")
                verification_results.append(True)
            except Exception as e:
                logger.error(f"✗ Failed to resolve {service}: {str(e)}")
                verification_results.append(False)

        # Check overall success
        success = all(verification_results)
        if success:
            logger.info("Container verification completed successfully")
        else:
            logger.warning("Container verification failed for some services")

        return success

    except Exception as e:
        logger.error(f"Error during container verification: {str(e)}")
        return False