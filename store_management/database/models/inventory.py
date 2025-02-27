# Path: database/models/inventory.py
"""
Inventory Model for Leatherworking Store Management.

Defines the database model for tracking inventory items.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from database.models.base import Base, BaseModel
from database.models.enums import MaterialType, MeasurementUnit
from database.models.mixins import TimestampMixin, TrackingMixin


class Inventory(Base, BaseModel, TimestampMixin, TrackingMixin):
    """
    Represents an inventory item in the leatherworking store management system.

    Attributes:
        id (int): Unique identifier for the inventory item
        material_type (MaterialType): Type of material
        name (str): Name or description of the inventory item
        quantity (float): Current quantity in stock
        unit_of_measurement (MeasurementUnit): Unit for measuring the item
        unit_price (float): Price per unit
        location (str, optional): Storage location of the item
        minimum_stock_level (float, optional): Minimum recommended stock level
        last_adjusted_at (DateTime, optional): Timestamp of last stock adjustment
        last_adjustment_reason (str, optional): Reason for last stock adjustment
    """
    __tablename__ = 'inventory'

    # Basic item identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_type = Column(Enum(MaterialType), nullable=False)
    name = Column(String(255), nullable=False)

    # Quantity and pricing
    quantity = Column(Float, nullable=False, default=0.0)
    unit_of_measurement = Column(Enum(MeasurementUnit), nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)

    # Optional tracking fields
    location = Column(String(255), nullable=True)
    minimum_stock_level = Column(Float, nullable=True)

    # Tracking stock adjustments
    last_adjusted_at = Column(DateTime, nullable=True, onupdate=func.now())
    last_adjustment_reason = Column(String(255), nullable=True)

    def __repr__(self):
        """
        String representation of the Inventory item.

        Returns:
            str: Descriptive string of the inventory item
        """
        return (
            f"<Inventory(id={self.id}, "
            f"material_type={self.material_type}, "
            f"name='{self.name}', "
            f"quantity={self.quantity}, "
            f"unit_price={self.unit_price})>"
        )

    def to_dict(self) -> dict:
        """
        Convert the Inventory item to a dictionary representation.

        Returns:
            dict: Dictionary representation of the inventory item
        """
        return {
            'id': self.id,
            'material_type': self.material_type.name if self.material_type else None,
            'name': self.name,
            'quantity': self.quantity,
            'unit_of_measurement': self.unit_of_measurement.name if self.unit_of_measurement else None,
            'unit_price': self.unit_price,
            'location': self.location,
            'minimum_stock_level': self.minimum_stock_level,
            'last_adjusted_at': self.last_adjusted_at,
            'last_adjustment_reason': self.last_adjustment_reason,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }