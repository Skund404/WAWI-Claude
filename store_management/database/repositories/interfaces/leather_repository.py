# database/repositories/interfaces/leather_repository.py

from typing import List, Tuple
from database.repositories.interfaces.base_repository import IBaseRepository
from ...models.leather import Leather


class ILeatherRepository(IBaseRepository[Leather]):
    """Interface for leather inventory repository."""

    @abstractmethod
    def get_low_stock(self) -> List[Leather]:
        """Get leather items with low stock."""
        pass

    @abstractmethod
    def get_by_type(self, leather_type: str) -> List[Leather]:
        """Get leather by type."""
        pass

    @abstractmethod
    def get_with_transactions(self, leather_id: int) -> Tuple[Leather, List[dict]]:
        """Get leather with its transaction history."""
        pass