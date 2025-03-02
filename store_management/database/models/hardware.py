# database/models/hardware.py
"""
Database model for hardware items used in leatherworking projects.
This model represents hardware components like buckles, snaps, rivets, etc.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Union
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from database.models.base import Base
from database.models.enums import InventoryStatus, TransactionType, MeasurementUnit
from database.models.hardware_enums import HardwareType, HardwareMaterial, HardwareFinish
from utils.validators import validate_string, validate_positive_number, validate_not_empty

logger = logging.getLogger(__name__)


class Hardware(Base):
    """
    Hardware model representing hardware components used in leatherworking projects.

    Attributes:
        id (str): Unique identifier for the hardware item
        name (str): Name of the hardware item
        description (str): Detailed description of the hardware
        hardware_type (HardwareType): Type of hardware (buckle, snap, rivet, etc.)
        material (HardwareMaterial): Material the hardware is made of (brass, nickel, steel)
        finish (HardwareFinish): Finish of the hardware (polished, antique, etc.)
        price (float): Price per unit
        quantity (int): Available quantity in stock
        supplier_id (str): Foreign key to the supplier
        supplier (Supplier): Relationship to the supplier object
        size (str): Size specifications of the hardware
        weight (float): Weight of the hardware item in grams
        is_active (bool): Whether the hardware is currently in use
        reorder_threshold (int): Quantity threshold for reordering
        measurement_unit (MeasurementUnit): Unit of measurement for the hardware
        status (InventoryStatus): Current inventory status
        projects (List[Project]): Projects using this hardware (relationship)
        created_at (datetime): Timestamp when the record was created
        updated_at (datetime): Timestamp when the record was last updated
        deleted_at (datetime): Timestamp when the record was soft deleted
        is_deleted (bool): Flag indicating if the record is soft deleted
    """
    __tablename__ = 'hardware'

    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    hardware_type = Column(Enum(HardwareType), nullable=False)
    material = Column(Enum(HardwareMaterial), nullable=False)
    finish = Column(Enum(HardwareFinish), nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    quantity = Column(Integer, nullable=False, default=0)
    supplier_id = Column(String(36), ForeignKey('supplier.id'), nullable=True)
    size = Column(String(50), nullable=True)
    weight = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    measurement_unit = Column(Enum(MeasurementUnit), nullable=False, default=MeasurementUnit.PIECE)
    status = Column(Enum(InventoryStatus), nullable=False, default=InventoryStatus.IN_STOCK)
    notes = Column(String(500), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="hardware_items")
    projects = relationship("Project", secondary="project_hardware", back_populates="hardware_items")

    def __init__(self, **kwargs):
        """Initialize a Hardware instance with validation.

        Args:
            **kwargs: Keyword arguments with hardware attributes

        Raises:
            ValueError: If validation fails for any field
        """
        # Log the initialization
        logger.debug(f"Initializing new Hardware with params: {kwargs}")

        # Run validations before setting attributes
        self.validate_hardware_data(kwargs)

        # Call parent constructor
        super().__init__(**kwargs)

        logger.info(f"Hardware '{kwargs.get('name')}' created successfully")

    def validate_hardware_data(self, data: Dict[str, Any]) -> None:
        """Validate hardware data to ensure all constraints are met.

        Args:
            data: Dictionary containing hardware data to validate

        Raises:
            ValueError: If any validation fails
        """
        try:
            # Validate required fields
            if 'name' in data:
                validate_string(data['name'], 'name', max_length=100)
                validate_not_empty(data['name'], 'name')

            if 'description' in data and data['description'] is not None:
                validate_string(data['description'], 'description', max_length=500)

            if 'price' in data:
                validate_positive_number(data['price'], 'price')

            if 'quantity' in data:
                validate_positive_number(data['quantity'], 'quantity', allow_zero=True)

            if 'weight' in data and data['weight'] is not None:
                validate_positive_number(data['weight'], 'weight')

            if 'reorder_threshold' in data:
                validate_positive_number(data['reorder_threshold'], 'reorder_threshold', allow_zero=True)

            # Hardware-specific validations
            if 'size' in data and data['size'] is not None:
                validate_string(data['size'], 'size', max_length=50)

            logger.debug("Hardware data validation completed successfully")
        except ValueError as e:
            logger.error(f"Hardware validation failed: {str(e)}")
            raise

    def update(self, **kwargs):
        """Update hardware attributes with validation.

        Args:
            **kwargs: Keyword arguments with hardware attributes to update

        Returns:
            Hardware: Self reference

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Updating Hardware {self.id} with data: {kwargs}")

        # Validate update data
        self.validate_hardware_data(kwargs)

        # Track quantity changes for logging
        old_quantity = self.quantity if hasattr(self, 'quantity') else None
        new_quantity = kwargs.get('quantity', old_quantity)

        # Use parent update method
        super().update(**kwargs)

        # Log quantity changes if applicable
        if old_quantity is not None and new_quantity != old_quantity:
            logger.info(f"Hardware '{self.name}' quantity changed from {old_quantity} to {new_quantity}")

        return self

    def soft_delete(self):
        """Soft delete the hardware item."""
        logger.info(f"Soft deleting hardware: {self.name} (ID: {self.id})")
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        return self

    def restore(self):
        """Restore a soft-deleted hardware item."""
        logger.info(f"Restoring hardware: {self.name} (ID: {self.id})")
        self.is_deleted = False
        self.deleted_at = None
        return self

    def adjust_quantity(self, quantity_change: int, transaction_type: TransactionType, notes: Optional[str] = None):
        """Adjust the quantity of hardware with proper validation and logging.

        Args:
            quantity_change: Amount to change (positive or negative)
            transaction_type: Type of transaction causing the adjustment
            notes: Optional notes about the adjustment

        Returns:
            Hardware: Self reference

        Raises:
            ValueError: If resulting quantity would be negative
        """
        new_quantity = self.quantity + quantity_change

        if new_quantity < 0:
            error_msg = f"Cannot adjust quantity to {new_quantity}. Current quantity is {self.quantity}."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Adjusting hardware '{self.name}' quantity by {quantity_change} "
                    f"({transaction_type.name}). Before: {self.quantity}, After: {new_quantity}")

        self.quantity = new_quantity

        # Update status based on quantity and threshold
        if self.quantity == 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.reorder_threshold:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

        return self

    def __repr__(self):
        """String representation of the hardware.

        Returns:
            str: String representation
        """
        return f"<Hardware(id='{self.id}', name='{self.name}', type='{self.hardware_type.name if self.hardware_type else None}')>"