# database/models/material.py
"""
This module defines the Material model and its subtypes for the leatherworking application.
"""
from __future__ import annotations
from sqlalchemy import Enum as SQLEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, CostingMixin, ModelValidationError, ValidationMixin
from database.models.enums import (
    HardwareFinish, HardwareMaterial, HardwareType, LeatherFinish,
    LeatherType, MaterialType, MeasurementUnit, QualityGrade
)

# Import the component_material_table (not the class)
from database.models.component_material import component_material_table


class Material(AbstractBase, ValidationMixin, CostingMixin):
    """
    Base class for all materials using single table inheritance.

    This is a polymorphic base class with material_type as the discriminator.
    """
    __tablename__ = 'materials'
    __table_args__ = {"extend_existing": True}

    # Basic attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    material_type: Mapped[MaterialType] = mapped_column(
        SQLEnum(MaterialType, native_enum=False),
        nullable=False
    )
    unit: Mapped[Optional[MeasurementUnit]] = mapped_column(Enum(MeasurementUnit))
    quality: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade))

    # Foreign keys
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    supplier = relationship(
        "Supplier",
        back_populates="materials",
        lazy="selectin"
    )

    # Relationship with components through junction table
    components = relationship(
        "Component",
        secondary="component_materials",
        back_populates="materials",
        overlaps="component",  # Changed to match exactly what's in the warning
        viewonly=True  # Making this side viewonly too to break all circular dependencies
    )

    # ORM relationship to ComponentMaterial for direct access
    component_materials = relationship(
        "ComponentMaterial",
        back_populates="material",
        overlaps="components"  # Add this parameter
    )

    # Relationship to inventory
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Material.id==Inventory.item_id, Inventory.item_type=='material')",
        foreign_keys="[Inventory.item_id]",
        back_populates="material",
        uselist=False,
        lazy="selectin",
        overlaps="inventory"  # Add this parameter
    )

    # Relationship to PickingListItem
    picking_list_items = relationship(
        "PickingListItem",
        back_populates="material",
        lazy="selectin"
    )

    # Relationship to PurchaseItem
    purchase_items = relationship(
        "PurchaseItem",
        primaryjoin="and_(Material.id==PurchaseItem.item_id, PurchaseItem.item_type=='material')",
        foreign_keys="[PurchaseItem.item_id]",
        back_populates="material",
        lazy="selectin"
    )

    __mapper_args__ = {
        'polymorphic_on': material_type,
        'polymorphic_identity': 'generic'
    }

    def __init__(self, **kwargs):
        """
        Initialize a Material instance with validation.

        Args:
            **kwargs: Keyword arguments for Material initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate material data.

        Raises:
            ModelValidationError: If validation fails
        """
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Material name cannot be empty")

        if len(self.name) > 100:
            raise ModelValidationError("Material name cannot exceed 100 characters")

        if self.description:
            if not isinstance(self.description, str):
                raise ModelValidationError("Material description must be a string")

            if len(self.description) > 500:
                raise ModelValidationError("Material description cannot exceed 500 characters")

        return self


class Leather(Material):
    """
    Leather material subclass.

    Additional Attributes:
        leather_type: Type of leather
        thickness: Thickness in mm
        area: Surface area in square feet
        is_full_hide: Whether this is a full hide or a cut piece
    """
    leather_type: Mapped[Optional[LeatherType]] = mapped_column(
        Enum(LeatherType),
        nullable=True
    )
    thickness: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    area: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    is_full_hide: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        default=False,
        nullable=True
    )

    __mapper_args__ = {
        'polymorphic_identity': 'leather'  # Changed from MaterialType.LEATHER to match data
    }

    def validate(self) -> None:
        """
        Validate leather data.

        Raises:
            ModelValidationError: If validation fails
        """
        super().validate()

        if self.thickness is not None:
            if not isinstance(self.thickness, (int, float)):
                raise ModelValidationError("Leather thickness must be a numeric value")

            if self.thickness <= 0:
                raise ModelValidationError("Leather thickness must be positive")

            if self.thickness > 100:  # Reasonable maximum thickness
                raise ModelValidationError("Leather thickness is unreasonably large")

        if self.area is not None:
            if not isinstance(self.area, (int, float)):
                raise ModelValidationError("Leather area must be a numeric value")

            if self.area <= 0:
                raise ModelValidationError("Leather area must be positive")

            if self.area > 1000:  # Reasonable maximum area in square feet
                raise ModelValidationError("Leather area is unreasonably large")

        return self


class Hardware(Material):
    """
    Hardware material subclass.

    Additional Attributes:
        hardware_type: Type of hardware
        hardware_material: Material the hardware is made of
        finish: Surface finish
        size: Size specification
    """
    hardware_type: Mapped[Optional[HardwareType]] = mapped_column(
        Enum(HardwareType),
        nullable=True
    )
    hardware_material: Mapped[Optional[HardwareMaterial]] = mapped_column(
        Enum(HardwareMaterial),
        nullable=True
    )
    finish: Mapped[Optional[HardwareFinish]] = mapped_column(
        Enum(HardwareFinish),
        nullable=True
    )
    size: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    __mapper_args__ = {
        'polymorphic_identity': 'hardware'  # Changed from MaterialType.HARDWARE to match data
    }

    def validate(self) -> None:
        """
        Validate hardware data.

        Raises:
            ModelValidationError: If validation fails
        """
        super().validate()

        if self.size:
            if not isinstance(self.size, str):
                raise ModelValidationError("Size must be a string")

            if len(self.size) > 50:
                raise ModelValidationError("Size description cannot exceed 50 characters")

        return self


class Supplies(Material):
    """
    Supplies material subclass for various consumables like thread, adhesive, dye, etc.

    Additional Attributes:
        supplies_type: Specific type of supplies (thread, adhesive, dye, etc.)
        color: Color information if applicable
        thread_thickness: Thickness/weight/viscosity information if applicable (renamed to avoid conflict)
        material_composition: Material composition information
    """
    supplies_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    # Renamed from 'thickness' to 'thread_thickness' to avoid column conflict
    thread_thickness: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    material_composition: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    __mapper_args__ = {
        'polymorphic_identity': 'supplies'  # Changed from MaterialType.SUPPLIES to match data
    }

    def validate(self) -> None:
        """
        Validate supplies data.

        Raises:
            ModelValidationError: If validation fails
        """
        super().validate()

        if self.supplies_type:
            if not isinstance(self.supplies_type, str):
                raise ModelValidationError("Supplies type must be a string")

            if len(self.supplies_type) > 50:
                raise ModelValidationError("Supplies type cannot exceed 50 characters")

        if self.color:
            if not isinstance(self.color, str):
                raise ModelValidationError("Color must be a string")

            if len(self.color) > 50:
                raise ModelValidationError("Color description cannot exceed 50 characters")

        if self.thread_thickness:  # Updated validation for renamed field
            if not isinstance(self.thread_thickness, str):
                raise ModelValidationError("Thread thickness must be a string")

            if len(self.thread_thickness) > 50:
                raise ModelValidationError("Thread thickness description cannot exceed 50 characters")

        if self.material_composition:
            if not isinstance(self.material_composition, str):
                raise ModelValidationError("Material composition must be a string")

            if len(self.material_composition) > 100:
                raise ModelValidationError("Material composition cannot exceed 100 characters")

        return self