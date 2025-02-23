# database/models/material.py

from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from database.base import BaseModel



class MaterialType(Enum):
    """Enumeration of possible material types."""
    LEATHER = "leather"
    THREAD = "thread"
    HARDWARE = "hardware"
    ADHESIVE = "adhesive"
    FINISH = "finish"
    OTHER = "other"


class LeatherType(Enum):
    """Enumeration of leather types."""
    FULL_GRAIN = "full_grain"
    TOP_GRAIN = "top_grain"
    GENUINE = "genuine"
    SUEDE = "suede"
    NUBUCK = "nubuck"
    EXOTIC = "exotic"


class MaterialQualityGrade(Enum):
    """Enumeration of material quality grades."""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    SECONDS = "seconds"


class Material(BaseModel):
    """
    Material model representing inventory materials with their properties
    and stock management attributes.
    """
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    material_type = Column(SQLEnum(MaterialType), nullable=False)

    # For leather materials
    leather_type = Column(SQLEnum(LeatherType))
    quality_grade = Column(SQLEnum(MaterialQualityGrade))
    thickness = Column(Float)  # in mm

    # Stock management
    quantity = Column(Float, default=0)
    unit = Column(String(20))  # e.g., sq ft, meters, pieces
    minimum_stock = Column(Float)
    reorder_point = Column(Float)

    # Pricing and supplier info
    cost_per_unit = Column(Float)
    supplier_id = Column(Integer)
    supplier_sku = Column(String(50))

    # Status and tracking
    is_active = Column(Boolean, default=True)
    location = Column(String(50))
    notes = Column(String(500))

    def __repr__(self) -> str:
        """String representation of the Material."""
        return f"<Material(id={self.id}, name='{self.name}', type={self.material_type})>"

    def calculate_sustainability_impact(self) -> Dict[str, float]:
        """
        Calculate the environmental impact metrics for this material.

        Returns:
            Dict[str, float]: Dictionary containing sustainability metrics
        """
        # Implement sustainability calculations based on material type and usage
        impact_factors = {
            "carbon_footprint": 0.0,
            "water_usage": 0.0,
            "recyclability": 0.0
        }

        # Base calculations - should be expanded based on specific materials
        if self.material_type == MaterialType.LEATHER:
            impact_factors["carbon_footprint"] = self.quantity * 2.5  # example factor
            impact_factors["water_usage"] = self.quantity * 4.0  # example factor
            impact_factors["recyclability"] = 0.7  # example factor

        return impact_factors

    def is_low_stock(self) -> bool:
        """
        Check if the material is at or below its reorder point.

        Returns:
            bool: True if stock is low, False otherwise
        """
        return self.quantity <= self.reorder_point

    def update_stock(self, quantity_change: float) -> None:
        """
        Update the material stock level.

        Args:
            quantity_change (float): Amount to change stock by (positive or negative)

        Raises:
            ValueError: If new quantity would be negative
        """
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            raise ValueError("Cannot reduce stock below zero")

        self.quantity = new_quantity
        self._trigger_reorder()

    def _trigger_reorder(self) -> None:
        """
        Internal method to check and trigger reorder if stock is low.
        Should be called after stock updates.
        """
        if self.is_low_stock():
            # Implement reorder logic here
            # Could emit signals or trigger notifications
            pass