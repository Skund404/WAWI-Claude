# database/models/components.py
"""
Enhanced Component Models with Advanced Relationship and Validation Strategies

This module defines the component-related models with comprehensive validation,
relationship management, and circular import resolution.

These models implement the Component, ProjectComponent, and PatternComponent
entities from the ER diagram.
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
register_lazy_import('database.models.material.Material', 'database.models.material', 'Material')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('database.models.picking_list_item.PickingListItem', 'database.models.picking_list_item',
                     'PickingListItem')


class Component(Base):
    """
    Base Component model with core attributes and validation.

    This corresponds to the Component entity in the ER diagram.
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

    # New relationships from ER diagram
    component_materials = relationship("ComponentMaterial", back_populates="component")
    component_leathers = relationship("ComponentLeather", back_populates="component")
    component_hardwares = relationship("ComponentHardware", back_populates="component")
    component_tools = relationship("ComponentTool", back_populates="component")

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

    This corresponds to the ProjectComponent entity in the ER diagram, which
    connects Project and Component.
    """
    __tablename__ = 'project_components'

    # Define the foreign key to the base Component table
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)

    # Additional project-specific columns
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=True)

    # Added to match ER diagram
    picking_list_item_id = Column(Integer, ForeignKey('picking_list_items.id'), nullable=True)

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
        foreign_keys=[leather_id],
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

    # New relationship for ER diagram compliance
    picking_list_item = relationship(
        "PickingListItem",
        back_populates="project_component",
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


# New junction tables from ER diagram
class ComponentMaterial(Base):
    """
    Junction table linking Component to Material with quantity.
    This corresponds to the ComponentMaterial entity in the ER diagram.
    """
    __tablename__ = 'component_materials'

    component_id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    material_id = Column(Integer, ForeignKey('materials.id'), primary_key=True)
    quantity = Column(Float, nullable=False, default=1.0)

    # Relationships
    component = relationship("Component", back_populates="component_materials")
    material = relationship("Material", back_populates="component_materials")

    def __init__(self, component_id: int, material_id: int, quantity: float, **kwargs):
        """
        Initialize a ComponentMaterial instance.

        Args:
            component_id: ID of the component
            material_id: ID of the material
            quantity: Amount of material needed
            **kwargs: Additional attributes
        """
        try:
            kwargs.update({
                'component_id': component_id,
                'material_id': material_id,
                'quantity': quantity
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing ComponentMaterial: {e}")
            raise ValueError(f"Failed to initialize component material: {str(e)}") from e


class ComponentLeather(Base):
    """
    Junction table linking Component to Leather with quantity.
    This corresponds to the ComponentLeather entity in the ER diagram.
    """
    __tablename__ = 'component_leathers'

    component_id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), primary_key=True)
    quantity = Column(Float, nullable=False, default=1.0)

    # Relationships
    component = relationship("Component", back_populates="component_leathers")
    leather = relationship("Leather", back_populates="component_leathers")

    def __init__(self, component_id: int, leather_id: int, quantity: float, **kwargs):
        """
        Initialize a ComponentLeather instance.

        Args:
            component_id: ID of the component
            leather_id: ID of the leather
            quantity: Amount of leather needed
            **kwargs: Additional attributes
        """
        try:
            kwargs.update({
                'component_id': component_id,
                'leather_id': leather_id,
                'quantity': quantity
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing ComponentLeather: {e}")
            raise ValueError(f"Failed to initialize component leather: {str(e)}") from e


class ComponentHardware(Base):
    """
    Junction table linking Component to Hardware with quantity.
    This corresponds to the ComponentHardware entity in the ER diagram.
    """
    __tablename__ = 'component_hardwares'

    component_id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    hardware_id = Column(Integer, ForeignKey('hardwares.id'), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    component = relationship("Component", back_populates="component_hardwares")
    hardware = relationship("Hardware", back_populates="component_hardwares")

    def __init__(self, component_id: int, hardware_id: int, quantity: int, **kwargs):
        """
        Initialize a ComponentHardware instance.

        Args:
            component_id: ID of the component
            hardware_id: ID of the hardware
            quantity: Number of hardware items needed
            **kwargs: Additional attributes
        """
        try:
            kwargs.update({
                'component_id': component_id,
                'hardware_id': hardware_id,
                'quantity': quantity
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing ComponentHardware: {e}")
            raise ValueError(f"Failed to initialize component hardware: {str(e)}") from e


class ComponentTool(Base):
    """
    Junction table linking Component to Tool.
    This corresponds to the ComponentTool entity in the ER diagram.
    """
    __tablename__ = 'component_tools'

    component_id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    tool_id = Column(Integer, ForeignKey('tools.id'), primary_key=True)

    # Relationships
    component = relationship("Component", back_populates="component_tools")
    tool = relationship("Tool", back_populates="component_tools")

    def __init__(self, component_id: int, tool_id: int, **kwargs):
        """
        Initialize a ComponentTool instance.

        Args:
            component_id: ID of the component
            tool_id: ID of the tool
            **kwargs: Additional attributes
        """
        try:
            kwargs.update({
                'component_id': component_id,
                'tool_id': tool_id
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing ComponentTool: {e}")
            raise ValueError(f"Failed to initialize component tool: {str(e)}") from e


# Final registration for lazy imports
register_lazy_import('database.models.components.Component', 'database.models.components', 'Component')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('database.models.components.PatternComponent', 'database.models.components', 'PatternComponent')
register_lazy_import('database.models.components.ComponentMaterial', 'database.models.components', 'ComponentMaterial')
register_lazy_import('database.models.components.ComponentLeather', 'database.models.components', 'ComponentLeather')
register_lazy_import('database.models.components.ComponentHardware', 'database.models.components', 'ComponentHardware')
register_lazy_import('database.models.components.ComponentTool', 'database.models.components', 'ComponentTool')