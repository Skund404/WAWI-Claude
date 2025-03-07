# di/core.py
"""
Dependency Injection Core Decorator and Utility
"""

from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

T = TypeVar('T')


def inject(service_type: Type[T]) -> Callable:
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
            # Dynamically import the DI container to avoid circular imports
            from di.setup import get_di_container

            # Retrieve the DI container
            di_container = get_di_container()

            # Resolve the service
            service_instance = di_container.get(service_type.__name__)

            # Inject the service if not already in kwargs
            if service_type.__name__ not in kwargs:
                kwargs[service_type.__name__] = service_instance

            return func(*args, **kwargs)
        return wrapper
    return decorator