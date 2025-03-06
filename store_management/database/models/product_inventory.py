# database/models/product_inventory.py
"""
Model for tracking product inventory.

This module defines the ProductInventory model, which keeps track of the
quantity and status of products in inventory.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import InventoryStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to avoid circular dependencies
register_lazy_import('Product', 'database.models.product', 'Product')


class ProductInventory(Base):
    """Model representing inventory of products."""

    __tablename__ = 'product_inventory'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign keys
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('product.id'), nullable=False)

    # Inventory details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus), nullable=False,
                                                    default=InventoryStatus.IN_STOCK)
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Inventory management fields
    reorder_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reorder_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # This will be populated by initialize_relationships
    product = relationship("Product", back_populates="inventory_items")

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a ProductInventory instance with validation.

        Args:
            **kwargs: Keyword arguments for inventory attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate required fields
            required_fields = ['product_id']
            for field in required_fields:
                if field not in kwargs or kwargs[field] is None:
                    raise ModelValidationError(f"Field '{field}' is required for ProductInventory")

            # Validate quantity is non-negative
            if 'quantity' in kwargs and kwargs['quantity'] < 0:
                raise ModelValidationError("Quantity cannot be negative")

            # Ensure status is a valid enum value
            if 'status' in kwargs and isinstance(kwargs['status'], str):
                try:
                    kwargs['status'] = InventoryStatus[kwargs['status']]
                except KeyError:
                    valid_statuses = ", ".join([status.name for status in InventoryStatus])
                    raise ModelValidationError(
                        f"Invalid inventory status: {kwargs['status']}. "
                        f"Valid values are: {valid_statuses}"
                    )

            # Call parent constructor
            super().__init__(**kwargs)
            logger.debug(f"ProductInventory created for product_id={self.product_id} with quantity={self.quantity}")
        except Exception as e:
            if not isinstance(e, ModelValidationError):
                logger.error(f"Error creating ProductInventory: {str(e)}")
                raise ModelValidationError(f"Failed to create ProductInventory: {str(e)}")
            raise

    def needs_reorder(self) -> bool:
        """
        Check if the inventory item needs to be reordered.

        Returns:
            bool: True if quantity is at or below reorder point
        """
        if self.reorder_point is None:
            return False
        return self.quantity <= self.reorder_point

    def update_quantity(self, change: int) -> int:
        """
        Update the quantity of the inventory item.

        Args:
            change: Amount to add (positive) or remove (negative)

        Returns:
            int: The new quantity

        Raises:
            ModelValidationError: If the resulting quantity would be negative
        """
        new_quantity = self.quantity + change
        if new_quantity < 0:
            raise ModelValidationError(
                f"Cannot reduce quantity by {abs(change)} as it would result in negative inventory")

        self.quantity = new_quantity

        # Update status if needed
        if new_quantity == 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.needs_reorder():
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

        logger.debug(f"Updated quantity for product_id={self.product_id} by {change} to {self.quantity}")
        return self.quantity

    def __repr__(self) -> str:
        """String representation of the ProductInventory."""
        return f"ProductInventory(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, status={self.status.name})"


def initialize_relationships() -> None:
    """Initialize relationships to avoid circular imports."""
    try:
        # This function will be called after all models are loaded
        from database.models.product import Product

        # Make sure relationships are properly set up
        if not hasattr(ProductInventory, 'product') or not hasattr(Product, 'inventory_items'):
            ProductInventory.product = relationship("Product", back_populates="inventory_items")
            Product.inventory_items = relationship("ProductInventory", back_populates="product",
                                                   cascade="all, delete-orphan")

        logger.debug("ProductInventory relationships initialized")
    except ImportError as e:
        logger.error(f"Error setting up ProductInventory relationships: {str(e)}")