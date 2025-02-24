

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ILeatherInventoryService(IBaseService[Leather]):
    pass
"""Interface for leather inventory management."""

@abstractmethod
@inject(MaterialService)
def update_stock(self, leather_id: int, area_change: float, notes: str
) -> bool:
"""Update leather stock levels."""
pass

@abstractmethod
@inject(MaterialService)
def get_low_stock_items(self) -> List[Leather]:
"""Get items with low stock."""
pass

@abstractmethod
@inject(MaterialService)
def track_wastage(self, leather_id: int, area_wasted: float, reason: str
) -> bool:
"""Track leather wastage."""
pass

@abstractmethod
@inject(MaterialService)
def get_usage_statistics(self, leather_id: int) -> Dict[str, float]:
"""Get usage statistics for leather."""
pass
