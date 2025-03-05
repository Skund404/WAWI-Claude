# database/models/hardware.py
"""
Enhanced Hardware Model with Advanced Relationship and Validation Strategies

This module defines the Hardware model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Float, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    InventoryStatus,
    MeasurementUnit,
    TransactionType
)
from database.models.enums import (
    HardwareType,
    HardwareMaterial,
    HardwareFinish
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

# Lazy import potential related models
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('database.models.storage.Storage', 'database.models.storage', 'Storage')
register_lazy_import('database.models.transaction.HardwareTransaction', 'database.models.transaction', 'HardwareTransaction')
register_lazy_import('database.models.project.Project', 'database.models.project', 'Project')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components', 'ProjectComponent')


class Hardware(Base):
    """
    Enhanced Hardware model with comprehensive validation and relationship management.

    Represents hardware items used in leatherworking projects with
    advanced tracking and relationship configuration.
    """
    __tablename__ = 'hardwares'

    # Core hardware attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    # Hardware characteristics
    hardware_type = Column(Enum(HardwareType), nullable=False)
    material = Column(Enum(HardwareMaterial), nullable=False)
    finish = Column(Enum(HardwareFinish), nullable=True)

    # Inventory management
    quantity = Column(Float, default=0.0, nullable=False)
    min_quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(Enum(MeasurementUnit), nullable=False, default=MeasurementUnit.PIECE)

    # Financial tracking
    cost_per_unit = Column(Float, default=0.0, nullable=False)
    price_per_unit = Column(Float, default=0.0, nullable=False)

    # Status tracking
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id"), nullable=True)

    # Relationships configured to avoid circular imports
    transactions = relationship(
        "HardwareTransaction",
        back_populates="hardware",
        lazy='select',
        cascade='all, delete-orphan'
    )

    supplier = relationship(
        "Supplier",
        back_populates="hardware_items",
        lazy='select'
    )

    storage = relationship(
        "Storage",
        back_populates="hardware_items",
        lazy='select'
    )

    project_components = relationship(
        "ProjectComponent",
        back_populates="hardware",
        viewonly=True,  # Add this line to make it a view-only relationship
        lazy='select'
    )
    def __init__(self, **kwargs):
        """
        Initialize a Hardware instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for hardware attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Hardware initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Hardware: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate hardware creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Hardware creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Hardware name is required')
        validate_not_empty(data, 'hardware_type', 'Hardware type is required')
        validate_not_empty(data, 'material', 'Hardware material is required')

        # Validate hardware type and material
        if 'hardware_type' in data:
            ModelValidator.validate_enum(
                data['hardware_type'],
                HardwareType,
                'hardware_type'
            )

        if 'material' in data:
            ModelValidator.validate_enum(
                data['material'],
                HardwareMaterial,
                'material'
            )

        # Validate optional finish
        if 'finish' in data and data['finish']:
            ModelValidator.validate_enum(
                data['finish'],
                HardwareFinish,
                'finish'
            )

        # Validate numeric fields
        numeric_fields = [
            'quantity', 'min_quantity',
            'cost_per_unit', 'price_per_unit'
        ]

        for field in numeric_fields:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate quantity and stock levels
        if self.quantity < 0:
            raise ValidationError(
                "Quantity cannot be negative",
                "quantity"
            )

    def adjust_quantity(self, quantity_change: float, transaction_type: TransactionType,
                        notes: Optional[str] = None) -> None:
        """
        Adjust hardware quantity with comprehensive validation.

        Args:
            quantity_change: Amount to adjust (positive for addition, negative for reduction)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ModelValidationError: If quantity adjustment is invalid
        """
        try:
            # Validate quantity change
            validate_positive_number(
                {'quantity_change': abs(quantity_change)},
                'quantity_change',
                message="Quantity change must be a non-negative number"
            )

            # Validate resulting quantity
            new_quantity = (self.quantity or 0.0) + quantity_change

            if new_quantity < 0:
                raise ModelValidationError(
                    f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: {quantity_change}"
                )

            # Update quantity
            self.quantity = new_quantity

            # Update status based on quantity
            if self.quantity <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif self.quantity <= self.min_quantity:
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK

            # Log the adjustment
            logger.info(
                f"Hardware {self.id} quantity adjusted. "
                f"Change: {quantity_change}, New Quantity: {self.quantity}"
            )

        except Exception as e:
            logger.error(f"Quantity adjustment failed: {e}")
            raise ModelValidationError(f"Hardware quantity adjustment failed: {str(e)}")

    def calculate_total_value(self) -> float:
        """
        Calculate the total value of the hardware based on current quantity.

        Returns:
            float: Total value of the hardware
        """
        try:
            total_value = (self.quantity or 0.0) * self.price_per_unit
            return total_value
        except Exception as e:
            logger.error(f"Value calculation failed: {e}")
            raise ModelValidationError(f"Hardware value calculation failed: {str(e)}")

    def mark_as_inactive(self) -> None:
        """
        Mark the hardware as inactive.
        """
        self.is_active = False
        self.status = InventoryStatus.OUT_OF_STOCK
        logger.info(f"Hardware {self.id} marked as inactive")

    def restore(self) -> None:
        """
        Restore an inactive hardware item.
        """
        self.is_active = True
        # Restore status based on quantity
        if self.quantity is not None:
            if self.quantity <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif self.quantity <= self.min_quantity:
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK
        logger.info(f"Hardware {self.id} restored")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the hardware.

        Returns:
            str: Detailed hardware representation
        """
        return (
            f"<Hardware(id={self.id}, name='{self.name}', "
            f"type={self.hardware_type}, "
            f"quantity={self.quantity or 0.0}, "
            f"status={self.status}, "
            f"active={self.is_active})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')