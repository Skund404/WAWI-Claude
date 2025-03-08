from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/material_inventory.py
"""
Material Inventory Model for Leatherworking Management System

This module defines the MaterialInventory model which implements
the MaterialInventory entity from the ER diagram with comprehensive
validation and relationship management.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    InventoryStatus,
    TransactionType,
    InventoryAdjustmentType,
    StorageLocationType,
    MaterialType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin,
    apply_mixins  # Import apply_mixins function
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
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('MaterialTransaction', 'database.models.transaction', 'MaterialTransaction')
register_lazy_import('Storage', 'database.models.storage', 'Storage')

from sqlalchemy.orm import declarative_base
MaterialInventoryBase = declarative_base()
MaterialInventoryBase.metadata = metadata
MaterialInventoryBase.metadata = metadata


class MaterialInventory(MaterialInventoryBase):
    """
    MaterialInventory model representing material stock quantities and locations.

    This implements the MaterialInventory entity from the ER diagram with
    comprehensive attributes and relationship management.
    """
    __tablename__ = 'material_inventories'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey('materials.id', ondelete='CASCADE'), nullable=False,
                                             index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

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

    # Storage reference
    storage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('storages.id', ondelete='SET NULL'),
        nullable=True
    )

    # Threshold for status updates
    min_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    max_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Tracking details
    lot_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    batch_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_count_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_restock_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Additional material-specific information
    material_condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    material = relationship("Material", back_populates="inventories")
    storage = relationship("Storage", back_populates="material_inventories")
    transactions = relationship(
        "MaterialTransaction",
        back_populates="material_inventory",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a MaterialInventory instance with comprehensive validation.

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
            logger.error(f"MaterialInventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create material inventory: {str(e)}") from e

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
        validate_not_empty(data, 'material_id', 'Material ID is required')

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

        # Validate expiration date is in the future if provided
        if 'expiration_date' in data and data['expiration_date'] is not None:
            if data['expiration_date'] < datetime.utcnow():
                raise ValidationError("Expiration date must be in the future", "expiration_date")

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

        logger.debug(f"Updated status for material inventory {self.id} to {self.status}")

        # Update parent material's status if needed
        if hasattr(self, 'material') and self.material:
            try:
                self.material._update_status_from_inventory()
            except Exception as e:
                logger.warning(f"Unable to update parent material status: {e}")

    def update_quantity(self,
                        amount: float,
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

            # Create transaction record
            self.create_transaction(amount, adjustment_type, notes)

            logger.info(
                f"Updated quantity for material inventory {self.id}. Change: {amount}, New total: {self.quantity}")

        except Exception as e:
            logger.error(f"Failed to update quantity: {e}")
            raise ModelValidationError(f"Quantity update failed: {str(e)}")

    def create_transaction(self,
                           amount: float,
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
            MaterialTransaction = lazy_import('database.models.transaction', 'MaterialTransaction')

            # Create transaction
            transaction = MaterialTransaction(
                material_inventory_id=self.id,
                material_id=self.material_id,
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

            logger.info(f"Created transaction record for material inventory {self.id}")
            return transaction

        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            raise ModelValidationError(f"Transaction creation failed: {str(e)}")

    def count_inventory(self, actual_quantity: float, notes: Optional[str] = None) -> None:
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

            logger.info(f"Completed inventory count for material inventory {self.id}")

        except Exception as e:
            logger.error(f"Failed to process inventory count: {e}")
            raise ModelValidationError(f"Inventory count failed: {str(e)}")

    def check_expiration(self) -> bool:
        """
        Check if inventory is expired.

        Returns:
            True if expired, False otherwise or if no expiration date
        """
        if not hasattr(self, 'expiration_date') or not self.expiration_date:
            return False

        return self.expiration_date <= datetime.utcnow()

    def deactivate(self) -> None:
        """
        Deactivate this inventory location.
        """
        self.is_active = False
        logger.info(f"Deactivated material inventory {self.id}")

    def reactivate(self) -> None:
        """
        Reactivate this inventory location.
        """
        self.is_active = True
        logger.info(f"Reactivated material inventory {self.id}")

    def transfer_to(self,
                    target_location: str,
                    quantity: float,
                    notes: Optional[str] = None) -> "MaterialInventory":
        """
        Transfer inventory to another location.

        Args:
            target_location: Destination location
            quantity: Amount to transfer
            notes: Optional notes

        Returns:
            The destination inventory record

        Raises:
            ModelValidationError: If transfer fails
        """
        try:
            # Validate quantity
            validate_positive_number(
                {'quantity': quantity},
                'quantity',
                allow_zero=False,
                message="Transfer quantity must be positive"
            )

            # Check if we have enough
            if quantity > self.quantity:
                raise ValidationError(
                    f"Cannot transfer more than available. Available: {self.quantity}, Requested: {quantity}",
                    "quantity"
                )

            # Find or create target inventory
            target_inventory = None
            if hasattr(self.material, 'inventories') and self.material.inventories:
                # Find inventory by location if it exists
                for inv in self.material.inventories:
                    if inv.storage_location == target_location and inv.id != self.id:
                        target_inventory = inv
                        break

            if not target_inventory:
                # Create new inventory at target location
                target_inventory = MaterialInventory(
                    material_id=self.material_id,
                    quantity=0,
                    storage_location=target_location,
                    min_quantity=self.min_quantity,
                    max_quantity=self.max_quantity,
                    location_type=self.location_type
                )
                if hasattr(self.material, 'inventories'):
                    self.material.inventories.append(target_inventory)

            # Remove from source
            self.update_quantity(
                -quantity,
                TransactionType.TRANSFER,
                notes or f"Transfer to {target_location}"
            )

            # Add to target
            target_inventory.update_quantity(
                quantity,
                TransactionType.TRANSFER,
                notes or f"Transfer from {self.storage_location}"
            )

            logger.info(f"Transferred {quantity} units from inventory {self.id} to {target_inventory.id}")
            return target_inventory

        except Exception as e:
            logger.error(f"Failed to transfer inventory: {e}")
            raise ModelValidationError(f"Inventory transfer failed: {str(e)}")

    def __repr__(self) -> str:
        """
        String representation of the MaterialInventory.

        Returns:
            Detailed material inventory representation
        """
        return (
            f"<MaterialInventory(id={self.id}, "
            f"material_id={self.material_id}, "
            f"quantity={self.quantity}, "
            f"status={self.status.name if self.status else 'None'}, "
            f"location='{self.storage_location}')>"
        )


# Register for lazy import resolution
register_lazy_import('MaterialInventory', 'database.models.material_inventory', 'MaterialInventory')