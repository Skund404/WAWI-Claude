# database/models/supplier.py
"""
Comprehensive Supplier Model for Leatherworking Management System

This module defines the Supplier model with extensive validation,
relationship management, and circular import resolution.

Implements the Supplier entity from the ER diagram with all its
relationships and attributes.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import sqltypes

from database.models.base import Base, ModelValidationError
from database.models.enums import SupplierStatus
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Tool', 'database.models.tool', 'Tool')
register_lazy_import('Purchase', 'database.models.purchase', 'Purchase')
register_lazy_import('Product', 'database.models.product', 'Product')


class Supplier(Base, apply_mixins(TimestampMixin, ValidationMixin, TrackingMixin)):
    """
    Supplier model representing vendors and suppliers for leatherworking materials.

    This implements the Supplier entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'suppliers'

    # Explicit primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Basic attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Use sqltypes for enum column
    status: Mapped[SupplierStatus] = mapped_column(
        sqltypes.Enum(SupplierStatus),
        nullable=False,
        default=SupplierStatus.ACTIVE
    )

    # Contact information
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Address
    street_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    materials = relationship("Material", back_populates="supplier")
    leathers = relationship("Leather", back_populates="supplier")
    hardwares = relationship("Hardware", back_populates="supplier")
    tools = relationship("Tool", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")
    products = relationship("Product", back_populates="supplier")

    def __init__(self, **kwargs):
        """
        Initialize a Supplier instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for supplier attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_supplier_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Supplier initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Supplier: {str(e)}") from e

    @classmethod
    def _validate_supplier_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of supplier creation data.

        Args:
            data: Supplier creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Supplier name is required')

        # Validate email format if provided
        if data.get('contact_email'):
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, data['contact_email']):
                raise ValidationError("Invalid email format", "contact_email")

        # Validate website format if provided
        if data.get('website'):
            website_pattern = r'^(http|https)://[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(:[0-9]+)?(/.*)?$'
            if not re.match(website_pattern, data['website']):
                # Try adding http:// prefix if missing
                if re.match(r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+', data['website']):
                    data['website'] = f"http://{data['website']}"
                else:
                    raise ValidationError("Invalid website URL format", "website")

        # Validate status if provided
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                SupplierStatus,
                'status'
            )

    def mark_as_inactive(self) -> None:
        """Mark the supplier as inactive."""
        self.status = SupplierStatus.INACTIVE
        logger.info(f"Supplier {self.id} marked as inactive")

    def mark_as_blacklisted(self) -> None:
        """Mark the supplier as blacklisted."""
        self.status = SupplierStatus.BLACKLISTED
        logger.info(f"Supplier {self.id} marked as blacklisted")

    def mark_as_active(self) -> None:
        """Mark the supplier as active."""
        self.status = SupplierStatus.ACTIVE
        logger.info(f"Supplier {self.id} marked as active")

    def get_full_address(self) -> str:
        """
        Get the full address as a formatted string.

        Returns:
            Formatted address
        """
        address_parts = []

        if self.street_address:
            address_parts.append(self.street_address)

        city_state_parts = []
        if self.city:
            city_state_parts.append(self.city)
        if self.state:
            city_state_parts.append(self.state)

        if city_state_parts:
            address_parts.append(', '.join(city_state_parts))

        if self.postal_code:
            address_parts.append(self.postal_code)

        if self.country:
            address_parts.append(self.country)

        return '\n'.join(address_parts)

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

        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Handle special types
                if isinstance(value, SupplierStatus):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add computed fields
        result['full_address'] = self.get_full_address()

        return result

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the supplier instance.

        Returns:
            Dictionary mapping field names to validation errors,
            or an empty dictionary if validation succeeds
        """
        errors = {}

        try:
            # Validate required fields
            if not self.name:
                errors.setdefault('name', []).append("Name is required")

            # Validate email format if provided
            if self.contact_email:
                email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                if not re.match(email_pattern, self.contact_email):errors.setdefault('contact_email', []).append("Invalid email format")

            # Validate website format if provided
            if self.website:
                website_pattern = r'^(http|https)://[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(:[0-9]+)?(/.*)?$'
                if not re.match(website_pattern, self.website):
                    errors.setdefault('website', []).append("Invalid website URL format")

        except Exception as e:
            errors.setdefault('general', []).append(f"Validation error: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the supplier instance is valid.

        Returns:
            True if the instance is valid, False otherwise
        """
        return len(self.validate()) == 0

    def __repr__(self) -> str:
        """
        String representation of the Supplier.

        Returns:
            Detailed supplier representation
        """
        return (
            f"<Supplier(id={self.id}, "
            f"name='{self.name}', "
            f"status={self.status.name if self.status else 'None'})>"
        )


# Register for lazy import resolution
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')