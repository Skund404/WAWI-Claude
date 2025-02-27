# Path: di/container.py
"""
Dependency injection container for the leatherworking store management application.

This module provides a container for managing dependencies between various services,
allowing for loose coupling and better testability.
"""

import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

# Type variable for generic service types
T = TypeVar('T')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Container for dependency injection.

    This class manages service dependencies and provides access to registered services.
    It supports both instance and factory registration.
    """

    _instance = None

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            DependencyContainer: Singleton instance of the container
        """
        if cls._instance is None:
            cls._instance = super(DependencyContainer, cls).__new__(cls)
            cls._instance._services: Dict[Type, Any] = {}
            cls._instance._factories: Dict[Type, Callable] = {}
        return cls._instance

    def register(self, service_type: Type[T], service_impl: Any) -> None:
        """
        Register a service implementation for a given service type.

        Args:
            service_type: The service interface/type
            service_impl: Either a service instance or a factory function that creates one

        Raises:
            TypeError: If service_type is not a type
        """
        try:
            if not isinstance(service_type, type):
                raise TypeError(f"Service type must be a class, got {type(service_type).__name__}")

            if callable(service_impl) and not isinstance(service_impl, type):
                # It's a factory function
                self._factories[service_type] = service_impl
                logger.info(f"Registered factory for {service_type.__name__}")
            elif isinstance(service_impl, type):
                # It's a class, create a factory function
                self._factories[service_type] = lambda: service_impl()
                logger.info(f"Registered class {service_impl.__name__} for {service_type.__name__}")
            else:
                # It's an instance
                self._services[service_type] = service_impl
                logger.info(f"Registered instance of {type(service_impl).__name__} for {service_type.__name__}")
        except Exception as e:
            logger.error(f"Failed to register service {service_type.__name__}: {e}")
            raise

    def get(self, service_type: Type[T]) -> T:
        """
        Get a service instance of the specified type.

        Args:
            service_type: The service interface/type to retrieve

        Returns:
            An instance of the requested service type

        Raises:
            KeyError: If no implementation is registered for the service type
        """
        try:
            # Check if we have an instance
            if service_type in self._services:
                return self._services[service_type]

            # Check if we have a factory
            if service_type in self._factories:
                try:
                    # Create an instance using the factory
                    instance = self._factories[service_type]()
                    # Cache the instance
                    self._services[service_type] = instance
                    return instance
                except Exception as e:
                    logger.error(f"Failed to create service {service_type.__name__}: {e}")
                    return None

            raise KeyError(f"No implementation found for {service_type.__name__}")
        except Exception as e:
            logger.error(f"Error retrieving service {service_type.__name__}: {e}")
            raise

    def clear(self) -> None:
        """Clear all registered services and factories."""
        self._services.clear()
        self._factories.clear()
        logger.info("Cleared all registered services and factories")

    @property
    def registered_services(self) -> Dict[Type, Any]:
        """
        Get all registered service types and their implementations.

        Returns:
            Dictionary mapping service types to instances or factories
        """
        services = {}
        services.update(self._services)
        services.update({k: f"Factory<{k.__name__}>" for k in self._factories})
        return services


def inject(service_type: Type[T]) -> Callable:
    """
    Decorator for injecting dependencies.

    Args:
        service_type: The service type to inject

    Returns:
        Decorator function

    Example:
        @inject(IMaterialService)
        def get_materials(material_service):
            return material_service.get_materials()
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get container
            container = DependencyContainer()

            # Get the service
            service = container.get(service_type)

            # Call original function with service as first argument
            return func(service, *args, **kwargs)

        return wrapper

    return decorator