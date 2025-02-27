# database/models/hardware.py
"""
Hardware model module for the leatherworking store management system.

Defines classes for hardware items used in leatherworking.
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database.models.base import Base, BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


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


class HardwareFinish(enum.Enum):
    """Finish options for hardware items."""
    POLISHED = "polished"
    BRUSHED = "brushed"
    ANTIQUE = "antique"
    MATTE = "matte"
    CHROME = "chrome"
    NICKEL_PLATED = "nickel_plated"
    BRASS_PLATED = "brass_plated"
    GOLD_PLATED = "gold_plated"
    BLACK_OXIDE = "black_oxide"
    PAINTED = "painted"
    POWDER_COATED = "powder_coated"
    COPPER_PLATED = "copper_plated"
    SATIN = "satin"
    NATURAL = "natural"
    OTHER = "other"


class Hardware(Base, BaseModel):
    """Hardware item model for leatherworking projects."""
    __tablename__ = "hardware"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    hardware_type = Column(Enum(HardwareType), nullable=False)
    material = Column(Enum(HardwareMaterial), nullable=False)
    finish = Column(Enum(HardwareFinish), nullable=True)
    size = Column(Float, nullable=True)
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    minimum_stock_level = Column(Integer, default=5)
    corrosion_resistance = Column(Integer, default=5)  # Scale of 1-10
    load_capacity = Column(Float, nullable=True)  # In kilograms, for structural hardware
    supplier_id = Column(Integer, ForeignKey("supplier.id"), nullable=True)
    supplier = relationship("Supplier", back_populates="hardware_items")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
        return self.quantity < self.minimum_stock_level

    def update_stock(self, quantity_change: int) -> None:
        """
        Update the stock quantity.

        Args:
            quantity_change: Amount to change the quantity by (positive or negative)
        """
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            raise ValueError("Stock cannot be negative")

        self.quantity = new_quantity

    def calculate_hardware_performance(self) -> float:
        """
        Calculate a performance score for the hardware based on various factors.

        This is a composite score considering material quality, corrosion resistance,
        and load capacity if applicable.

        Returns:
            float: Performance score from 0-100
        """
        # Base score from corrosion resistance (0-50 points)
        base_score = (self.corrosion_resistance / 10) * 50

        # Material quality factor (0-30 points)
        material_scores = {
            HardwareMaterial.STAINLESS_STEEL: 30,
            HardwareMaterial.BRASS: 25,
            HardwareMaterial.STEEL: 20,
            HardwareMaterial.BRONZE: 20,
            HardwareMaterial.NICKEL: 18,
            HardwareMaterial.ALUMINUM: 15,
            HardwareMaterial.SILVER: 15,
            HardwareMaterial.GOLD: 10,  # Good for appearance, not durability
            HardwareMaterial.PLASTIC: 5,
            HardwareMaterial.OTHER: 10
        }
        material_score = material_scores.get(self.material, 10)

        # Finish quality factor (0-20 points)
        finish_scores = {
            HardwareFinish.POWDER_COATED: 20,
            HardwareFinish.CHROME: 18,
            HardwareFinish.NICKEL_PLATED: 16,
            HardwareFinish.BLACK_OXIDE: 15,
            HardwareFinish.BRASS_PLATED: 14,
            HardwareFinish.COPPER_PLATED: 14,
            HardwareFinish.GOLD_PLATED: 12,
            HardwareFinish.POLISHED: 10,
            HardwareFinish.BRUSHED: 10,
            HardwareFinish.SATIN: 8,
            HardwareFinish.MATTE: 7,
            HardwareFinish.ANTIQUE: 6,
            HardwareFinish.NATURAL: 5,
            HardwareFinish.PAINTED: 12,
            HardwareFinish.OTHER: 10
        }
        finish_score = finish_scores.get(self.finish, 5) if self.finish else 5

        # Calculate total score
        total_score = base_score + material_score + finish_score

        # Add load capacity bonus for structural hardware (up to 10 bonus points)
        if self.load_capacity and self.hardware_type in (HardwareType.BUCKLE, HardwareType.D_RING,
                                                         HardwareType.O_RING, HardwareType.CLASP):
            if self.load_capacity > 50:  # More than 50kg capacity
                total_score += 10
            elif self.load_capacity > 25:  # 25-50kg capacity
                total_score += 5
            elif self.load_capacity > 10:  # 10-25kg capacity
                total_score += 2

        # Cap at 100
        return min(total_score, 100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the hardware item to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the hardware item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hardware_type": self.hardware_type.value if self.hardware_type else None,
            "material": self.material.value if self.material else None,
            "finish": self.finish.value if self.finish else None,
            "size": self.size,
            "quantity": self.quantity,
            "price": self.price,
            "minimum_stock_level": self.minimum_stock_level,
            "corrosion_resistance": self.corrosion_resistance,
            "load_capacity": self.load_capacity,
            "supplier_id": self.supplier_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }