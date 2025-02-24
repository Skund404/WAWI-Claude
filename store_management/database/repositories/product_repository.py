# Path: database/repositories/product_repository.py

from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.product import Product
from database.repositories.interfaces.base_repository import IBaseRepository


class ProductRepository(IBaseRepository):
    """
    Repository for managing Product-related database operations.
    """

    def __init__(self, session: Session):
        """
        Initialize the Product Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        self._session = session

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieve a product by its ID.

        Args:
            product_id (int): Unique identifier for the product

        Returns:
            Optional[Product]: Product instance or None if not found
        """
        try:
            return self._session.query(Product).get(product_id)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error retrieving product {product_id}", str(e))

    def get_all(self, limit: Optional[int] = None,
                offset: Optional[int] = None) -> List[Product]:
        """
        Retrieve all products with optional pagination.

        Args:
            limit (Optional[int]): Maximum number of products to return
            offset (Optional[int]): Number of products to skip

        Returns:
            List[Product]: List of product instances
        """
        try:
            query = self._session.query(Product)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError("Error retrieving all products", str(e))

    def add(self, product: Product) -> Product:
        """
        Add a new product to the database.

        Args:
            product (Product): Product instance to add

        Returns:
            Product: Added product instance
        """
        try:
            self._session.add(product)
            self._session.commit()
            return product
        except SQLAlchemyError as e:
            self._session.rollback()
            raise DatabaseError("Error adding product", str(e))

    def update(self, product: Product) -> Product:
        """
        Update an existing product.

        Args:
            product (Product): Product instance to update

        Returns:
            Product: Updated product instance
        """
        try:
            updated_product = self._session.merge(product)
            self._session.commit()
            return updated_product
        except SQLAlchemyError as e:
            self._session.rollback()
            raise DatabaseError(f"Error updating product {product.id}", str(e))

    def delete(self, product_id: int) -> bool:
        """
        Delete a product by its ID.

        Args:
            product_id (int): Unique identifier for the product

        Returns:
            bool: True if deletion was successful
        """
        try:
            product = self.get_by_id(product_id)
            if product:
                self._session.delete(product)
                self._session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self._session.rollback()
            raise DatabaseError(f"Error deleting product {product_id}", str(e))

    def search_by_name(self, name: str) -> List[Product]:
        """
        Search products by name (case-insensitive, partial match).

        Args:
            name (str): Search term

        Returns:
            List[Product]: List of matching products
        """
        try:
            return (
                self._session.query(Product)
                .filter(Product.name.ilike(f"%{name}%"))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error searching products by name: {name}", str(e))

    def get_active_products(self) -> List[Product]:
        """
        Retrieve all active products.

        Returns:
            List[Product]: List of active product instances
        """
        try:
            return (
                self._session.query(Product)
                .filter(Product.is_active == True)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError("Error retrieving active products", str(e))

    def get_low_stock_products(self, include_zero_stock: bool = False) -> List[Product]:
        """
        Retrieve products with low stock.

        Args:
            include_zero_stock (bool): Whether to include products with zero stock

        Returns:
            List[Product]: List of products with low stock
        """
        try:
            query = self._session.query(Product).filter(
                Product.current_stock <= Product.minimum_stock_level
            )

            if not include_zero_stock:
                query = query.filter(Product.current_stock > 0)

            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError("Error retrieving low stock products", str(e))

    def get_products_by_category(self, category: str) -> List[Product]:
        """
        Retrieve products by category.

        Args:
            category (str): Product category

        Returns:
            List[Product]: List of products in the specified category
        """
        try:
            return (
                self._session.query(Product)
                .filter(Product.category == category)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error retrieving products in category: {category}", str(e))

    def get_product_sales_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of product sales.

        Returns:
            Dict[str, Any]: Product sales summary
        """
        try:
            # Total number of products
            total_products = self._session.query(Product).count()

            # Total active products
            active_products = (
                self._session.query(Product)
                .filter(Product.is_active == True)
                .count()
            )

            # Products with low stock
            low_stock_products = len(self.get_low_stock_products())

            return {
                'total_products': total_products,
                'active_products': active_products,
                'low_stock_products': low_stock_products
            }
        except SQLAlchemyError as e:
            raise DatabaseError("Error generating product sales summary", str(e))


# Custom exception for database-related errors
class DatabaseError(Exception):
    """
    Custom exception for database operation errors.

    Attributes:
        message (str): Error message
        details (str): Detailed error description
    """

    def __init__(self, message: str, details: str = None):
        """
        Initialize DatabaseError.

        Args:
            message (str): Primary error message
            details (str, optional): Additional error details
        """
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        """
        String representation of the error.

        Returns:
            str: Formatted error message
        """
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message