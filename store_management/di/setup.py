# di/setup.py
"""
Dependency Injection Setup for the Leatherworking Application
"""

import logging
import os
import sys
import traceback
from typing import Optional, Tuple, Type, Any

from di.container import DependencyContainer
from di.service_configuration import setup_di as configure_services
from utils.circular_import_resolver import CircularImportResolver

# Setup logging
logger = logging.getLogger(__name__)

# Global service mappings to support non-database services
NON_DB_SERVICES = [
    # List of services that can be instantiated without a database connection
]


def safe_import(path: str) -> Optional[Any]:
    """
    Safely import a module with comprehensive error tracking.

    Args:
        path (str): Full import path

    Returns:
        Imported module or None
    """
    try:
        module = __import__(path, fromlist=[''])
        return module
    except ImportError as e:
        logger.error(f"Failed to import {path}: {e}")
        logger.error(traceback.format_exc())
        return None


def create_mock_service(interface_path: str) -> Any:
    """
    Create a mock service that implements the bare minimum of the interface.

    Used as a fallback when database is not initialized yet.

    Args:
        interface_path: Path to the interface

    Returns:
        A minimal mock implementation of the service
    """
    try:
        # Split the interface path
        module_path, class_name = interface_path.rsplit('.', 1)

        # Import the interface
        interface_module = safe_import(module_path)
        if not interface_module:
            raise ImportError(f"Could not import module {module_path}")

        interface_class = getattr(interface_module, class_name)

        # Create a minimal mock implementation
        class MockService(interface_class):
            def __init__(self, *args, **kwargs):
                logger.warning(f"Using mock implementation for {interface_path}")

            # Implement abstract methods with minimal functionality
            def __getattribute__(self, name):
                def mock_method(*args, **kwargs):
                    logger.warning(f"Called mock method {name} on {interface_path}")
                    return None

                try:
                    original_method = super().__getattribute__(name)
                    if hasattr(original_method, '__isabstractmethod__'):
                        return mock_method
                    return original_method
                except AttributeError:
                    return mock_method

        return MockService

    except Exception as e:
        logger.error(f"Failed to create mock service for {interface_path}: {e}")
        raise


def setup_project_dependencies(container: DependencyContainer) -> None:
    """
    Set up dependency injection for project-related services and repositories.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    try:
        # Configure services
        configure_services(container)

        # Additional project-specific dependency setup can be added here
        logger.info("Project dependencies configured successfully")
    except Exception as e:
        logger.error(f"Failed to set up project dependencies: {e}")
        raise


def verify_container(container: DependencyContainer) -> None:
    """
    Verify that all services can be resolved from the container.

    Args:
        container: Dependency injection container to verify
    """
    try:
        # List of services to verify (can be expanded)
        services_to_verify = [
            'IProjectService',
            'ISalesService',
            'IPurchaseService',
            # Add other critical services
        ]

        for service in services_to_verify:
            try:
                container.get(service)
                logger.info(f"Successfully resolved {service}")
            except Exception as e:
                logger.warning(f"Could not resolve {service}: {e}")
    except Exception as e:
        logger.error(f"Container verification failed: {e}")


def setup_dependency_injection() -> DependencyContainer:
    """
    Set up dependency injection container with comprehensive service registration.

    Returns:
        DependencyContainer: Configured dependency injection container
    """
    try:
        # Create the main dependency container
        container = DependencyContainer()

        # Set up project-specific dependencies
        setup_project_dependencies(container)

        # Verify container resolution
        verify_container(container)

        return container
    except Exception as e:
        logger.error(f"Dependency injection setup failed: {e}")
        raise


# Create a global DI container
di_container = setup_dependency_injection()


def get_di_container() -> DependencyContainer:
    """
    Retrieve the global DI container.

    Returns:
        DependencyContainer: The global dependency injection container
    """
    return di_container