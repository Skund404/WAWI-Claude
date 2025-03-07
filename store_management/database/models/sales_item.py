# database/models/sales_item.py
"""
Sales Item Model for Leatherworking Management System

Represents individual items within a sales transaction,
providing detailed tracking and validation.
"""

import logging
from typing import Any, Optional, Dict, Union

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError
)

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports to resolve potential circular dependencies
register_lazy_import('Sales', 'database.models.sales', 'Sales')
register_lazy_import('Product', 'database.models.product', 'Product')


class SalesItem(Base, TimestampMixin, ValidationMixin):
    """
    Represents an individual item within a sales transaction.

    Tracks detailed information about products sold,
    including quantity, pricing, and relationships.
    """
    __tablename__ = 'sales_items'

    # Foreign keys
    sales_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('sales.id'),
        nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('products.id'),
        nullable=False
    )

    # Item details
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    # Relationships with lazy loading
    sale: Mapped['Sales'] = relationship(
        "Sales",
        back_populates="items",
        lazy="selectin"
    )

    product: Mapped['Product'] = relationship(
        "Product",
        back_populates="sales_items",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a SalesItem instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for sales item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_sales_item_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"SalesItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create SalesItem: {str(e)}") from e

    @classmethod
    def _validate_sales_item_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of sales item creation data.

        Args:
            data (Dict[str, Any]): Sales item creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        required_fields = ['sales_id', 'product_id', 'price']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValidationError(f"{field.replace('_', ' ').title()} is required", field)

        # Validate quantity
        cls._validate_quantity(data.get('quantity', 1))

        # Validate price
        cls._validate_price(data['price'])

    @classmethod
    def _validate_quantity(cls, quantity: int) -> None:
        """
        Validate sales item quantity.

        Args:
            quantity: Quantity to validate

        Raises:
            ValidationError: If quantity is invalid
        """
        if not isinstance(quantity, int):
            raise ValidationError("Quantity must be an integer", "quantity")

        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero", "quantity")

    @classmethod
    def _validate_price(cls, price: float) -> None:
        """
        Validate sales item price.

        Args:
            price: Price to validate

        Raises:
            ValidationError: If price is invalid
        """
        if not isinstance(price, (int, float)):
            raise ValidationError("Price must be a number", "price")

        if price < 0:
            raise ValidationError("Price cannot be negative", "price")

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Ensure quantity is at least 1 if not specified
        if not hasattr(self, 'quantity') or self.quantity is None:
            self.quantity = 1

    @property
    def total_price(self) -> float:
        """
        Calculate the total price for this sales item.

        Returns:
            float: Total price (price * quantity)
        """
        try:
            return self.price * self.quantity
        except Exception as e:
            logger.error(f"Total price calculation failed: {e}")
            raise ModelValidationError(f"Cannot calculate total price: {e}")

    def update_quantity(self, new_quantity: int) -> None:
        """
        Update the quantity of the sales item.

        Args:
            new_quantity: New quantity to set

        Raises:
            ModelValidationError: If quantity update fails
        """
        try:
            # Validate new quantity
            self._validate_quantity(new_quantity)

            # Update quantity
            self.quantity = new_quantity

            # If part of a sale, recalculate sale total
            if hasattr(self, 'sale') and self.sale:
                self.sale.calculate_total_amount()

            logger.info(f"SalesItem {self.id} quantity updated to {new_quantity}")

        except Exception as e:
            logger.error(f"Quantity update failed for SalesItem {self.id}: {e}")
            raise ModelValidationError(f"Cannot update sales item quantity: {e}")

    def update_price(self, new_price: float) -> None:
        """
        Update the price of the sales item.

        Args:
            new_price: New price to set

        Raises:
            ModelValidationError: If price update fails
        """
        try:
            # Validate new price
            self._validate_price(new_price)

            # Update price
            self.price = new_price

            # If part of a sale, recalculate sale total
            if hasattr(self, 'sale') and self.sale:
                self.sale.calculate_total_amount()

            logger.info(f"SalesItem {self.id} price updated to {new_price}")

        except Exception as e:
            logger.error(f"Price update failed for SalesItem {self.id}: {e}")
            raise ModelValidationError(f"Cannot update sales item price: {e}")

    def __repr__(self) -> str:
        """
        String representation of the SalesItem.

        Returns:
            str: Detailed sales item representation
        """
        return (
            f"SalesItem("
            f"id={self.id}, "
            f"sales_id={self.sales_id}, "
            f"product_id={self.product_id}, "
            f"quantity={self.quantity}, "
            f"price={self.price}, "
            f"total_price={self.total_price}"
            f")"
        )


def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing SalesItem relationships")
    try:
        # Import necessary models
        from database.models.sales import Sales
        from database.models.product import Product

        # Ensure relationships are properly configured
        logger.info("SalesItem relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up SalesItem relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('SalesItem', 'database.models.sales_item', 'SalesItem')