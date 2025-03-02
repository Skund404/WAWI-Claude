# database/models/material.py
"""
Material model module for the leatherworking store management system.

Defines the Material class for tracking inventory materials.
"""

from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, Float, ForeignKey, Enum,
    Text, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base
from database.models.enums import (
    MaterialType, MaterialQualityGrade, InventoryStatus
)


class Material(Base):
    """
    Represents a generic material in the inventory.
    """
    __tablename__ = 'materials'

    # Basic material information
    name = Column(String(255), nullable=False)
    material_type = Column(Enum(MaterialType), nullable=False)

    # Supplier relationship
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="materials")

    # Inventory tracking
    price_per_unit = Column(Float, nullable=False)
    units_in_stock = Column(Float, default=0.0)
    reorder_level = Column(Float, nullable=True)
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)

    # Optional location tracking
    location_id = Column(Integer, ForeignKey('storage.id'), nullable=True)
    location = relationship("Storage", back_populates="materials")

    # Descriptive fields
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Optional timestamp tracking
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    project_components = relationship("ProjectComponent", back_populates="material")

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate data before creating a material.

        Args:
            data (Dict[str, Any]): Data to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate name
        if not data.get('name'):
            raise ValueError("Material name is required")

        # Validate material type
        if 'material_type' not in data:
            raise ValueError("Material type is required")

        try:
            MaterialType(data['material_type'])
        except ValueError:
            raise ValueError(f"Invalid material type: {data['material_type']}")

        # Validate price
        if 'price_per_unit' in data:
            if data['price_per_unit'] < 0:
                raise ValueError("Price per unit cannot be negative")

        # Validate stock
        if 'units_in_stock' in data:
            if data['units_in_stock'] < 0:
                raise ValueError("Units in stock cannot be negative")

        # Validate reorder level if provided
        if 'reorder_level' in data and data['reorder_level'] is not None:
            if data['reorder_level'] < 0:
                raise ValueError("Reorder level cannot be negative")

    def _validate_update(self, update_data: Dict[str, Any]) -> None:
        """
        Validate data before updating a material.

        Args:
            update_data (Dict[str, Any]): Data to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate price if updating
        if 'price_per_unit' in update_data:
            if update_data['price_per_unit'] < 0:
                raise ValueError("Price per unit cannot be negative")

        # Validate stock if updating
        if 'units_in_stock' in update_data:
            if update_data['units_in_stock'] < 0:
                raise ValueError("Units in stock cannot be negative")

        # Validate reorder level if updating
        if 'reorder_level' in update_data and update_data['reorder_level'] is not None:
            if update_data['reorder_level'] < 0:
                raise ValueError("Reorder level cannot be negative")

        # Validate material type if updating
        if 'material_type' in update_data:
            try:
                MaterialType(update_data['material_type'])
            except ValueError:
                raise ValueError(f"Invalid material type: {update_data['material_type']}")

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert material to dictionary with enhanced details.

        Args:
            include_relationships (bool): Whether to include relationship data

        Returns:
            Dict[str, Any]: Dictionary representation of the material
        """
        result = super().to_dict(include_relationships)

        # Format price and stock with 2 decimal places
        if 'price_per_unit' in result:
            result['price_per_unit'] = round(result['price_per_unit'], 2)
        if 'units_in_stock' in result:
            result['units_in_stock'] = round(result['units_in_stock'], 2)

        # Add additional derived information
        if include_relationships:
            result['total_project_components'] = len(self.project_components)

            # Include supplier name if available
            if self.supplier:
                result['supplier_name'] = self.supplier.name

        return result

    def update_stock(self, quantity_change: float) -> None:
        """
        Update the stock quantity and adjust status accordingly.

        Args:
            quantity_change (float): Positive or negative change in stock
        """
        self.units_in_stock += quantity_change

        # Update status based on stock level
        if self.units_in_stock <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.reorder_level and self.units_in_stock <= self.reorder_level:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK