# database/models/customer.py
"""
This module defines the Customer model for the leatherworking application.
"""

from __future__ import annotations  # For forward references
from typing import Any, Dict, Optional

from sqlalchemy import Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource


class Customer(AbstractBase, ValidationMixin):
    """
    Customer model representing a client who makes purchases.

    Attributes:
        first_name (str): Customer's first name.
        last_name (str): Customer's last name.
        email (str): Customer's email address.
        status (CustomerStatus): Current status of the customer.
        tier (Optional[CustomerTier]): Customer loyalty tier.
        source (Optional[CustomerSource]): How the customer was acquired.
        notes (Optional[Dict[str, Any]]): Additional notes about the customer.
    """
    __tablename__ = "customers"
    __table_args__ = {"extend_existing": True}

    # Basic information
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus), nullable=False, default=CustomerStatus.ACTIVE
    )

    # Optional attributes
    tier: Mapped[Optional[CustomerTier]] = mapped_column(
        Enum(CustomerTier), nullable=True
    )
    source: Mapped[Optional[CustomerSource]] = mapped_column(
        Enum(CustomerSource), nullable=True
    )
    notes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    sales = relationship(
        "Sales",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Customer instance with validation.

        Args:
            **kwargs: Keyword arguments for Customer initialization.
        """
        super().__init__(**kwargs)
        self.validate()

    @property
    def full_name(self) -> str:
        """
        Return the full name for convenience.
        """
        return f"{self.first_name} {self.last_name}"

    def validate(self) -> None:
        """
        Validate customer data.

        Raises:
            ModelValidationError: If validation fails.
        """
        # Validate first_name
        if not self.first_name or not isinstance(self.first_name, str):
            raise ModelValidationError(
                "Customer first name must be a non-empty string"
            )
        if len(self.first_name) > 255:
            raise ModelValidationError(
                "Customer first name cannot exceed 255 characters"
            )

        # Validate last_name
        if not self.last_name or not isinstance(self.last_name, str):
            raise ModelValidationError(
                "Customer last name must be a non-empty string"
            )
        if len(self.last_name) > 255:
            raise ModelValidationError(
                "Customer last name cannot exceed 255 characters"
            )

        # Validate email
        if not self.email or not isinstance(self.email, str):
            raise ModelValidationError("Customer email must be a non-empty string")
        if len(self.email) > 255:
            raise ModelValidationError(
                "Customer email cannot exceed 255 characters"
            )
        if "@" not in self.email:
            raise ModelValidationError("Customer email must be a valid email address")

        # Validate status
        if not self.status:
            raise ModelValidationError("Customer status must be specified")

        # Validate notes (if provided)
        if self.notes and not isinstance(self.notes, dict):
            raise ModelValidationError("Customer notes must be a dictionary")

        return self
