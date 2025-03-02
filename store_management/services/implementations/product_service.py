# services/implementations/product_service.py
from database.models.product import Product
from database.models.enums import MaterialType
from database.repositories.product_repository import ProductRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.product_service import IProductService

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
import logging
import uuid


class ProductService(BaseService, IProductService):
    """
    Service implementation for managing Product entities.

    Responsibilities:
    - Create, read, update, and delete product records
    - Validate product data
    - Handle database interactions
    - Provide business logic for product management
    """

    def __init__(self,
                 session: Optional[Session] = None,
                 product_repository: Optional[ProductRepository] = None):
        """
        Initialize the Product Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
            product_repository (Optional[ProductRepository]): Product data access repository
        """
        self.session = session or get_db_session()
        self.repository = product_repository or ProductRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Create a new product with comprehensive validation.

        Args:
            product_data (Dict[str, Any]): Product creation data

        Returns:
            Product: Newly created product instance

        Raises:
            ValidationError: If product data is invalid
        """
        try:
            # Generate a unique SKU if not provided
            if not product_data.get('sku'):
                product_data['sku'] = self._generate_unique_sku()

            # Validate material type
            if 'material_type' in product_data:
                product_data['material_type'] = MaterialType(product_data['material_type'])

            # Create product instance (will trigger internal validation)
            product = Product(**product_data)

            # Save to database
            self.session.add(product)
            self.session.commit()

            self.logger.info(f"Product created successfully", extra={
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku
            })

            return product

        except (ValueError, TypeError) as e:
            self.logger.error(f"Product creation failed: {str(e)}", extra={
                "error": str(e),
                "product_data": product_data
            })
            raise ValidationError(f"Invalid product data: {str(e)}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error during product creation: {str(e)}", extra={
                "error": str(e),
                "product_data": product_data
            })
            raise ValidationError(f"Database error: {str(e)}")

    def get_product_by_id(self, product_id: int) -> Product:
        """
        Retrieve a product by its ID.

        Args:
            product_id (int): Unique identifier of the product

        Returns:
            Product: Retrieved product instance

        Raises:
            NotFoundError: If no product is found with the given ID
        """
        try:
            product = self.repository.get_by_id(product_id)

            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            return product

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving product: {str(e)}", extra={
                "product_id": product_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error retrieving product: {str(e)}")

    def update_product(self, product_id: int, update_data: Dict[str, Any]) -> Product:
        """
        Update an existing product.

        Args:
            product_id (int): ID of the product to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Product: Updated product instance

        Raises:
            NotFoundError: If product doesn't exist
            ValidationError: If update data is invalid
        """
        try:
            # Retrieve existing product
            product = self.get_product_by_id(product_id)

            # Update material type if provided
            if 'material_type' in update_data:
                update_data['material_type'] = MaterialType(update_data['material_type'])

            # Update product (method includes validation)
            product.update(**update_data)

            # Commit changes
            self.session.commit()

            self.logger.info(f"Product updated successfully", extra={
                "product_id": product.id,
                "updates": list(update_data.keys())
            })

            return product

        except (ValueError, TypeError) as e:
            self.logger.error(f"Product update failed: {str(e)}", extra={
                "product_id": product_id,
                "update_data": update_data,
                "error": str(e)
            })
            raise ValidationError(f"Invalid update data: {str(e)}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error during product update: {str(e)}", extra={
                "product_id": product_id,
                "update_data": update_data,
                "error": str(e)
            })
            raise ValidationError(f"Database error: {str(e)}")

    def delete_product(self, product_id: int) -> None:
        """
        Soft delete a product.

        Args:
            product_id (int): ID of the product to delete

        Raises:
            NotFoundError: If product doesn't exist
        """
        try:
            # Retrieve existing product
            product = self.get_product_by_id(product_id)

            # Soft delete
            product.soft_delete()

            # Commit changes
            self.session.commit()

            self.logger.info(f"Product soft deleted", extra={
                "product_id": product_id
            })

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error soft deleting product: {str(e)}", extra={
                "product_id": product_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error deleting product: {str(e)}")

    def list_products(self,
                      active_only: bool = True,
                      material_type: Optional[MaterialType] = None) -> List[Product]:
        """
        List products with optional filtering.

        Args:
            active_only (bool): Filter for only active products
            material_type (Optional[MaterialType]): Filter by material type

        Returns:
            List[Product]: List of products matching the criteria
        """
        try:
            # Construct query
            query = self.session.query(Product)

            if active_only:
                query = query.filter(Product.is_active == True)

            if material_type:
                query = query.filter(Product.material_type == material_type)

            products = query.all()

            self.logger.info(f"Product list retrieved", extra={
                "total_products": len(products),
                "active_only": active_only,
                "material_type": material_type
            })

            return products

        except SQLAlchemyError as e:
            self.logger.error(f"Error listing products: {str(e)}", extra={
                "error": str(e)
            })
            raise ValidationError(f"Error retrieving products: {str(e)}")

    def _generate_unique_sku(self) -> str:
        """
        Generate a unique SKU for a new product.

        Returns:
            str: Unique SKU in format LTH-PRD-XXXX
        """
        while True:
            # Generate a random 4-digit number
            unique_suffix = str(uuid.uuid4().int)[-4:]
            sku = f"LTH-PRD-{unique_suffix}"

            # Check if SKU already exists
            existing = self.session.query(Product).filter_by(sku=sku).first()

            if not existing:
                return sku