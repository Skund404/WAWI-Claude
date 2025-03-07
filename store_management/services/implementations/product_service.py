# database/services/implementations/product_service.py
"""
Service implementation for managing Product entities and their relationships.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
import logging

from database.models.enums import MaterialType
from database.models.product import Product
from database.models.product_inventory import ProductInventory
from database.models.product_pattern import ProductPattern
from database.repositories.product_repository import ProductRepository
from database.repositories.product_inventory_repository import ProductInventoryRepository
from database.repositories.product_pattern_repository import ProductPatternRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.product_service import IProductService


class ProductService(BaseService[Product], IProductService):
    """
    Service for managing Product-related operations.

    Handles creation, retrieval, updating, and deletion of products,
    along with inventory and pattern management.
    """

    def __init__(
            self,
            session=None,
            product_repository: Optional[ProductRepository] = None,
            product_inventory_repository: Optional[ProductInventoryRepository] = None,
            product_pattern_repository: Optional[ProductPatternRepository] = None
    ):
        """
        Initialize the Product Service.

        Args:
            session: SQLAlchemy database session
            product_repository: Repository for product data access
            product_inventory_repository: Repository for product inventory
            product_pattern_repository: Repository for product pattern relationships
        """
        self.session = session or get_db_session()
        self.product_repository = product_repository or ProductRepository(self.session)
        self.product_inventory_repository = (
                product_inventory_repository or
                ProductInventoryRepository(self.session)
        )
        self.product_pattern_repository = (
                product_pattern_repository or
                ProductPatternRepository(self.session)
        )
        self.logger = logging.getLogger(__name__)

    def create_product(
            self,
            name: str,
            price: float,
            **kwargs
    ) -> Product:
        """
        Create a new product with optional additional attributes.

        Args:
            name: Product name
            price: Product price
            **kwargs: Additional product attributes

        Returns:
            Created Product instance

        Raises:
            ValidationError: If product creation fails validation
        """
        try:
            # Validate required fields
            if not name or price <= 0:
                raise ValidationError("Invalid product name or price")

            # Generate a unique identifier
            product_id = str(uuid.uuid4())

            # Create product
            product_data = {
                'id': product_id,
                'name': name,
                'price': price,
                **kwargs
            }

            product = Product(**product_data)

            # Save product
            with self.session:
                self.session.add(product)
                self.session.commit()
                self.session.refresh(product)

            self.logger.info(f"Created product: {product.name}")
            return product

        except Exception as e:
            self.logger.error(f"Error creating product: {str(e)}")
            raise ValidationError(f"Product creation failed: {str(e)}")

    def get_product_by_id(self, product_id: str) -> Product:
        """
        Retrieve a product by its ID.

        Args:
            product_id: Unique identifier of the product

        Returns:
            Product instance

        Raises:
            NotFoundError: If product is not found
        """
        try:
            product = self.product_repository.get(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")
            return product
        except Exception as e:
            self.logger.error(f"Error retrieving product: {str(e)}")
            raise NotFoundError(f"Product retrieval failed: {str(e)}")

    def update_product(
            self,
            product_id: str,
            **update_data: Dict[str, Any]
    ) -> Product:
        """
        Update an existing product.

        Args:
            product_id: Unique identifier of the product
            update_data: Dictionary of fields to update

        Returns:
            Updated Product instance

        Raises:
            NotFoundError: If product is not found
            ValidationError: If update fails validation
        """
        try:
            # Retrieve existing product
            product = self.get_product_by_id(product_id)

            # Update product attributes
            for key, value in update_data.items():
                setattr(product, key, value)

            # Save updates
            with self.session:
                self.session.add(product)
                self.session.commit()
                self.session.refresh(product)

            self.logger.info(f"Updated product: {product.name}")
            return product

        except Exception as e:
            self.logger.error(f"Error updating product: {str(e)}")
            raise ValidationError(f"Product update failed: {str(e)}")

    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product.

        Args:
            product_id: Unique identifier of the product

        Returns:
            Boolean indicating successful deletion

        Raises:
            NotFoundError: If product is not found
        """
        try:
            # Retrieve product
            product = self.get_product_by_id(product_id)

            # Delete product
            with self.session:
                self.session.delete(product)
                self.session.commit()

            self.logger.info(f"Deleted product: {product_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting product: {str(e)}")
            raise NotFoundError(f"Product deletion failed: {str(e)}")

    def get_products_by_type(
            self,
            material_type: Optional[MaterialType] = None
    ) -> List[Product]:
        """
        Retrieve products filtered by material type.

        Args:
            material_type: Optional material type to filter products

        Returns:
            List of Product instances
        """
        try:
            # Use repository method to filter products
            products = self.product_repository.get_by_material_type(material_type)
            return products
        except Exception as e:
            self.logger.error(f"Error retrieving products: {str(e)}")
            return []

    def add_product_inventory(
            self,
            product_id: str,
            quantity: int,
            storage_location: Optional[str] = None
    ) -> ProductInventory:
        """
        Add inventory for a specific product.

        Args:
            product_id: Unique identifier of the product
            quantity: Quantity to add to inventory
            storage_location: Optional storage location

        Returns:
            ProductInventory instance

        Raises:
            NotFoundError: If product is not found
            ValidationError: If inventory addition fails
        """
        try:
            # Verify product exists
            product = self.get_product_by_id(product_id)

            # Create inventory entry
            inventory_data = {
                'product_id': product_id,
                'quantity': quantity,
                'storage_location': storage_location
            }

            product_inventory = ProductInventory(**inventory_data)

            # Save inventory
            with self.session:
                self.session.add(product_inventory)
                self.session.commit()
                self.session.refresh(product_inventory)

            self.logger.info(f"Added inventory for product: {product_id}")
            return product_inventory

        except Exception as e:
            self.logger.error(f"Error adding product inventory: {str(e)}")
            raise ValidationError(f"Product inventory addition failed: {str(e)}")