# database/models/pattern.py
"""
Comprehensive Pattern Model for Leatherworking Management System

Implements the Pattern entity from the ER diagram with advanced
relationship management, validation, and business logic.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, String, Text, Integer, JSON, Float, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    SkillLevel,
    ComponentType,
    MaterialType,
    EdgeFinishType
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin
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
register_lazy_import('ProductPattern', 'database.models.product_pattern', 'ProductPattern')
register_lazy_import('PatternComponent', 'database.models.components', 'PatternComponent')
register_lazy_import('Component', 'database.models.components', 'Component')


class Pattern(Base, TimestampMixin, ValidationMixin):
    """
    Pattern model representing design patterns for leatherworking projects.

    Implements comprehensive tracking of pattern details,
    relationships, and business logic.
    """
    __tablename__ = 'patterns'

    # Core pattern attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pattern classification and metadata
    skill_level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel),
        nullable=False,
        default=SkillLevel.INTERMEDIATE
    )
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Design and technical details
    estimated_time_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Pattern status and publication
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_instructions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Detailed component specifications
    components_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Manufacturing and production details
    cutting_complexity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stitching_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    edge_finish_type: Mapped[Optional[EdgeFinishType]] = mapped_column(
        Enum(EdgeFinishType),
        nullable=True
    )

    # Relationships with lazy loading and circular import resolution
    products: Mapped[List['ProductPattern']] = relationship(
        "ProductPattern",
        back_populates="pattern",
        cascade="all, delete-orphan"
    )

    components: Mapped[List['PatternComponent']] = relationship(
        "PatternComponent",
        back_populates="pattern",
        cascade="all, delete-orphan"
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
            # Validate and filter input data
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

        # Validate skill level
        if 'skill_level' in data:
            cls._validate_skill_level(data['skill_level'])

        # Validate estimated time
        if 'estimated_time_hours' in data and data['estimated_time_hours'] is not None:
            validate_positive_number(
                data,
                'estimated_time_hours',
                allow_zero=False,
                message="Estimated time must be a positive number"
            )

        # Validate edge finish type if provided
        if 'edge_finish_type' in data and data['edge_finish_type']:
            cls._validate_edge_finish_type(data['edge_finish_type'])

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Set default version if not provided
        if not self.version:
            self.version = "1.0"

        # Default instructions flag
        if not hasattr(self, 'has_instructions'):
            self.has_instructions = False

    @classmethod
    def _validate_skill_level(cls, skill_level: Union[str, SkillLevel]) -> SkillLevel:
        """
        Validate skill level.

        Args:
            skill_level: Skill level to validate

        Returns:
            Validated SkillLevel

        Raises:
            ValidationError: If skill level is invalid
        """
        if isinstance(skill_level, str):
            try:
                return SkillLevel[skill_level.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid skill level. Must be one of {[l.name for l in SkillLevel]}",
                    "skill_level"
                )

        if not isinstance(skill_level, SkillLevel):
            raise ValidationError("Invalid skill level", "skill_level")

        return skill_level

    @classmethod
    def _validate_edge_finish_type(cls, edge_finish_type: Union[str, EdgeFinishType]) -> EdgeFinishType:
        """
        Validate edge finish type.

        Args:
            edge_finish_type: Edge finish type to validate

        Returns:
            Validated EdgeFinishType

        Raises:
            ValidationError: If edge finish type is invalid
        """
        if isinstance(edge_finish_type, str):
            try:
                return EdgeFinishType[edge_finish_type.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid edge finish type. Must be one of {[t.name for t in EdgeFinishType]}",
                    "edge_finish_type"
                )

        if not isinstance(edge_finish_type, EdgeFinishType):
            raise ValidationError("Invalid edge finish type", "edge_finish_type")

        return edge_finish_type

    def add_component(self, component, quantity: float = 1.0, component_type: Optional[ComponentType] = None) -> None:
        """
        Add a component to the pattern.

        Args:
            component: Component to add
            quantity: Quantity of the component
            component_type: Optional component type specification
        """
        # Lazy import to avoid circular dependencies
        PatternComponent = lazy_import('database.models.components', 'PatternComponent')

        # Create pattern component
        pattern_component = PatternComponent(
            pattern_id=self.id,
            component_id=component.id,
            quantity=quantity,
            component_type=component_type or ComponentType.OTHER
        )

        if pattern_component not in self.components:
            self.components.append(pattern_component)
            logger.info(f"Component {component.id} added to Pattern {self.id}")

    def publish(self) -> None:
        """
        Publish the pattern.
        """
        self.is_published = True
        self.updated_at = datetime.utcnow()
        logger.info(f"Pattern {self.id} published")

    def unpublish(self) -> None:
        """
        Unpublish the pattern.
        """
        self.is_published = False
        self.updated_at = datetime.utcnow()
        logger.info(f"Pattern {self.id} unpublished")

    def increment_version(self) -> None:
        """
        Increment the pattern version.
        """
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
            raise ModelValidationError(f"Failed to increment version: {str(e)}")

    def generate_component_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of components used in the pattern.

        Returns:
            Dictionary summarizing component details
        """
        component_summary = {
            'total_components': len(self.components),
            'component_types': {},
            'material_breakdown': {}
        }

        for pc in self.components:
            # Count component types
            component_type = pc.component_type or ComponentType.OTHER
            component_summary['component_types'][component_type.name] = \
                component_summary['component_types'].get(component_type.name, 0) + 1

        return component_summary

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
            f"skill_level={self.skill_level.name}, "
            f"version={self.version}, "
            f"published={self.is_published}"
            f")>"
        )


def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing Pattern relationships")
    try:
        # Import necessary models
        from database.models.product_pattern import ProductPattern
        from database.models.components import PatternComponent

        # Ensure relationships are properly configured
        logger.info("Pattern relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Pattern relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')