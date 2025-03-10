# database/models/pattern.py
from typing import Any, Dict, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin
from database.models.enums import SkillLevel

# Import the relationship tables from the central location
from database.models.relationship_tables import pattern_component_table, product_pattern_table

class Pattern(AbstractBase, ValidationMixin):
    """
    Pattern model for leatherworking designs.

    Attributes:
        name (str): Pattern name
        description (Optional[str]): Detailed description
        skill_level (SkillLevel): Required skill level
        version (Optional[str]): Pattern version information
        instructions (Optional[Dict]): JSON instructions for pattern usage
    """
    __tablename__ = 'patterns'
    __table_args__ = {'extend_existing': True}

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
    skill_level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel),
        nullable=False,
        default=SkillLevel.INTERMEDIATE
    )
    version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    instructions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    # Relationships
    components = relationship(
        "Component",
        secondary=pattern_component_table,
        backref="patterns",
        lazy="selectin"
    )

    # Uncommenting the relationship to Product
    products = relationship(
        "Product",
        secondary=product_pattern_table,
        back_populates="patterns",  # Using back_populates to match Product class
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Pattern instance with validation.
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate pattern data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Name validation
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Pattern name must be a non-empty string")

        if len(self.name) > 255:
            raise ModelValidationError("Pattern name cannot exceed 255 characters")

        # Description validation
        if self.description is not None:
            if not isinstance(self.description, str):
                raise ModelValidationError("Pattern description must be a string")

            if len(self.description) > 500:
                raise ModelValidationError("Pattern description cannot exceed 500 characters")

        # Version validation
        if self.version is not None:
            if not isinstance(self.version, str):
                raise ModelValidationError("Pattern version must be a string")

            if len(self.version) > 50:
                raise ModelValidationError("Pattern version cannot exceed 50 characters")

        # Instructions validation
        if self.instructions is not None and not isinstance(self.instructions, dict):
            raise ModelValidationError("Pattern instructions must be a dictionary")

        return self