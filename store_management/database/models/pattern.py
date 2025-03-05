# database/models/pattern.py
"""
Enhanced Pattern Model with Standard SQLAlchemy Relationship Approach

This module defines the Pattern model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, String, Text, Float, Integer, Boolean, JSON, DateTime
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SkillLevel
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('PatternComponent', 'database.models.components', 'PatternComponent')

# Setup logger
logger = logging.getLogger(__name__)


class Pattern(Base):
    """
    Enhanced Pattern model with comprehensive validation and relationship management.

    Represents leatherworking patterns with advanced tracking
    and relationship configuration.
    """
    __tablename__ = 'patterns'

    # Core pattern attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)

    # Skill and complexity
    skill_level = Column(Enum(SkillLevel), nullable=True)

    # Dimensional and design details
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)

    # Metadata and additional information
    design_notes = Column(Text, nullable=True)
    pattern_metadata = Column(JSON, nullable=True)

    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)

    # Timestamp tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships using standard SQLAlchemy approach
    products = relationship("Product", back_populates="pattern", lazy="select")
    projects = relationship("Project", back_populates="pattern", lazy="select")
    components = relationship("PatternComponent", back_populates="pattern",
                              cascade="all, delete-orphan", lazy="selectin")

    project_components = relationship(
        "ProjectComponent",
        back_populates="pattern",
        lazy="select"
    )

    def update_version(self, new_version: str) -> None:
        """
        Update the pattern version with validation.

        Args:
            new_version (str): New version identifier

        Raises:
            ModelValidationError: If version update fails
        """
        try:
            # Validate new version
            if not new_version or len(new_version.strip()) == 0:
                raise ValidationError("Version cannot be empty", "version")

            # Prevent redundant version updates
            if self.version == new_version:
                logger.info(f"Pattern {self.id} version already set to {new_version}")
                return

            # Update version and timestamp
            old_version = self.version
            self.version = new_version
            self.updated_at = datetime.utcnow()

            logger.info(
                f"Pattern {self.id} version updated from "
                f"{old_version or 'None'} to {new_version}"
            )

        except Exception as e:
            logger.error(f"Version update failed: {e}")
            raise ModelValidationError(f"Cannot update pattern version: {str(e)}")

    def calculate_complexity(self) -> float:
        """
        Calculate pattern complexity based on components and skill level.

        Returns:
            float: Complexity score
        """
        try:
            # Base complexity from skill level
            skill_complexity_map = {
                SkillLevel.BEGINNER: 1.0,
                SkillLevel.INTERMEDIATE: 2.0,
                SkillLevel.ADVANCED: 3.0,
                SkillLevel.EXPERT: 4.0
            }

            # Base complexity from skill level
            base_complexity = skill_complexity_map.get(
                self.skill_level,
                1.0  # Default to beginner if not set
            )

            # Add complexity from number of components
            component_complexity = len(self.components or []) * 0.5

            # Consider dimensional complexity
            dimension_complexity = 0
            if self.width and self.height and self.depth:
                dimension_complexity = (
                                               (self.width + self.height + self.depth) / 3
                                       ) * 0.1

            # Calculate total complexity
            total_complexity = base_complexity + component_complexity + dimension_complexity

            return round(total_complexity, 2)

        except Exception as e:
            logger.error(f"Complexity calculation failed: {e}")
            raise ModelValidationError(f"Cannot calculate pattern complexity: {str(e)}")

    def archive(self) -> None:
        """
        Archive the pattern by marking it as inactive.

        Raises:
            ModelValidationError: If archiving fails
        """
        try:
            # Prevent re-archiving
            if not self.is_active:
                logger.info(f"Pattern {self.id} is already archived")
                return

            # Disable active status
            self.is_active = False
            self.is_published = False

            # Update timestamp
            self.updated_at = datetime.utcnow()

            logger.info(f"Pattern {self.id} archived successfully")

        except Exception as e:
            logger.error(f"Pattern archiving failed: {e}")
            raise ModelValidationError(f"Cannot archive pattern: {str(e)}")

    def restore(self) -> None:
        """
        Restore an archived pattern.

        Raises:
            ModelValidationError: If restoration fails
        """
        try:
            # Prevent re-restoring
            if self.is_active:
                logger.info(f"Pattern {self.id} is already active")
                return

            # Require at least one component to restore
            if not self.components or len(self.components) == 0:
                raise ValidationError(
                    "Cannot restore pattern without components",
                    "components"
                )

            # Reactivate pattern
            self.is_active = True
            self.updated_at = datetime.utcnow()

            logger.info(f"Pattern {self.id} restored successfully")

        except Exception as e:
            logger.error(f"Pattern restoration failed: {e}")
            raise ModelValidationError(f"Cannot restore pattern: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the pattern.

        Returns:
            str: Detailed pattern representation
        """
        return (
            f"<Pattern(id={self.id}, name='{self.name}', "
            f"version='{self.version or 'None'}', "
            f"skill_level={self.skill_level}, "
            f"active={self.is_active}, "
            f"published={self.is_published}, "
            f"components={len(self.components or [])})"
        )


# Register this class for lazy imports by others
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')