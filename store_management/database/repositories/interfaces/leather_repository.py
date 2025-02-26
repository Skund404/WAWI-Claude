from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.leather import Leather
from core.database.base_repository import IBaseRepository

class ILeatherRepository(IBaseRepository[Leather]):
    """Interface for leather inventory repository."""

    @abstractmethod
    @inject(MaterialService)
    def get_low_stock(self) -> List[Leather]:
        """Get leather items with low stock."""
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_by_type(self, leather_type: str) -> List[Leather]:
        """Get leather by type."""
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_with_transactions(self, leather_id: int) -> Tuple[Leather, List[dict]]:
        """Get leather with its transaction history."""
        pass