# Path: application.py
"""
Main application class for the leatherworking store management system.
"""

import logging
from typing import Any, Optional, Type

from di.container import DependencyContainer
from di.setup import setup_dependency_injection


class Application:
    """
    Main application class that coordinates the application components.

    This class is responsible for initializing the dependency injection container,
    setting up services, and providing access to those services.
    """

    def __init__(self):
        """
        Initialize the application with dependency injection setup.

        Sets up the dependency injection container and configures services.
        """
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing application")

        # Set up dependency injection
        self.container = setup_dependency_injection()
        self.logger.info("Dependency injection setup complete")

    def get_service(self, service_type: Type) -> Any:
        """
        Get a service instance from the DI container.

        Args:
            service_type: The type of service to retrieve

        Returns:
            An instance of the requested service

        Raises:
            KeyError: If the service is not registered
        """
        return self.container.get(service_type)

    def run(self):
        """
        Run the application.

        This method is a placeholder for any additional startup logic
        and is called externally by run_fixed_app.py.
        """
        self.logger.info("Application running")

    def quit(self):
        """
        Perform cleanup operations before application shutdown.

        This method can be used to handle any necessary cleanup,
        such as closing database connections, saving state, etc.
        """
        self.logger.info("Application shutting down")