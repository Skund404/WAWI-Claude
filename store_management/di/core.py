# Relative path: store_management/di/core.py

"""
Dependency Injection (DI) Core Module

This module provides a lightweight dependency injection mechanism 
for managing service dependencies and registrations.
"""

import typing
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """
    A dependency injection container for managing service registrations and resolutions.

    Attributes:
        _services (Dict[str, Any]): A dictionary to store registered services.
        _factories (Dict[str, Callable]): A dictionary to store service factories.
    """

    _instance = None
    _services: Dict[str, Any] = {}
    _factories: Dict[str, Callable] = {}

    def __new__(cls):
        """
        Implement singleton pattern to ensure only one instance of DIContainer exists.

        Returns:
            DIContainer: The singleton instance of the DIContainer.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, service_type: Type[T], service_impl: Any = None, factory: Optional[Callable[[], Any]] = None):
        """
        Register a service implementation or factory.

        Args:
            service_type (Type[T]): The type or interface of the service.
            service_impl (Any, optional): The concrete implementation of the service.
            factory (Optional[Callable[[], Any]], optional): A factory method to create the service.
        """
        key = service_type.__name__

        if service_impl is not None:
            cls._services[key] = service_impl
            logger.info(f"Registered service implementation for {key}")

        if factory is not None:
            cls._factories[key] = factory
            logger.info(f"Registered factory for {key}")

    @classmethod
    def resolve(cls, service_type: Type[T]) -> T:
        """
        Resolve a service instance.

        Args:
            service_type (Type[T]): The type of service to resolve.

        Returns:
            T: An instance of the requested service.

        Raises:
            ValueError: If no implementation or factory is found for the service type.
        """
        key = service_type.__name__

        # Check if a concrete implementation is registered
        if key in cls._services:
            return cls._services[key]

        # Check if a factory is registered
        if key in cls._factories:
            service = cls._factories[key]()
            cls._services[key] = service
            return service

        logger.error(f"No implementation found for service type: {key}")
        raise ValueError(f"No implementation found for service type: {key}")


def inject(service_type: Type[T]):
    """
    A decorator to inject dependencies into method arguments.

    Args:
        service_type (Type[T]): The type of service to inject.

    Returns:
        Callable: A decorator function for dependency injection.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if the service type is already in kwargs
            if service_type.__name__ not in kwargs:
                try:
                    # Resolve the service
                    service = DIContainer.resolve(service_type)
                    # Add the resolved service to kwargs
                    kwargs[service_type.__name__.lower()] = service
                except ValueError as e:
                    logger.error(f"Dependency injection failed: {e}")
                    raise

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Provide a default container initialization
default_container = DIContainer()