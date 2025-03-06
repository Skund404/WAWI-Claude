# database/models/supplier.py
"""
Supplier Model

This module defines the Supplier model which implements
the Supplier entity from the ER diagram.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, String, Text, Boolean, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SupplierStatus
from store_management.utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports
register_lazy_import('database.models.material.Material', 'database.models.material', 'Material')
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('database.models.tool.Tool', 'database.models.tool', 'Tool')
register_lazy_import('database.models.purchase.Purchase', 'database.models.purchase', 'Purchase')
register_lazy_import('database.models.product.Product', 'database.models.product', 'Product')


class Supplier(Base):
    """
    Supplier model representing vendors and suppliers.
    This corresponds to the Supplier entity in the ER diagram.
    """
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=True)
    status = Column(Enum(SupplierStatus), nullable=False, default=SupplierStatus.ACTIVE)

    # Contact information
    contact_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)

    # Address
    street_address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Additional information
    notes = Column(Text, nullable=True)

    # Relationships
    materials = relationship("Material", back_populates="supplier")
    leathers = relationship("Leather", back_populates="supplier")
    hardwares = relationship("Hardware", back_populates="supplier")
    tools = relationship("Tool", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")
    products = relationship("Product", back_populates="supplier")

    def __init__(self, name: str, status: SupplierStatus = SupplierStatus.ACTIVE,
                 contact_email: Optional[str] = None, contact_name: Optional[str] = None,
                 phone: Optional[str] = None, website: Optional[str] = None,
                 street_address: Optional[str] = None, city: Optional[str] = None,
                 state: Optional[str] = None, postal_code: Optional[str] = None,
                 country: Optional[str] = None, notes: Optional[str] = None, **kwargs):
        """
        Initialize a Supplier instance with comprehensive validation.

        Args:
            name: Supplier name
            status: Supplier status
            contact_email: Optional email address
            contact_name: Optional contact person name
            phone: Optional phone number
            website: Optional website URL
            street_address: Optional street address
            city: Optional city
            state: Optional state/province
            postal_code: Optional postal/zip code
            country: Optional country
            notes: Optional notes
            **kwargs: Additional attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Prepare data
            kwargs.update({
                'name': name,
                'status': status,
                'contact_email': contact_email,
                'contact_name': contact_name,
                'phone': phone,
                'website': website,
                'street_address': street_address,
                'city': city,
                'state': state,
                'postal_code': postal_code,
                'country': country,
                'notes': notes
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Supplier initialization failed: {e}")
            raise ModelValidationError(f"Failed to create supplier: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate supplier creation data with comprehensive checks.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Supplier name is required')

        # Validate email format if provided
        if data.get('contact_email'):
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, data['contact_email']):
                raise ValidationError("Invalid email format")

        # Validate website format if provided
        if data.get('website'):
            website_pattern = r'^(http|https)://[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(:[0-9]+)?(/.*)?$'
            if not re.match(website_pattern, data['website']):
                # Try adding http:// prefix if missing
                if re.match(website_pattern, f"http://{data['website']}"):
                    data['website'] = f"http://{data['website']}"
                else:
                    raise ValidationError("Invalid website URL format")

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
            str: Formatted address
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

    def __repr__(self) -> str:
        """String representation of the supplier."""
        return f"<Supplier(id={self.id}, name='{self.name}', status={self.status})>"


# Final registration
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier', 'Supplier')