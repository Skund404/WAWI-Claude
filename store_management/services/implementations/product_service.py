# Path: services/implementations/product_service.py

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from database.models.product import Product
from database.repositories.product_repository import ProductRepository, DatabaseError
from services.interfaces.product_service import IProductService
from di.service import Service
from utils.exceptions import ValidationError, ResourceNotFoundError


class ProductService(Service, IProductService):
    """
    Implementation of the Product Service.

    Provides comprehensive methods for managing product-related operations.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the Product Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
        """
        super().__init__(None)  # Placeholder for dependency container
        self._session = session or get_db()
        self._logger = logging.getLogger(__name__)
        self._repository = ProductRepository(self._session)

    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product with comprehensive validation.

        Args:
            product_data (Dict[str, Any]): Data for creating a new product

        Returns:
            Dict[str, Any]: Created product details

        Raises:
            ValidationError: If product data is invalid
        """
        try:
            # Validate required fields
            required_fields = ['name', 'price']
            for field in required_fields:
                if field not in product_data:
                    raise ValidationError(f"Missing required field: {field}")

            # Validate input data
            name = product_data['name']
            price = product_data['price']
            description = product_data.get('description', '')
            sku = product_data.get('sku')
            category = product_data.get('category')
            cost_price = product_data.get('cost_price')
            minimum_stock_level = product_data.get('minimum_stock_level', 0.0)

            # Create product using class method with built-in validation
            product = Product.create_product(
                name=name,
                price=price,
                description=description,
                sku=sku,
                category=category,
                cost_price=cost_price,
                minimum_stock_level=minimum_stock_level
            )

            # Save product
            created_product = self._repository.add(product)

            return created_product.to_dict(include_details=True)
        except (DatabaseError, ValidationError) as e:
            self._logger.error(f"Error creating product: {e}")
            raise

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific product by ID with detailed information.

        Args:
            product_id (int): Unique identifier for the product

        Returns:
            Optional[Dict[str, Any]]: Product details

        Raises:
            ResourceNotFoundError: If product is not found
        """
        try:
            product = self._repository.get_by_id(product_id)

            if not product:
                raise ResourceNotFoundError("Product", str(product_id))

            return product.to_dict(include_details=True)
        except DatabaseError as e:
            self._logger.error(f"Error retrieving product {product_id}: {e}")
            raise

    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product with comprehensive validation.

        Args:
            product_id (int): Unique identifier for the product
            product_data (Dict[str, Any]): Updated product information

        Returns:
            Dict[str, Any]: Updated product details

        Raises:
            ResourceNotFoundError: If product is not found
            ValidationError: If product data is invalid
        """
        try:
            # Retrieve existing product
            product = self._repository.get_by_id(product_id)

            if not product:
                raise ResourceNotFoundError("Product", str(product_id))

            # Validate and update fields
            if 'name' in product_data:
                if not product_data['name']:
                    raise ValidationError("Product name cannot be empty")
                product.name = product_data['name']

            if 'description' in product_data:
                product.description = product_data['description']

            if 'price' in product_data:
                if product_data['price'] < 0:
                    raise ValidationError("Price cannot be negative")
                product.price = product_data['price']

            if 'sku' in product_data:
                product.sku = product_data['sku']

            if 'category' in product_data:
                product.category = product_data['category']

            if 'cost_price' in product_data:
                if product_data['cost_price'] < 0:
                    raise ValidationError("Cost price cannot be negative")
                product.cost_price = product_data['cost_price']

            if 'minimum_stock_level' in product_data:
                if product_data['minimum_stock_level'] < 0:
                    raise ValidationError("Minimum stock level cannot be negative")
                product.minimum_stock_level = product_data['minimum_stock_level']

            if 'is_active' in product_data:
                product.is_active = product_data['is_active']

            # Save updated product
            updated_product = self._repository.update(product)

            return updated_product.to_dict(include_details=True)
        except (DatabaseError, ValidationError) as e:
            self._logger.error(f"Error updating product {product_id}: {e}")
            raise

    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product with additional checks.

        Args:
            product_id (int): Unique identifier for the product

        Returns:
            bool: True if deletion was successful

        Raises:
            ResourceNotFoundError: If product is not found
            ValidationError: If product cannot be deleted
        """
        try:
            # Check if product exists
            product = self._repository.get_by_id(product_id)

            if not product:
                raise ResourceNotFoundError("Product", str(product_id))

            # Additional deletion checks
            if product.order_items:
                raise ValidationError("Cannot delete product with existing order history")

            # Perform deletion
            return self._repository.delete(product_id)
        except (DatabaseError, ValidationError) as e:
            self._logger.error(f"Error deleting product {product_id}: {e}")
            raise

    def search_products(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Advanced search for products with multiple search criteria.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Dict[str, Any]]: List of matching products
        """
        try:
            # Name-based search
            if 'name' in search_params:
                return [
                    product.to_dict(include_details=True)
                    for product in self._repository.search_by_name(search_params['name'])
                ]

            # Category-based search
            if 'category' in search_params:
                return [
                    product.to_dict(include_details=True)
                    for product in self._repository.get_products_by_category(search_params['category'])
                ]

            # Active status filter
            if 'is_active' in search_params:
                return [
                    product.to_dict(include_details=True)
                    for product in self._repository.get_active_products()
                ]

            # Low stock filter
            if 'low_stock' in search_params:
                include_zero = search_params.get('include_zero_stock', False)
                return [
                    product.to_dict(include_details=True)
                    for product in self._repository.get_low_stock_products(include_zero)
                ]

            # Price range filter
            if 'min_price' in search_params or 'max_price' in search_params:
                min_price = search_params.get('min_price', 0)
                max_price = search_params.get('max_price', float('inf'))
                return [
                    product.to_dict(include_details=True)
                    for product in self._repository.get_all()
                    if min_price <= product.price <= max_price
                ]

            # If no specific search criteria, return all products
            return [
                product.to_dict(include_details=True)
                for product in self._repository.get_all()
            ]
        except DatabaseError as e:
            self._logger.error(f"Error searching products: {e}")
            raise

    def update_product_stock(self, product_id: int, quantity_change: float,
                             transaction_type: str = 'ADJUSTMENT',
                             notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the stock of a product.

        Args:
            product_id (int): Unique identifier for the product
            quantity_change (float): Amount to change stock by
            transaction_type (str): Type of stock transaction
            notes (Optional[str]): Additional notes for the transaction

        Returns:
            Dict[str, Any]: Updated product details

        Raises:
            ResourceNotFoundError: If product is not found
            ValidationError: If stock update is invalid
        """
        try:
            # Retrieve product
            product = self._repository.get_by_id(product_id)

            if not product:
                raise ResourceNotFoundError("Product", str(product_id))

            # Update stock
            product.update_stock(quantity_change, transaction_type)

            # Save updated product
            updated_product = self._repository.update(product)

            return updated_product.to_dict(include_details=True)
        except (DatabaseError, ValidationError) as e:
            self._logger.error(f"Error updating stock for product {product_id}: {e}")
            raise

    def generate_product_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive product report.

        Returns:
            Dict[str, Any]: Detailed product report
        """
        try:
            # Get product sales summary
            summary = self._repository.get_product_sales_summary()

            # Get low stock products
            low_stock_products = self._repository.get_low_stock_products()

            # Prepare detailed report
            report = {
                'summary': summary,
                'low_stock_products': [
                    product.to_dict(include_details=True)
                    for product in low_stock_products
                ]
            }

            return report
        except DatabaseError as e:
            self._logger.error(f"Error generating product report: {e}")
            raise