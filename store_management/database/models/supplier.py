# database/models/supplier.py
from sqlalchemy import Column, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import SupplierStatus


class Supplier(AbstractBase, ValidationMixin):
    """
    Supplier entity for material and tool vendors.

    Attributes:
        name: Supplier name
        contact_email: Primary contact email
        phone: Contact phone number
        address: Physical address
        status: Supplier status
    """
    __tablename__ = 'suppliers'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[SupplierStatus] = mapped_column(Enum(SupplierStatus), nullable=False, default=SupplierStatus.ACTIVE)

    # Relationships
    materials = relationship("Material", back_populates="supplier")
    tools = relationship("Tool", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")

    def __init__(self, **kwargs):
        """Initialize a Supplier instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate supplier data."""
        if not self.name:
            raise ModelValidationError("Supplier name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Supplier name cannot exceed 255 characters")

        if self.contact_email and '@' not in self.contact_email:
            raise ModelValidationError("Invalid email format for supplier contact")