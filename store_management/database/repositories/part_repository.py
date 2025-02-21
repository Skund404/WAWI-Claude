# store_management/database/repositories/part_repository.py

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.part import Part
from ..models.enums import InventoryStatus


class PartRepository(BaseRepository[Part]):
    """Repository for Part model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Part)

    def get_low_stock(self) -> List[Part]:
        """
        Get parts with low stock levels.

        Returns:
            List of parts with low stock
        """
        return self.session.query(Part) \
            .filter(Part.status.in_([InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK])) \
            .all()

    def get_by_supplier(self, supplier_id: int) -> List[Part]:
        """
        Get parts by supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of parts from the specified supplier
        """
        return self.session.query(Part).filter(Part.supplier_id == supplier_id).all()

    def get_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Get part with transaction history.

        Args:
            part_id: Part ID

        Returns:
            Part with loaded transactions or None
        """
        return self.session.query(Part) \
            .options(joinedload(Part.transactions)) \
            .filter(Part.id == part_id) \
            .first()