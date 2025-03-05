# database/models/components.py
"""
Enhanced Component Models with Advanced Relationship and Validation Strategies

This module defines the component-related models with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship, declared_attr, Mapped
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    ComponentType,
    EdgeFinishType,
    MaterialQualityGrade
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
register_lazy_import('database.models.project.Project', 'database.models.project', 'Project')
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')
register_lazy_import('database.models.pattern.Pattern', 'database.models.pattern', 'Pattern')


class Component(Base):
    """
    Base Component model with core attributes and validation.
    """
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    component_type = Column(Enum(ComponentType), nullable=False)

    # Common physical attributes
    quantity = Column(Float, default=1.0, nullable=False)
    dimensions = Column(String(100), nullable=True)

    type = Column(String(50))  # Discriminator column for inheritance

    __mapper_args__ = {
        'polymorphic_identity': 'component',
        'polymorphic_on': type
    }

    def __init__(self, **kwargs):
        """
        Initialize a Component instance with validation.

        Args:
            **kwargs: Keyword arguments for component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Component initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Component: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate component creation data.

        Args:
            data (Dict[str, Any]): Component creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Component name is required')
        validate_not_empty(data, 'component_type', 'Component type is required')

        # Validate component type
        if 'component_type' in data:
            ModelValidator.validate_enum(
                data['component_type'],
                ComponentType,
                'component_type'
            )

        # Validate quantity
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )


class ProjectComponent(Component):
    """
    Project-specific component with additional attributes and relationships.
    """
    __tablename__ = 'project_components'

    # Define the foreign key to the base Component table
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)

    # Additional project-specific columns
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=True)

    # Edge finish specifics
    edge_finish_type = Column(Enum(EdgeFinishType), nullable=True)
    edge_finish_color = Column(String(50), nullable=True)

    # Tracking attributes
    is_complete = Column(Boolean, default=False, nullable=False)

    hardware_id = Column(Integer, ForeignKey('hardwares.id'), nullable=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)

    # Relationships

    hardware = relationship(
        "Hardware",
        back_populates="project_components",
        foreign_keys=[hardware_id],
        lazy='select'
    )

    project = relationship(
        "Project",
        back_populates="components",
        lazy='select'
    )

    pattern = relationship(
        "Pattern",
        back_populates="project_components",
        lazy='select'
    )

    leather = relationship(
        "Leather",
        back_populates="project_components",
        foreign_keys=[leather_id],  # Explicitly specify which column is the foreign key
        lazy='select'
    )

    material = relationship(
        "Material",
        back_populates="project_components",
        foreign_keys=[material_id],
        lazy='select'
    )

    product = relationship(
        "Product",
        back_populates="components",
        foreign_keys=[product_id],
        lazy='select'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'project_component',
        'inherit_condition': (id == Component.id)
    }

    def __init__(self, **kwargs):
        """
        Initialize a ProjectComponent instance with validation.

        Args:
            **kwargs: Keyword arguments for project component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Additional project component validation
            self._validate_project_component(kwargs)

            # Initialize parent and base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ProjectComponent initialization failed: {e}")
            raise ModelValidationError(f"Failed to create ProjectComponent: {str(e)}") from e

    @classmethod
    def _validate_project_component(cls, data: Dict[str, Any]) -> None:
        """
        Validate project-specific component attributes.

        Args:
            data (Dict[str, Any]): Project component data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate project_id
        if 'project_id' not in data or not data['project_id']:
            raise ValidationError("Project ID is required for a project component")

        # Validate edge finish type if provided
        if 'edge_finish_type' in data and data['edge_finish_type']:
            ModelValidator.validate_enum(
                data['edge_finish_type'],
                EdgeFinishType,
                'edge_finish_type'
            )

    def mark_complete(self) -> None:
        """
        Mark the project component as complete.
        """
        self.is_complete = True
        logger.info(f"Project component {self.id} marked as complete")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation.

        Returns:
            str: Detailed project component representation
        """
        return (
            f"<ProjectComponent(id={self.id}, name='{self.name}', "
            f"type={self.component_type}, "
            f"project_id={self.project_id}, "
            f"complete={self.is_complete})>"
        )


class PatternComponent(Component):
    """
    Pattern-specific component with additional attributes and relationships.
    """
    __tablename__ = 'pattern_components'

    # Define the foreign key to the base Component table
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)

    # Additional pattern-specific columns
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=False)

    # Material and dimensional details
    material_type = Column(String(100), nullable=True)
    material_thickness = Column(Float, nullable=True)

    # Tracking attributes
    is_template = Column(Boolean, default=False, nullable=False)

    # Relationships
    pattern = relationship(
        "Pattern",
        back_populates="components",
        lazy='select'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'pattern_component',
        'inherit_condition': (id == Component.id)
    }

    def __init__(self, **kwargs):
        """
        Initialize a PatternComponent instance with validation.

        Args:
            **kwargs: Keyword arguments for pattern component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Additional pattern component validation
            self._validate_pattern_component(kwargs)

            # Initialize parent and base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PatternComponent initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PatternComponent: {str(e)}") from e

    @classmethod
    def _validate_pattern_component(cls, data: Dict[str, Any]) -> None:
        """
        Validate pattern-specific component attributes.

        Args:
            data (Dict[str, Any]): Pattern component data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate pattern_id
        if 'pattern_id' not in data or not data['pattern_id']:
            raise ValidationError("Pattern ID is required for a pattern component")

        # Validate material thickness if provided
        if 'material_thickness' in data and data['material_thickness'] is not None:
            validate_positive_number(
                data,
                'material_thickness',
                allow_zero=False,
                message="Material thickness must be a positive number"
            )

    def mark_as_template(self) -> None:
        """
        Mark the pattern component as a template.
        """
        self.is_template = True
        logger.info(f"Pattern component {self.id} marked as template")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation.

        Returns:
            str: Detailed pattern component representation
        """
        return (
            f"<PatternComponent(id={self.id}, name='{self.name}', "
            f"type={self.component_type}, "
            f"pattern_id={self.pattern_id}, "
            f"template={self.is_template})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.components.Component', 'database.models.components', 'Component')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('database.models.components.PatternComponent', 'database.models.components', 'PatternComponent')