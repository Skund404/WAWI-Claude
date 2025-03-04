# database/models/pattern.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, String, Text, Float, Boolean, JSON, DateTime, Integer
from sqlalchemy.orm import relationship, validates
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base
from database.models.enums import SkillLevel
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Lazy import to prevent circular dependencies
Project = lazy_import("database.models.project", "Project")
PatternComponent = lazy_import("database.models.components", "PatternComponent")


class Pattern(Base):
    """
    Model representing leatherworking patterns with comprehensive
    validation and relationship management.
    """
    __tablename__ = 'patterns'

    # Pattern specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    skill_level = Column(Enum(SkillLevel), nullable=False, default=SkillLevel.BEGINNER)
    version = Column(String(20), nullable=True)

    width_mm = Column(Float, nullable=True)
    height_mm = Column(Float, nullable=True)

    estimated_time_hours = Column(Float, nullable=True)
    estimated_leather_sqft = Column(Float, nullable=True)

    instructions = Column(Text, nullable=True)
    tools_required = Column(Text, nullable=True)
    materials_required = Column(Text, nullable=True)

    is_published = Column(Boolean, default=False, nullable=False)
    publication_date = Column(DateTime, nullable=True)

    file_path = Column(String(255), nullable=True)
    pattern_metadata = Column(JSON, nullable=True)

    # Relationships with explicit configuration
    components = relationship(
        "PatternComponent",
        back_populates="pattern",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Add the missing projects relationship to match Project.pattern
    projects = relationship(
        "Project",
        back_populates="pattern",
        lazy="select",
        cascade="save-update, merge"
    )

    # Products relationship (if needed)
    products = relationship(
        "Product",
        back_populates="pattern",
        lazy="select",
        cascade="save-update, merge"
    )

    @validates('name')
    def validate_name(self, key, name):
        """Validate pattern name."""
        if not name or len(name) > 255:
            raise ValueError("Pattern name must be between 1 and 255 characters")
        return name

    def __init__(self, **kwargs):
        """
        Initialize a Pattern instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments with pattern attributes

        Raises:
            ValueError: If validation fails for any field
            TypeError: If invalid data types are provided
        """
        try:
            # Remove any keys not in the model to prevent unexpected attribute errors
            filtered_kwargs = {k: v for k, v in kwargs.items() if hasattr(self.__class__, k)}

            super().__init__(**filtered_kwargs)
        except (ValueError, TypeError, SQLAlchemyError) as e:
            self._handle_initialization_error(e, kwargs)

    def _handle_initialization_error(self, error: Exception, data: Dict[str, Any]) -> None:
        """
        Handle initialization errors with detailed logging.

        Args:
            error (Exception): The caught exception
            data (dict): The input data that caused the error

        Raises:
            ValueError: Re-raises the original error with additional context
        """
        error_context = {
            'input_data': data,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }

        # Log the error
        logger.error(f"Pattern Initialization Error: {error_context}")

        # Re-raise with more context
        raise ValueError(f"Failed to create Pattern: {str(error)}") from error

    def publish(self) -> None:
        """
        Mark the pattern as published and set publication date.

        Raises:
            RuntimeError: If publication fails
        """
        try:
            self.is_published = True
            self.publication_date = datetime.utcnow()
            logger.info(f"Pattern {self.id} published")
        except Exception as e:
            logger.error(f"Error publishing pattern: {e}")
            raise RuntimeError(f"Failed to publish pattern: {str(e)}") from e

    def calculate_leather_requirement(self) -> float:
        """
        Calculate total leather requirement based on components.

        Returns:
            float: Total estimated leather requirement in square feet

        Raises:
            RuntimeError: If calculation fails
        """
        try:
            total = self.estimated_leather_sqft or 0.0

            # If component relationships are loaded, add their requirements
            if self.components:
                for component in self.components:
                    try:
                        component_area = getattr(component, 'area_sqft', 0) or 0
                        total += component_area
                    except Exception as component_error:
                        logger.warning(f"Error calculating component area: {component_error}")

            logger.debug(f"Calculated leather requirement for Pattern {self.id}: {total} sq ft")
            return total
        except Exception as e:
            logger.error(f"Error calculating leather requirement: {e}")
            raise RuntimeError(f"Failed to calculate leather requirement: {str(e)}") from e

    def __repr__(self) -> str:
        """
        Detailed string representation of the pattern.

        Returns:
            str: Comprehensive string representation
        """
        return (
            f"<Pattern(id={self.id}, name='{self.name}', "
            f"skill_level={self.skill_level}, "
            f"published={self.is_published}, "
            f"version='{self.version or 'N/A'}')>"
        )


# Explicitly register lazy imports to ensure proper configuration
register_lazy_import('database.models.pattern.Pattern', 'database.models.pattern')
register_lazy_import('database.models.pattern.Pattern.projects', 'database.models.project.Project')