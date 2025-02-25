# database/models/hardware.py
"""
Hardware model module for the leatherworking store management system.

Defines classes for hardware items used in leatherworking.
"""

import enum
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel


class HardwareType(enum.Enum):
    """Enumeration of hardware types."""
    BUCKLE = "buckle"
    SNAP = "snap"
    RIVET = "rivet"
    ZIPPER = "zipper"
    CLASP = "clasp"
    BUTTON = "button"
    D_RING = "d_ring"
    O_RING = "o_ring"
    MAGNETIC_CLOSURE = "magnetic_closure"
    OTHER = "other"


class HardwareMaterial(enum.Enum):
    """Enumeration of hardware materials."""
    BRASS = "brass"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    NICKEL = "nickel"
    SILVER = "silver"
    GOLD = "gold"
    BRONZE = "bronze"
    ALUMINUM = "aluminum"
    PLASTIC = "plastic"
    OTHER = "other"


class Hardware(Base, BaseModel):
    """
    Model for hardware items used in leatherworking.

    This model represents physical hardware components like buckles,
    rivets, snaps, etc. that are used in leatherworking projects.
    """
    __tablename__ = 'hardware'

    name = Column(String(255), nullable=False)
    hardware_type = Column(Enum(HardwareType), nullable=False)
    material = Column(Enum(HardwareMaterial), nullable=True)

    # Inventory tracking
    current_quantity = Column(Integer, default=0, nullable=False)
    minimum_quantity = Column(Integer, default=1, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)

    # Physical properties
    dimensions = Column(String(100), nullable=True)  # e.g., "25mm x 15mm"
    weight = Column(Float, nullable=True)  # in grams
    color = Column(String(50), nullable=True)
    finish = Column(String(50), nullable=True)

    # Supplier information
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=True)
    supplier = relationship("Supplier", backref="hardware_items")

    # Product information
    sku = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """
        Return a string representation of the hardware item.

        Returns:
            str: String representation with id, name, and type
        """
        return f"<Hardware id={self.id}, name='{self.name}', type={self.hardware_type.name}>"

    def is_low_stock(self) -> bool:
        """
        Check if the hardware is low in stock.

        Returns:
            bool: True if the quantity is below the minimum stock level
        """
        return self.current_quantity < self.minimum_quantity

    def update_stock(self, quantity_change: int) -> None:
        """
        Update the stock quantity.

        Args:
            quantity_change: Amount to change the quantity by (positive or negative)
        """
        new_quantity = self.current_quantity + quantity_change
        if new_quantity < 0:
            raise ValueError("Stock cannot be negative")

        self.current_quantity = new_quantity

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the hardware to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the hardware
        """
        result = super().to_dict()
        result['hardware_type'] = self.hardware_type.name
        if self.material:
            result['material'] = self.material.name
        result['supplier'] = self.supplier.name if self.supplier else None
        return result