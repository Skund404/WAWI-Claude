# database/models/component.py
from __future__ import annotations  # For forward references
from typing import Any, Dict, List, Optional

from sqlalchemy import Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ComponentType
from database.models.component_material import component_material_table


class Component(AbstractBase, ValidationMixin):
    """
    Component used in patterns and projects.

    Attributes:
        name (str): Component name
        description (Optional[str]): Detailed description
        component_type (ComponentType): Type of component
        attributes (Optional[Dict[str, Any]]): Flexible attributes for the component
    """
    __tablename__ = 'components'
    __table_args__ = {"extend_existing": True}

    # SQLAlchemy 2.0 type annotated columns
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    component_type: Mapped[ComponentType] = mapped_column(
        Enum(ComponentType),
        nullable=False,
        index=True
    )
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Relationship with materials through junction table
    component_materials = relationship("database.models.component_material.ComponentMaterial", back_populates="component")

    # Direct relationship to the junction table
    component_materials = relationship(
        "database.models.component_material.ComponentMaterial",
        back_populates="component",
        cascade="all, delete-orphan"
    )

    # Uncommented the picking_list_items relationship to match PickingListItem
    picking_list_items = relationship(
        "PickingListItem",
        back_populates="component",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # These relationships will be added back later
    # project_components: Mapped[List[object]] = relationship(
    #     "ProjectComponent",
    #     back_populates="component",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )
    #
    # patterns: Mapped[List[object]] = relationship(
    #     "Pattern",
    #     secondary="pattern_components",
    #     back_populates="components",
    #     lazy="selectin"
    # )

    def __init__(self, **kwargs):
        """
        Initialize a Component instance with validation.

        Args:
            **kwargs: Keyword arguments for Component initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate component data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Name validation
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Component name must be a non-empty string")

        if len(self.name) > 255:
            raise ModelValidationError("Component name cannot exceed 255 characters")

        # Description validation
        if self.description and len(self.description) > 500:
            raise ModelValidationError("Component description cannot exceed 500 characters")

        # Component type validation
        if not self.component_type:
            raise ModelValidationError("Component type must be specified")

        # Attributes validation
        if self.attributes is not None:
            if not isinstance(self.attributes, dict):
                raise ModelValidationError("Attributes must be a dictionary")

            # Optional: Additional attribute validation
            for key, value in self.attributes.items():
                if not isinstance(key, str):
                    raise ModelValidationError("Attribute keys must be strings")

                if len(key) > 100:
                    raise ModelValidationError("Attribute key cannot exceed 100 characters")

        return self