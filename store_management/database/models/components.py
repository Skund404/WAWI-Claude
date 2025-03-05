# database/models/components.py
"""
Enhanced Components Models with Advanced Relationship and Validation Strategies

This module defines the components used across leatherworking projects,
with comprehensive validation and relationship management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship, declarative_base

from database.models.base import Base, ModelValidationError
from database.models.enums import ComponentType, EdgeFinishType
from utils.circular_import_resolver import (
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty
)

# Setup logger
logger = logging.getLogger(__name__)


class Component(Base):
    """
    Base Component model for generic component tracking.
    Provides a foundational structure for more specific component types.
    """
    __tablename__ = 'base_components'

    # Primary key with explicit inheritance support
    id = Column(Integer, primary_key=True)

    # Core component attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Classification and type
    component_type = Column(Enum(ComponentType), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Polymorphic discriminator for inheritance
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'base_component',
        'polymorphic_on': type
    }

    def __repr__(self) -> str:
        """
        Provide a string representation of the base component.

        Returns:
            str: Detailed base component representation
        """
        return (
            f"<BaseComponent(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.component_type})>"
        )


class PatternComponent(Component):
    """
    Specialized component model for pattern-specific details.
    Extends the base Component with pattern-related attributes.
    """
    __tablename__ = 'pattern_components'

    # Primary key with explicit foreign key to base components
    id = Column(Integer, ForeignKey('base_components.id'), primary_key=True)

    # Additional pattern-specific fields
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    thickness = Column(Float, nullable=True)

    # Edge finishing details
    edge_finish = Column(Enum(EdgeFinishType), nullable=True)

    # Relationships with pattern
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)
    pattern = relationship(
        "Pattern",
        back_populates="components",
        lazy='select'
    )

    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'pattern_component',
    }

    def __repr__(self) -> str:
        """
        Provide a string representation of the pattern component.

        Returns:
            str: Detailed pattern component representation
        """
        return (
            f"<PatternComponent(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.component_type}, "
            f"edge_finish={self.edge_finish})>"
        )


class ProjectComponent(Component):
    """
    Model representing a component within a project or pattern.

    Tracks detailed information about individual components used
    in leatherworking projects.
    """
    __tablename__ = 'project_components'

    # Primary key with explicit foreign key to base components
    id = Column(Integer, ForeignKey('base_components.id'), primary_key=True)

    # Quantity and usage tracking
    quantity_required = Column(Float, default=1.0, nullable=False)
    quantity_used = Column(Float, default=0.0, nullable=False)

    # Additional metadata
    is_optional = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    # Foreign keys for relationships
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)

    # Relationships configured with string-based back_populates to avoid circular imports
    pattern = relationship(
        "Pattern",
        back_populates="components",
        lazy='select'
    )

    project = relationship(
        "Project",
        back_populates="components",
        lazy='select'
    )

    product = relationship(
        "Product",
        back_populates="components",
        lazy='select'
    )

    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'project_component',
    }

    def update_usage(self, quantity_used: float) -> None:
        """
        Update the quantity used for this component.

        Args:
            quantity_used (float): Quantity of the component used

        Raises:
            ModelValidationError: If usage update is invalid
        """
        try:
            # Validate quantity
            if quantity_used < 0:
                raise ModelValidationError("Quantity used must be non-negative")

            if quantity_used > self.quantity_required:
                raise ModelValidationError(
                    f"Cannot use more than required. "
                    f"Required: {self.quantity_required}, "
                    f"Attempted: {quantity_used}"
                )

            # Update quantity used
            self.quantity_used = quantity_used

            logger.info(
                f"ProjectComponent {self.id} usage updated. "
                f"Quantity Used: {quantity_used}"
            )

        except Exception as e:
            logger.error(f"Usage update failed: {e}")
            raise ModelValidationError(f"Cannot update component usage: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the project component.

        Returns:
            str: Detailed project component representation
        """
        return (
            f"<ProjectComponent(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.component_type}, "
            f"edge_finish={self.edge_finish if hasattr(self, 'edge_finish') else 'N/A'}, "
            f"quantity_required={self.quantity_required}, "
            f"quantity_used={self.quantity_used})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.components.Component', 'database.models.components')
register_lazy_import('database.models.components.PatternComponent', 'database.models.components')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components')