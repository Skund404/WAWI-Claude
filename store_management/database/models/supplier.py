# database/models/supplier.py
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import SupplierStatus


class Supplier(AbstractBase, ValidationMixin):
    """
    Supplier model representing vendors that provide materials and tools.

    Attributes:
        name (str): Supplier name
        contact_email (str): Contact email address
        contact_phone (Optional[str]): Contact phone number
        address (Optional[str]): Supplier address
        status (SupplierStatus): Current supplier status
        notes (Optional[str]): Additional notes about the supplier
    """
    __tablename__ = 'suppliers'
    __table_args__ = {'extend_existing': True}  # Fix for duplicate table definition

    # SQLAlchemy 2.0 type annotated columns
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    contact_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    status: Mapped[SupplierStatus] = mapped_column(
        Enum(SupplierStatus),
        nullable=False,
        default=SupplierStatus.ACTIVE,
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )

    # Relationships
    materials: Mapped[List[object]] = relationship(
        "Material",
        back_populates="supplier",
        lazy="selectin"
    )

    tools: Mapped[List[object]] = relationship(
        "Tool",
        back_populates="supplier",
        lazy="selectin"
    )

    # Restore the relationship to Purchase
    purchases: Mapped[List["Purchase"]] = relationship(
        "Purchase",
        back_populates="supplier",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Supplier instance with validation.

        Args:
            **kwargs: Keyword arguments for Supplier initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate supplier data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Name validation
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Supplier name must be a non-empty string")

        if len(self.name) > 255:
            raise ModelValidationError("Supplier name cannot exceed 255 characters")

        # Email validation
        if not self.contact_email or not isinstance(self.contact_email, str):
            raise ModelValidationError("Supplier contact email must be a non-empty string")

        if len(self.contact_email) > 255:
            raise ModelValidationError("Supplier contact email cannot exceed 255 characters")

        if '@' not in self.contact_email:
            raise ModelValidationError("Supplier contact email must be a valid email address")

        # Phone validation
        if self.contact_phone and len(self.contact_phone) > 50:
            raise ModelValidationError("Phone number cannot exceed 50 characters")

        # Address validation
        if self.address and len(self.address) > 500:
            raise ModelValidationError("Address cannot exceed 500 characters")

        # Notes validation
        if self.notes and len(self.notes) > 1000:
            raise ModelValidationError("Notes cannot exceed 1000 characters")

        return self