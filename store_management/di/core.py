# Relative path: store_management/di/core.py

"""
Dependency Injection Core Module

Provides a comprehensive dependency injection mechanism for the application.
"""

import functools
import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic service type
T = TypeVar('T')


class DIContainer:
    pass
"""
Dependency Injection Container for managing service registrations and resolutions.

Provides a thread-safe singleton mechanism for service registration and retrieval.
"""

_instance = None
_services: Dict[str, Any] = {}
_factories: Dict[str, Callable[[], Any]] = {}

def __new__(cls):
    pass
"""
Ensure only one instance of DIContainer exists (Singleton pattern).

Returns:
DIContainer: The singleton instance of the container.
"""
if cls._instance is None:
    pass
cls._instance = super().__new__(cls)
return cls._instance

@classmethod
def register(
cls,
service_type: Type[T],
service_impl: Optional[Any] = None,
factory: Optional[Callable[[], Any]] = None
):
    pass
"""
Register a service implementation or factory.

Args:
service_type (Type[T]): The type or interface of the service.
service_impl (Optional[Any], optional): Concrete service implementation.
factory (Optional[Callable[[], Any]], optional): Factory method to create service.
"""
key = service_type.__name__

if service_impl is not None:
    pass
cls._services[key] = service_impl
logger.info(f"Registered service implementation for {key}")

if factory is not None:
    pass
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
ValueError: If no implementation or factory is found.
"""
key = service_type.__name__

# Check if a concrete implementation is registered
if key in cls._services:
    pass
return cls._services[key]

# Check if a factory is registered
if key in cls._factories:
    pass
service = cls._factories[key]()
cls._services[key] = service
return service

logger.error(f"No implementation found for service type: {key}")
raise ValueError(f"No implementation found for service type: {key}")

@classmethod
def clear(cls):
    pass
"""
Clear all registered services and factories.
Useful for testing or resetting the container.
"""
cls._services.clear()
cls._factories.clear()


def inject(service_type: Type[T]):
    pass
"""
Decorator for dependency injection.

Automatically injects the specified service type into the method.

Args:
service_type (Type[T]): The type of service to inject.

Returns:
Callable: Decorated function with dependency injection.
"""

def decorator(func: Callable):
    pass
@functools.wraps(func)
def wrapper(*args, **kwargs):
    pass
# Determine the signature of the original function
sig = inspect.signature(func)

# Check if the service type is already in kwargs
service_name = service_type.__name__.lower()
if service_name not in kwargs:
    pass
try:
    pass
# Resolve the service
service = DIContainer.resolve(service_type)

# Add the resolved service to kwargs
kwargs[service_name] = service
except ValueError as e:
    pass
logger.error(f"Dependency injection failed: {e}")
raise

return func(*args, **kwargs)

return wrapper

return decorator


# Global container instance for easy access
container = DIContainer()
