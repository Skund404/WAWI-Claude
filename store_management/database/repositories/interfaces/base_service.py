from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
T = TypeVar('T')


class IBaseService(ABC, Generic[T]):
    """Base interface for all services."""

        @abstractmethod
    @inject(MaterialService)
    def get_by_id(self, id: int) ->Optional[T]:
        """Get entity by ID."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_all(self) ->List[T]:
        """Get all entities."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def create(self, data: dict) ->T:
        """Create new entity."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def update(self, id: int, data: dict) ->Optional[T]:
        """Update existing entity."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def delete(self, id: int) ->bool:
        """Delete entity."""
        pass
