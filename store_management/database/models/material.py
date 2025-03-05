# database/models/material.py
"""
Enhanced Material Model with Advanced Relationship and Validation Strategies

This module defines the Material model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Float, DateTime, Text
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    MaterialType,
    InventoryStatus,
    TransactionType
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
register_lazy_import('database.models.transaction.MaterialTransaction', 'database.models.transaction')
register_lazy_import('database.models.project.Project', 'database.models.project')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components')


class Material(Base):
    """
    Enhanced Material model with comprehensive validation and relationship management.

    Represents materials in the inventory system with advanced tracking
    and relationship configuration.
    """
    __tablename__ = 'materials'

    # Core material attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Classification
    material_type = Column(Enum(MaterialType), nullable=False)

    # Inventory tracking
    quantity = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(InventoryStatus),
                    default=InventoryStatus.IN_STOCK,
                    nullable=False)

    # Optional material-specific attributes
    color = Column(String(50), nullable=True)
    thickness = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    area = Column(Float, nullable=True)

    # Timestamp for last update
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=True)

    # Relationships configured to avoid circular imports
    transactions = relationship(
        "MaterialTransaction",
        back_populates="material",
        lazy='select',
        cascade='all, delete-orphan'
    )

    project_components = relationship(
        "ProjectComponent",
        back_populates="material",
        lazy='select'
    )

    def __init__(self, **kwargs):
        """
        Initialize a Material instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for material attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Material initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Material: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate material creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Material creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Material name is required')
        validate_not_empty(data, 'material_type', 'Material type is required')

        # Validate material type
        if 'material_type' in data:
            ModelValidator.validate_enum(
                data['material_type'],
                MaterialType,
                'material_type'
            )

        # Validate numeric fields
        numeric_fields = ['quantity', 'thickness', 'price', 'area']

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
        # Validate quantity consistency
        if self.quantity < 0:
            raise ValidationError(
                "Quantity cannot be negative",
                "quantity"
            )

    def prepare_for_usage(self, required_quantity: float) -> bool:
        """
        Prepare material for usage by checking and reducing quantity.

        Args:
            required_quantity (float): Quantity of material needed

        Returns:
            bool: True if sufficient material is available, False otherwise

        Raises:
            ModelValidationError: If preparation fails
        """
        try:
            # Validate required quantity
            validate_positive_number(
                {'required_quantity': required_quantity},
                'required_quantity',
                message="Required quantity must be a positive number"
            )

            # Check if sufficient quantity is available
            if self.quantity < required_quantity:
                logger.warning(
                    f"Insufficient material. "
                    f"Available: {self.quantity}, Required: {required_quantity}"
                )
                return False

            # Reduce quantity
            self.quantity -= required_quantity

            # Update status based on remaining quantity
            if self.quantity <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif self.quantity <= 1.0:  # Low stock threshold
                self.status = InventoryStatus.LOW_STOCK

            # Update last updated timestamp
            self.last_updated = datetime.utcnow()

            logger.info(
                f"Material {self.id} prepared for usage. "
                f"Quantity used: {required_quantity}, Remaining: {self.quantity}"
            )

            return True

        except Exception as e:
            logger.error(f"Material preparation failed: {e}")
            raise ModelValidationError(f"Cannot prepare material: {str(e)}")

    def log_transaction(self, transaction_type: TransactionType,
                        quantity: float,
                        notes: Optional[str] = None) -> None:
        """
        Log a transaction for the material.

        Args:
            transaction_type (TransactionType): Type of transaction
            quantity (float): Quantity involved in the transaction
            notes (Optional[str]): Additional notes about the transaction

        Raises:
            ModelValidationError: If transaction logging fails
        """
        try:
            # Validate transaction details
            validate_positive_number(
                {'quantity': quantity},
                'quantity',
                message="Transaction quantity must be a positive number"
            )

            # Log transaction (actual transaction creation would depend on
            # your specific transaction model implementation)
            logger.info(
                f"Transaction logged for Material {self.id}. "
                f"Type: {transaction_type}, Quantity: {quantity}"
            )

        except Exception as e:
            logger.error(f"Transaction logging failed: {e}")
            raise ModelValidationError(f"Cannot log material transaction: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the material.

        Returns:
            str: Detailed material representation
        """
        return (
            f"<Material(id={self.id}, name='{self.name}', "
            f"type={self.material_type}, "
            f"quantity={self.quantity or 0.0}, "
            f"status={self.status})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.material.Material', 'database.models.material')