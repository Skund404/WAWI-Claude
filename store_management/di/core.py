# File: di/core.py
from functools import wraps
from typing import Any, Callable, TypeVar, Type, Optional

T = TypeVar('T')


class DependencyContainer:
    """
    Dependency injection container.
    """
    _instance = None
    _services: dict = {}

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            DependencyContainer: Singleton instance
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, service_type: Type[T], service_impl: Any):
        """
        Register a service implementation.

        Args:
            service_type (Type[T]): Interface/abstract base class
            service_impl (Any): Concrete implementation
        """
        cls._services[service_type] = service_impl

    @classmethod
    def resolve(cls, service_type: Type[T]) -> Optional[Any]:
        """
        Resolve a service implementation.

        Args:
            service_type (Type[T]): Interface/abstract base class

        Returns:
            Optional[Any]: Registered service implementation
        """
        return cls._services.get(service_type)


def inject(service_type: Type[T]):
    """
    Dependency injection decorator.

    Args:
        service_type (Type[T]): Service type to inject

    Returns:
        Callable: Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find the service
            service = DependencyContainer.resolve(service_type)

            # If no service is registered, call the original function
            if not service:
                return func(*args, **kwargs)

            # Replace or add the service to kwargs
            kwargs['service'] = service

            return func(*args, **kwargs)

        return wrapper

    return decorator