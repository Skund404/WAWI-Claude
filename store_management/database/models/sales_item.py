# database/models/sales_item.py
"""
Model for sales items in the leatherworking application.

This module defines the SalesItem model, which represents individual items
within a sales transaction. Each item is associated with a product and quantity.
"""

import logging
from typing import Any, Optional

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to avoid circular dependencies
register_lazy_import('Sales', 'database.models.sales', 'Sales')
register_lazy_import('Product', 'database.models.product', 'Product')


class SalesItem(Base):
    """Model representing an item within a sales transaction."""

    __tablename__ = 'sales_item'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign keys
    sales_id: Mapped[int] = mapped_column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('product.id'), nullable=False)

    # Item details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships will be set up by initialize_relationships
    # These are just placeholders that will be properly defined later
    # Don't initialize relationship objects here to avoid circular imports

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the SalesItem instance.

        Args:
            **kwargs: Keyword arguments for sales item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate required fields
            required_fields = ['sales_id', 'product_id', 'price']
            for field in required_fields:
                if field not in kwargs or kwargs[field] is None:
                    raise ModelValidationError(f"Field '{field}' is required for SalesItem")

            # Validate numeric fields
            if 'quantity' in kwargs and kwargs['quantity'] <= 0:
                raise ModelValidationError("Quantity must be greater than zero")

            if 'price' in kwargs and kwargs['price'] < 0:
                raise ModelValidationError("Price cannot be negative")

            # Call parent constructor
            super().__init__(**kwargs)
            logger.debug(
                f"SalesItem created: ID={self.id}, sales_id={self.sales_id}, product_id={self.product_id}, quantity={self.quantity}, price={self.price}")
        except Exception as e:
            if not isinstance(e, ModelValidationError):
                logger.error(f"Error creating SalesItem: {str(e)}")
                raise ModelValidationError(f"Failed to create SalesItem: {str(e)}")
            raise

    @property
    def total_price(self) -> float:
        """
        Calculate the total price for this item.

        Returns:
            float: The total price (price * quantity)
        """
        return self.price * self.quantity

    def __repr__(self) -> str:
        """String representation of the SalesItem."""
        return f"SalesItem(id={self.id}, sales_id={self.sales_id}, product_id={self.product_id}, quantity={self.quantity}, price={self.price})"


def initialize_relationships() -> None:
    """
    Set up relationships to avoid circular imports.
    This function is called after all models are imported.
    """
    logger.debug("Initializing SalesItem relationships")
    try:
        # Import models using lazy_import to avoid issues
        Sales = lazy_import('database.models.sales', 'Sales')
        Product = lazy_import('database.models.product', 'Product')

        # Set up relationships if not already done
        if not hasattr(SalesItem, 'sale') or SalesItem.sale is None:
            SalesItem.sale = relationship("Sales", back_populates="items")
            logger.debug("Set up SalesItem.sale relationship")

        if not hasattr(SalesItem, 'product') or SalesItem.product is None:
            SalesItem.product = relationship("Product", back_populates="sales_items")
            logger.debug("Set up SalesItem.product relationship")

        logger.info("SalesItem relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up SalesItem relationships: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())