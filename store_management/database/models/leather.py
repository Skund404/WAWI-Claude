# database/models/leather.py
"""
Leather model module for the leatherworking store management system.

Defines the Leather class for tracking leather inventory.
"""

import datetime
from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import LeatherType, MaterialQualityGrade, InventoryStatus


class Leather(Base, BaseModel):
    """
    Model for leather materials used in leatherworking.

    This model represents leather materials with detailed properties
    specific to leatherworking, tracked by area rather than count.
    """
    __tablename__ = 'leather'

    name = Column(String(255), nullable=False)
    leather_type = Column(Enum(LeatherType), nullable=False)
    quality_grade = Column(Enum(MaterialQualityGrade), nullable=False)

    # Inventory tracking by area
    current_area = Column(Float, default=0.0, nullable=False)  # in square feet/meters
    minimum_area = Column(Float, default=1.0, nullable=False)
    thickness = Column(Float, nullable=True)  # in mm
    unit_cost_per_area = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)

    # Color and finish properties
    color = Column(String(50), nullable=True)
    finish = Column(String(50), nullable=True)

    # Supplier relationship
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="leathers")

    # Related components
    components = relationship("ProjectComponent", back_populates="leather")

    def __init__(self, name: str, leather_type: LeatherType,
                 quality_grade: MaterialQualityGrade,
                 current_area: float, minimum_area: float, **kwargs):
        """
        Initialize a new leather material.

        Args:
            name: Name of the leather
            leather_type: Type of leather
            quality_grade: Quality grade of the leather
            current_area: Current available area
            minimum_area: Minimum area threshold for reordering
        """
        super().__init__(**kwargs)  # Initialize the BaseModel
        self.name = name
        self.leather_type = leather_type
        self.quality_grade = quality_grade
        self.current_area = current_area
        self.minimum_area = minimum_area

    def __repr__(self) -> str:
        """
        Return a string representation of the leather.

        Returns:
            str: String representation with id, name, and type
        """
        return f"<Leather id={self.id}, name='{self.name}', type={self.leather_type.name}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the leather to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the leather
        """
        result = super().to_dict()
        result['leather_type'] = self.leather_type.name
        result['quality_grade'] = self.quality_grade.name
        result['supplier'] = self.supplier.name if self.supplier else None
        return result

    def needs_reorder(self) -> bool:
        """
        Check if the leather needs to be reordered.

        Returns:
            bool: True if the area is below the minimum threshold
        """
        return self.current_area < self.minimum_area

    def update_area(self, area_change: float) -> None:
        """
        Update the available area.

        Args:
            area_change: Amount to change the area by (positive or negative)
        """
        new_area = self.current_area + area_change
        if new_area < 0:
            raise ValueError("Area cannot be negative")

        self.current_area = new_area
        self._update_status()

    def _update_status(self) -> None:
        """
        Update the inventory status based on current area.
        """
        if self.current_area <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.current_area < self.minimum_area:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

    def calculate_value(self) -> float:
        """
        Calculate the current value of the leather.

        Returns:
            float: Current value based on area and cost per unit area
        """
        return self.current_area * self.unit_cost_per_area