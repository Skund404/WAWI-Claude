# database/models/part.py
"""
Enhanced Part Model with Advanced Relationship and Validation Strategies

This module defines the Part model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import InventoryStatus
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
register_lazy_import('database.models.product.Product', 'database.models.product')
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier')
register_lazy_import('database.models.storage.Storage', 'database.models.storage')
register_lazy_import('database.models.project.Project', 'database.models.project')


class Part(Base):
    """
    Enhanced Part model with comprehensive validation and relationship management.

    Represents individual parts used in leatherworking projects
    with advanced tracking and relationship configuration.
    """
    __tablename__ = 'parts'

    # Core part attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    # Inventory management
    quantity = Column(Float, default=0.0, nullable=False)
    min_quantity = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)

    # Pricing and cost
    cost_per_unit = Column(Float, default=0.0, nullable=False)
    price_per_unit = Column(Float, default=0.0, nullable=False)

    # Additional attributes
    material_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id"), nullable=True)

    # Relationships configured to avoid circular imports
    product = relationship(
        "Product",
        back_populates="parts",
        lazy='select'
    )

    supplier = relationship(
        "Supplier",
        back_populates="parts",
        lazy='select'
    )

    storage = relationship(
        "Storage",
        back_populates="parts",
        lazy='select'
    )

    def __init__(self, **kwargs):
        """
        Initialize a Part instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for part attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Part initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Part: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate part creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Part creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Part name is required')

        # Validate numeric fields
        numeric_fields = [
            'quantity', 'min_quantity', 'cost_per_unit', 'price_per_unit'
        ]

        for field in numeric_fields:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

        # Validate status
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                InventoryStatus,
                'status'
            )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate quantity consistency
        if self.quantity < 0:
            raise ValidationError(
                "Quantity cannot be negative",
                "quantity"
            )

    def adjust_quantity(self, quantity_change: float) -> None:
        """
        Adjust part quantity with comprehensive validation.

        Args:
            quantity_change (float): Amount to adjust (positive or negative)

        Raises:
            ModelValidationError: If quantity adjustment is invalid
        """
        try:
            # Validate quantity change
            validate_positive_number(
                {'quantity_change': abs(quantity_change)},
                'quantity_change',
                message="Quantity change must be a positive number"
            )

            # Calculate new quantity
            new_quantity = (self.quantity or 0.0) + quantity_change

            # Validate resulting quantity
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

            logger.info(
                f"Part {self.id} quantity adjusted. "
                f"Change: {quantity_change}, New Quantity: {self.quantity}"
            )

        except Exception as e:
            logger.error(f"Quantity adjustment failed: {e}")
            raise ModelValidationError(f"Part quantity adjustment failed: {str(e)}")

    def calculate_total_value(self) -> float:
        """
        Calculate the total value of the part based on current quantity.

        Returns:
            float: Total value of the part
        """
        try:
            total_value = (self.quantity or 0.0) * self.price_per_unit
            return total_value
        except Exception as e:
            logger.error(f"Value calculation failed: {e}")
            raise ModelValidationError(f"Part value calculation failed: {str(e)}")

    def mark_as_inactive(self) -> None:
        """
        Mark the part as inactive.
        """
        self.is_active = False
        self.status = InventoryStatus.OUT_OF_STOCK
        logger.info(f"Part {self.id} marked as inactive")

    def restore(self) -> None:
        """
        Restore an inactive part.
        """
        self.is_active = True
        # Restore status based on quantity
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.min_quantity:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK
        logger.info(f"Part {self.id} restored")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the part.

        Returns:
            str: Detailed part representation
        """
        return (
            f"<Part(id={self.id}, name='{self.name}', "
            f"material_type='{self.material_type}', "
            f"quantity={self.quantity}, "
            f"status={self.status}, "
            f"active={self.is_active})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.part.Part', 'database.models.part')