# di/container.py
from typing import Any, Callable, Dict, Optional, Type
import logging


class DependencyContainer:
    """
    A flexible dependency injection container.

    Manages service registrations and resolutions with support for
    singleton and factory-based dependency creation.
    """

    def __init__(self):
        """
        Initialize the dependency container.

        Stores registered services with their factories and singleton instances.
        """
        self._services: Dict[Type, Dict[str, Any]] = {}
        self._logger = logging.getLogger(self.__class__.__name__)

    def register(
            self,
            interface_type: Type,
            implementation_factory: Callable[[Any], Any],
            singleton: bool = False
    ) -> None:
        """
        Register a service in the container.

        Args:
            interface_type (Type): The interface/abstract base class
            implementation_factory (Callable): A factory function to create the implementation
            singleton (bool, optional): Whether to cache the first created instance. Defaults to False.

        Raises:
            ValueError: If the interface type is already registered
        """
        # Check if already registered
        if self.is_registered(interface_type):
            # Optionally log a warning or raise an error
            self._logger.warning(f"Service {interface_type} is already registered. Skipping.")
            return

        self._services[interface_type] = {
            'factory': implementation_factory,
            'singleton': singleton,
            'instance': None
        }
        self._logger.info(f"Registered service for {interface_type}")

    def resolve(self, interface_type: Type) -> Any:
        """
        Resolve a service implementation for a given interface.

        Args:
            interface_type (Type): The interface type to resolve.

        Returns:
            The service implementation.

        Raises:
            ValueError: If no implementation is registered for the interface type.
        """
        # Validate registration
        if not self.is_registered(interface_type):
            raise ValueError(f"No implementation registered for {interface_type}")

        # Retrieve service registration
        service_reg = self._services[interface_type]

        # If singleton and instance exists, return cached instance
        if service_reg['singleton'] and service_reg['instance'] is not None:
            return service_reg['instance']

        # Create new instance
        try:
            instance = service_reg['factory'](self)

            # Cache instance if singleton
            if service_reg['singleton']:
                service_reg['instance'] = instance

            return instance
        except Exception as e:
            self._logger.error(f"Error resolving {interface_type}: {e}")
            raise

    def is_registered(self, interface_type: Type) -> bool:
        """
        Check if a service is registered in the container.

        Args:
            interface_type (Type): The interface type to check.

        Returns:
            bool: True if registered, False otherwise.
        """
        return interface_type in self._services

    def get_service(self, interface_type: Type) -> Any:
        """
        Convenience method to resolve a service.

        Alias for resolve method.

        Args:
            interface_type (Type): The interface type to resolve.

        Returns:
            The service implementation.
        """
        return self.resolve(interface_type)

    def clear(self) -> None:
        """
        Clear all registered services.

        Useful for testing or resetting the container.
        """
        self._services.clear()
        self._logger.info("Dependency container cleared")

    def __repr__(self) -> str:
        """
        String representation of the container.

        Returns:
            str: Description of registered services.
        """
        return f"DependencyContainer(registered_services={list(self._services.keys())})"