# database/services/service_provider.py

from typing import TypeVar, Type
from .service_registry import ServiceRegistry
from database.repositories.interfaces.base_service import IBaseService

T = TypeVar('T', bound=IBaseService)


class ServiceProvider:
    """Dependency injection container for services."""

    def __init__(self):
        self.registry = ServiceRegistry()

    def get_service(self, service_type: Type[T]) -> T:
        """Get service instance."""
        service = self.registry.get(service_type)
        if not service:
            raise ValueError(f"Service {service_type.__name__} not registered")
        return service

    def register_services(self) -> None:
        """Register all services."""
        # Import implementations here to avoid circular imports
        from .implementations.pattern_service import PatternService
        from .implementations.leather_inventory_service import LeatherInventoryService

        # Register services
        self.registry.register(IPatternService, PatternService())
        self.registry.register(ILeatherInventoryService, LeatherInventoryService())