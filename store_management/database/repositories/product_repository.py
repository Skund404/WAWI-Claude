# store_management/database/repositories/product_repository.py
"""
Repository for Product model database access.

This module provides specialized operations for retrieving, 
creating, and managing product-related database interactions.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import logging

from di.core import inject
from services.interfaces import MaterialService
from models.product import Product, ProductStatus

# Configure logging
logger = logging.getLogger(__name__)


class ProductRepository:
    """
    Repository for Product model database access.

    Provides advanced querying and management methods for products,
    including retrieval, filtering, and statistical analysis.
    """

    @inject(MaterialService)
    def __init__(self, session):
        """
        Initialize the ProductRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Retrieve a product by its unique identifier.

        Args:
            product_id (int): The unique identifier of the product

        Returns:
            Optional[Product]: The retrieved product or None if not found
        """
        try:
            return self.session.query(Product).get(product_id)
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving product with ID {product_id}: {e}')
            raise

    def get_all(
            self,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Product]:
        """
        Retrieve all products with optional pagination.

        Args:
            limit (Optional[int], optional): Maximum number of products to return
            offset (Optional[int], optional): Number of products to skip

        Returns:
            List[Product]: List of retrieved products
        """
        try:
            query = self.session.query(Product)

            if offset is not None:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving products: {e}')
            raise

    def search_by_name(self, name: str) -> List[Product]:
        """
        Search for products by name using case-insensitive partial matching.

        Args:
            name (str): The name to search for

        Returns:
            List[Product]: List of products matching the name
        """
        try:
            return (
                self.session.query(Product)
                .filter(Product.name.ilike(f'%{name}%'))
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error searching products by name '{name}': {e}")
            raise

    def get_active_products(self) -> List[Product]:
        """
        Retrieve all active products.

        Returns:
            List[Product]: List of active products
        """
        try:
            return (
                self.session.query(Product)
                .filter(Product.is_active == True)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving active products: {e}')
            raise

    def get_low_stock_products(
            self,
            include_zero_stock: bool = True
    ) -> List[Product]:
        """
        Retrieve products with low stock levels.

        Args:
            include_zero_stock (bool, optional): 
                Whether to include products with zero stock. 
                Defaults to True.

        Returns:
            List[Product]: List of products with low stock
        """
        try:
            query = (
                self.session.query(Product)
                .filter(Product.stock_quantity <= Product.reorder_point)
            )

            if not include_zero_stock:
                query = query.filter(Product.stock_quantity > 0)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving low stock products: {e}')
            raise

    def get_products_by_category(self, category: str) -> List[Product]:
        """
        Retrieve products by material type or category.

        Args:
            category (str): The material type/category

        Returns:
            List[Product]: List of products in the specified category
        """
        try:
            return (
                self.session.query(Product)
                .filter(Product.material_type == category)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving products by category '{category}': {e}")
            raise

    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Create a new product.

        Args:
            product_data (Dict[str, Any]): Product creation data

        Returns:
            Product: Created product instance

        Raises:
            ValueError: If required product data is missing
        """
        try:
            # Validate required fields
            if 'name' not in product_data or not product_data['name']:
                raise ValueError("Product name is required")

            # Set default status if not provided
            if 'status' not in product_data:
                product_data['status'] = ProductStatus.ACTIVE

            # Create product instance
            product = Product(**product_data)

            # Add to session and commit
            self.session.add(product)
            self.session.commit()

            return product
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating product: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error creating product: {e}')
            raise

    def get_product_sales_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of product sales and inventory.

        Returns:
            Dict[str, Any]: Product sales statistics
        """
        try:
            # Total products
            total_products = self.session.query(Product).count()

            # Active products
            active_products = (
                self.session.query(Product)
                .filter(Product.is_active == True)
                .count()
            )

            # Low stock products
            low_stock_products = (
                self.session.query(Product)
                .filter(Product.stock_quantity <= Product.reorder_point)
                .count()
            )

            # Calculate profit margins
            products = self.session.query(Product).all()

            # Calculate total and average margin
            total_margin = sum(
                product.calculate_profit_margin() for product in products
            ) if products else 0

            avg_margin = (
                total_margin / len(products) if products else 0
            )

            return {
                'total_products': total_products,
                'active_products': active_products,
                'low_stock_products': low_stock_products,
                'average_profit_margin': round(avg_margin, 2)
            }
        except SQLAlchemyError as e:
            logger.error(f'Error generating product sales summary: {e}')
            raise

    def update_product_stock(
            self,
            product_id: int,
            quantity_change: float
    ) -> Product:
        """
        Update the stock quantity of a product.

        Args:
            product_id (int): Unique identifier of the product
            quantity_change (float): Amount to add or subtract from stock

        Returns:
            Product: Updated product instance

        Raises:
            ValueError: If stock update would result in negative stock
        """
        try:
            product = self.get_by_id(product_id)

            if not product:
                raise ValueError(f"Product with ID {product_id} not found")

            # Calculate new stock
            new_stock = product.stock_quantity + quantity_change

            # Prevent negative stock
            if new_stock < 0:
                raise ValueError(
                    f"Insufficient stock. Cannot reduce below zero. "
                    f"Current: {product.stock_quantity}, Change: {quantity_change}"
                )

            # Update stock quantity
            product.stock_quantity = new_stock

            # Update product status based on stock level
            if new_stock == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif new_stock <= product.reorder_point:
                product.status = ProductStatus.LOW_STOCK
            else:
                product.status = ProductStatus.IN_STOCK

            # Commit changes
            self.session.commit()

            return product
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating product stock for product {product_id}: {e}')
            raise
        except ValueError as e:
            self.session.rollback()
            logger.error(f'Stock update validation error: {e}')
            raise