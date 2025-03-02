# database/models/supplier.py
"""
Supplier model module for the leatherworking store management system.

Defines the Supplier class for tracking suppliers of materials.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Enum, Text, DateTime
)
from sqlalchemy.orm import relationship

from database.models.base import Base
from database.models.enums import SupplierStatus


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if email is valid, False otherwise
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone (str): Phone number to validate

    Returns:
        bool: True if phone number is valid, False otherwise
    """
    # Remove any non-digit characters
    cleaned_phone = re.sub(r'\D', '', phone)
    return len(cleaned_phone) >= 10 and len(cleaned_phone) <= 15


class Supplier(Base):
    """
    Model for suppliers of leatherworking materials and tools.

    This model represents businesses that supply the leatherworking
    operation with leather, hardware, tools, and other materials.
    """
    __tablename__ = 'suppliers'

    # Basic information
    name = Column(String(255), nullable=False)
    contact_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)

    # Business relationship data
    account_number = Column(String(50), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Performance tracking
    rating = Column(Float, default=0.0)  # 0-5 scale
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE)
    last_order_date = Column(DateTime, nullable=True)

    # Relationships
    materials = relationship("Material", back_populates="supplier")
    parts = relationship("Part", back_populates="supplier")
    leathers = relationship("Leather", back_populates="supplier")
    hardware_items = relationship("Hardware", back_populates="supplier")
    orders = relationship("Order", back_populates="supplier")

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate data before creating a supplier.

        Args:
            data (Dict[str, Any]): Data to validate

        Raises:
            ModelValidationError: If validation fails
        """
        # Validate name
        if not data.get('name'):
            raise ValueError("Supplier name is required")

        # Validate email if provided
        if data.get('email'):
            if not is_valid_email(data['email']):
                raise ValueError(f"Invalid email format: {data['email']}")

        # Validate phone if provided
        if data.get('phone'):
            if not is_valid_phone(data['phone']):
                raise ValueError(f"Invalid phone number format: {data['phone']}")

        # Validate rating if provided
        if 'rating' in data:
            if not (0 <= data['rating'] <= 5):
                raise ValueError("Rating must be between 0 and 5")

    def _validate_update(self, update_data: Dict[str, Any]) -> None:
        """
        Validate data before updating a supplier.

        Args:
            update_data (Dict[str, Any]): Data to validate

        Raises:
            ModelValidationError: If validation fails
        """
        # Validate email if provided
        if 'email' in update_data:
            if not is_valid_email(update_data['email']):
                raise ValueError(f"Invalid email format: {update_data['email']}")

        # Validate phone if provided
        if 'phone' in update_data:
            if not is_valid_phone(update_data['phone']):
                raise ValueError(f"Invalid phone number format: {update_data['phone']}")

        # Validate rating if provided
        if 'rating' in update_data:
            if not (0 <= update_data['rating'] <= 5):
                raise ValueError("Rating must be between 0 and 5")

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert supplier to dictionary with enhanced details.

        Args:
            include_relationships (bool): Whether to include relationship data

        Returns:
            Dict[str, Any]: Dictionary representation of the supplier
        """
        result = super().to_dict(include_relationships)

        # Round rating to 2 decimal places
        if 'rating' in result:
            result['rating'] = round(result['rating'], 2)

        # Format last order date if exists
        if result.get('last_order_date'):
            result['last_order_date'] = (
                datetime.fromisoformat(result['last_order_date']).strftime('%Y-%m-%d')
                if result['last_order_date'] else None
            )

        # Add additional derived information
        if include_relationships:
            result['total_materials'] = len(self.materials)
            result['total_leathers'] = len(self.leathers)
            result['total_hardware_items'] = len(self.hardware_items)

        return result

    def update_rating(self, new_rating: float) -> None:
        """
        Update the supplier's rating.

        Args:
            new_rating (float): New rating value (0-5)
        """
        if 0 <= new_rating <= 5:
            self.rating = new_rating
        else:
            raise ValueError("Rating must be between 0 and 5")

    def get_materials(self) -> List[Any]:
        """
        Get all materials supplied by this supplier.

        Returns:
            List[Any]: List of materials from this supplier
        """
        return self.materials

    def get_parts(self) -> List[Any]:
        """
        Get all parts supplied by this supplier.

        Returns:
            List[Any]: List of parts from this supplier
        """
        return self.parts