# database/models/product.py
"""
Product Model

This module defines the Product model which implements
the Product entity from the ER diagram.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Float, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import MaterialType  # Assuming you have an enum for material types
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('database.models.product_pattern.ProductPattern',
                     'database.models.product_pattern',
                     'ProductPattern')
register_lazy_import('database.models.product_inventory.ProductInventory',
                     'database.models.product_inventory',
                     'ProductInventory')
register_lazy_import('database.models.sales_item.SalesItem',
                     'database.models.sales_item',
                     'SalesItem')
register_lazy_import('database.models.components.ProjectComponent',
                     'database.models.components',
                     'ProjectComponent')
register_lazy_import('database.models.supplier.Supplier',
                     'database.models.supplier',
                     'Supplier')


class Product(Base):
    """
    Product model representing items that can be sold.
    This corresponds to the Product entity in the ER diagram.
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)

    # SKU and tracking
    sku = Column(String(50), nullable=True, unique=True)
    barcode = Column(String(50), nullable=True, unique=True)

    # Visibility and availability
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)

    # Additional attributes
    weight = Column(Float, nullable=True)
    dimensions = Column(String(100), nullable=True)  # Format: LxWxH

    # Renamed from 'metadata' to 'extra_metadata' to avoid conflict with SQLAlchemy's internal attribute.
    extra_metadata = Column(JSON, nullable=True)

    # Foreign keys
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Relationships
    patterns = relationship("ProductPattern", back_populates="product", cascade="all, delete-orphan")
    inventories = relationship("ProductInventory", back_populates="product", cascade="all, delete-orphan")
    sales_items = relationship("SalesItem", back_populates="product")
    components = relationship("ProjectComponent", back_populates="product", foreign_keys="ProjectComponent.product_id")
    supplier = relationship("Supplier", back_populates="products")

    def __init__(self,
                 name: str,
                 price: float,
                 description: Optional[str] = None,
                 sku: Optional[str] = None,
                 is_active: bool = True,
                 is_featured: bool = False,
                 supplier_id: Optional[int] = None,
                 weight: Optional[float] = None,
                 dimensions: Optional[str] = None,
                 extra_metadata: Optional[Dict[str, Any]] = None,
                 **kwargs):
        """
        Initialize a Product instance.

        Args:
            name: Product name
            price: Product price
            description: Optional product description
            sku: Optional Stock Keeping Unit
            is_active: Whether the product is active
            is_featured: Whether the product is featured
            supplier_id: Optional supplier ID
            weight: Optional product weight
            dimensions: Optional product dimensions
            extra_metadata: Optional additional dynamic attributes
            **kwargs: Additional attributes
        """
        try:
            # Generate SKU if not provided
            if not sku:
                sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"

            # Prepare data
            kwargs.update({
                'name': name,
                'price': price,
                'description': description,
                'sku': sku,
                'is_active': is_active,
                'is_featured': is_featured,
                'supplier_id': supplier_id,
                'weight': weight,
                'dimensions': dimensions,
                'extra_metadata': extra_metadata
            })

            # Validate creation data
            self._validate_creation(kwargs)

            # Initialize the base class
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Product initialization failed: {e}")
            raise ModelValidationError(f"Failed to create product: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate product creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Product name is required')

        # Validate price
        validate_positive_number(data, 'price', allow_zero=False, message="Price must be positive")

        # Validate weight if provided
        if data.get('weight') is not None:
            validate_positive_number(data, 'weight', allow_zero=False, message="Weight must be positive")

    def deactivate(self) -> None:
        """Deactivate the product."""
        self.is_active = False
        logger.info(f"Product {self.id} deactivated")

    def activate(self) -> None:
        """Activate the product."""
        self.is_active = True
        logger.info(f"Product {self.id} activated")

    def update_price(self, new_price: float) -> None:
        """
        Update the product price.

        Args:
            new_price: New product price

        Raises:
            ValidationError: If price is invalid
        """
        if new_price <= 0:
            raise ValidationError("Price must be positive")

        self.price = new_price
        logger.info(f"Product {self.id} price updated to {new_price}")

    def __repr__(self) -> str:
        """String representation of the product."""
        return (
            f"<Product(id={self.id}, name='{self.name}', "
            f"price={self.price}, active={self.is_active})>"
        )


# Initialize relationships
def initialize_relationships():
    """
    Initialize relationships after all models are loaded.
    """
    try:
        logger.info("Initializing Product model relationships")

        # Import necessary models directly to avoid circular import issues
        from database.models.product_pattern import ProductPattern
        from database.models.product_inventory import ProductInventory
        from database.models.sales_item import SalesItem

        logger.info("Product relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing product relationships: {e}")


# Final registration
register_lazy_import('database.models.product.Product', 'database.models.product', 'Product')
