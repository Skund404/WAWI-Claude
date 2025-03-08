from database.models.base import metadata
# database/models/inventory.py
"""
Enhanced Inventory Model for Leatherworking Management System

Provides a comprehensive and flexible inventory tracking system
with advanced validation, relationship management, and business logic.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type, ClassVar, Callable

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import (
    Base,
    ModelValidationError,
    ModelFactory,
    metadata
)
from database.models.base import (
    TrackingMixin,
    ComplianceMixin,
    CostingMixin
)
from database.models.enums import (
    InventoryStatus,
    MaterialType,
    MeasurementUnit,
    InventoryAdjustmentType,
    StorageLocationType,
    TransactionType,
    QualityGrade
)

from utils.circular_import_resolver import (
    register_lazy_import,
    resolve_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Lazy import registration for potential circular dependencies
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Storage', 'database.models.storage', 'Storage')
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')


class Inventory(Base, TrackingMixin, ComplianceMixin, CostingMixin):
    """
    Enhanced Inventory model with comprehensive tracking and management capabilities.
    Inherits from Base model and applies multiple mixins for advanced functionality.
    """
    __tablename__ = 'inventories'

    # Core inventory attributes
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    item_type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType),
        nullable=False,
        default=MaterialType.OTHER
    )

    # Quantity and measurement tracking
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit),
        nullable=False,
        default=MeasurementUnit.PIECE
    )

    # Reorder management
    reorder_point: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reorder_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Item references with lazy loading
    material_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("materials.id"),
        nullable=True
    )
    leather_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("leathers.id"),
        nullable=True
    )
    hardware_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("hardwares.id"),
        nullable=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=True
    )

    # Storage relationship
    storage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("storages.id"),
        nullable=True
    )
    storage_location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    location_type: Mapped[Optional[StorageLocationType]] = mapped_column(
        Enum(StorageLocationType),
        nullable=True
    )

    # Relationships with lazy loading
    material: Mapped[Optional["Material"]] = relationship(
        "Material",
        lazy="selectin",
        foreign_keys=[material_id]
    )
    leather: Mapped[Optional["Leather"]] = relationship(
        "Leather",
        lazy="selectin",
        foreign_keys=[leather_id]
    )
    hardware: Mapped[Optional["Hardware"]] = relationship(
        "Hardware",
        lazy="selectin",
        foreign_keys=[hardware_id]
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        lazy="selectin",
        foreign_keys=[product_id]
    )
    storage: Mapped[Optional["Storage"]] = relationship(
        "Storage",
        lazy="selectin",
        foreign_keys=[storage_id]
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="inventory",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Class-level validators
    _inventory_validators: ClassVar[List[Callable]] = []

    @classmethod
    def register_inventory_validator(
            cls,
            validator_func: Callable[['Inventory'], Optional[str]]
    ) -> None:
        """
        Register a custom inventory-level validator.

        Args:
            validator_func: Function that validates the entire inventory
        """
        cls._inventory_validators.append(validator_func)

    def validate_inventory(self) -> Dict[str, List[str]]:
        """
        Perform comprehensive inventory-specific validation.

        Returns:
            Dictionary of validation errors
        """
        errors: Dict[str, List[str]] = {}

        # Validate quantity cannot be negative
        if self.quantity < 0:
            errors['quantity'] = ["Quantity cannot be negative"]

        # Validate reorder points
        if self.reorder_point < 0:
            errors['reorder_point'] = ["Reorder point cannot be negative"]

        if self.reorder_quantity < 0:
            errors['reorder_quantity'] = ["Reorder quantity cannot be negative"]

        # Validate at least one item reference
        if not any([
            self.material_id,
            self.leather_id,
            self.hardware_id,
            self.product_id
        ]):
            errors['item_reference'] = [
                "At least one of material_id, leather_id, hardware_id, or product_id must be specified"
            ]

        # Run custom inventory validators
        for validator in self._inventory_validators:
            try:
                result = validator(self)
                if result:
                    errors.setdefault('custom_validation', []).append(result)
            except Exception as e:
                errors.setdefault('custom_validation', []).append(str(e))

        return errors

    def adjust_quantity(
            self,
            quantity_change: float,
            transaction_type: Union[str, TransactionType, InventoryAdjustmentType],
            notes: Optional[str] = None
    ) -> None:
        """
        Adjust inventory quantity with comprehensive validation and logging.

        Args:
            quantity_change: Amount to change (positive or negative)
            transaction_type: Type of transaction
            notes: Optional transaction notes

        Raises:
            ModelValidationError: If adjustment is invalid
        """
        try:
            # Validate quantity change
            ModelValidator.validate_positive_number(
                abs(quantity_change),
                allow_zero=True,
                message="Quantity change must be a non-negative number"
            )

            # Process transaction type
            if isinstance(transaction_type, str):
                try:
                    transaction_type = (
                        TransactionType[transaction_type.upper()]
                        if transaction_type.upper() in TransactionType.__members__
                        else InventoryAdjustmentType[transaction_type.upper()]
                    )
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
                    f"Cannot reduce quantity below zero. "
                    f"Current: {self.quantity}, Change: {quantity_change}",
                    "quantity"
                )

            # Update quantity and status
            self.quantity = new_quantity
            self._update_status()

            # Log transaction
            self._log_transaction(quantity_change, transaction_type, notes)

            logger.info(
                f"Adjusted quantity for inventory {self.id}: "
                f"{quantity_change} ({transaction_type.name})"
            )

        except Exception as e:
            logger.error(f"Inventory adjustment failed: {e}")
            raise ModelValidationError(f"Inventory adjustment failed: {str(e)}")

    def _update_status(self) -> None:
        """
        Update inventory status based on current quantity and thresholds.
        """
        old_status = self.inventory_status

        # Update status based on quantity
        if self.quantity <= 0:
            self.inventory_status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.reorder_point:
            self.inventory_status = InventoryStatus.LOW_STOCK
        else:
            self.inventory_status = InventoryStatus.IN_STOCK

        # Log status change if different
        if old_status != self.inventory_status:
            logger.info(
                f"Inventory {self.id} status changed from "
                f"{old_status.name} to {self.inventory_status.name}"
            )

    def _log_transaction(
            self,
            quantity_change: float,
            transaction_type: Union[TransactionType, InventoryAdjustmentType],
            notes: Optional[str] = None
    ) -> None:
        """
        Create and log a transaction record for quantity changes.

        Args:
            quantity_change: Amount of quantity change
            transaction_type: Type of transaction
            notes: Optional transaction notes
        """
        try:
            # Lazy import Transaction model to avoid circular imports
            Transaction = resolve_lazy_import('Transaction')

            if Transaction:
                transaction = Transaction(
                    inventory_id=self.id,
                    quantity=quantity_change,
                    transaction_type=transaction_type,
                    notes=notes
                )
                # Note: This assumes the session will be used to add the transaction
                # In a real implementation, you'd pass the session or use a service layer
        except Exception as e:
            logger.warning(f"Failed to log transaction: {e}")

    def needs_reorder(self) -> bool:
        """
        Check if inventory needs reordering.

        Returns:
            True if quantity is at or below reorder point
        """
        return self.quantity <= self.reorder_point


# Factory method for creating inventory instances
def create_inventory(
        item_name: str,
        item_type: MaterialType,
        quantity: float = 0.0,
        unit: MeasurementUnit = MeasurementUnit.PIECE,
        **kwargs
) -> Inventory:
    """
    Factory method to create an Inventory instance with validation.

    Args:
        item_name: Name of the inventory item
        item_type: Type of the item
        quantity: Initial quantity (default 0.0)
        unit: Measurement unit (default PIECE)
        **kwargs: Additional inventory attributes

    Returns:
        Validated Inventory instance
    """
    inventory_data = {
        'item_name': item_name,
        'item_type': item_type,
        'quantity': quantity,
        'unit': unit,
        **kwargs
    }

    return Inventory(**inventory_data)


# Register for lazy import resolution
register_lazy_import('Inventory', 'database.models.inventory', 'Inventory')