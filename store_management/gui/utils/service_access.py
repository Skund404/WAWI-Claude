# utils/service_access.py
"""
Service access utilities for the GUI.
Provides backward compatibility and delegates to ServiceProvider.
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from gui.utils.service_provider import ServiceProvider, ServiceProviderError

# Type variable for service type hints
T = TypeVar('T')

logger = logging.getLogger(__name__)


def get_service(service_name: str) -> Any:
    """
    Backward-compatible service resolution method.

    Args:
        service_name: Service name or interface name

    Returns:
        Service instance
    """
    try:
        return ServiceProvider.get_service(service_name)
    except ServiceProviderError as e:
        logger.error(f"Failed to resolve service {service_name}: {e}")
        raise


def with_service(service_type: str):
    """
    Decorator to inject a service into a method.

    Args:
        service_type: The service type/name to inject

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                service = ServiceProvider.get_service(service_type)
                return func(self, service, *args, **kwargs)
            except ServiceProviderError as e:
                # Optionally handle UI error display
                if hasattr(self, 'show_error'):
                    self.show_error("Service Error", str(e))
                logger.error(f"Service injection failed: {e}")
                return None

        return wrapper

    return decorator


def execute_service_operation(service_type: str, operation: str, *args: Any, **kwargs: Any) -> Any:
    """
    Execute a service operation with standard error handling.

    Args:
        service_type: Service name or interface
        operation: Method name to execute
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        Result of the service operation
    """
    return ServiceProvider.execute_service_operation(service_type, operation, *args, **kwargs)


def clear_service_cache():
    """Clear the service resolution cache."""
    ServiceProvider._service_cache.clear()
    logger.info("Service provider cache cleared")