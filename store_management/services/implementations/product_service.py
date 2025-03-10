"""
services/implementations/product_service.py

Implementation of the product service for managing products in the leatherworking application.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from database.models.enums import (
    InventoryStatus,
    ProjectType,
    TransactionType
)
from database.repositories.product_repository import ProductRepository
from database.repositories.pattern_repository import PatternRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.sales_repository import SalesRepository
from database.repositories.sales_item_repository import SalesItemRepository

from services.base_service import BaseService
from services.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessRuleError
)
from services.dto.product_dto import ProductDTO

from di.inject import inject


class ProductService(BaseService):
    """
    Service for managing products, including inventory, sales, and patterns.
    """

    @inject
    def __init__(
            self,
            session: Session,
            product_repository: Optional[ProductRepository] = None,
            pattern_repository: Optional[PatternRepository] = None,
            inventory_repository: Optional[InventoryRepository] = None,
            sales_repository: Optional[SalesRepository] = None,
            sales_item_repository: Optional[SalesItemRepository] = None
    ):
        """
        Initialize the product service with necessary repositories.

        Args:
            session: Database session
            product_repository: Repository for product operations
            pattern_repository: Repository for pattern operations
            inventory_repository: Repository for inventory operations
            sales_repository: Repository for sales operations
            sales_item_repository: Repository for sales item operations
        """
        super().__init__(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.pattern_repository = pattern_repository or PatternRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.sales_item_repository = sales_item_repository or SalesItemRepository(session)
        self.logger = logging.getLogger(__name__)

    def _validate_product_data(
            self,
            product_data: Dict[str, Any],
            update: bool = False
    ) -> None:
        """
        Validate product data before creation or update.

        Args:
            product_data: Data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for new products
        if not update:
            required_fields = ['name']
            for field in required_fields:
                if field not in product_data or not product_data[field]:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate price if provided
        if 'price' in product_data:
            price = product_data['price']
            if price is not None and price < 0:
                raise ValidationError("Price cannot be negative")

        # Validate cost price if provided
        if 'cost_price' in product_data:
            cost_price = product_data['cost_price']
            if cost_price is not None and cost_price < 0:
                raise ValidationError("Cost price cannot be negative")

        # Validate initial quantity if provided
        if 'initial_quantity' in product_data:
            quantity = product_data['initial_quantity']
            if quantity is not None and quantity < 0:
                raise ValidationError("Initial quantity cannot be negative")

    def get_by_id(self, product_id: int) -> Dict[str, Any]:
        """
        Retrieve a product by its ID.

        Args:
            product_id: ID of the product to retrieve

        Returns:
            Product data as a dictionary
        """
        try:
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            return ProductDTO.from_model(
                product,
                include_inventory=True,
                include_patterns=True,
                include_sales=True
            ).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving product {product_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all products, optionally filtered.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            List of product data dictionaries
        """
        try:
            products = self.product_repository.get_all(filters=filters)
            return [
                ProductDTO.from_model(product).to_dict()
                for product in products
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving products: {str(e)}")
            raise

    def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product.

        Args:
            product_data: Data for creating the product

        Returns:
            Created product data
        """
        try:
            # Validate product data
            self._validate_product_data(product_data)

            # Add timestamps
            product_data['created_at'] = datetime.now()
            product_data['updated_at'] = datetime.now()

            # Set default active status if not provided
            if 'is_active' not in product_data:
                product_data['is_active'] = True

            # Separate initial quantity and pattern IDs
            initial_quantity = product_data.pop('initial_quantity', 0)
            pattern_ids = product_data.pop('pattern_ids', [])

            with self.transaction():
                # Create product
                product = self.product_repository.create(product_data)

                # Create inventory entry
                inventory_data = {
                    'item_type': 'product',
                    'item_id': product.id,
                    'quantity': initial_quantity,
                    'status': (
                        InventoryStatus.IN_STOCK.value
                        if initial_quantity > 0
                        else InventoryStatus.OUT_OF_STOCK.value
                    ),
                    'storage_location': product_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                # Add patterns if provided
                if pattern_ids:
                    for pattern_id in pattern_ids:
                        pattern = self.pattern_repository.get_by_id(pattern_id)
                        if not pattern:
                            self.logger.warning(
                                f"Pattern with ID {pattern_id} not found, skipping association"
                            )
                            continue
                        self.product_repository.add_pattern(product.id, pattern_id)

                # Retrieve updated product
                result = self.product_repository.get_by_id(product.id)
                return ProductDTO.from_model(
                    result,
                    include_inventory=True,
                    include_patterns=True
                ).to_dict()

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating product: {str(e)}")
            raise

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product.

        Args:
            product_id: ID of the product to update
            product_data: Updated data for the product

        Returns:
            Updated product data
        """
        try:
            # Check if product exists
            existing_product = self.product_repository.get_by_id(product_id)
            if not existing_product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Validate product data
            self._validate_product_data(product_data, update=True)

            # Add update timestamp
            product_data['updated_at'] = datetime.now()

            # Handle pattern associations if provided
            pattern_ids = product_data.pop('pattern_ids', None)

            with self.transaction():
                # Update product
                updated_product = self.product_repository.update(
                    product_id,
                    product_data
                )

                # Update pattern associations if provided
                if pattern_ids is not None:
                    # First remove existing patterns
                    existing_patterns = self.product_repository.get_patterns(product_id)
                    for pattern in existing_patterns:
                        self.product_repository.remove_pattern(
                            product_id,
                            pattern.id
                        )

                    # Add new patterns
                    for pattern_id in pattern_ids:
                        pattern = self.pattern_repository.get_by_id(pattern_id)
                        if not pattern:
                            self.logger.warning(
                                f"Pattern with ID {pattern_id} not found, skipping association"
                            )
                            continue
                        self.product_repository.add_pattern(product_id, pattern_id)

                # Retrieve updated product
                result = self.product_repository.get_by_id(product_id)
                return ProductDTO.from_model(
                    result,
                    include_inventory=True,
                    include_patterns=True
                ).to_dict()

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating product {product_id}: {str(e)}")
            raise

    def delete(self, product_id: int) -> bool:
        """
        Delete a product.

        Args:
            product_id: ID of the product to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Check if product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Check for associated sales
            sales_items = self.sales_item_repository.get_by_product(product_id)
            if sales_items:
                raise BusinessRuleError(
                    f"Cannot delete product with ID {product_id} because it has associated sales"
                )

            with self.transaction():
                # Delete inventory entry if exists
                inventory = self.inventory_repository.get_by_item('product', product_id)
                if inventory:
                    self.inventory_repository.delete(inventory.id)

                # Delete product
                return self.product_repository.delete(product_id)

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting product {product_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for products by name or other properties.

        Args:
            query: Search query string

        Returns:
            List of products matching the search query
        """
        try:
            products = self.product_repository.search(query)
            return [
                ProductDTO.from_model(product).to_dict()
                for product in products
            ]
        except Exception as e:
            self.logger.error(f"Error searching products with query '{query}': {str(e)}")
            raise

    def get_by_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve products using a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of products using the specified pattern
        """
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            products = self.product_repository.get_by_pattern(pattern_id)
            return [
                ProductDTO.from_model(product).to_dict()
                for product in products
            ]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error retrieving products for pattern {pattern_id}: {str(e)}"
            )
            raise

    def get_inventory_status(self, product_id: int) -> Dict[str, Any]:
        """
        Get inventory status for a product.

        Args:
            product_id: ID of the product

        Returns:
            Inventory status details
        """
        try:
            # Check if product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            inventory = self.inventory_repository.get_by_item('product', product_id)

            if not inventory:
                return {
                    'product_id': product_id,
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': '',
                    'last_update': None
                }

            return {
                'product_id': product_id,
                'quantity': inventory.quantity,
                'status': inventory.status,
                'storage_location': inventory.storage_location,
                'last_update': inventory.updated_at
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error retrieving inventory status for product {product_id}: {str(e)}"
            )
            raise

    def get_sales_history(
            self,
            product_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales history for a product.

        Args:
            product_id: ID of the product
            start_date: Optional start date for sales history
            end_date: Optional end date for sales history

        Returns:
            List of sales history entries
        """
        try:
            # Check if product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=365)  # Last year by default

            sales_items = self.sales_item_repository.get_by_product(
                product_id=product_id,
                start_date=start_date,
                end_date=end_date
            )

            result = []
            for item in sales_items:
                sale = self.sales_repository.get_by_id(item.sales_id) if item.sales_id else None
                result.append({
                    'sales_item_id': item.id,
                    'sales_id': item.sales_id,
                    'date': sale.created_at if sale else None,
                    'quantity': item.quantity,
                    'price': item.price,
                    'total': item.quantity * item.price,
                    'customer_id': sale.customer_id if sale else None,
                    'status': sale.status if sale else None
                })

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error retrieving sales history for product {product_id}: {str(e)}"
            )
            raise

    def get_best_sellers(
            self,
            limit: int = 10,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the best-selling products.

        Args:
            limit: Maximum number of best sellers to return
            start_date: Optional start date for sales period
            end_date: Optional end date for sales period

        Returns:
            List of best-selling products
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # Last 90 days by default

            # Get best sellers
            best_sellers = self.product_repository.get_best_sellers(
                limit=limit,
                start_date=start_date,
                end_date=end_date
            )

            result = []
            for product_data in best_sellers:
                product_id = product_data['product_id']
                product = self.product_repository.get_by_id(product_id)

                if not product:
                    continue

                inventory = self.inventory_repository.get_by_item('product', product_id)

                result.append({
                    'product_id': product_id,
                    'product_name': product.name,
                    'quantity_sold': product_data['quantity_sold'],
                    'total_revenue': product_data['total_revenue'],
                    'current_stock': inventory.quantity if inventory else 0,
                    'stock_status': inventory.status if inventory else InventoryStatus.OUT_OF_STOCK.value,
                    'price': getattr(product, 'price', 0),
                    'rank': len(result) + 1
                })

            return result
        except Exception as e:
            self.logger.error(f"Error retrieving best-selling products: {str(e)}")
            raise