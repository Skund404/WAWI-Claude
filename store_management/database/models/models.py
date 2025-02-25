# path: database/models/material.py
"""
Material model for the leatherworking store management application.

This module defines the database model for materials used in
leatherworking projects, such as leather, thread, adhesives, etc.
"""

import enum
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

# Import base classes without causing circular dependencies
from database.models.base import Base, BaseModel


class MaterialType(enum.Enum):
    """Enumeration of material types."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"


class LeatherType(enum.Enum):
    """Enumeration of leather types."""
    FULL_GRAIN = "full_grain"
    TOP_GRAIN = "top_grain"
    GENUINE = "genuine"
    SPLIT = "split"
    BONDED = "bonded"
    SYNTHETIC = "synthetic"
    EXOTIC = "exotic"
    OTHER = "other"


class MaterialQualityGrade(enum.Enum):
    """Enumeration of material quality grades."""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    SECONDS = "seconds"
    REMNANT = "remnant"


class Material(Base, BaseModel):
    """
    Model for materials used in leatherworking.

    This model represents all types of materials used in leatherworking projects,
    such as leather, thread, adhesives, etc.
    """
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Material categorization
    material_type = Column(Enum(MaterialType), nullable=False)

    # For leather materials
    leather_type = Column(Enum(LeatherType), nullable=True)
    quality_grade = Column(Enum(MaterialQualityGrade), nullable=True)
    thickness = Column(Float, nullable=True)  # in mm

    # Inventory
    in_stock = Column(Boolean, default=True)
    quantity = Column(Float, default=0)
    unit = Column(String(20), default="piece")  # piece, meter, sq_foot, etc.
    min_stock_level = Column(Float, default=5)
    reorder_quantity = Column(Float, default=10)

    # Location
    location = Column(String(100), nullable=True)

    # Supplier information
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier_sku = Column(String(100), nullable=True)
    supplier = relationship("Supplier", backref="materials")

    # Pricing
    cost_per_unit = Column(Float, nullable=True)

    # Sustainability and impact
    eco_friendly = Column(Boolean, default=False)
    carbon_footprint = Column(Float, nullable=True)  # in kg CO2e per unit

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """
        Return a string representation of the material.

        Returns:
            str: String representation with id, name, and type
        """
        return f"<Material(id={self.id}, name='{self.name}', type={self.material_type})>"

    def calculate_sustainability_impact(self) -> Dict[str, float]:
        """
        Calculate the sustainability impact metrics.

        Returns:
            Dict[str, float]: Dictionary of sustainability metrics
        """
        return {
            "carbon_footprint": self.carbon_footprint or 0,
            "eco_friendly": 1 if self.eco_friendly else 0
        }

    def is_low_stock(self) -> bool:
        """
        Check if the material is low in stock.

        Returns:
            bool: True if the quantity is below the minimum stock level
        """
        return self.quantity <= self.min_stock_level

    def update_stock(self, quantity_change: float) -> None:
        """
        Update the stock quantity.

        Args:
            quantity_change: Amount to change the quantity by (positive or negative)
        """
        self.quantity += quantity_change
        if self.quantity < 0:
            self.quantity = 0

        self.in_stock = self.quantity > 0

        # Trigger reorder if needed
        if self.is_low_stock():
            self._trigger_reorder()

    def _trigger_reorder(self) -> None:
        """
        Trigger a reorder for this material.

        This is a placeholder method that would typically
        interact with the ordering system.
        """
        pass  # In a real implementation, this would create a reorder request