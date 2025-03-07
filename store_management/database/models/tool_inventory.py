# database/models/tool_inventory.py
"""
Comprehensive Tool Inventory Model for Leatherworking Management System

This module defines the ToolInventory model with extensive validation,
relationship management, and circular import resolution.

Implements the ToolInventory entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    InventoryStatus,
    InventoryAdjustmentType,
    StorageLocationType
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Tool', 'database.models.tool', 'Tool')


class ToolInventory(Base, TimestampMixin, ValidationMixin, TrackingMixin):
    """
    ToolInventory model representing tool stock quantities and locations.

    This implements the ToolInventory entity from the ER diagram with
    comprehensive attributes and relationship management.
    """
    __tablename__ = 'tool_inventories'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status and location
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        nullable=False,
        default=InventoryStatus.IN_STOCK
    )
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_type: Mapped[Optional[StorageLocationType]] = mapped_column(
        Enum(StorageLocationType),
        nullable=True
    )

    # Thresholds for automated status updates
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Tracking attributes
    last_count_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_restock_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    tool = relationship("Tool", back_populates="inventories")

    def __init__(self, **kwargs):
        """
        Initialize a ToolInventory instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for inventory attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_inventory_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ToolInventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create tool inventory: {str(e)}") from e

    @classmethod
    def _validate_inventory_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of inventory creation data.

        Args:
            data: Inventory creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'tool_id', 'Tool ID is required')

        # Validate quantity
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=True,
                message="Quantity cannot be negative"
            )

        # Validate min and max quantities
        if 'min_quantity' in data:
            validate_positive_number(
                data,
                'min_quantity',
                allow_zero=True,
                message="Minimum quantity cannot be negative"
            )

        if 'max_quantity' in data and data['max_quantity'] is not None:
            validate_positive_number(
                data,
                'max_quantity',
                allow_zero=False,
                message="Maximum quantity must be positive"
            )

            # Validate min/max relationship
            if 'min_quantity' in data and data['min_quantity'] is not None:
                if data['max_quantity'] <= data['min_quantity']:
                    raise ValidationError(
                        "Maximum quantity must be greater than minimum quantity",
                        "max_quantity"
                    )

        # Validate status
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                InventoryStatus,
                'status'
            )

        # Validate location type
        if 'location_type' in data and data['location_type'] is not None:
            ModelValidator.validate_enum(
                data['location_type'],
                StorageLocationType,
                'location_type'
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Set initial status based on quantity
        self._update_status()

        # Set tracking date for new inventory
        if not hasattr(self, 'last_count_date') or self.last_count_date is None:
            self.last_count_date = datetime.utcnow()

    def _update_status(self) -> None:
        """
        Update the inventory status based on quantity and thresholds.
        """
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.min_quantity:
            self.status = InventoryStatus.LOW_STOCK
        elif hasattr(self, 'max_quantity') and self.max_quantity is not None and self.quantity >= self.max_quantity:
            self.status = InventoryStatus.ON_ORDER
        else:
            self.status = InventoryStatus.IN_STOCK

        logger.debug(f"Updated status for tool inventory {self.id} to {self.status}")

    def update_quantity(self, amount: int, is_addition: bool = True, notes: Optional[str] = None) -> None:
        """
        Update the inventory quantity.

        Args:
            amount: Amount to change
            is_addition: Whether to add or subtract
            notes: Optional notes about the adjustment

        Raises:
            ModelValidationError: If resulting quantity would be negative
        """
        try:
            # Calculate new quantity
            new_quantity = self.quantity + amount if is_addition else self.quantity - amount

            # Validate
            if new_quantity < 0:
                change_amount = amount if is_addition else -amount
                raise ValidationError(
                    f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: {change_amount}",
                    "quantity"
                )

            # Update quantity
            self.quantity = new_quantity

            # Update tracking dates
            if is_addition and amount > 0:
                self.last_restock_date = datetime.utcnow()

            self.last_count_date = datetime.utcnow()

            # Update status
            self._update_status()

            logger.info(f"ToolInventory {self.id} quantity updated to {self.quantity}")

        except Exception as e:
            logger.error(f"Error updating quantity: {e}")
            raise ModelValidationError(f"Failed to update quantity: {str(e)}") from e

    def count_inventory(self, actual_quantity: int, notes: Optional[str] = None) -> None:
        """
        Update inventory based on physical count.

        Args:
            actual_quantity: Actual counted quantity
            notes: Optional notes about the count

        Raises:
            ModelValidationError: If count is negative
        """
        try:
            # Validate count
            validate_positive_number(
                {'actual_quantity': actual_quantity},
                'actual_quantity',
                allow_zero=True,
                message="Counted quantity cannot be negative"
            )

            # Calculate difference
            difference = actual_quantity - self.quantity

            # Skip if no change
            if difference == 0:
                logger.info(
                    f"Inventory count for tool inventory {self.id} confirmed current quantity of {self.quantity}")
                self.last_count_date = datetime.utcnow()
                return

            # Update quantity
            is_addition = difference > 0
            self.update_quantity(abs(difference), is_addition, notes or f"Inventory count adjustment: {difference}")

            logger.info(f"Completed inventory count for tool inventory {self.id}")

        except Exception as e:
            logger.error(f"Failed to process inventory count: {e}")
            raise ModelValidationError(f"Inventory count failed: {str(e)}") from e

    def deactivate(self) -> None:
        """
        Deactivate this inventory location.
        """
        self.is_active = False
        logger.info(f"Deactivated tool inventory {self.id}")

    def reactivate(self) -> None:
        """
        Reactivate this inventory location.
        """
        self.is_active = True
        logger.info(f"Reactivated tool inventory {self.id}")

    def needs_reorder(self) -> bool:
        """
        Check if the inventory needs to be reordered.

        Returns:
            True if quantity is at or below minimum quantity
        """
        return self.quantity <= self.min_quantity

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Handle special types
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif isinstance(value, InventoryStatus):
                    result[column.name] = value.name
                elif isinstance(value, StorageLocationType):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add computed fields
        result['needs_reorder'] = self.needs_reorder()

        return result

    def __repr__(self) -> str:
        """
        String representation of the ToolInventory.

        Returns:
            Detailed tool inventory representation
        """
        return (
            f"<ToolInventory(id={self.id}, "
            f"tool_id={self.tool_id}, "
            f"quantity={self.quantity}, "
            f"status={self.status.name if self.status else 'None'}, "
            f"location='{self.storage_location or 'None'}')>"
        )


# Register for lazy import resolution
register_lazy_import('ToolInventory', 'database.models.tool_inventory', 'ToolInventory')