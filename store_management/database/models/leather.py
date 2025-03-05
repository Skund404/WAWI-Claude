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
from sqlalchemy.orm import relationship
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column
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
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('database.models.storage.Storage', 'database.models.storage', 'Storage')
register_lazy_import('database.models.transaction.LeatherTransaction', 'database.models.transaction', 'LeatherTransaction')
register_lazy_import('database.models.project.Project', 'database.models.project', 'Project')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components', 'ProjectComponent')


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
    transactions: Mapped[List["LeatherTransaction"]] = relationship(
        "LeatherTransaction",
        back_populates="leather",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Update supplier relationship
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier",
        back_populates="leathers",
        lazy="selectin"
    )

    # Update storage relationship
    storage: Mapped[Optional["Storage"]] = relationship(
        "Storage",
        back_populates="leathers",
        lazy="selectin"
    )

    # Update project_components relationship
    project_components: Mapped[List["ProjectComponent"]] = relationship(
        "ProjectComponent",
        back_populates="leather",
        lazy="selectin",
        cascade="save-update, merge"  # Removed refresh-expire
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
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')