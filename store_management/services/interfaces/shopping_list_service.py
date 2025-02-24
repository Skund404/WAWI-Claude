

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class IShoppingListService(ABC):
    """Interface for shopping list management service."""

        @abstractmethod
    @inject(MaterialService)
    def get_all_shopping_lists(self) ->List[Any]:
        """Get all shopping lists."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_shopping_list_by_id(self, list_id: int) ->Optional[Any]:
        """Get shopping list by ID."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def create_shopping_list(self, list_data: Dict[str, Any]) ->Any:
        """Create a new shopping list."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def update_shopping_list(self, list_id: int, list_data: Dict[str, Any]
        ) ->Optional[Any]:
        """Update existing shopping list."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def delete_shopping_list(self, list_id: int) ->bool:
        """Delete shopping list."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) ->Any:
        """Add item to shopping list."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def remove_item_from_list(self, list_id: int, item_id: int) ->bool:
        """Remove item from shopping list."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def mark_item_purchased(self, list_id: int, item_id: int, quantity: float
        ) ->bool:
        """Mark item as purchased."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_active_lists(self) ->List[Any]:
        """Get all active shopping lists."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_pending_items(self) ->List[Any]:
        """Get all pending items across all lists."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_lists_by_status(self, status: str) ->List[Any]:
        """Get lists by status."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def search_shopping_lists(self, search_term: str) ->List[Any]:
        """Search shopping lists."""
        pass
