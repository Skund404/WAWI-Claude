# database/models/component_material.py
from __future__ import annotations  # For forward references
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, ModelValidationError, ValidationMixin

# Define junction table with a single primary key for better compatibility
component_material_table = Table(
    'component_materials',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('component_id', Integer, ForeignKey('components.id', ondelete='CASCADE'), nullable=False),
    Column('material_id', Integer, ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
    Column('quantity', Float, default=1.0, nullable=False),
    UniqueConstraint('component_id', 'material_id', name='uq_component_material'),
    extend_existing=True  # This helps avoid "table already exists" errors
)


# We'll use this class for when you need to interact with the junction table directly
class ComponentMaterial(Base, ValidationMixin):
    """
    Represents the relationship between components and materials with quantity.

    This is a junction table with additional attributes.

    Attributes:
        component_id: Foreign key to the component
        material_id: Foreign key to the material
        quantity: Quantity of material needed for the component
    """
    __tablename__ = 'component_materials'
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey('components.id', ondelete='CASCADE'))
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id', ondelete='CASCADE'))
    quantity: Mapped[float] = mapped_column(default=1.0)

    # Relationships
    component = relationship("Component", back_populates="component_materials")
    material = relationship("Material", back_populates="component_materials")

    def __init__(self, component_id, material_id, quantity=1.0):
        self.component_id = component_id
        self.material_id = material_id
        self.quantity = quantity

    def validate(self) -> None:
        """
        Validate component material data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Component ID validation
        if not self.component_id or not isinstance(self.component_id, int):
            raise ModelValidationError("Component ID must be a positive integer")

        if self.component_id <= 0:
            raise ModelValidationError("Component ID must be a positive integer")

        # Material ID validation
        if not self.material_id or not isinstance(self.material_id, int):
            raise ModelValidationError("Material ID must be a positive integer")

        if self.material_id <= 0:
            raise ModelValidationError("Material ID must be a positive integer")

        # Quantity validation
        if not self.quantity or not isinstance(self.quantity, (int, float)):
            raise ModelValidationError("Quantity must be a positive number")

        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be a positive number")

        return self