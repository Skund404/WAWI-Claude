# database/models/production.py
"""
Enhanced Production Model with Standard SQLAlchemy Relationship Approach

This module defines the Production model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Union

from sqlalchemy import Column, Date, Float, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Project', 'database.models.project', 'Project')

# Setup logger
logger = logging.getLogger(__name__)


class Production(Base):
    """
    Enhanced Production model with comprehensive validation and relationship management.

    Represents production records for leatherworking items with advanced
    tracking and relationship configuration.
    """
    __tablename__ = 'productions'

    # Production specific fields
    production_date = Column(Date, default=date.today, nullable=False)
    batch_number = Column(String(50), nullable=True)

    product_name = Column(String(255), nullable=False)
    quantity_produced = Column(Integer, default=0, nullable=False)

    labor_hours = Column(Float, default=0.0, nullable=False)
    material_cost = Column(Float, default=0.0, nullable=False)
    labor_cost = Column(Float, default=0.0, nullable=False)
    overhead_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)

    notes = Column(Text, nullable=True)

    # Foreign keys with explicit support for circular imports
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships using standard SQLAlchemy approach
    product = relationship("Product", back_populates="production_records", lazy="select")
    project = relationship("Project", back_populates="production_records", lazy="select")

    def __init__(self, **kwargs):
        """
        Initialize a Production instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for production attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Set default production date if not provided
            if 'production_date' not in kwargs:
                kwargs['production_date'] = date.today()

            # Initialize base model
            super().__init__(**kwargs)

            # Calculate total cost if not provided
            if 'total_cost' not in kwargs:
                self.calculate_total_cost()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Production initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Production record: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate production data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Production creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'product_name', 'Product name is required')

        # Validate numeric fields
        numeric_fields = [
            'quantity_produced', 'labor_hours',
            'material_cost', 'labor_cost', 'overhead_cost'
        ]

        for field in numeric_fields:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

        # Validate production date
        if 'production_date' in data and data['production_date']:
            if not isinstance(data['production_date'], (date, datetime)):
                raise ValidationError(
                    "Production date must be a valid date",
                    "production_date"
                )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate relationships
        if self.product and not hasattr(self.product, 'id'):
            raise ValidationError("Invalid product reference", "product")

        if self.project and not hasattr(self.project, 'id'):
            raise ValidationError("Invalid project reference", "project")

        # Ensure total cost matches individual cost components
        calculated_total = (
                self.material_cost +
                self.labor_cost +
                self.overhead_cost
        )
        if abs(calculated_total - self.total_cost) > 0.01:  # Allow small floating-point differences
            raise ValidationError(
                "Total cost does not match cost components",
                "total_cost"
            )

    def calculate_total_cost(self) -> float:
        """
        Calculate the total production cost.

        Returns:
            float: The calculated total cost
        """
        try:
            self.total_cost = self.material_cost + self.labor_cost + self.overhead_cost
            return self.total_cost
        except Exception as e:
            logger.error(f"Total cost calculation failed: {e}")
            raise ModelValidationError(f"Failed to calculate total production cost: {str(e)}")

    def get_unit_cost(self) -> Optional[float]:
        """
        Calculate the per-unit production cost.

        Returns:
            Optional[float]: The per-unit cost, or None if quantity is zero
        """
        try:
            if self.quantity_produced > 0:
                return self.total_cost / self.quantity_produced
            return None
        except Exception as e:
            logger.error(f"Unit cost calculation failed: {e}")
            raise ModelValidationError(f"Failed to calculate unit production cost: {str(e)}")

    def generate_batch_number(self) -> str:
        """
        Generate a unique batch number for the production record.

        Returns:
            str: Generated batch number
        """
        try:
            # Use date and product name to create unique batch number
            product_code = ''.join(c for c in self.product_name if c.isalnum())[:3].upper()
            date_part = self.production_date.strftime('%Y%m%d')

            # Append last 4 digits of ID for uniqueness
            id_part = str(self.id).zfill(4)[-4:]

            return f"{product_code}-{date_part}-{id_part}"
        except Exception as e:
            logger.error(f"Batch number generation failed: {e}")
            raise ModelValidationError(f"Cannot generate batch number: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the production record.

        Returns:
            str: Detailed production record representation
        """
        return (
            f"<Production(id={self.id}, "
            f"date={self.production_date}, "
            f"product='{self.product_name}', "
            f"quantity={self.quantity_produced}, "
            f"total_cost={self.total_cost})>"
        )


# Register this class for lazy imports by others
register_lazy_import('Production', 'database.models.production', 'Production')