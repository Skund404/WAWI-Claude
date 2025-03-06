# database/models/pattern.py
"""
Pattern Model

This module defines the Pattern model which implements
the Pattern entity from the ER diagram.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, String, Text, Integer, JSON, Float, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SkillLevel
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports
register_lazy_import('ProductPattern', 'database.models.product_pattern', 'ProductPattern')
register_lazy_import('Component', 'database.models.components', 'Component')
register_lazy_import('PatternComponent', 'database.models.components', 'PatternComponent')


class Pattern(Base):
    """
    Pattern model representing design patterns for leatherworking.
    This corresponds to the Pattern entity in the ER diagram.
    """
    __tablename__ = 'patterns'

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skill_level: Mapped[SkillLevel] = mapped_column(Enum(SkillLevel), nullable=False, default=SkillLevel.INTERMEDIATE)

    # Metadata
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                                                 nullable=False)

    # Pattern details
    components: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)  # JSON structure of pattern components
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_instructions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    # Product relationship (many-to-many via ProductPattern)
    products = relationship(
        "ProductPattern",
        back_populates="pattern",
        cascade="all, delete-orphan"
    )

    # Component relationship (many-to-many via PatternComponent)
    pattern_components = relationship(
        "PatternComponent",
        back_populates="pattern",
        cascade="all, delete-orphan"
    )

    def __init__(self, name: str, skill_level: SkillLevel, description: Optional[str] = None,
                 version: Optional[str] = "1.0", components: Optional[Dict] = None,
                 is_published: bool = False, has_instructions: bool = False,
                 estimated_time_hours: Optional[float] = None, **kwargs):
        """
        Initialize a Pattern instance.

        Args:
            name: Pattern name
            skill_level: Skill level required
            description: Optional description
            version: Optional version number
            components: Optional JSON structure of components
            is_published: Whether the pattern is published
            has_instructions: Whether the pattern has instructions
            estimated_time_hours: Optional estimated completion time
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'name': name,
                'skill_level': skill_level,
                'description': description,
                'version': version,
                'components': components or {},
                'is_published': is_published,
                'has_instructions': has_instructions,
                'estimated_time_hours': estimated_time_hours,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Pattern initialization failed: {e}")
            raise ModelValidationError(f"Failed to create pattern: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate pattern creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Pattern name is required')

        # Validate estimated time if provided
        if data.get('estimated_time_hours') is not None and data['estimated_time_hours'] <= 0:
            raise ValidationError("Estimated time must be positive")

    def add_component(self, component, quantity: float = 1.0):
        """
        Add a component to the pattern.

        Args:
            component: The component to add
            quantity: Quantity of the component (default 1.0)
        """
        from .components import PatternComponent

        pattern_component = PatternComponent(
            pattern_id=self.id,
            component_id=component.id,
            quantity=quantity
        )
        self.pattern_components.append(pattern_component)

    def publish(self) -> None:
        """Publish the pattern."""
        self.is_published = True
        self.updated_at = datetime.utcnow()
        logger.info(f"Pattern {self.id} published")

    def unpublish(self) -> None:
        """Unpublish the pattern."""
        self.is_published = False
        self.updated_at = datetime.utcnow()
        logger.info(f"Pattern {self.id} unpublished")

    def increment_version(self) -> None:
        """Increment the pattern version."""
        try:
            # Parse current version
            major, minor = (self.version or "1.0").split('.')

            # Increment minor version
            new_minor = int(minor) + 1

            # Update version
            self.version = f"{major}.{new_minor}"
            self.updated_at = datetime.utcnow()

            logger.info(f"Pattern {self.id} version updated to {self.version}")
        except Exception as e:
            logger.error(f"Error incrementing pattern version: {e}")
            raise ValueError(f"Failed to increment version: {str(e)}") from e

    def __repr__(self) -> str:
        """String representation of the pattern."""
        return f"<Pattern(id={self.id}, name='{self.name}', skill_level={self.skill_level}, version={self.version})>"


def initialize_relationships():
    """
    Initialize relationships for the Pattern model.
    This helps resolve potential circular import issues.
    """
    from .product_pattern import ProductPattern
    from .components import PatternComponent, Component

    # Ensure lazy loaded relationships are set up
    if not hasattr(Pattern, 'products'):
        Pattern.products = relationship(
            'ProductPattern',
            back_populates='pattern',
            cascade='all, delete-orphan'
        )

    if not hasattr(Pattern, 'pattern_components'):
        Pattern.pattern_components = relationship(
            'PatternComponent',
            back_populates='pattern',
            cascade='all, delete-orphan'
        )


# Final registration
register_lazy_import('database.models.pattern.Pattern', 'database.models.pattern', 'Pattern')