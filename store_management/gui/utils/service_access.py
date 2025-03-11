# gui/utils/service_access.py
"""
Service access utilities for the GUI.
Provides helper functions to access services through dependency injection.
"""

import logging
from typing import Any, Dict, Optional, Type, TypeVar

from di import resolve

# Type variable for service type hints
T = TypeVar('T')

logger = logging.getLogger(__name__)

# Cache for resolved services
_service_cache: Dict[str, Any] = {}


def get_service(service_type: str) -> Optional[Any]:
    """
    Get a service instance using dependency injection.
    Caches services to avoid repeated resolution.

    Args:
        service_type: The service type/name to resolve

    Returns:
        The resolved service instance or None if resolution fails
    """
    if service_type not in _service_cache:
        try:
            _service_cache[service_type] = resolve(service_type)
        except Exception as e:
            logger.error(f"Error resolving service {service_type}: {str(e)}")
            return None

    return _service_cache[service_type]


def clear_service_cache():
    """Clear the service cache."""
    _service_cache.clear()


def with_service(service_type: str):
    """
    Decorator to inject a service into a method.

    Args:
        service_type: The service type/name to inject

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            service = get_service(service_type)
            if service is None:
                if hasattr(self, 'show_error'):
                    self.show_error("Service Error", f"Failed to access {service_type} service")
                return None
            return func(self, service, *args, **kwargs)

        return wrapper

    return decorator