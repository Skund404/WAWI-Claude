# database/models/supplier.py
from database.models.base import Base
from database.models.enums import SupplierStatus
from sqlalchemy import Column, Enum, String, Text, Boolean
from sqlalchemy.orm import relationship
import re
from utils.validators import validate_not_empty


class Supplier(Base):
    """
    Model representing material suppliers.
    """
    # Supplier specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    contact_person = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)

    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE, nullable=False)
    is_preferred = Column(Boolean, default=False, nullable=False)

    payment_terms = Column(String(255), nullable=True)
    delivery_terms = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    orders = relationship("Order", back_populates="supplier")
    products = relationship("Product", back_populates="supplier")
    leathers = relationship("Leather", back_populates="supplier")
    hardware = relationship("Hardware", back_populates="supplier")

    def __init__(self, **kwargs):
        """Initialize a Supplier instance with validation.

        Args:
            **kwargs: Keyword arguments with supplier attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate supplier data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'name', 'Supplier name is required')

        # Validate email format if provided
        if 'email' in data and data['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                raise ValueError("Invalid email format")

        # Validate phone format if provided
        if 'phone' in data and data['phone']:
            # Allow various formats, just check for minimum digits
            digits = re.sub(r'\D', '', data['phone'])
            if len(digits) < 10:
                raise ValueError("Phone number should have at least 10 digits")

    def mark_as_inactive(self):
        """Mark the supplier as inactive."""
        self.status = SupplierStatus.INACTIVE

    def mark_as_active(self):
        """Mark the supplier as active."""
        self.status = SupplierStatus.ACTIVE

    def set_as_preferred(self, is_preferred=True):
        """Set the supplier as preferred or not preferred.

        Args:
            is_preferred (bool): Whether the supplier is preferred
        """
        self.is_preferred = is_preferred

    def __repr__(self):
        """String representation of the supplier.

        Returns:
            str: String representation
        """
        return f"<Supplier(id={self.id}, name='{self.name}', status={self.status})>"