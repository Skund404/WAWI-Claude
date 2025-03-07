# database/models/customer.py
"""
Enhanced Customer Model with Comprehensive Validation and Relationship Management

This module defines the Customer model for the leatherworking management system,
providing robust tracking of customer information and sales interactions.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    CustomerStatus,
    CustomerTier,
    CustomerSource
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    CircularImportResolver,
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError
)

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports to resolve potential circular dependencies
register_lazy_import('Sales', 'database.models.sales', 'Sales')


class Customer(Base, TimestampMixin, ValidationMixin, TrackingMixin):
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
    tier: Mapped[Optional[CustomerTier]] = mapped_column(
        String(50),
        nullable=True
    )
    source: Mapped[Optional[CustomerSource]] = mapped_column(
        String(50),
        nullable=True
    )

    # Notes and additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Customer Preferences
    accepts_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_contact_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships with lazy loading and circular import resolution
    sales_records: Mapped[List["Sales"]] = relationship(
        "Sales",
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
            self._validate_customer_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Additional post-initialization validation
            self._post_init_validation()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Customer initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Customer: {str(e)}") from e

    @classmethod
    def _validate_customer_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of customer creation data.

        Args:
            data (Dict[str, Any]): Customer creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        if not data.get('first_name'):
            raise ValidationError("First name is required", "first_name")

        if not data.get('last_name'):
            raise ValidationError("Last name is required", "last_name")

        # Validate email if provided
        if data.get('email'):
            cls._validate_email(data['email'])

        # Validate phone number if provided
        if data.get('phone'):
            cls._validate_phone_number(data['phone'])

        # Validate customer status
        if data.get('status'):
            cls._validate_customer_status(data['status'])

        # Validate customer tier if provided
        if data.get('tier'):
            cls._validate_customer_tier(data['tier'])

        # Validate customer source if provided
        if data.get('source'):
            cls._validate_customer_source(data['source'])

    def _post_init_validation(self) -> None:
        """
        Additional validation after instance creation.

        Raises:
            ValidationError: If post-initialization validation fails
        """
        # Validate total sales records
        if hasattr(self, 'sales_records'):
            total_sales = len(self.sales_records)
            # Example business logic: Update tier based on sales
            if total_sales > 10:
                self.tier = CustomerTier.VIP
            elif total_sales > 5:
                self.tier = CustomerTier.PREMIUM

    @classmethod
    def _validate_email(cls, email: str) -> None:
        """
        Validate email format using comprehensive regex.

        Args:
            email: Email address to validate

        Raises:
            ValidationError: If email is invalid
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError("Invalid email format", "email")

    @classmethod
    def _validate_phone_number(cls, phone: str) -> None:
        """
        Validate phone number format.

        Args:
            phone: Phone number to validate

        Raises:
            ValidationError: If phone number is invalid
        """
        # Robust phone number validation
        phone_regex = r'^\+?1?\d{9,15}$'
        cleaned_phone = re.sub(r'\D', '', phone)

        if not re.match(phone_regex, cleaned_phone):
            raise ValidationError("Invalid phone number format", "phone")

    @classmethod
    def _validate_customer_status(cls, status: Union[str, CustomerStatus]) -> None:
        """
        Validate customer status.

        Args:
            status: Customer status to validate

        Raises:
            ValidationError: If status is invalid
        """
        if isinstance(status, str):
            try:
                status = CustomerStatus[status.upper()]
            except KeyError:
                raise ValidationError("Invalid customer status", "status")

    @classmethod
    def _validate_customer_tier(cls, tier: Union[str, CustomerTier]) -> None:
        """
        Validate customer tier.

        Args:
            tier: Customer tier to validate

        Raises:
            ValidationError: If tier is invalid
        """
        if isinstance(tier, str):
            try:
                tier = CustomerTier[tier.upper()]
            except KeyError:
                raise ValidationError("Invalid customer tier", "tier")

    @classmethod
    def _validate_customer_source(cls, source: Union[str, CustomerSource]) -> None:
        """
        Validate customer source.

        Args:
            source: Customer source to validate

        Raises:
            ValidationError: If source is invalid
        """
        if isinstance(source, str):
            try:
                source = CustomerSource[source.upper()]
            except KeyError:
                raise ValidationError("Invalid customer source", "source")

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
            method: Preferred contact method

        Raises:
            ValidationError: If method is invalid
        """
        valid_methods = ['email', 'phone', 'mail', 'sms']
        if method.lower() not in valid_methods:
            raise ValidationError(
                f"Invalid contact method. Must be one of {valid_methods}",
                "preferred_contact_method"
            )

        self.preferred_contact_method = method.lower()
        logger.info(f"Updated contact preference for {self.full_name()}")

    def toggle_marketing_consent(self, consent: bool) -> None:
        """
        Toggle marketing communication consent.

        Args:
            consent: Whether to accept marketing communications
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
            f"<Customer("
            f"id={self.id}, "
            f"name='{self.full_name()}', "
            f"email='{self.email or 'N/A'}', "
            f"status={self.status.name}, "
            f"tier={self.tier.name if self.tier else 'N/A'}"
            f")>"
        )


# Register for lazy import resolution
register_lazy_import('Customer', 'database.models.customer', 'Customer')