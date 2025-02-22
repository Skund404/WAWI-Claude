# database/sqlalchemy/core/specialized/product_manager.py
"""
database/sqlalchemy/core/specialized/product_manager.py
Specialized manager for Product models with additional capabilities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from database.sqlalchemy.core.base_manager import BaseManager
from database.models import Product, Storage, Recipe
from utils.error_handling import DatabaseError


class ProductManager(BaseManager[Product]):
    """
    Specialized manager for Product model operations.

    Extends BaseManager with product-specific operations.
    """

    def get_product_with_recipe(self, product_id: int) -> Optional[Product]:
        """
        Get product with its recipe.

        Args:
            product_id: Product ID

        Returns:
            Product with recipe loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Product).options(
                    joinedload(Product.recipe)
                ).where(Product.id == product_id)

                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve product with recipe", str(e))

    def get_by_storage(self, storage_id: int) -> List[Product]:
        """
        Get products by storage location.

        Args:
            storage_id: Storage location ID

        Returns:
            List of products in the specified storage

        Raises:
            DatabaseError: If retrieval fails
        """
        return self.filter_by(storage_id=storage_id)

    def assign_to_storage(self, product_id: int, storage_id: int) -> Optional[Product]:
        """
        Assign a product to a storage location.

        Args:
            product_id: Product ID
            storage_id: Storage location ID

        Returns:
            Updated Product or None if not found

        Raises:
            DatabaseError: If update fails
        """
        return self.update(product_id, {'storage_id': storage_id})

    def search_by_name(self, name: str) -> List[Product]:
        """
        Search products by name.

        Args:
            name: Product name to search for

        Returns:
            List of matching products

        Raises:
            DatabaseError: If search fails
        """
        return self.search(name, fields=['name', 'sku'])