# database/models/product.py
"""
Enhanced Product Model with SQLAlchemy 2.0 Relationship Approach

This module defines the Product model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import String, Text, Float, Boolean, Integer, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import MaterialType  # Assuming you have an enum for material types
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')  # This one is already correct
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('Storage', 'database.models.storage', 'Storage')
register_lazy_import('OrderItem', 'database.models.order', 'OrderItem')
register_lazy_import('Part', 'database.models.part', 'Part')
register_lazy_import('Production', 'database.models.production', 'Production')
register_lazy_import('Sales', 'database.models.sales', 'Sales')
register_lazy_import('Component', 'database.models.components', 'Component')

# Setup logger
logger = logging.getLogger(__name__)


class Product(Base):
    """
    Enhanced Product model with comprehensive validation and relationship management.

    Represents products sold in the leatherworking business with advanced
    tracking and relationship configuration.
    """
    __tablename__ = 'products'

    # Core product attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)

    # Categorization and metadata
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Comma-separated tags

    # Product type
    material_type: Mapped[Optional[MaterialType]] = mapped_column(
        Enum(MaterialType),
        nullable=True
    )

    # Financial tracking
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Inventory management
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Physical characteristics
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Format: "LxWxH"

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Additional metadata
    product_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Foreign keys with explicitly configured relationships
    pattern_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("patterns.id", ondelete="SET NULL"),
        nullable=True
    )
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    storage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("storages.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships with careful configuration
    pattern: Mapped[Optional["Pattern"]] = relationship(
        "Pattern",
        back_populates="products",
        lazy="selectin",
        foreign_keys=[pattern_id]
    )
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier",
        back_populates="products",
        lazy="selectin",
        foreign_keys=[supplier_id]
    )
    storage: Mapped[Optional["Storage"]] = relationship(
        "Storage",
        back_populates="products",
        lazy="selectin",
        foreign_keys=[storage_id]
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="selectin"
    )
    parts: Mapped[List["Part"]] = relationship(
        "Part",
        back_populates="product",
        lazy="selectin"
    )
    production_records: Mapped[List["Production"]] = relationship(
        "Production",
        back_populates="product",
        lazy="selectin"
    )
    sales: Mapped[List["Sales"]] = relationship(
        "Sales",
        back_populates="product",
        lazy="selectin"
    )
    components: Mapped[List["Component"]] = relationship(
        "ProjectComponent",
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Product instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for product attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Generate SKU if not provided
            if 'sku' not in kwargs and 'name' in kwargs:
                kwargs['sku'] = self._generate_sku(kwargs['name'])

            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization validation
            self._validate_instance()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Product initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Product: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate product creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Product creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Product name is required')

        # Validate numeric fields
        numeric_fields = [
            'price', 'cost',
            'stock_quantity', 'min_stock_quantity',
            'weight'
        ]

        for field in numeric_fields:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

        # Validate SKU if provided
        if 'sku' in data and data['sku']:
            cls._validate_sku(data['sku'])

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate relationships
        if self.pattern and not hasattr(self.pattern, 'id'):
            raise ValidationError("Invalid pattern reference", "pattern")

        if self.supplier and not hasattr(self.supplier, 'id'):
            raise ValidationError("Invalid supplier reference", "supplier")

        # Validate stock levels
        if self.stock_quantity < 0:
            raise ValidationError(
                "Stock quantity cannot be negative",
                "stock_quantity"
            )

    @classmethod
    def _validate_sku(cls, sku: str) -> None:
        """
        Validate SKU format.

        Args:
            sku (str): SKU to validate

        Raises:
            ValidationError: If SKU is invalid
        """
        # Example SKU validation (adjust as needed)
        if not sku or len(sku) < 3 or len(sku) > 50:
            raise ValidationError(
                "SKU must be between 3 and 50 characters",
                "sku",
                "invalid_sku_length"
            )

    def _generate_sku(self, name: str) -> str:
        """
        Generate a SKU for the product based on name.

        Args:
            name (str): Product name

        Returns:
            str: Generated SKU
        """
        # Take first 3 letters of name (uppercase) + 8 chars of a UUID
        name_part = ''.join(c for c in name if c.isalnum())[:3].upper()
        uuid_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"{name_part}-{uuid_part}"

    def adjust_stock(self, quantity_change: int) -> None:
        """
        Adjust the stock quantity with validation.

        Args:
            quantity_change (int): The quantity to add (positive) or remove (negative)

        Raises:
            ModelValidationError: If stock adjustment is invalid
        """
        try:
            new_quantity = self.stock_quantity + quantity_change

            if new_quantity < 0:
                raise ModelValidationError(
                    f"Cannot adjust stock to {new_quantity}. Current stock is {self.stock_quantity}."
                )

            self.stock_quantity = new_quantity

            # Update status based on stock levels
            if self.stock_quantity == 0:
                self.is_active = False
            elif self.stock_quantity < self.min_stock_quantity:
                logger.warning(f"Product {self.id} is below minimum stock quantity")

        except Exception as e:
            logger.error(f"Stock adjustment failed: {e}")
            raise ModelValidationError(f"Stock adjustment failed: {str(e)}")

    def calculate_profit_margin(self) -> Optional[float]:
        """
        Calculate the product's profit margin.

        Returns:
            float: Profit margin as a percentage, or None if price is zero
        """
        try:
            if self.price > 0:
                return ((self.price - self.cost) / self.price) * 100
            return None
        except Exception as e:
            logger.error(f"Profit margin calculation failed: {e}")
            raise ModelValidationError(f"Profit margin calculation failed: {str(e)}")

    def needs_restock(self) -> bool:
        """
        Check if the product needs to be restocked.

        Returns:
            bool: True if the stock quantity is below the minimum stock quantity
        """
        return self.stock_quantity <= self.min_stock_quantity

    def soft_delete(self) -> None:
        """
        Soft delete the product by marking it as inactive.
        """
        self.is_active = False
        logger.info(f"Product {self.id} marked as inactive")

    def restore(self) -> None:
        """
        Restore a soft-deleted product.
        """
        self.is_active = True
        logger.info(f"Product {self.id} restored to active status")

    def __repr__(self) -> str:
        """
        String representation of the product.

        Returns:
            str: Descriptive string of the product
        """
        return (
            f"<Product(id={self.id}, name='{self.name}', "
            f"sku='{self.sku}', "
            f"stock={self.stock_quantity}, "
            f"active={self.is_active})>"
        )


# Register this class for lazy imports by others
register_lazy_import('Product', 'database.models.product', 'Product')