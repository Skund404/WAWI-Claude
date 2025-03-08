# database/models/customer.py
"""
Customer Model for Leatherworking Management System

Implements detailed customer information tracking and relationship management.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    CustomerStatus,
    CustomerTier,
    CustomerSource
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_email,
    validate_phone_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports for related models
register_lazy_import('Sales', 'database.models.sales', 'Sales')


class Customer(Base, apply_mixins(TimestampMixin, ValidationMixin, TrackingMixin)):
    """
    Customer model representing detailed customer information.

    Tracks customer data, preferences, history, and relationships with sales.
    """
    __tablename__ = 'customers'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Core customer information
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Address information
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Customer classification and metadata
    status: Mapped[CustomerStatus] = mapped_column(
        String(20),
        default=CustomerStatus.ACTIVE.name,
        nullable=False
    )
    tier: Mapped[CustomerTier] = mapped_column(
        String(20),
        default=CustomerTier.STANDARD.name,
        nullable=False
    )
    source: Mapped[Optional[CustomerSource]] = mapped_column(
        String(20),
        nullable=True
    )

    # Customer preferences and notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Marketing and communication preferences
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps for customer-specific events
    last_purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    sales_records: Mapped[List['Sales']] = relationship(
        "Sales",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin"
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

            # Initialize base models
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Customer initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Customer: {str(e)}") from e

    @classmethod
    def _validate_customer_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate customer data before initialization.

        Args:
            data: Customer data to validate

        Raises:
            ValidationError: If data validation fails
        """
        # Validate required fields
        required_fields = ['first_name', 'last_name']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"{field.replace('_', ' ').title()} is required", field)

        # Validate email if provided
        if 'email' in data and data['email']:
            validate_email(data['email'])

        # Validate phone if provided
        if 'phone' in data and data['phone']:
            validate_phone_number(data['phone'])

        # Validate enums
        cls._validate_customer_enums(data)

    @classmethod
    def _validate_customer_enums(cls, data: Dict[str, Any]) -> None:
        """
        Validate enum fields in customer data.

        Args:
            data: Customer data containing enum fields

        Raises:
            ValidationError: If enum validation fails
        """
        # Validate status
        if 'status' in data and data['status']:
            if isinstance(data['status'], str):
                try:
                    data['status'] = CustomerStatus[data['status'].upper()].name
                except KeyError:
                    raise ValidationError(
                        f"Invalid customer status. Must be one of {[s.name for s in CustomerStatus]}",
                        "status"
                    )

        # Validate tier
        if 'tier' in data and data['tier']:
            if isinstance(data['tier'], str):
                try:
                    data['tier'] = CustomerTier[data['tier'].upper()].name
                except KeyError:
                    raise ValidationError(
                        f"Invalid customer tier. Must be one of {[t.name for t in CustomerTier]}",
                        "tier"
                    )

        # Validate source
        if 'source' in data and data['source']:
            if isinstance(data['source'], str):
                try:
                    data['source'] = CustomerSource[data['source'].upper()].name
                except KeyError:
                    raise ValidationError(
                        f"Invalid customer source. Must be one of {[s.name for s in CustomerSource]}",
                        "source"
                    )

    def _post_init_processing(self) -> None:
        """
        Perform post-initialization processing.

        Sets defaults and performs any necessary data transformations.
        """
        # Set default status if not provided
        if not hasattr(self, 'status') or self.status is None:
            self.status = CustomerStatus.ACTIVE.name

        # Set default tier if not provided
        if not hasattr(self, 'tier') or self.tier is None:
            self.tier = CustomerTier.STANDARD.name

        # Format phone number if provided
        if hasattr(self, 'phone') and self.phone:
            self.phone = self._format_phone_number(self.phone)

    @staticmethod
    def _format_phone_number(phone: str) -> str:
        """
        Format phone number to standardized format.

        Args:
            phone: Phone number to format

        Returns:
            Formatted phone number
        """
        # Remove all non-numeric characters
        digits_only = re.sub(r'\D', '', phone)

        # Format based on length
        if len(digits_only) == 10:  # US number without country code
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only[0] == '1':  # US number with country code
            return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        else:
            # Return original format for international numbers or other formats
            return phone

    def get_full_name(self) -> str:
        """
        Get customer's full name.

        Returns:
            Customer's full name
        """
        return f"{self.first_name} {self.last_name}"

    def get_address(self) -> str:
        """
        Get formatted complete address.

        Returns:
            Formatted address or empty string if no address
        """
        address_parts = []

        if getattr(self, 'address_line1', None):
            address_parts.append(self.address_line1)

        if getattr(self, 'address_line2', None):
            address_parts.append(self.address_line2)

        city_state = []
        if getattr(self, 'city', None):
            city_state.append(self.city)

        if getattr(self, 'state', None):
            city_state.append(self.state)

        if city_state:
            address_parts.append(', '.join(city_state))

        if getattr(self, 'postal_code', None):
            address_parts.append(self.postal_code)

        if getattr(self, 'country', None):
            address_parts.append(self.country)

        return '\n'.join(address_parts)

    def update_status(self, new_status: Union[str, CustomerStatus]) -> None:
        """
        Update customer status.

        Args:
            new_status: New status to set

        Raises:
            ValidationError: If status is invalid
        """
        if isinstance(new_status, str):
            try:
                new_status = CustomerStatus[new_status.upper()].name
            except KeyError:
                raise ValidationError(
                    f"Invalid customer status. Must be one of {[s.name for s in CustomerStatus]}",
                    "status"
                )
        elif isinstance(new_status, CustomerStatus):
            new_status = new_status.name

        self.status = new_status
        logger.info(f"Customer {self.id} status updated to {new_status}")

    def __repr__(self) -> str:
        """
        String representation of the customer.

        Returns:
            str: Customer representation
        """
        return (
            f"Customer("
            f"id={self.id}, "
            f"name='{self.get_full_name()}', "
            f"email='{self.email or 'N/A'}', "
            f"status={self.status}"
            f")"
        )


# Register for lazy import resolution
register_lazy_import('Customer', 'database.models.customer', 'Customer')