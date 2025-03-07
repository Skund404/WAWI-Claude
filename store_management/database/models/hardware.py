# database/models/hardware.py
"""
Comprehensive Hardware Model for Leatherworking Management System

This module defines the Hardware model with extensive validation,
relationship management, and circular import resolution.

Implements the Hardware entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    HardwareType,
    HardwareMaterial,
    HardwareFinish,
    InventoryStatus,
    MeasurementUnit,
    QualityGrade,
    TransactionType
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('PurchaseItem', 'database.models.purchase', 'PurchaseItem')
register_lazy_import('PickingListItem', 'database.models.picking_list', 'PickingListItem')
register_lazy_import('HardwareInventory', 'database.models.hardware_inventory', 'HardwareInventory')
register_lazy_import('ComponentHardware', 'database.models.components', 'ComponentHardware')
register_lazy_import('HardwareTransaction', 'database.models.transaction', 'HardwareTransaction')


# Validation utility functions
def validate_not_empty(data: Dict[str, Any], field_name: str, message: str = None):
    """
    Validate that a field is not empty.

    Args:
        data: Data dictionary to validate
        field_name: Field to check
        message: Optional custom error message

    Raises:
        ValidationError: If the field is empty
    """
    if field_name not in data or data[field_name] is None:
        raise ValidationError(message or f"{field_name} cannot be empty")


def validate_positive_number(data: Dict[str, Any], field_name: str, allow_zero: bool = False, message: str = None):
    """
    Validate that a field is a positive number.

    Args:
        data: Data dictionary to validate
        field_name: Field to check
        allow_zero: Whether zero is considered valid
        message: Optional custom error message

    Raises:
        ValidationError: If the field is not a positive number
    """
    if field_name not in data:
        return

    value = data[field_name]

    if value is None:
        return

    try:
        number_value = float(value)
        if allow_zero:
            if number_value < 0:
                raise ValidationError(message or f"{field_name} must be a non-negative number")
        else:
            if number_value <= 0:
                raise ValidationError(message or f"{field_name} must be a positive number")
    except (ValueError, TypeError):
        raise ValidationError(message or f"{field_name} must be a valid number")


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class ModelValidator:
    """Utility class for model validation."""

    @staticmethod
    def validate_enum(value: Any, enum_class: Type, field_name: str) -> None:
        """
        Validate that a value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            field_name: Name of the field being validated

        Raises:
            ValidationError: If validation fails
        """
        try:
            if not isinstance(value, enum_class):
                # Try to convert string to enum
                if isinstance(value, str):
                    try:
                        enum_class[value.upper()]
                        return
                    except (KeyError, AttributeError):
                        pass
                raise ValidationError(f"{field_name} must be a valid {enum_class.__name__}")
        except Exception:
            raise ValidationError(f"Invalid {field_name} value")


class Hardware(Base, TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin):
    """
    Hardware model representing hardware items used in leatherworking projects.

    This implements the Hardware entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'hardwares'

    # Basic attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Hardware-specific attributes
    hardware_type = Column(Enum(HardwareType), nullable=False)
    material = Column(Enum(HardwareMaterial), nullable=False)
    finish = Column(Enum(HardwareFinish), nullable=True)

    # Inventory attributes
    sku = Column(String(50), nullable=True, unique=True, index=True)
    cost = Column(Float, default=0.0, nullable=False)
    price = Column(Float, default=0.0, nullable=False)

    # Measurement attributes
    unit = Column(
        Enum(MeasurementUnit),
        default=MeasurementUnit.PIECE,
        nullable=False
    )

    # Quality tracking
    quality = Column(Enum(QualityGrade), nullable=True)

    # Supplier relationship
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Relationships - following the ER diagram
    supplier = relationship("Supplier", back_populates="hardware")
    purchase_items = relationship("PurchaseItem", back_populates="hardware")
    component_hardwares = relationship("ComponentHardware", back_populates="hardware")
    inventories = relationship("HardwareInventory", back_populates="hardware")
    picking_list_items = relationship("PickingListItem", back_populates="hardware")
    transactions = relationship("HardwareTransaction", back_populates="hardware")

    def __init__(self, **kwargs):
        """
        Initialize a Hardware instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for hardware attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_hardware_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Hardware initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Hardware: {str(e)}") from e

    @classmethod
    def _validate_hardware_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of hardware creation data.

        Args:
            data: Hardware creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Hardware name is required')
        validate_not_empty(data, 'hardware_type', 'Hardware type is required')
        validate_not_empty(data, 'material', 'Hardware material is required')

        # Validate hardware type
        if 'hardware_type' in data:
            ModelValidator.validate_enum(
                data['hardware_type'],
                HardwareType,
                'hardware_type'
            )

        # Validate hardware material
        if 'material' in data:
            ModelValidator.validate_enum(
                data['material'],
                HardwareMaterial,
                'material'
            )

        # Validate hardware finish if provided
        if 'finish' in data and data['finish'] is not None:
            ModelValidator.validate_enum(
                data['finish'],
                HardwareFinish,
                'finish'
            )

        # Validate unit if provided
        if 'unit' in data:
            ModelValidator.validate_enum(
                data['unit'],
                MeasurementUnit,
                'unit'
            )

        # Validate quality if provided
        if 'quality' in data and data['quality'] is not None:
            ModelValidator.validate_enum(
                data['quality'],
                QualityGrade,
                'quality'
            )

        # Validate cost and price
        for field in ['cost', 'price']:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.capitalize()} cannot be negative"
                )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize inventory status if not set
        if not hasattr(self, 'inventory_status') or self.inventory_status is None:
            self.inventory_status = InventoryStatus.OUT_OF_STOCK

        # Generate SKU if not provided
        if not hasattr(self, 'sku') or not self.sku:
            self._generate_sku()

    def _generate_sku(self) -> None:
        """
        Generate a unique SKU for the hardware.
        """
        # Simple implementation - in practice would have more complexity
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        type_prefix = self.hardware_type.name[:3].upper()
        self.sku = f"HW-{type_prefix}-{timestamp}"
        logger.debug(f"Generated SKU for hardware {self.id}: {self.sku}")

    def update_inventory(self, quantity: int, location: str) -> "HardwareInventory":
        """
        Update or create an inventory record for this hardware.

        Args:
            quantity: The quantity to set
            location: The storage location

        Returns:
            The updated or created inventory record
        """
        try:
            # Import the HardwareInventory model
            HardwareInventory = lazy_import('HardwareInventory')

            # Find or create inventory record
            inventory = None
            if hasattr(self, 'inventories') and self.inventories:
                # Find inventory by location if it exists
                for inv in self.inventories:
                    if inv.storage_location == location:
                        inventory = inv
                        break

            if inventory:
                # Update existing inventory
                inventory.quantity = quantity
                inventory._update_status()
                logger.info(f"Updated inventory for hardware {self.id} at {location}")
            else:
                # Create new inventory
                inventory = HardwareInventory(
                    hardware_id=self.id,
                    quantity=quantity,
                    storage_location=location
                )
                if hasattr(self, 'inventories'):
                    self.inventories.append(inventory)
                logger.info(f"Created new inventory for hardware {self.id} at {location}")

            return inventory

        except Exception as e:
            logger.error(f"Failed to update inventory: {e}")
            raise ModelValidationError(f"Inventory update failed: {str(e)}")

    def calculate_total_inventory(self) -> int:
        """
        Calculate the total inventory across all locations.

        Returns:
            Total quantity in inventory
        """
        try:
            total = 0
            if hasattr(self, 'inventories') and self.inventories:
                total = sum(inv.quantity for inv in self.inventories)
            return total
        except Exception as e:
            logger.error(f"Failed to calculate total inventory: {e}")
            raise ModelValidationError(f"Inventory calculation failed: {str(e)}")

    def update_status_from_inventory(self) -> None:
        """
        Update inventory status based on total inventory.
        """
        try:
            total = self.calculate_total_inventory()

            if total <= 0:
                self.inventory_status = InventoryStatus.OUT_OF_STOCK
            elif total < 10:  # Example threshold
                self.inventory_status = InventoryStatus.LOW_STOCK
            else:
                self.inventory_status = InventoryStatus.IN_STOCK

            logger.info(f"Updated status for hardware {self.id} to {self.inventory_status}")

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            raise ModelValidationError(f"Status update failed: {str(e)}")

    def __repr__(self) -> str:
        """
        String representation of the Hardware.

        Returns:
            Detailed hardware representation
        """
        return (
            f"<Hardware(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.hardware_type.name if self.hardware_type else 'None'}, "
            f"status={self.inventory_status.name if hasattr(self, 'inventory_status') and self.inventory_status else 'None'})>"
        )


# Register for lazy import resolution
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')