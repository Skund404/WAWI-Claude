# database/models/leather.py

"""
Leather model definition.
"""

import logging
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from typing import Optional, List, Dict, Any
from database.base import BaseModel
from .base import BaseModel
from .enums import LeatherType, MaterialQualityGrade

logger = logging.getLogger(__name__)


class Leather(BaseModel):
    """
    Model for leather inventory.

    Attributes:
        id (int): Primary key
        name (str): Leather name/identifier
        leather_type (LeatherType): Type of leather
        quality_grade (MaterialQualityGrade): Quality grade
        area (float): Current area available
        minimum_area (float): Minimum area before reorder
        supplier_id (int): Foreign key to supplier
        transactions (List[LeatherTransaction]): Related transactions
        supplier (Supplier): Related supplier
    """

    __tablename__ = 'leather'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    leather_type = Column(SQLEnum(LeatherType), nullable=False)
    quality_grade = Column(SQLEnum(MaterialQualityGrade), nullable=False)
    area = Column(Float, default=0)
    minimum_area = Column(Float, default=0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))

    # Relationships
    transactions = relationship("LeatherTransaction", back_populates="leather",
                                cascade="all, delete-orphan")
    supplier = relationship("Supplier", back_populates="leathers")

    def __init__(self, name: str, leather_type: LeatherType,
                 quality_grade: MaterialQualityGrade, area: float = 0,
                 minimum_area: float = 0):
        """
        Initialize a new leather instance.

        Args:
            name: Leather name/identifier
            leather_type: Type of leather
            quality_grade: Quality grade
            area: Initial area available
            minimum_area: Minimum area before reorder
        """
        self.name = name
        self.leather_type = leather_type
        self.quality_grade = quality_grade
        self.area = area
        self.minimum_area = minimum_area

    def __repr__(self) -> str:
        """Return string representation of the leather."""
        return (f"<Leather(id={self.id}, name='{self.name}', "
                f"type={self.leather_type.name}, area={self.area})>")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert leather instance to dictionary representation.

        Returns:
            Dictionary containing leather data
        """
        return {
            'id': self.id,
            'name': self.name,
            'leather_type': self.leather_type.name,
            'quality_grade': self.quality_grade.name,
            'area': self.area,
            'minimum_area': self.minimum_area,
            'supplier_id': self.supplier_id
        }

    def needs_reorder(self) -> bool:
        """
        Check if leather needs to be reordered.

        Returns:
            True if area is at or below minimum area
        """
        return self.area <= self.minimum_area