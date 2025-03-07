# services/implementations/product_service.py
from database.models.product import Product
from database.models.product_inventory import ProductInventory
from database.models.enums import MaterialType
from database.repositories.product_repository import ProductRepository
from database.repositories.product_inventory_repository import ProductInventoryRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.product_service import IProductService
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, List, Optional
import logging
import uuid


class ProductService(BaseService, IProductService):
    def __init__(
            self,
            session: Optional[Session] = None,
            product_repository: Optional[ProductRepository] = None,
            product_inventory_repository: Optional[ProductInventoryRepository] = None
    ):
        """
        Initialize the Product Service.

        Args:
            session: SQLAlchemy database session
            product_repository: Repository for product data access
            product_inventory_repository: Repository for product inventory data access
        """
        self.session = session or get_db_session()
        self.product_repository = product_repository or ProductRepository(self.session)
        self.product_inventory_repository = product_inventory_repository or ProductInventoryRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_product(
            self,
            name: str,
            price: float,
            description: Optional[str] = None
    ) -> Product:
        """
        Create a new product.

        Args:
            name: Product name
            price: Product price
            description: Optional product description

        Returns:
            Created Product instance
        """
        try:
            # Generate a unique identifier for the product
            product_uuid = str(uuid.uuid4())

            product = Product(
                name=name,
                price=price,
                description=description or '',
                product_uuid=product_uuid
            )

            self.session.add(product)
            self.session.flush()  # To get the generated ID

            # Create initial product inventory
            product_inventory = ProductInventory(
                product_id=product.id,
                quantity=0,
                storage_location='DEFAULT'
            )
            self.session.add(product_inventory)

            self.session.commit()

            self.logger.info(f"Created product {product.id}: {name}")
            return product

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating product: {str(e)}")
            raise ValidationError(f"Failed to create product: {str(e)}")

    def get_product_by_id(self, product_id: int) -> Product:
        """
        Retrieve a product by its ID.

        Args:
            product_id: ID of the product to retrieve

        Returns:
            Product instance

        Raises:
            NotFoundError: If product is not found
        """
        try:
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")
            return product
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving product: {str(e)}")
            raise NotFoundError(f"Failed to retrieve product: {str(e)}")

    def update_product(
            self,
            product_id: int,
            name: Optional[str] = None,
            price: Optional[float] = None,
            description: Optional[str] = None
    ) -> Product:
        """
        Update an existing product.

        Args:
            product_id: ID of the product to update
            name: Optional new product name
            price: Optional new product price
            description: Optional new product description

        Returns:
            Updated Product instance
        """
        try:
            product = self.get_product_by_id(product_id)

            if name is not None:
                product.name = name
            if price is not None:
                product.price = price
            if description is not None:
                product.description = description

            self.session.commit()

            self.logger.info(f"Updated product {product_id}")
            return product

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating product: {str(e)}")
            raise ValidationError(f"Failed to update product: {str(e)}")

    def delete_product(self, product_id: int) -> None:
        """
        Delete a product.

        Args:
            product_id: ID of the product to delete
        """
        try:
            product = self.get_product_by_id(product_id)

            # First, delete associated inventory
            inventory = self.product_inventory_repository.get_by_product_id(product_id)
            if inventory:
                self.session.delete(inventory)

            # Then delete the product
            self.session.delete(product)
            self.session.commit()

            self.logger.info(f"Deleted product {product_id}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting product: {str(e)}")
            raise ValidationError(f"Failed to delete product: {str(e)}")

    def list_products(
            self,
            page: int = 1,
            per_page: int = 20
    ) -> List[Product]:
        """
        List products with pagination.

        Args:
            page: Page number
            per_page: Number of products per page

        Returns:
            List of Product instances
        """
        try:
            return self.product_repository.list_products(page, per_page)
        except SQLAlchemyError as e:
            self.logger.error(f"Error listing products: {str(e)}")
            raise NotFoundError(f"Failed to list products: {str(e)}")

    def update_product_inventory(
            self,
            product_id: int,
            quantity: int,
            storage_location: Optional[str] = None
    ) -> ProductInventory:
        """
        Update product inventory quantity and optional storage location.

        Args:
            product_id: ID of the product
            quantity: New quantity of the product
            storage_location: Optional new storage location

        Returns:
            Updated ProductInventory instance
        """
        try:
            # Ensure product exists
            self.get_product_by_id(product_id)

            # Get or create product inventory
            inventory = self.product_inventory_repository.get_by_product_id(product_id)

            if not inventory:
                inventory = ProductInventory(
                    product_id=product_id,
                    quantity=quantity,
                    storage_location=storage_location or 'DEFAULT'
                )
                self.session.add(inventory)
            else:
                inventory.quantity = quantity
                if storage_location:
                    inventory.storage_location = storage_location

            self.session.commit()

            self.logger.info(f"Updated inventory for product {product_id}")
            return inventory

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating product inventory: {str(e)}")
            raise ValidationError(f"Failed to update product inventory: {str(e)}")

    def get_product_inventory(self, product_id: int) -> ProductInventory:
        """
        Retrieve product inventory information.

        Args:
            product_id: ID of the product

        Returns:
            ProductInventory instance
        """
        try:
            # Ensure product exists
            self.get_product_by_id(product_id)

            inventory = self.product_inventory_repository.get_by_product_id(product_id)

            if not inventory:
                # Create default inventory if not exists
                inventory = ProductInventory(
                    product_id=product_id,
                    quantity=0,
                    storage_location='DEFAULT'
                )
                self.session.add(inventory)
                self.session.commit()

            return inventory

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving product inventory: {str(e)}")
            raise NotFoundError(f"Failed to retrieve product inventory: {str(e)}")