# database/models/pattern.py
"""
Pattern model module for the leatherworking store management system.

Defines the Pattern class for tracking product patterns.
"""

import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Enum
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import SkillLevel


class Pattern(Base, BaseModel):
    """
    Represents a leatherworking pattern.
    """
    __tablename__ = 'patterns'  # Changed to plural for consistency

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty_level = Column(Enum(SkillLevel), nullable=True)

    # Pattern metadata
    estimated_time = Column(Integer, nullable=True)  # in minutes
    estimated_cost = Column(Float, nullable=True)
    materials_needed = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    version = Column(String(20), nullable=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="pattern")
    projects = relationship("Project", back_populates="pattern")

    def __repr__(self) -> str:
        """
        String representation of the Pattern.

        Returns:
            str: Descriptive string of the pattern
        """
        return f"<Pattern id={self.id}, name='{self.name}', difficulty='{self.difficulty_level.name if self.difficulty_level else 'N/A'}'>"

    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Convert pattern to dictionary representation.

        Args:
            include_details (bool): Whether to include additional details

        Returns:
            Dict[str, Any]: Dictionary representation of the pattern
        """
        result = super().to_dict()
        result['created_at'] = self.created_at.isoformat() if self.created_at else None

        if include_details:
            result['products_count'] = len(self.products)
            result['projects_count'] = len(self.projects)

        return result

    def update_version(self, new_version: str) -> None:
        """
        Update the pattern version.

        Args:
            new_version (str): New version number
        """
        self.version = new_version
        # Optionally, you could add timestamp or other version tracking logic here

    def get_related_products(self) -> List[Any]:
        """
        Get all products using this pattern.

        Returns:
            List[Any]: List of related products
        """
        return self.products