# database/models/inventory.py
"""
Generic Inventory Model for Leatherworking Management System

This module defines a comprehensive generic Inventory model that can be
used across different inventory types, facilitating consistent inventory
management throughout the application.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    InventoryStatus,
    MaterialType,
    MeasurementUnit,
    InventoryAdjustmentType,
    StorageLocationType,
    TransactionType,
    QualityGrade
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from database.models.interfaces import IInventoryItem
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
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Storage', 'database.models.storage', 'Storage')
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')


class Inventory(Base, TimestampMixin, ValidationMixin, TrackingMixin, IInventoryItem):
    """
    Generic Inventory model to track quantities and locations of various items.

    This model serves as a flexible inventory tracking system that can be linked
    to different item types (materials, leather, hardware, products) and provides
    consistent inventory management functionality.
    """
    __tablename__ = 'inventories'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    item_type: Mapped[MaterialType] = mapped_column(Enum(MaterialType), nullable=False)

    # Inventory quantities and measurements
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit),
        nullable=False,
        default=MeasurementUnit.PIECE
    )

    # Reorder settings
    reorder_point: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reorder_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Status and tracking
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        nullable=False,
        default=InventoryStatus.IN_STOCK
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quality_grade: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade), nullable=True)

    # Tracking dates
    last_count_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_restock_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Item reference foreign keys - only one should be used at a time
    material_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("hardwares.id"), nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)

    # Storage location
    storage_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("storages.id"), nullable=True)
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_type: Mapped[Optional[StorageLocationType]] = mapped_column(
        Enum(StorageLocationType),
        nullable=True
    )

    # Relationships with explicit join conditions
    material: Mapped[Optional["Material"]] = relationship(
        "Material",
        uselist=False,
        primaryjoin="Inventory.material_id == Material.id",
        lazy="selectin"
    )

    leather: Mapped[Optional["Leather"]] = relationship(
        "Leather",
        uselist=False,
        primaryjoin="Inventory.leather_id == Leather.id",
        lazy="selectin"
    )

    hardware: Mapped[Optional["Hardware"]] = relationship(
        "Hardware",
        uselist=False,
        primaryjoin="Inventory.hardware_id == Hardware.id",
        lazy="selectin"
    )

    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        uselist=False,
        primaryjoin="Inventory.product_id == Product.id",
        lazy="selectin"
    )

    storage: Mapped[Optional["Storage"]] = relationship(
        "Storage",
        uselist=False,
        primaryjoin="Inventory.storage_id == Storage.id",
        lazy="selectin"
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="inventory",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize an Inventory instance with comprehensive validation.

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
            logger.error(f"Inventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Inventory: {str(e)}") from e

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
        validate_not_empty(data, 'item_name', 'Item name is required')
        validate_not_empty(data, 'item_type', 'Item type is required')

        # Validate item type
        if 'item_type' in data:
            ModelValidator.validate_enum(
                data['item_type'],
                MaterialType,
                'item_type'
            )

        # Validate unit
        if 'unit' in data:
            ModelValidator.validate_enum(
                data['unit'],
                MeasurementUnit,
                'unit'
            )

        # Validate quantity and reorder fields
        for field in ['quantity', 'reorder_point', 'reorder_quantity']:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} cannot be negative"
                )

        # Validate status
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                InventoryStatus,
                'status'
            )

        # Ensure at least one item reference is provided
        if not any(field in data and data[field] is not None
                   for field in ['material_id', 'leather_id', 'hardware_id', 'product_id']):
            raise ValidationError(
                "At least one of material_id, leather_id, hardware_id, or product_id must be specified",
                "item_reference"
            )

        # Validate location type if provided
        if 'location_type' in data and data['location_type'] is not None:
            ModelValidator.validate_enum(
                data['location_type'],
                StorageLocationType,
                'location_type'
            )

        # Validate quality grade if provided
        if 'quality_grade' in data and data['quality_grade'] is not None:
            ModelValidator.validate_enum(
                data['quality_grade'],
                QualityGrade,
                'quality_grade'
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Set initial status based on quantity
        self._update_status()

        # Set tracking dates for new inventory
        if not hasattr(self, 'last_count_date') or self.last_count_date is None:
            self.last_count_date = datetime.utcnow()

    def _update_status(self) -> None:
        """
        Update the inventory status based on quantity and thresholds.
        """
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.reorder_point:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

        logger.debug(f"Updated status for inventory {self.id} to {self.status}")

    def adjust_quantity(self,
                        quantity_change: float,
                        transaction_type: Union[str, TransactionType, InventoryAdjustmentType],
                        notes: Optional[str] = None) -> None:
        """
        Adjust the inventory quantity and create a transaction record.

        Args:
            quantity_change: Amount to change (positive for addition, negative for reduction)
            transaction_type: Type of transaction or adjustment
            notes: Optional notes about the transaction

        Raises:
            ModelValidationError: If quantity would become negative
        """
        try:
            # Validate quantity change
            validate_positive_number(
                {'quantity_change': abs(quantity_change)},
                'quantity_change',
                message="Quantity change must be a non-negative number"
            )

            # Process transaction type
            if isinstance(transaction_type, str):
                try:
                    # Try TransactionType first
                    transaction_type = TransactionType[transaction_type.upper()]
                except KeyError:
                    try:
                        # Try InventoryAdjustmentType next
                        transaction_type = InventoryAdjustmentType[transaction_type.upper()]
                    except KeyError:
                        raise ValidationError(
                            f"Invalid transaction type: {transaction_type}",
                            "transaction_type"
                        )

            # Calculate new quantity
            new_quantity = self.quantity + quantity_change

            # Validate new quantity
            if new_quantity < 0:
                raise ValidationError(
                    f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: {quantity_change}",
                    "quantity"
                )

            # Update quantity
            self.quantity = new_quantity

            # Update status
            self._update_status()

            # Update tracking dates
            if quantity_change > 0 and isinstance(transaction_type,
                                                  TransactionType) and transaction_type == TransactionType.PURCHASE:
                self.last_restock_date = datetime.utcnow()

            self.last_count_date = datetime.utcnow()

            # Create transaction record if needed
            if hasattr(self, 'create_transaction'):
                self.create_transaction(quantity_change, transaction_type, notes)

            logger.info(f"Adjusted quantity for inventory {self.id}: {quantity_change} ({transaction_type.name})")

        except Exception as e:
            logger.error(f"Failed to adjust inventory quantity: {e}")
            raise ModelValidationError(f"Inventory adjustment failed: {str(e)}")

    def get_stock_value(self) -> float:
        """
        Calculate the total stock value based on linked item.

        Returns:
            Total value of inventory
        """
        try:
            unit_price = 0.0

            # Get price from linked item
            if self.material_id and self.material:
                unit_price = getattr(self.material, 'price_per_unit', 0.0)
            elif self.leather_id and self.leather:
                unit_price = getattr(self.leather, 'price_per_sqft', 0.0)
            elif self.hardware_id and self.hardware:
                unit_price = getattr(self.hardware, 'price_per_unit', 0.0)
            elif self.product_id and self.product:
                unit_price = getattr(self.product, 'price', 0.0)

            # Calculate total value
            stock_value = self.quantity * unit_price
            return stock_value

        except Exception as e:
            logger.error(f"Failed to calculate stock value: {e}")
            raise ModelValidationError(f"Stock value calculation failed: {str(e)}")

    def update_status(self, new_status: Union[str, InventoryStatus]) -> None:
        """
        Manually update the inventory status.

        Args:
            new_status: New status to set

        Raises:
            ValidationError: If status is invalid
        """
        try:
            # Process status value
            if isinstance(new_status, str):
                try:
                    new_status = InventoryStatus[new_status.upper()]
                except KeyError:
                    raise ValidationError(
                        f"Invalid inventory status: {new_status}",
                        "status"
                    )

            # Validate status type
            if not isinstance(new_status, InventoryStatus):
                raise ValidationError(
                    "Status must be a valid InventoryStatus enum value",
                    "status"
                )

            # Update status
            self.status = new_status
            logger.info(f"Manually updated status for inventory {self.id} to {new_status.name}")

        except Exception as e:
            logger.error(f"Failed to update inventory status: {e}")
            raise ModelValidationError(f"Status update failed: {str(e)}")

    def needs_reorder(self) -> bool:
        """
        Check if the inventory item needs to be reordered.

        Returns:
            True if quantity is at or below reorder point
        """
        return self.quantity <= self.reorder_point

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
                self.adjust_quantity(
                    difference,
                    adjustment_type,
                    notes or f"Inventory count adjustment: {difference}"
                )

            # Update count date regardless of change
            self.last_count_date = datetime.utcnow()

            logger.info(f"Completed inventory count for inventory {self.id}")

        except Exception as e:
            logger.error(f"Failed to process inventory count: {e}")
            raise ModelValidationError(f"Inventory count failed: {str(e)}")

    def deactivate(self) -> None:
        """
        Deactivate this inventory item.
        """
        self.is_active = False
        logger.info(f"Deactivated inventory {self.id}")

    def reactivate(self) -> None:
        """
        Reactivate this inventory item.
        """
        self.is_active = True
        logger.info(f"Reactivated inventory {self.id}")

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

        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Inventory':
        """
        Create a new Inventory instance from dictionary data.

        Args:
            data: Dictionary containing model attributes

        Returns:
            A new Inventory instance
        """
        return cls(**data)

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the inventory instance.

        Returns:
            Dictionary mapping field names to validation errors,
            or an empty dictionary if validation succeeds
        """
        errors = {}

        try:
            # Validate quantity is not negative
            if self.quantity < 0:
                errors.setdefault('quantity', []).append("Quantity cannot be negative")

            # Validate reorder values
            if self.reorder_point < 0:
                errors.setdefault('reorder_point', []).append("Reorder point cannot be negative")

            if self.reorder_quantity < 0:
                errors.setdefault('reorder_quantity', []).append("Reorder quantity cannot be negative")

            # Validate at least one item reference is set
            if not any([self.material_id, self.leather_id, self.hardware_id, self.product_id]):
                errors.setdefault('item_reference', []).append(
                    "At least one of material_id, leather_id, hardware_id, or product_id must be specified"
                )

        except Exception as e:
            errors.setdefault('general', []).append(f"Validation error: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the inventory instance is valid.

        Returns:
            True if the instance is valid, False otherwise
        """
        return len(self.validate()) == 0

    def __repr__(self) -> str:
        """
        String representation of the Inventory item.

        Returns:
            Descriptive string of the inventory item
        """
        return (
            f"<Inventory(id={self.id}, "
            f"name='{self.item_name}', "
            f"type={self.item_type.name if self.item_type else 'None'}, "
            f"quantity={self.quantity}, "
            f"status={self.status.name if self.status else 'None'})>"
        )


# Register for lazy import resolution
register_lazy_import('Inventory', 'database.models.inventory', 'Inventory')