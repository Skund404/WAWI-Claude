from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
T = TypeVar('T', bound=IBaseService)


class ServiceProvider:
    """Dependency injection container for services."""

        @inject(MaterialService)
        def __init__(self):
        self.registry = ServiceRegistry()

        @inject(MaterialService)
        def get_service(self, service_type: Type[T]) ->T:
        """Get service instance."""
        service = self.registry.get(service_type)
        if not service:
            raise ValueError(f'Service {service_type.__name__} not registered')
        return service

        @inject(MaterialService)
        def register_services(self) ->None:
        """Register all services."""
        from .implementations.pattern_service import PatternService
        from .implementations.leather_inventory_service import LeatherInventoryService
        self.registry.register(IPatternService, PatternService())
        self.registry.register(ILeatherInventoryService,
            LeatherInventoryService())
