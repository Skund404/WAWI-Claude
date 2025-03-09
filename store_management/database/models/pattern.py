# database/models/pattern.py
from sqlalchemy import Column, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import SkillLevel
from database.models.relationship_tables import pattern_component_table


class Pattern(AbstractBase, ValidationMixin):
    """
    Pattern represents a design template for products.

    Attributes:
        name: Pattern name
        description: Detailed description
        skill_level: Required skill level
        instructions: Step-by-step instructions in JSON format
    """
    __tablename__ = 'patterns'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    skill_level: Mapped[SkillLevel] = mapped_column(Enum(SkillLevel), nullable=False)
    instructions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    components = relationship(
        "Component",
        secondary="pattern_components",
        back_populates="patterns",
        lazy="joined"
    )

    products = relationship(
        "Product",
        secondary="product_patterns",
        back_populates="patterns"
    )

    def __init__(self, **kwargs):
        """Initialize a Pattern instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate pattern data."""
        if not self.name:
            raise ModelValidationError("Pattern name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Pattern name cannot exceed 255 characters")

        if not self.skill_level:
            raise ModelValidationError("Skill level is required")