# store_management/database/repositories/product_repository.py

from typing import List, Optional
from sqlalchemy.orm import Session
from ..interfaces.base_repository import BaseRepository
from ..models.product import Product


class ProductRepository(BaseRepository[Product]):
    """Repository for Product model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Product)

    def get_by_storage(self, storage_id: int) -> List[Product]:
        """
        Get products by storage location.

        Args:
            storage_id: Storage location ID

        Returns:
            List of products in the specified storage
        """
        return self.session.query(Product).filter(Product.storage_id == storage_id).all()

    def search_by_name(self, name: str) -> List[Product]:
        """
        Search products by name.

        Args:
            name: Product name to search for

        Returns:
            List of matching products
        """
        search_term = f"%{name}%"
        return self.session.query(Product).filter(Product.name.like(search_term)).all()