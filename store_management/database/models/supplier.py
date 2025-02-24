# Path: store_management/database/models/supplier.py
"""
Supplier model definition with comprehensive attributes and relationships.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import List, Optional, Any

from .base import BaseModel
from .mixins import TimestampMixin, ValidationMixin


class Supplier(BaseModel, TimestampMixin, ValidationMixin):
    """
    Represents a supplier in the system with comprehensive tracking.

    Attributes:
        id (int): Unique identifier for the supplier.
        name (str): Name of the supplier.
        contact_name (str): Primary contact person's name.
        email (str): Supplier's contact email.
        phone (str): Supplier's contact phone number.
        address (str): Supplier's physical address.
        tax_id (str): Tax identification number.
        rating (float): Supplier performance rating.
        is_active (bool): Whether the supplier is currently active.
        payment_terms (str): Payment terms for the supplier.
        credit_limit (float): Credit limit for the supplier.

    Relationships:
        products (List[Product]): Products supplied by this supplier.
        orders (List[Order]): Orders placed with this supplier.
    """
    __tablename__ = 'suppliers'

    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True)

    # Performance and status tracking
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100))
    credit_limit: Mapped[Optional[float]] = mapped_column(Float)
    last_order_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    products: Mapped[List['Product']] = relationship(
        "Product",
        back_populates="supplier",
        lazy='subquery'
    )
    orders: Mapped[List['Order']] = relationship(
        "Order",
        back_populates="supplier",
        lazy='subquery'
    )

    def __init__(self,
                 name: str,
                 contact_name: Optional[str] = None,
                 email: Optional[str] = None,
                 phone: Optional[str] = None,
                 address: Optional[str] = None,
                 tax_id: Optional[str] = None):
        """
        Initialize a Supplier instance.

        Args:
            name (str): Name of the supplier.
            contact_name (Optional[str], optional): Primary contact person. Defaults to None.
            email (Optional[str], optional): Supplier's contact email. Defaults to None.
            phone (Optional[str], optional): Supplier's contact phone. Defaults to None.
            address (Optional[str], optional): Supplier's physical address. Defaults to None.
            tax_id (Optional[str], optional): Tax identification number. Defaults to None.
        """
        self.name = name
        self.contact_name = contact_name
        self.email = email
        self.phone = phone
        self.address = address
        self.tax_id = tax_id

        # Default initialization
        self.rating = 0.0
        self.is_active = True
        self.credit_limit = 0.0

    def validate(self) -> bool:
        """
        Validate supplier data.

        Returns:
            bool: True if data is valid, False otherwise.
        """
        # Comprehensive validation
        if not self.name:
            return False

        # Email validation (basic)
        if self.email and '@' not in self.email:
            return False

        # Phone validation (basic)
        if self.phone and not self.phone.replace(' ', '').isdigit():
            return False

        return True

    def update_rating(self, new_rating: float) -> None:
        """
        Update supplier rating.

        Args:
            new_rating (float): New rating value.

        Raises:
            ValueError: If rating is out of valid range.
        """
        if not 0 <= new_rating <= 5:
            raise ValueError("Rating must be between 0 and 5")

        self.rating = new_rating

    def activate(self) -> None:
        """
        Activate the supplier.
        """
        self.is_active = True

    def deactivate(self) -> None:
        """
        Deactivate the supplier.
        """
        self.is_active = False

    def to_dict(self, exclude_fields: Optional[List[str]] = None, include_relationships: bool = False) -> Dict[
        str, Any]:
        """
        Convert Supplier to dictionary representation.

        Args:
            exclude_fields (Optional[List[str]], optional): Fields to exclude.
            include_relationships (bool, optional): Whether to include related entities.

        Returns:
            Dict[str, Any]: Dictionary of supplier attributes.
        """
        exclude_fields = exclude_fields or []

        supplier_dict = {
            'id': self.id,
            'name': self.name,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'tax_id': self.tax_id,
            'rating': self.rating,
            'is_active': self.is_active,
            'payment_terms': self.payment_terms,
            'credit_limit': self.credit_limit,
            'last_order_date': (self.last_order_date.isoformat()
                                if self.last_order_date else None)
        }

        # Remove excluded fields
        for field in exclude_fields:
            supplier_dict.pop(field, None)

        # Optionally include relationships
        if include_relationships:
            supplier_dict['products'] = [
                product.to_dict() for product in self.products
            ]
            supplier_dict['orders'] = [
                order.to_dict() for order in self.orders
            ]

        return supplier_dict