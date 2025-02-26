# store_management/di/container.py
"""
Dependency Injection Container Implementation.

Provides a flexible and extensible dependency injection mechanism
for the Leatherworking Store Management application.
"""

import logging
import inspect
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar('T')


class DependencyContainer:
    """
    Centralized dependency injection container.

    Manages service registrations, dependencies, and instantiations.
    """
    _instance = None
    _services: Dict[Type, Callable[[], Any]] = {}
    _instances: Dict[Type, Any] = {}

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            DependencyContainer: Singleton instance of the container
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._instances = {}
        return cls._instance

    def register(
            self,
            service_type: Type[T],
            service_factory: Optional[Callable[[], T]] = None
    ) -> None:
        """
        Register a service implementation.

        Args:
            service_type (Type[T]): Service interface or base class
            service_factory (Optional[Callable[[], T]], optional):
                Factory function to create service instance.
                If None, uses default constructor.
        """
        try:
            # If no factory provided, use default constructor
            if service_factory is None:
                service_factory = lambda: service_type()

            # Register the service factory
            self._services[service_type] = service_factory
            logging.info(f"Registered service: {service_type.__name__}")
        except Exception as e:
            logging.error(f"Failed to register service {service_type.__name__}: {e}")
            raise

    def get(self, service_type: Type[T]) -> T:
        """
        Retrieve a service instance.

        Args:
            service_type (Type[T]): Service interface or base class to retrieve

        Returns:
            T: Service instance

        Raises:
            ValueError: If no implementation is found for the service type
        """
        try:
            # Check if an instance already exists
            if service_type in self._instances:
                return self._instances[service_type]

            # Find the factory for the service type
            factory = self._find_service_factory(service_type)

            # Create and cache the instance
            instance = factory()
            self._instances[service_type] = instance

            return instance
        except Exception as e:
            logging.error(f"Failed to retrieve service {service_type.__name__}: {e}")
            raise ValueError(f"No implementation found for {service_type.__name__}")

    def _find_service_factory(self, service_type: Type[T]) -> Callable[[], T]:
        """
        Find the appropriate service factory for a given type.

        Args:
            service_type (Type[T]): Service type to find factory for

        Returns:
            Callable[[], T]: Factory function for creating service instance

        Raises:
            ValueError: If no factory is found
        """
        # Direct match
        if service_type in self._services:
            return self._services[service_type]

        # Check for subclass or interface implementations
        matching_factories = [
            factory for service, factory in self._services.items()
            if issubclass(service, service_type)
        ]

        if matching_factories:
            return matching_factories[0]

        raise ValueError(f"No implementation found for {service_type.__name__}")

    def reset(self) -> None:
        """
        Reset the dependency container, clearing all registered services and instances.
        """
        try:
            self._services.clear()
            self._instances.clear()
            logging.info("Dependency container reset")
        except Exception as e:
            logging.error(f"Error resetting dependency container: {e}")

    def inject(self, service_type: Type[T]) -> T:
        """
        Decorator for dependency injection.

        Args:
            service_type (Type[T]): Service type to inject

        Returns:
            T: Injected service instance
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Inject the service if not already provided
                if not any(isinstance(arg, service_type) for arg in args):
                    service = self.get(service_type)
                    # If it's a method, inject as first argument after self
                    if inspect.ismethod(func) or (
                            inspect.isfunction(func) and
                            len(inspect.signature(func).parameters) > 0
                    ):
                        args = list(args)
                        args.insert(1, service)
                    else:
                        args = (service,) + args

                return func(*args, **kwargs)

            return wrapper

        return decorator


def get_dependency_container() -> DependencyContainer:
    """
    Get the singleton dependency injection container.

    Returns:
        DependencyContainer: Singleton container instance
    """
    return DependencyContainer()