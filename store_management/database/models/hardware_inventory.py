from database.models.base import metadata
# database/models/hardware_inventory.py
"""
Hardware Inventory Model for Leatherworking Management System

This module defines the HardwareInventory model which implements
the HardwareInventory entity from the ER diagram with comprehensive
validation and relationship management.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Integer, ForeignKey, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    InventoryStatus,
    TransactionType,
    InventoryAdjustmentType,
    StorageLocationType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
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
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('HardwareTransaction', 'database.models.transaction', 'HardwareTransaction')

# Register this model for lazy import resolution
register_lazy_import('HardwareInventory', 'database.models.hardware_inventory', 'HardwareInventory')

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import declarative_base
HardwareInventoryBase = declarative_base()
HardwareInventoryBase.metadata = metadata
HardwareInventoryBase.metadata = metadata


class HardwareInventory(HardwareInventoryBase):
    """
    HardwareInventory model representing hardware stock quantities and locations.

    This implements the HardwareInventory entity from the ER diagram with
    comprehensive attributes and relationship management.
    """
    __tablename__ = 'hardware_inventories'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hardware_id: Mapped[int] = mapped_column(Integer, ForeignKey('hardwares.id'), nullable=False)
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

    # Threshold for status updates
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Tracking details
    last_count_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_restock_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    hardware = relationship("Hardware", back_populates="inventories")
    transactions = relationship(
        "HardwareTransaction",
        back_populates="hardware_inventory",
        cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        """
        Initialize a HardwareInventory instance with comprehensive validation.

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
            logger.error(f"HardwareInventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create hardware inventory: {str(e)}") from e

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
        validate_not_empty(data, 'hardware_id', 'Hardware ID is required')

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

        logger.debug(f"Updated status for hardware inventory {self.id} to {self.status}")

    def update_quantity(self,
                        amount: int,
                        adjustment_type: Union[TransactionType, InventoryAdjustmentType, str],
                        notes: Optional[str] = None) -> None:
        """
        Update the inventory quantity and create a transaction record.

        Args:
            amount: Amount to change (positive for addition, negative for reduction)
            adjustment_type: Type of adjustment
            notes: Optional notes about the adjustment

        Raises:
            ModelValidationError: If quantity would become negative
        """
        try:
            # Validate adjustment type
            if isinstance(adjustment_type, str):
                try:
                    # Try TransactionType first
                    adjustment_type = TransactionType[adjustment_type.upper()]
                except KeyError:
                    try:
                        # Try InventoryAdjustmentType next
                        adjustment_type = InventoryAdjustmentType[adjustment_type.upper()]
                    except KeyError:
                        raise ValidationError(
                            f"Invalid adjustment type: {adjustment_type}",
                            "adjustment_type"
                        )

            # Calculate new quantity
            new_quantity = self.quantity + amount

            # Validate new quantity
            if new_quantity < 0:
                raise ValidationError(
                    f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: {amount}",
                    "quantity"
                )

            # Update quantity
            self.quantity = new_quantity

            # Update status
            self._update_status()

            # Update tracking dates
            if amount > 0 and isinstance(adjustment_type,
                                         TransactionType) and adjustment_type == TransactionType.PURCHASE:
                self.last_restock_date = datetime.utcnow()

            self.last_count_date = datetime.utcnow()

            # Create transaction record if needed
            if hasattr(self, 'create_transaction'):
                self.create_transaction(amount, adjustment_type, notes)

            logger.info(
                f"Updated quantity for hardware inventory {self.id}. Change: {amount}, New total: {self.quantity}")

        except Exception as e:
            logger.error(f"Failed to update quantity: {e}")
            raise ModelValidationError(f"Quantity update failed: {str(e)}")

    def create_transaction(self,
                           amount: int,
                           transaction_type: Union[TransactionType, InventoryAdjustmentType],
                           notes: Optional[str] = None) -> Any:
        """
        Create a transaction record for this inventory change.

        Args:
            amount: Amount changed
            transaction_type: Type of transaction
            notes: Optional notes

        Returns:
            The created transaction record
        """
        try:
            # Lazy import transaction model
            HardwareTransaction = lazy_import('database.models.transaction', 'HardwareTransaction')

            # Create transaction
            transaction = HardwareTransaction(
                hardware_inventory_id=self.id,
                hardware_id=self.hardware_id,
                quantity=abs(amount),
                is_addition=amount > 0,
                transaction_type=transaction_type if isinstance(transaction_type, TransactionType)
                else TransactionType.ADJUSTMENT,
                notes=notes or (f"Adjustment type: {transaction_type.name}"
                                if isinstance(transaction_type, InventoryAdjustmentType) else None)
            )

            # Add to relationships
            if hasattr(self, 'transactions'):
                self.transactions.append(transaction)

            logger.info(f"Created transaction record for hardware inventory {self.id}")
            return transaction

        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            raise ModelValidationError(f"Transaction creation failed: {str(e)}")

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

            # Update quantity
            if difference != 0:
                adjustment_type = InventoryAdjustmentType.FOUND if difference > 0 else InventoryAdjustmentType.LOST
                self.update_quantity(
                    difference,
                    adjustment_type,
                    notes or f"Inventory count adjustment: {difference}"
                )

            # Update count date regardless of change
            self.last_count_date = datetime.utcnow()

            logger.info(f"Completed inventory count for hardware inventory {self.id}")

        except Exception as e:
            logger.error(f"Failed to process inventory count: {e}")
            raise ModelValidationError(f"Inventory count failed: {str(e)}")

    def deactivate(self) -> None:
        """
        Deactivate this inventory location.
        """
        self.is_active = False
        logger.info(f"Deactivated hardware inventory {self.id}")

    def reactivate(self) -> None:
        """
        Reactivate this inventory location.
        """
        self.is_active = True
        logger.info(f"Reactivated hardware inventory {self.id}")

    def __repr__(self) -> str:
        """
        String representation of the HardwareInventory.

        Returns:
            Detailed hardware inventory representation
        """
        return (
            f"<HardwareInventory(id={self.id}, "
            f"hardware_id={self.hardware_id}, "
            f"quantity={self.quantity}, "
            f"status={self.status.name if self.status else 'None'}, "
            f"location='{self.storage_location}')>"
        )