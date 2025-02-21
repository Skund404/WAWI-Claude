# store_management/database/repositories/leather_repository.py

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.leather import Leather
from ..models.enums import InventoryStatus


class LeatherRepository(BaseRepository[Leather]):
    """Repository for Leather model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Leather)

    def get_low_stock(self) -> List[Leather]:
        """
        Get leathers with low stock levels.

        Returns:
            List of leathers with low stock
        """
        return self.session.query(Leather) \
            .filter(Leather.status.in_([InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK])) \
            .all()

    def get_by_supplier(self, supplier_id: int) -> List[Leather]:
        """
        Get leathers by supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of leathers from the specified supplier
        """
        return self.session.query(Leather).filter(Leather.supplier_id == supplier_id).all()

    def get_with_transactions(self, leather_id: int) -> Optional[Leather]:
        """
        Get leather with transaction history.

        Args:
            leather_id: Leather ID

        Returns:
            Leather with loaded transactions or None
        """
        return self.session.query(Leather) \
            .options(joinedload(Leather.transactions)) \
            .filter(Leather.id == leather_id) \
            .first()