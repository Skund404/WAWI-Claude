from database.models.base import metadata
# database/models/production.py
"""
Comprehensive Production Model for Leatherworking Management System

This module defines the Production model with extensive validation,
relationship management, and circular import resolution.

Provides functionality for tracking production records, material usage,
and cost calculations for the leatherworking business.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    ProjectStatus,
    ProjectType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
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
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')


class Production(Base, TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin):
    """
    Production model representing manufacturing activities.

    This model tracks production records for leatherworking items, capturing
    details about products produced, resources used, and costs incurred.
    """
    __tablename__ = 'productions'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Production details
    production_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_produced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Cost tracking
    labor_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    material_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    labor_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overhead_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    production_staff: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quality_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Related records
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)

    # Metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Material usage tracking
    material_usage: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="production_records")
    project = relationship("Project", back_populates="production_records")

    def __init__(self, **kwargs):
        """
        Initialize a Production instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for production attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Set default production date if not provided
            if 'production_date' not in kwargs:
                kwargs['production_date'] = date.today()

            # Validate input data
            self._validate_production_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Production initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Production: {str(e)}") from e

    @classmethod
    def _validate_production_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of production creation data.

        Args:
            data: Production creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'product_name', 'Product name is required')

        # Validate quantity
        if 'quantity_produced' in data:
            validate_positive_number(
                data,
                'quantity_produced',
                allow_zero=False,
                message="Quantity produced must be a positive number"
            )

        # Validate cost fields
        for field in ['labor_hours', 'material_cost', 'labor_cost', 'overhead_cost']:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} cannot be negative"
                )

        # Validate production date
        if 'production_date' in data and data['production_date']:
            if not isinstance(data['production_date'], (date, datetime)):
                raise ValidationError("Production date must be a valid date", "production_date")

        # Validate quality rating if provided
        if 'quality_rating' in data and data['quality_rating'] is not None:
            if not isinstance(data['quality_rating'], int) or data['quality_rating'] < 1 or data['quality_rating'] > 5:
                raise ValidationError("Quality rating must be an integer between 1 and 5", "quality_rating")

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize metadata if not provided
        if not hasattr(self, 'metadata') or self.metadata is None:
            self.metadata = {}

        # Initialize material usage if not provided
        if not hasattr(self, 'material_usage') or self.material_usage is None:
            self.material_usage = {}

        # Calculate total cost if not already set
        if hasattr(self, 'total_cost') and self.total_cost == 0.0:
            self.calculate_total_cost()

        # Generate batch number if not provided
        if not hasattr(self, 'batch_number') or not self.batch_number:
            self.batch_number = self.generate_batch_number()

        # Ensure tracking ID is set
        if not hasattr(self, 'tracking_id') or not self.tracking_id:
            self.generate_tracking_id()

    def calculate_total_cost(self) -> float:
        """
        Calculate and update the total production cost.

        Returns:
            The calculated total cost
        """
        try:
            self.total_cost = (
                    (self.material_cost or 0.0) +
                    (self.labor_cost or 0.0) +
                    (self.overhead_cost or 0.0)
            )
            return self.total_cost

        except Exception as e:
            logger.error(f"Total cost calculation failed: {e}")
            raise ModelValidationError(f"Failed to calculate total production cost: {str(e)}")

    def get_unit_cost(self) -> Optional[float]:
        """
        Calculate the per-unit production cost.

        Returns:
            The per-unit cost, or None if quantity is zero
        """
        try:
            if not hasattr(self, 'quantity_produced') or not self.quantity_produced or self.quantity_produced <= 0:
                return None

            return self.total_cost / self.quantity_produced

        except Exception as e:
            logger.error(f"Unit cost calculation failed: {e}")
            raise ModelValidationError(f"Failed to calculate unit production cost: {str(e)}")

    def generate_batch_number(self) -> str:
        """
        Generate a unique batch number for the production record.

        Returns:
            Generated batch number
        """
        try:
            # Use date and product name to create unique batch number
            product_code = ''.join(c for c in self.product_name if c.isalnum())[:3].upper()
            date_part = self.production_date.strftime('%Y%m%d')

            # Append last 4 digits of ID for uniqueness or timestamp if ID is not available
            id_part = str(self.id).zfill(4)[-4:] if hasattr(self, 'id') and self.id else datetime.utcnow().strftime(
                '%H%M')

            return f"{product_code}-{date_part}-{id_part}"

        except Exception as e:
            logger.error(f"Batch number generation failed: {e}")
            raise ModelValidationError(f"Cannot generate batch number: {str(e)}")

    def add_material_usage(self,
                           material_type: str,
                           material_id: int,
                           quantity: float,
                           cost: Optional[float] = None,
                           description: Optional[str] = None) -> None:
        """
        Add material usage information to the production record.

        Args:
            material_type: Type of material ('material', 'leather', 'hardware')
            material_id: ID of the specific material
            quantity: Quantity used
            cost: Optional cost of the material used
            description: Optional description of the material usage

        Raises:
            ValidationError: If material usage data is invalid
        """
        try:
            # Initialize material usage dict if needed
            if not hasattr(self, 'material_usage') or not self.material_usage:
                self.material_usage = {}

            if 'items' not in self.material_usage:
                self.material_usage['items'] = []

            # Add material usage entry
            material_entry = {
                'material_type': material_type,
                'material_id': material_id,
                'quantity': quantity,
                'timestamp': datetime.utcnow().isoformat()
            }

            if cost is not None:
                material_entry['cost'] = cost

            if description is not None:
                material_entry['description'] = description

            # Add to list of materials
            self.material_usage['items'].append(material_entry)

            # Update material cost if cost was provided
            if cost is not None:
                self.material_cost += cost
                self.calculate_total_cost()

            logger.info(f"Added material usage to production {self.id}: {material_type} ID {material_id}")

        except Exception as e:
            logger.error(f"Error adding material usage: {e}")
            raise ModelValidationError(f"Failed to add material usage: {str(e)}")

    def calculate_efficiency(self) -> Dict[str, Any]:
        """
        Calculate production efficiency metrics.

        Returns:
            Dictionary with efficiency metrics
        """
        try:
            metrics = {
                'cost_per_unit': self.get_unit_cost() or 0.0,
                'labor_hours_per_unit': self.labor_hours / self.quantity_produced if self.quantity_produced > 0 else 0,
                'material_cost_percentage': (self.material_cost / self.total_cost * 100) if self.total_cost > 0 else 0,
                'labor_cost_percentage': (self.labor_cost / self.total_cost * 100) if self.total_cost > 0 else 0,
                'overhead_cost_percentage': (self.overhead_cost / self.total_cost * 100) if self.total_cost > 0 else 0
            }

            return metrics

        except Exception as e:
            logger.error(f"Efficiency calculation failed: {e}")
            raise ModelValidationError(f"Failed to calculate efficiency metrics: {str(e)}")

    def to_dict(self, exclude_fields: Optional[List[str]] = None, include_efficiency: bool = False) -> Dict[str, Any]:
        """
        Convert production record to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude
            include_efficiency: Whether to include efficiency metrics

        Returns:
            Dictionary representation of the production record
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        # Build the dictionary
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert date to ISO format
                if isinstance(value, date):
                    result[column.name] = value.isoformat()
                # Handle other special types here if needed
                else:
                    result[column.name] = value

        # Add unit cost
        unit_cost = self.get_unit_cost()
        if unit_cost is not None:
            result['unit_cost'] = unit_cost

        # Add efficiency metrics if requested
        if include_efficiency:
            result['efficiency_metrics'] = self.calculate_efficiency()

        # Add product name if available
        if hasattr(self, 'product') and self.product:
            result['product_name'] = getattr(self.product, 'name', self.product_name)

        # Add project name if available
        if hasattr(self, 'project') and self.project:
            result['project_name'] = getattr(self.project, 'name', None)

        return result

    def __repr__(self) -> str:
        """
        String representation of the Production record.

        Returns:
            Detailed production record representation
        """
        return (
            f"<Production(id={self.id}, "
            f"date={self.production_date}, "
            f"product='{self.product_name}', "
            f"quantity={self.quantity_produced}, "
            f"total_cost={self.total_cost})>"
        )


# Register for lazy import resolution
register_lazy_import('Production', 'database.models.production', 'Production')