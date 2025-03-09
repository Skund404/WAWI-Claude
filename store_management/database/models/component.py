# database/models/component.py
from sqlalchemy import Column, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ComponentType
from database.models.relationship_tables import component_material_table


class Component(AbstractBase, ValidationMixin):
    """
    Component used in patterns and projects.

    Attributes:
        name: Component name
        description: Detailed description
        component_type: Type of component
        attributes: Flexible attributes for the component
    """
    __tablename__ = 'components'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    component_type: Mapped[ComponentType] = mapped_column(Enum(ComponentType), nullable=False)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships with string references to avoid circular imports
    materials = relationship(
        "Material",
        secondary="component_materials",
        backref="components",
        lazy="joined"
    )

    project_components = relationship("ProjectComponent", back_populates="component")
    picking_list_items = relationship("PickingListItem", back_populates="component")
    patterns = relationship(
        "Pattern",
        secondary="pattern_components",
        back_populates="components"
    )

    def __init__(self, **kwargs):
        """Initialize a Component instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate component data."""
        if not self.name:
            raise ModelValidationError("Component name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Component name cannot exceed 255 characters")