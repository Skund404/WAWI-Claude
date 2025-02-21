# store_management/database/repositories/supplier_repository.py

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.supplier import Supplier


class SupplierRepository(BaseRepository[Supplier]):
    """Repository for Supplier model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Supplier)

    def get_with_products(self, supplier_id: int) -> Optional[Supplier]:
        """
        Get supplier with eagerly loaded products.

        Args:
            supplier_id: Supplier ID

        Returns:
            Supplier with products if found, None otherwise
        """
        return self.session.query(Supplier) \
            .options(joinedload(Supplier.parts), joinedload(Supplier.leathers)) \
            .filter(Supplier.id == supplier_id) \
            .first()

    def search(self, term: str) -> List[Supplier]:
        """
        Search suppliers by name or contact name.

        Args:
            term: Search term

        Returns:
            List of matching suppliers
        """
        search_term = f"%{term}%"
        return self.session.query(Supplier) \
            .filter(Supplier.name.like(search_term) |
                    Supplier.contact_name.like(search_term)) \
            .all()