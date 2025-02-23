# database/services/service_registry.py

from typing import Dict, Type, TypeVar, Optional
from database.repositories.interfaces.base_service import IBaseService

T = TypeVar('T', bound=IBaseService)


class ServiceRegistry:
    """Service locator pattern implementation."""

    _instance = None
    _services: Dict[Type[IBaseService], IBaseService] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, interface: Type[T], implementation: T) -> None:
        """Register a service implementation."""
        cls._services[interface] = implementation

    @classmethod
    def get(cls, interface: Type[T]) -> Optional[T]:
        """Get a service implementation."""
        return cls._services.get(interface)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services."""
        cls._services.clear()