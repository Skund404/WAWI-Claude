# Path: store_management\store_management\application.py
from typing import Type, TypeVar

from store_management.di.config import ApplicationConfig
from store_management.di.container import DependencyContainer

T = TypeVar('T')

class Application:
    """
    Main application class that manages dependency injection and service resolution.

    This class is responsible for initializing the application's dependency container
    and providing access to application services.
    """

    def __init__(self):
        """
        Initialize the Application instance.

        Sets up the dependency injection container using ApplicationConfig.
        """
        self._container = ApplicationConfig.configure_container()

    def get_service(self, service_type: Type[T]) -> T:
        """
        Retrieve a service instance from the dependency container.

        Args:
            service_type: The type of service to retrieve.

        Returns:
            An instance of the requested service.

        Raises:
            ValueError: If the service cannot be resolved.
        """
        return self._container.get_service(service_type)