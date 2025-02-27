# relative path: store_management/application.py
"""
Application class for the Leatherworking Store Management application.

Provides centralized dependency injection and service management.
"""

import logging
from typing import Type, Any, Optional

from di.container import DependencyContainer
from di.setup import setup_dependency_injection


class Application:
    """
    Central application class managing dependency injection and services.

    Provides a unified interface for retrieving services across the application
    using the dependency injection container.

    Attributes:
        container (DependencyContainer): Dependency injection container
    """

    def __init__(self):
        """
        Initialize the application with dependency injection setup.

        Sets up the dependency injection container and configures services.
        """
        logging.info("Initializing Application...")

        try:
            # Setup dependency injection and get the container
            self.container = DependencyContainer()

            # Perform initial dependency injection setup
            setup_dependency_injection()

            logging.info("Application initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize application: {e}")
            raise

    def get_service(self, service_type: Type[Any]) -> Any:
        """
        Retrieve a service from the dependency injection container.

        Args:
            service_type (Type): The type/interface of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            ValueError: If the service cannot be retrieved
        """
        try:
            # Directly use the container's get method
            return self.container.get(service_type)
        except Exception as e:
            logging.error(f"Error getting service {service_type}: {e}")
            raise ValueError(f"Service {service_type} not available") from e

    def get(self, service_type: Type[Any]) -> Any:
        """
        Alias for get_service to maintain compatibility.

        Args:
            service_type (Type): The type/interface of the service to retrieve

        Returns:
            The requested service instance
        """
        return self.get_service(service_type)

    def run(self):
        """
        Run the application.

        This method is a placeholder for any additional startup logic
        and is called externally by run_fixed_app.py.
        """
        logging.info("Application is running...")

    def quit(self):
        """
        Perform cleanup operations before application shutdown.

        This method can be used to handle any necessary cleanup,
        such as closing database connections, saving state, etc.
        """
        logging.info("Performing application cleanup...")
        # Add any necessary cleanup logic here