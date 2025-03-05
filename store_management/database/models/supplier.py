# database/models/supplier.py
"""
Enhanced Supplier Model with Standard SQLAlchemy Relationship Approach

This module defines the Supplier model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SupplierStatus
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty
)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Order', 'database.models.order')
register_lazy_import('Product', 'database.models.product')
register_lazy_import('Leather', 'database.models.leather')
register_lazy_import('Hardware', 'database.models.hardware')
register_lazy_import('Part', 'database.models.part')

# Setup logger
logger = logging.getLogger(__name__)


class Supplier(Base):
    """
    Enhanced Supplier model with comprehensive validation and relationship management.

    Represents material suppliers with advanced tracking and relationship configuration.
    """
    __tablename__ = 'suppliers'

    # Core supplier attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Contact information
    contact_person = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)

    # Address details
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Status and preferences
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE, nullable=False)
    is_preferred = Column(Boolean, default=False, nullable=False)

    # Additional details
    payment_terms = Column(String(255), nullable=True)
    delivery_terms = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships using standard SQLAlchemy approach
    orders = relationship("Order", back_populates="supplier", lazy="lazy")
    products = relationship("Product", back_populates="supplier", lazy="lazy")
    leathers = relationship("Leather", back_populates="supplier", lazy="lazy")
    hardware_items = relationship("Hardware", back_populates="supplier", lazy="lazy")
    parts = relationship("Part", back_populates="supplier", lazy="lazy")

    def __init__(self, **kwargs):
        """
        Initialize a Supplier instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for supplier attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Supplier initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Supplier: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate supplier creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Supplier creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Supplier name is required')

        # Validate email if provided
        if 'email' in data and data['email']:
            email = data['email']
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValidationError(
                    "Invalid email format",
                    "email"
                )

        # Validate phone if provided
        if 'phone' in data and data['phone']:
            phone = data['phone']
            if not re.match(r"^\+?[0-9\-\s()]+$", phone):
                raise ValidationError(
                    "Invalid phone number format",
                    "phone"
                )

    def mark_as_active(self) -> None:
        """
        Mark the supplier as active.
        """
        if self.status != SupplierStatus.ACTIVE:
            self.status = SupplierStatus.ACTIVE
            logger.info(f"Supplier {self.id} ({self.name}) marked as active")

    def set_as_preferred(self, is_preferred: bool = True) -> None:
        """
        Set the supplier as preferred or not preferred.

        Args:
            is_preferred (bool): Whether the supplier is preferred
        """
        try:
            # Only change if the status is different
            if self.is_preferred != is_preferred:
                self.is_preferred = is_preferred
                status = "preferred" if is_preferred else "not preferred"
                logger.info(f"Supplier {self.id} ({self.name}) set as {status}")
        except Exception as e:
            logger.error(f"Error setting preferred status for supplier {self.id}: {e}")
            raise ModelValidationError(f"Cannot set preferred status: {str(e)}")

    def generate_supplier_code(self) -> str:
        """
        Generate a unique supplier code based on the supplier's name.

        Returns:
            str: Generated supplier code
        """
        try:
            # Take first 3 letters of name (uppercase)
            name_part = ''.join(c for c in self.name if c.isalnum())[:3].upper()

            # Append last 4 digits of ID
            id_part = str(self.id).zfill(4)[-4:]

            return f"{name_part}-{id_part}"
        except Exception as e:
            logger.error(f"Supplier code generation failed: {e}")
            raise ModelValidationError(f"Cannot generate supplier code: {str(e)}")

    def validate_contact_info(self) -> bool:
        """
        Validate the completeness of supplier contact information.

        Returns:
            bool: True if contact information is complete, False otherwise
        """
        required_fields = [
            self.contact_person,
            self.email,
            self.phone,
            self.address_line1,
            self.city,
            self.country
        ]

        return all(required_fields)

    def calculate_total_product_value(self) -> float:
        """
        Calculate the total value of all products from this supplier.

        Returns:
            float: Total value of products
        """
        try:
            # Safely check if products exist and have the expected attributes
            if not hasattr(self, 'products') or not self.products:
                return 0.0

            total_value = sum(
                getattr(product, 'stock_quantity', 0) * getattr(product, 'price', 0)
                for product in self.products
                if hasattr(product, 'stock_quantity') and hasattr(product, 'price')
            )
            return total_value
        except Exception as e:
            logger.error(f"Total product value calculation failed: {e}")
            raise ModelValidationError(f"Cannot calculate product value: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the supplier.

        Returns:
            str: Detailed supplier representation
        """
        # Safely get products count
        products_count = 0
        if hasattr(self, 'products') and self.products is not None:
            products_count = len(self.products)

        return (
            f"<Supplier(id={self.id}, name='{self.name}', "
            f"status={self.status}, "
            f"preferred={self.is_preferred}, "
            f"products={products_count})>"
        )


# Register this class for lazy imports by others
register_lazy_import('Supplier', 'database.models.supplier')