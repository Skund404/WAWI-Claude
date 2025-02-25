# database/sqlalchemy/core/specialized/product_manager.py
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from di.core import inject
from services.interfaces import MaterialService
from models.product import Product
from core.exceptions import DatabaseError
from core.base_manager import BaseManager


class ProductManager(BaseManager[Product]):
    """
    Specialized manager for Product models with additional capabilities.

    Extends BaseManager with product-specific operations.
    """

    def __init__(self, session_factory):
        """
        Initialize the ProductManager.

        Args:
            session_factory (Callable[[], Session]): A factory function 
            that returns a SQLAlchemy Session.
        """
        super().__init__(Product, session_factory)
        self._logger = logging.getLogger(self.__class__.__name__)

    @inject(MaterialService)
    def get_product_with_recipe(self, product_id: int) -> Optional[Product]:
        """
        Get product with its pattern.

        Args:
            product_id (int): Product ID

        Returns:
            Optional[Product]: Product with pattern loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Product).options(
                    joinedload(Product.pattern)
                ).where(Product.id == product_id)
                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            self._logger.error(f'Failed to retrieve product with pattern: {e}')
            raise DatabaseError(f'Failed to retrieve product with pattern', str(e))

    @inject(MaterialService)
    def get_by_storage(self, storage_id: int) -> List[Product]:
        """
        Get products by storage location.

        Args:
            storage_id (int): Storage location ID

        Returns:
            List[Product]: List of products in the specified storage

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                return session.query(Product).filter(Product.storage_id == storage_id).all()
        except Exception as e:
            self._logger.error(f'Failed to retrieve products by storage {storage_id}: {e}')
            raise DatabaseError(f'Failed to retrieve products by storage', str(e))

    @inject(MaterialService)
    def assign_to_storage(self, product_id: int, storage_id: int) -> Optional[Product]:
        """
        Assign a product to a storage location.

        Args:
            product_id (int): Product ID
            storage_id (int): Storage location ID

        Returns:
            Optional[Product]: Updated Product or None if not found

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                product = session.get(Product, product_id)

                if not product:
                    self._logger.warning(f'Product with ID {product_id} not found.')
                    return None

                product.storage_id = storage_id
                session.commit()
                session.refresh(product)
                return product
        except Exception as e:
            self._logger.error(f'Failed to assign product {product_id} to storage {storage_id}: {e}')
            raise DatabaseError(f'Failed to assign product to storage', str(e))

    @inject(MaterialService)
    def search_by_name(self, name: str) -> List[Product]:
        """
        Search products by name.

        Args:
            name (str): Product name to search for

        Returns:
            List[Product]: List of matching products

        Raises:
            DatabaseError: If search fails
        """
        try:
            with self.session_scope() as session:
                return session.query(Product).filter(
                    Product.name.ilike(f'%{name}%')
                ).all()
        except Exception as e:
            self._logger.error(f'Failed to search products by name {name}: {e}')
            raise DatabaseError(f'Failed to search products', str(e))

    @inject(MaterialService)
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Create a new product.

        Args:
            product_data (Dict[str, Any]): Dictionary containing product information

        Returns:
            Product: The created Product instance

        Raises:
            DatabaseError: If product creation fails
        """
        try:
            with self.session_scope() as session:
                product = Product(**product_data)
                session.add(product)
                session.commit()
                session.refresh(product)
                return product
        except Exception as e:
            self._logger.error(f'Failed to create product: {e}')
            raise DatabaseError(f'Failed to create product', str(e))

    @inject(MaterialService)
    def update_product(self, product_id: int, update_data: Dict[str, Any]) -> Optional[Product]:
        """
        Update an existing product.

        Args:
            product_id (int): ID of the product to update
            update_data (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Optional[Product]: Updated Product instance or None if not found

        Raises:
            DatabaseError: If product update fails
        """
        try:
            with self.session_scope() as session:
                product = session.get(Product, product_id)

                if not product:
                    self._logger.warning(f'Product with ID {product_id} not found.')
                    return None

                for key, value in update_data.items():
                    setattr(product, key, value)

                session.commit()
                session.refresh(product)
                return product
        except Exception as e:
            self._logger.error(f'Failed to update product {product_id}: {e}')
            raise DatabaseError(f'Failed to update product', str(e))

    @inject(MaterialService)
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product by its ID.

        Args:
            product_id (int): ID of the product to delete

        Returns:
            bool: True if product was deleted, False otherwise

        Raises:
            DatabaseError: If product deletion fails
        """
        try:
            with self.session_scope() as session:
                product = session.get(Product, product_id)

                if not product:
                    self._logger.warning(f'Product with ID {product_id} not found.')
                    return False

                session.delete(product)
                session.commit()
                return True
        except Exception as e:
            self._logger.error(f'Failed to delete product {product_id}: {e}')
            raise DatabaseError(f'Failed to delete product', str(e))