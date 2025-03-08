# database/models/pattern.py
"""
Comprehensive Pattern Model for Leatherworking Management System

Implements the Pattern entity from the ER diagram with advanced
relationship management and validation strategies.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, JSON, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    ProjectType,
    SkillLevel,
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    apply_mixins  # Added import for apply_mixins
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('PatternComponent', 'database.models.components', 'PatternComponent')
register_lazy_import('ProductPattern', 'database.models.product_pattern', 'ProductPattern')


class Pattern(Base, apply_mixins(TimestampMixin, ValidationMixin)):  # Updated to use apply_mixins
    """
    Pattern model representing leatherworking patterns that can be used in projects.

    Implements comprehensive pattern management with validations and relationships.
    """
    __tablename__ = 'patterns'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Added explicit id column

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pattern classification
    project_type: Mapped[Optional[ProjectType]] = mapped_column(
        Enum(ProjectType),
        nullable=True
    )
    skill_level: Mapped[Optional[SkillLevel]] = mapped_column(
        Enum(SkillLevel),
        nullable=True
    )

    # Version and status tracking
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Design details
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    design_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # References
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata - renamed to pattern_metadata to avoid conflicts with SQLAlchemy's metadata
    pattern_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships with lazy loading and circular import resolution
    components: Mapped[List['PatternComponent']] = relationship(
        "PatternComponent",
        back_populates="pattern",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    product_patterns: Mapped[List['ProductPattern']] = relationship(
        "ProductPattern",
        back_populates="pattern",
        lazy="selectin"
    )

    projects: Mapped[List['Project']] = relationship(
        "Project",
        back_populates="pattern",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Pattern instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for pattern attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Handle metadata rename if present
            if 'metadata' in kwargs:
                kwargs['pattern_metadata'] = kwargs.pop('metadata')

            # Validate input data
            self._validate_pattern_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Pattern initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Pattern: {str(e)}") from e

    @classmethod
    def _validate_pattern_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of pattern creation data.

        Args:
            data (Dict[str, Any]): Pattern creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Pattern name is required')

        # Validate project type if provided
        if 'project_type' in data and data['project_type'] is not None:
            ModelValidator.validate_enum(
                data['project_type'],
                ProjectType,
                'project_type'
            )

        # Validate skill level if provided
        if 'skill_level' in data and data['skill_level'] is not None:
            ModelValidator.validate_enum(
                data['skill_level'],
                SkillLevel,
                'skill_level'
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize metadata if not provided
        if not hasattr(self, 'pattern_metadata') or self.pattern_metadata is None:
            self.pattern_metadata = {}

        # Set default values if not specified
        if not hasattr(self, 'version') or self.version is None:
            self.version = "1.0"

        if not hasattr(self, 'is_active') or self.is_active is None:
            self.is_active = True

    def add_component(self, component, quantity: int = 1, position: Optional[str] = None) -> 'PatternComponent':
        """
        Add a component to this pattern.

        Args:
            component: Component to add
            quantity: Number of this component needed
            position: Optional position description

        Returns:
            The created PatternComponent junction object
        """
        try:
            # Lazy import to avoid circular dependencies
            PatternComponent = lazy_import('database.models.components', 'PatternComponent')

            pattern_component = PatternComponent(
                pattern_id=self.id,
                component_id=component.id,
                quantity=quantity,
                position=position
            )

            self.components.append(pattern_component)

            logger.info(f"Added component {component.id} to pattern {self.id}")
            return pattern_component

        except Exception as e:
            logger.error(f"Failed to add component to pattern: {e}")
            raise ModelValidationError(f"Failed to add component: {str(e)}")

    def deactivate(self) -> None:
        """
        Deactivate the pattern.
        """
        self.is_active = False
        logger.info(f"Pattern {self.id} deactivated")

    def activate(self) -> None:
        """
        Activate the pattern.
        """
        self.is_active = True
        logger.info(f"Pattern {self.id} activated")

    def update_version(self, new_version: str) -> None:
        """
        Update the pattern version.

        Args:
            new_version: New version string
        """
        self.version = new_version
        logger.info(f"Pattern {self.id} version updated to {new_version}")

    def __repr__(self) -> str:
        """
        String representation of the pattern.

        Returns:
            str: Detailed pattern representation
        """
        return (
            f"<Pattern("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"version='{self.version}', "
            f"active={self.is_active}"
            f")>"
        )


def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing Pattern relationships")
    try:
        # Import necessary models
        from database.models.components import PatternComponent
        from database.models.project import Project
        from database.models.product_pattern import ProductPattern

        # Ensure relationships are properly configured
        logger.info("Pattern relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Pattern relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')