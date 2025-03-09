# database/models/component_material.py
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError


class ComponentMaterial(AbstractBase, ValidationMixin):
    """
    Represents the relationship between a component and the material it requires.

    Attributes:
        component_id: Foreign key to the component
        material_id: Foreign key to the material
        quantity: Amount of material needed
    """
    __tablename__ = 'component_materials'

    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), nullable=False)
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey('materials.id'), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    component = relationship("Component", back_populates="component_materials")
    material = relationship("Material", back_populates="component_materials")

    def __init__(self, **kwargs):
        """Initialize a ComponentMaterial instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate component material data."""
        if self.quantity is not None and self.quantity <= 0:
            raise ModelValidationError("Material quantity must be positive")