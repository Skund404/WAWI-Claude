"""
Supplier model definition.
"""

import logging
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from typing import Optional, List, Dict, Any

from .base import BaseModel
from .enums import MaterialQualityGrade


logger = logging.getLogger(__name__)


class Supplier(BaseModel):
    """
    Model for suppliers.

    Attributes:
        id (int): Primary key
        name (str): Supplier name
        notes (str): Additional notes about supplier
        rating (MaterialQualityGrade): Supplier quality rating
        parts (List[Part]): Related parts
        leathers (List[Leather]): Related leather materials
    """

    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    notes = Column(String(500), nullable=True)  # Allow null
    rating = Column(SQLEnum(MaterialQualityGrade), nullable=True)  # Allow null

    # Relationships
    parts = relationship("Part", back_populates="supplier")
    leathers = relationship("Leather", back_populates="supplier")

    def __init__(self, name: str, notes: Optional[str] = None,
                 rating: Optional[MaterialQualityGrade] = None):
        """
        Initialize a new supplier.

        Args:
            name: Supplier name
            notes: Optional additional notes
            rating: Optional quality rating
        """
        self.name = name
        self.notes = notes
        self.rating = rating

    def __repr__(self) -> str:
        """Return string representation of the supplier."""
        return f"<Supplier(id={self.id}, name='{self.name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert supplier to dictionary representation.

        Returns:
            Dictionary containing supplier data
        """
        return {
            'id': self.id,
            'name': self.name,
            'notes': self.notes,
            'rating': self.rating.value if self.rating else None
        }