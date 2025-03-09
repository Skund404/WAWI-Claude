# database/models/material.py
from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from sqlalchemy import and_, text
from typing import List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError, CostingMixin
from database.models.enums import (
    MaterialType, LeatherType, HardwareType,
    MeasurementUnit, QualityGrade
)


class Material(AbstractBase, ValidationMixin, CostingMixin):
    """
    Base class for all materials using single table inheritance.

    Attributes:
        name: Material name
        material_type: Discriminator field for polymorphic identity
        unit: Measurement unit for the material
        quality: Quality grade
        supplier_id: Foreign key to the supplier
    """
    __tablename__ = 'materials'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    unit: Mapped[Optional[MeasurementUnit]] = mapped_column(Enum(MeasurementUnit), nullable=True)
    quality: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade), nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Polymorphic identity setup
    __mapper_args__ = {
        'polymorphic_on': material_type,
        'polymorphic_identity': 'generic'
    }

    # Relationships
    supplier = relationship("Supplier", back_populates="materials")
    purchase_items = relationship("PurchaseItem",
                                  primaryjoin="and_(Material.id==PurchaseItem.item_id, PurchaseItem.item_type=='material')",
                                  back_populates="material")
    picking_list_items = relationship("PickingListItem", back_populates="material")
    component_materials = relationship("ComponentMaterial", back_populates="material")

    # Fixed inventory relationship with proper foreign key annotation
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Material.id==Inventory.item_id, Inventory.item_type=='material')",
        foreign_keys="[Inventory.item_id]",
        back_populates="material",
        uselist=False
    )
    def __init__(self, **kwargs):
        """Initialize a Material instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate material data."""
        if not self.name:
            raise ModelValidationError("Material name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Material name cannot exceed 255 characters")


class Leather(Material):
    """
    Leather material subclass.

    Additional Attributes:
        leather_type: Type of leather
        thickness: Thickness in mm
        area: Surface area in square feet
    """
    leather_type: Mapped[Optional[LeatherType]] = mapped_column(Enum(LeatherType), nullable=True)
    thickness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_full_hide: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': MaterialType.LEATHER
    }

    def validate(self):
        """Validate leather data."""
        super().validate()

        if self.thickness is not None and self.thickness <= 0:
            raise ModelValidationError("Leather thickness must be positive")

        if self.area is not None and self.area <= 0:
            raise ModelValidationError("Leather area must be positive")


class Hardware(Material):
    """
    Hardware material subclass.

    Additional Attributes:
        hardware_type: Type of hardware
        hardware_material: Material the hardware is made of
        finish: Surface finish
        size: Size specification
    """
    hardware_type: Mapped[Optional[HardwareType]] = mapped_column(Enum(HardwareType), nullable=True)
    hardware_material: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    finish: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': MaterialType.HARDWARE
    }


class Thread(Material):
    """
    Thread material subclass.

    Additional Attributes:
        color: Thread color
        thickness: Thread thickness/weight
        material_composition: Thread material (e.g., polyester, nylon)
    """
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thickness: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material_composition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': MaterialType.THREAD
    }