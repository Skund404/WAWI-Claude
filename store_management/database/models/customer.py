# database/models/customer.py
"""
Enhanced Customer Model with Comprehensive Validation and Relationship Management

This module defines the Customer model for the leatherworking management system,
providing robust tracking of customer information and sales interactions.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    CustomerStatus,
    CustomerTier,
    CustomerSource
)
from utils.circular_import_resolver import (
    register_lazy_import,
    lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    ModelValidator
)

# Setup logger
logger = logging.getLogger(__name__)

class Customer(Base):
    """
    Comprehensive Customer model with advanced tracking and validation.

    Represents customer information with detailed contact and interaction tracking.
    """
    __tablename__ = 'customers'

    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Address Information
    street_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Customer Status and Metadata
    status: Mapped[CustomerStatus] = mapped_column(
        String(50),
        default=CustomerStatus.ACTIVE,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Customer Preferences
    accepts_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_contact_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships with lazy imports and loading
    sales: Mapped[List["Sales"]] = relationship(
        "Sales",
        back_populates="customer",
        lazy="selectin",
        cascade="save-update, merge"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="customer",
        lazy="selectin",
        cascade="save-update, merge"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Customer instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for customer attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization validation
            self._validate_instance()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Customer initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Customer: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate customer creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Customer creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'first_name', 'First name is required')
        validate_not_empty(data, 'last_name', 'Last name is required')

        # Validate email if provided
        if 'email' in data and data['email']:
            try:
                ModelValidator.validate_email(data['email'])
            except ValidationError:
                raise ValidationError("Invalid email format", "email")

        # Validate phone number format if provided
        if 'phone' in data and data['phone']:
            cls._validate_phone_number(data['phone'])

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Additional instance-level validations can be added here
        pass

    @classmethod
    def _validate_phone_number(cls, phone: str) -> None:
        """
        Validate phone number format.

        Args:
            phone (str): Phone number to validate

        Raises:
            ValidationError: If phone number is invalid
        """
        # Basic phone number validation (adjust regex as needed)
        phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
        if not phone_pattern.match(phone):
            raise ValidationError("Invalid phone number format", "phone")

    def full_name(self) -> str:
        """
        Generate the customer's full name.

        Returns:
            str: Concatenated first and last name
        """
        return f"{self.first_name} {self.last_name}".strip()

    def update_contact_preference(self, method: str) -> None:
        """
        Update customer's preferred contact method.

        Args:
            method (str): Preferred contact method

        Raises:
            ModelValidationError: If update fails
        """
        try:
            # Validate contact method
            valid_methods = ['email', 'phone', 'mail', 'sms']
            if method.lower() not in valid_methods:
                raise ValidationError(
                    f"Invalid contact method. Must be one of {valid_methods}",
                    "preferred_contact_method"
                )

            self.preferred_contact_method = method.lower()
            logger.info(f"Updated contact preference for {self.full_name()}")

        except Exception as e:
            logger.error(f"Failed to update contact preference: {e}")
            raise ModelValidationError(f"Contact preference update failed: {str(e)}")

    def toggle_marketing_consent(self, consent: bool) -> None:
        """
        Toggle marketing communication consent.

        Args:
            consent (bool): Whether to accept marketing communications
        """
        self.accepts_marketing = consent
        logger.info(
            f"Marketing consent for {self.full_name()} "
            f"{'enabled' if consent else 'disabled'}"
        )

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the customer.

        Returns:
            str: Detailed customer representation
        """
        return (
            f"<Customer(id={self.id}, "
            f"name='{self.full_name()}', "
            f"email='{self.email or 'N/A'}', "
            f"status={self.status})>"
        )

# Explicitly return the Customer class for import
__all__ = ['Customer']