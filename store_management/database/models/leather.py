# database/models/leather.py
"""
Enhanced Leather Model with Advanced Relationship and Validation Strategies

This module defines the Leather model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    InventoryStatus,
    TransactionType,
    LeatherType,
    MaterialQualityGrade
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
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier')
register_lazy_import('database.models.storage.Storage', 'database.models.storage')
register_lazy_import('database.models.transaction.LeatherTransaction', 'database.models.transaction')
register_lazy_import('database.models.project.Project', 'database.models.project')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components')


class Leather(Base):
    """
    Enhanced Leather model with comprehensive validation and relationship management.

    Represents leather materials with advanced tracking and relationship configuration.
    """
    __tablename__ = 'leathers'

    # Core leather attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    # Leather characteristics
    leather_type = Column(Enum(LeatherType), nullable=False)
    tannage = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    finish = Column(String(50), nullable=True)
    quality_grade = Column(Enum(MaterialQualityGrade), nullable=True)

    # Physical properties
    thickness_mm = Column(Float, nullable=True)
    size_sqft = Column(Float, nullable=True)
    area_available_sqft = Column(Float, nullable=True)

    # Financial tracking
    cost_per_sqft = Column(Float, default=0.0, nullable=False)
    price_per_sqft = Column(Float, default=0.0, nullable=False)

    # Status and availability
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id"), nullable=True)

    # Relationships configured to avoid circular imports
    transactions = relationship(
        "LeatherTransaction",
        back_populates="leather",
        lazy='select',
        cascade='all, delete-orphan'
    )

    supplier = relationship(
        "Supplier",
        back_populates="leathers",
        lazy='select'
    )

    storage = relationship(
        "Storage",
        back_populates="leathers",
        lazy='select'
    )

    project_components = relationship(
        "ProjectComponent",
        back_populates="leather",
        lazy='select'
    )

    def __init__(self, **kwargs):
        """
        Initialize a Leather instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for leather attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Leather initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Leather: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate leather creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Leather creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Leather name is required')
        validate_not_empty(data, 'leather_type', 'Leather type is required')

        # Validate leather type
        if 'leather_type' in data:
            ModelValidator.validate_enum(
                data['leather_type'],
                LeatherType,
                'leather_type'
            )

        # Validate quality grade if provided
        if 'quality_grade' in data and data['quality_grade']:
            ModelValidator.validate_enum(
                data['quality_grade'],
                MaterialQualityGrade,
                'quality_grade'
            )

        # Validate numeric fields
        numeric_fields = [
            'thickness_mm', 'size_sqft', 'area_available_sqft',
            'cost_per_sqft', 'price_per_sqft'
        ]

        for field in numeric_fields:
            if field in data and data[field] is not None:
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
        # Validate area availability
        if self.area_available_sqft is not None and self.area_available_sqft < 0:
            raise ValidationError(
                "Available area cannot be negative",
                "area_available_sqft"
            )

    def adjust_area(self, area_change: float, transaction_type: TransactionType,
                    notes: Optional[str] = None) -> None:
        """
        Adjust available leather area with comprehensive validation.

        Args:
            area_change: Amount to adjust in square feet
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ModelValidationError: If area adjustment is invalid
        """
        try:
            # Validate area change
            validate_positive_number(
                {'area_change': abs(area_change)},
                'area_change',
                message="Area change must be a non-negative number"
            )

            # Validate resulting area
            new_area = (self.area_available_sqft or 0.0) + area_change

            if new_area < 0:
                raise ModelValidationError(
                    f"Cannot reduce area below zero. Current: {self.area_available_sqft}, Change: {area_change}"
                )

            # Update area
            self.area_available_sqft = new_area

            # Update status based on available area
            if self.area_available_sqft <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif self.area_available_sqft <= 1.0:  # Example threshold for low stock
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK

            # Log the adjustment
            logger.info(
                f"Leather {self.id} area adjusted. "
                f"Change: {area_change}, New Area: {self.area_available_sqft}"
            )

        except Exception as e:
            logger.error(f"Area adjustment failed: {e}")
            raise ModelValidationError(f"Leather area adjustment failed: {str(e)}")

    def calculate_total_value(self) -> float:
        """
        Calculate the total value of the leather based on available area.

        Returns:
            float: Total value of the leather
        """
        try:
            total_value = (self.area_available_sqft or 0.0) * self.price_per_sqft
            return total_value
        except Exception as e:
            logger.error(f"Value calculation failed: {e}")
            raise ModelValidationError(f"Leather value calculation failed: {str(e)}")

    def mark_as_inactive(self) -> None:
        """
        Mark the leather as inactive.
        """
        self.is_active = False
        self.status = InventoryStatus.OUT_OF_STOCK
        logger.info(f"Leather {self.id} marked as inactive")

    def restore(self) -> None:
        """
        Restore an inactive leather item.
        """
        self.is_active = True
        # Restore status based on available area
        if self.area_available_sqft is not None:
            if self.area_available_sqft <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif self.area_available_sqft <= 1.0:
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK
        logger.info(f"Leather {self.id} restored")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the leather.

        Returns:
            str: Detailed leather representation
        """
        return (
            f"<Leather(id={self.id}, name='{self.name}', "
            f"type={self.leather_type}, "
            f"area={self.area_available_sqft or 0.0} sqft, "
            f"status={self.status}, "
            f"active={self.is_active})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.leather.Leather', 'database.models.leather')