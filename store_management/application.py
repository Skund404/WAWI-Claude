# application.py
"""
Main application class for store management system.
"""
import logging
from typing import Any, Optional, Type

from di.container import DependencyContainer
from di.setup import setup_dependency_injection


class Application:
    """
    Main application class for the store management system.
    Handles service registration, dependency injection setup,
    and provides access to services.
    """

    def __init__(self):
        """
        Initialize the application with dependency injection setup.

        Sets up the dependency injection container and configures services.
        """
        self.logger = logging.getLogger("application")
        self.logger.info("Initializing application")

        # Set up dependency injection
        self.logger.info("Setting up dependency injection...")
        setup_dependency_injection()
        self.container = DependencyContainer()
        self.logger.info("Dependency injection setup complete")

    def run(self):
        """
        Run the application.

        This method is a placeholder for any additional startup logic
        and is called externally by run_fixed_app.py.
        """
        self.logger.info("Running application")
        # Additional startup logic can be added here

    def quit(self):
        """
        Perform cleanup operations before application shutdown.

        This method can be used to handle any necessary cleanup,
        such as closing database connections, saving state, etc.
        """
        self.logger.info("Shutting down application")
        # Cleanup operations can be added here

    def get(self, service_type: Type) -> Any:
        """
        Get a service implementation from the dependency container.

        This method delegates to the container's get method to provide backward
        compatibility with code that expects the application to have a get method.

        Args:
            service_type: The interface/service type to retrieve

        Returns:
            An instance of the requested service

        Raises:
            ValueError: If the service cannot be resolved
        """
        try:
            return self.container.get(service_type)
        except Exception as e:
            self.logger.error(f"Error resolving service {service_type.__name__}: {str(e)}")
            raise ValueError(f"Service {service_type.__name__} not available") from e