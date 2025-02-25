# database/models/supplier.py
"""
Supplier model module for the leatherworking store management system.

Defines the Supplier class for tracking suppliers of materials.
"""

import enum
import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import SupplierStatus


class Supplier(Base, BaseModel):
    """
    Model for suppliers of leatherworking materials and tools.

    This model represents businesses that supply the leatherworking
    operation with leather, hardware, tools, and other materials.
    """
    __tablename__ = 'supplier'

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
    orders = relationship("Order", back_populates="supplier")

    def __init__(self, name: str, notes: Optional[str] = None, rating: float = 0.0, **kwargs):
        """
        Initialize a new supplier.

        Args:
            name: Name of the supplier
            notes: Additional notes about the supplier
            rating: Supplier rating (0-5 scale)
        """
        super().__init__(**kwargs)  # Initialize the BaseModel
        self.name = name
        self.notes = notes
        self.rating = rating

    def __repr__(self) -> str:
        """
        Return a string representation of the supplier.

        Returns:
            str: String representation with id and name
        """
        return f"<Supplier id={self.id}, name='{self.name}'>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the supplier to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the supplier
        """
        result = super().to_dict()
        return result

    def update_rating(self, new_rating: float) -> None:
        """
        Update the supplier's rating.

        Args:
            new_rating: New rating value (0-5)
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