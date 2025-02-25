# database/models/hardware.py
"""
Hardware-related models and enumerations.
"""

from enum import Enum, auto
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel, Base


class HardwareType(str, Enum):
    """
    Enumeration of different hardware types.
    """
    BUCKLE = 'buckle'
    SNAP = 'snap'
    ZIPPER = 'zipper'
    D_RING = 'd_ring'
    RIVET = 'rivet'
    MAGNETIC_CLASP = 'magnetic_clasp'
    BUTTON = 'button'
    OTHER = 'other'


class HardwareMaterial(str, Enum):
    """
    Enumeration of hardware materials.
    """
    BRASS = 'brass'
    STEEL = 'steel'
    NICKEL = 'nickel'
    ZINC = 'zinc'
    ALUMINUM = 'aluminum'
    COPPER = 'copper'
    BRONZE = 'bronze'
    OTHER = 'other'


class Hardware(BaseModel, Base):
    """
    Model representing hardware items in the inventory.
    """
    __tablename__ = 'hardware'

    # Basic hardware attributes
    name = Column(String, nullable=False)
    hardware_type = Column(String, nullable=False)  # Using HardwareType
    material = Column(String, nullable=False)  # Using HardwareMaterial

    # Quantity and pricing
    quantity = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)

    # Optional relationships
    supplier_id = Column(ForeignKey('suppliers.id'), nullable=True)
    supplier = relationship('Supplier', back_populates='hardware')

    def __repr__(self) -> str:
        """
        String representation of the hardware.

        Returns:
            str: A string describing the hardware
        """
        return (
            f"<Hardware(id={self.id}, "
            f"name='{self.name}', "
            f"type='{self.hardware_type}', "
            f"material='{self.material}', "
            f"quantity={self.quantity})>"
        )

    @classmethod
    def create_hardware(cls, data: Dict[str, Any]) -> 'Hardware':
        """
        Create a new hardware instance.

        Args:
            data (Dict[str, Any]): Hardware creation data

        Returns:
            Hardware: A new hardware instance
        """
        # Validate hardware type
        if data.get('hardware_type') not in HardwareType.__members__:
            raise ValueError(f"Invalid hardware type: {data.get('hardware_type')}")

        # Validate hardware material
        if data.get('material') not in HardwareMaterial.__members__:
            raise ValueError(f"Invalid hardware material: {data.get('material')}")

        return cls(**data)


def validate_hardware_data(hardware_data: Dict[str, Any]) -> bool:
    """
    Validate hardware data against predefined constraints.

    Args:
        hardware_data (Dict[str, Any]): Hardware data to validate

    Returns:
        bool: Whether the hardware data is valid
    """
    # Check required fields
    required_fields = ['name', 'hardware_type', 'material']
    if not all(field in hardware_data for field in required_fields):
        return False

    # Validate hardware type
    if hardware_data['hardware_type'] not in HardwareType.__members__:
        return False

    # Validate material
    if hardware_data['material'] not in HardwareMaterial.__members__:
        return False

    # Additional validation can be added here
    return True