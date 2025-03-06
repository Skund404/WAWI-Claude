# database/models/hardware_inventory.py
"""
Hardware Inventory Model

This module defines the HardwareInventory model which implements
the HardwareInventory entity from the ER diagram.
"""

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import InventoryStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Hardware = lazy_import('database.models.hardware', 'Hardware')

# Register lazy imports
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')


class HardwareInventory(Base):
    """
    HardwareInventory model representing hardware stock quantities and locations.
    This corresponds to the HardwareInventory entity in the ER diagram.
    """
    __tablename__ = 'hardware_inventories'

    id = Column(Integer, primary_key=True)
    hardware_id = Column(Integer, ForeignKey('hardwares.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    status = Column(Enum(InventoryStatus), nullable=False, default=InventoryStatus.IN_STOCK)
    storage_location = Column(String(100), nullable=True)

    # Relationships
    hardware = relationship("Hardware", back_populates="inventories")
    transactions = relationship("HardwareTransaction", back_populates="hardware_inventory")

    def __init__(self, hardware_id: int, quantity: int, status: InventoryStatus = InventoryStatus.IN_STOCK,
                 storage_location: Optional[str] = None, **kwargs):
        """
        Initialize a HardwareInventory instance.

        Args:
            hardware_id: ID of the hardware
            quantity: Quantity in stock
            status: Inventory status
            storage_location: Where the hardware is stored
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'hardware_id': hardware_id,
                'quantity': quantity,
                'status': status,
                'storage_location': storage_location
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"HardwareInventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create hardware inventory: {str(e)}") from e

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
        validate_not_empty(data, 'hardware_id', 'Hardware ID is required')

        # Validate quantity
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=True,
                message="Quantity cannot be negative"
            )

    def update_quantity(self, amount: int, is_addition: bool = True) -> None:
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

            logger.info(f"HardwareInventory {self.id} quantity updated to {self.quantity}")

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
        return f"<HardwareInventory(id={self.id}, hardware_id={self.hardware_id}, quantity={self.quantity})>"


# Final registration
register_lazy_import('database.models.hardware_inventory.HardwareInventory', 'database.models.hardware_inventory',
                     'HardwareInventory')