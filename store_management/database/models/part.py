# database/models/part.py
"""
Part model module for the leatherworking store management system.

Defines the Part class for tracking non-leather inventory components.
"""

import datetime
from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import InventoryStatus


class Part(Base, BaseModel):
    """
    Model for hardware parts and small items used in leatherworking.

    This model represents non-leather components like buckles, rivets,
    snaps, zippers, etc. that are tracked by count rather than area.
    """
    __tablename__ = 'part'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    part_number = Column(String(50), unique=True, nullable=True)

    # Inventory tracking
    current_quantity = Column(Float, default=0.0, nullable=False)
    minimum_quantity = Column(Float, default=1.0, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)

    # Supplier relationship
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="parts")

    # Related components
    components = relationship("ProjectComponent", back_populates="part")

    def __repr__(self) -> str:
        """
        Return a string representation of the part.

        Returns:
            str: String representation with id, name, and type
        """
        return f"<Part id={self.id}, name='{self.name}'>"

    def is_low_stock(self) -> bool:
        """
        Check if the part is low in stock.

        Returns:
            bool: True if the quantity is below the minimum stock level
        """
        return self.current_quantity < self.minimum_quantity

    def is_out_of_stock(self) -> bool:
        """
        Check if the part is out of stock.

        Returns:
            bool: True if the quantity is zero
        """
        return self.current_quantity <= 0

    def update_stock(self, quantity_change: float) -> None:
        """
        Update the stock quantity.

        Args:
            quantity_change: Amount to change the quantity by (positive or negative)
        """
        new_quantity = self.current_quantity + quantity_change
        if new_quantity < 0:
            raise ValueError("Stock cannot be negative")

        self.current_quantity = new_quantity
        self._update_status()

    def _update_status(self) -> None:
        """Update the inventory status based on current quantity."""
        if self.current_quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.current_quantity < self.minimum_quantity:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the part to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the part
        """
        result = super().to_dict()
        result['supplier'] = self.supplier.name if self.supplier else None
        return result