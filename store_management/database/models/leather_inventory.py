# database/models/leather_inventory.py
"""
Leather Inventory Model

This module defines the LeatherInventory model which implements
the LeatherInventory entity from the ER diagram.
"""

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import InventoryStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Leather = lazy_import('database.models.leather', 'Leather')

# Register lazy imports
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')


class LeatherInventory(Base):
    """
    LeatherInventory model representing leather stock quantities and locations.
    This corresponds to the LeatherInventory entity in the ER diagram.
    """
    __tablename__ = 'leather_inventories'

    id = Column(Integer, primary_key=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(InventoryStatus), nullable=False, default=InventoryStatus.IN_STOCK)
    storage_location = Column(String(100), nullable=True)

    # Relationships
    leather = relationship("Leather", back_populates="inventories")
    transactions = relationship("LeatherTransaction", back_populates="leather_inventory")

    def __init__(self, leather_id: int, quantity: float, status: InventoryStatus = InventoryStatus.IN_STOCK,
                 storage_location: Optional[str] = None, **kwargs):
        """
        Initialize a LeatherInventory instance.

        Args:
            leather_id: ID of the leather
            quantity: Quantity in stock
            status: Inventory status
            storage_location: Where the leather is stored
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'leather_id': leather_id,
                'quantity': quantity,
                'status': status,
                'storage_location': storage_location
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"LeatherInventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create leather inventory: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate inventory creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'leather_id', 'Leather ID is required')

        # Validate quantity
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=True,
                message="Quantity cannot be negative"
            )

    def update_quantity(self, amount: float, is_addition: bool = True) -> None:
        """
        Update the inventory quantity.

        Args:
            amount: Amount to change
            is_addition: Whether to add or subtract

        Raises:
            ModelValidationError: If resulting quantity would be negative
        """
        try:
            # Calculate new quantity
            new_quantity = self.quantity + amount if is_addition else self.quantity - amount

            # Validate
            if new_quantity < 0:
                raise ValidationError(f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: -{amount}")

            # Update
            self.quantity = new_quantity

            # Update status
            self._update_status()

            logger.info(f"LeatherInventory {self.id} quantity updated to {self.quantity}")

        except Exception as e:
            logger.error(f"Error updating quantity: {e}")
            raise ModelValidationError(f"Failed to update quantity: {str(e)}") from e

    def _update_status(self) -> None:
        """
        Update the inventory status based on quantity.
        """
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity < 10:  # Example threshold
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

    def __repr__(self) -> str:
        """String representation of the inventory."""
        return f"<LeatherInventory(id={self.id}, leather_id={self.leather_id}, quantity={self.quantity})>"


# Final registration
register_lazy_import('database.models.leather_inventory.LeatherInventory', 'database.models.leather_inventory',
                     'LeatherInventory')