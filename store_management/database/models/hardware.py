# database/models/hardware.py

from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.base import BaseModel


class HardwareType(Enum):
    """Enumeration of hardware types."""
    BUCKLE = "buckle"
    SNAP = "snap"
    ZIPPER = "zipper"
    D_RING = "d_ring"
    RIVET = "rivet"
    MAGNETIC_CLASP = "magnetic_clasp"
    BUTTON = "button"
    OTHER = "other"


class HardwareMaterial(Enum):
    """Enumeration of hardware materials."""
    BRASS = "brass"
    STEEL = "steel"
    NICKEL = "nickel"
    ZINC = "zinc"
    ALUMINUM = "aluminum"
    COPPER = "copper"
    BRONZE = "bronze"
    OTHER = "other"


class Hardware(BaseModel):
    """
    Hardware model representing metal fixtures and accessories used in leatherworking,
    including stock management and specifications.
    """
    __tablename__ = 'hardware'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    hardware_type = Column(SQLEnum(HardwareType), nullable=False)
    material = Column(SQLEnum(HardwareMaterial), nullable=False)

    # Specifications
    finish = Column(String(50))  # e.g., antique brass, nickel plated
    size = Column(String(50))  # e.g., 10mm, 1/2 inch
    weight = Column(Float)  # in grams
    load_capacity = Column(Float)  # in kg, for load-bearing hardware

    # Stock management
    quantity = Column(Integer, default=0)
    minimum_stock = Column(Integer)
    reorder_point = Column(Integer)
    unit_price = Column(Float)

    # Supplier information
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier_sku = Column(String(50))

    # Status and tracking
    is_active = Column(Boolean, default=True)
    location = Column(String(50))
    notes = Column(String(500))

    # Relationships
    supplier = relationship("Supplier", back_populates="hardware_items")
    project_components = relationship("ProjectComponent", back_populates="hardware")

    def __repr__(self) -> str:
        """String representation of the Hardware item."""
        return f"<Hardware(id={self.id}, name='{self.name}', type={self.hardware_type})>"

    def is_low_stock(self) -> bool:
        """
        Check if the hardware item is at or below its reorder point.

        Returns:
            bool: True if stock is low, False otherwise
        """
        return self.quantity <= self.reorder_point

    def update_stock(self, quantity_change: int) -> None:
        """
        Update the hardware stock level.

        Args:
            quantity_change (int): Amount to change stock by (positive or negative)

        Raises:
            ValueError: If resulting quantity would be negative
        """
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            raise ValueError(f"Cannot reduce stock below zero. Current stock: {self.quantity}")

        self.quantity = new_quantity

        # Trigger reorder check
        if self.is_low_stock():
            # Implement reorder logic or notification system
            pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the hardware item to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the hardware item
        """
        base_dict = super().to_dict()
        # Add enum string values
        base_dict.update({
            'hardware_type': self.hardware_type.value,
            'material': self.material.value
        })
        return base_dict