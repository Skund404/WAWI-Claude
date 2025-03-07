# database/models/components.py
"""
Comprehensive Component Models for Leatherworking Management System

This module defines the component-related models with comprehensive validation,
relationship management, and circular import resolution.

Implements the Component, ProjectComponent, PatternComponent, and junction table entities
from the ER diagram, ensuring proper relationship tracking and validation.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    ComponentType,
    EdgeFinishType,
    MaterialType,
    QualityGrade,
    SkillLevel,
    MeasurementUnit
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
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
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Tool', 'database.models.tool', 'Tool')
register_lazy_import('PickingListItem', 'database.models.picking_list', 'PickingListItem')
register_lazy_import('Product', 'database.models.product', 'Product')


class Component(Base, TimestampMixin, ValidationMixin):
    """
    Base Component model representing a fundamental building block for patterns and projects.

    This corresponds to the Component entity in the ER diagram.
    """
    __tablename__ = 'components'

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    component_type: Mapped[ComponentType] = mapped_column(Enum(ComponentType), nullable=False)

    # Metadata attributes
    skill_level: Mapped[Optional[SkillLevel]] = mapped_column(Enum(SkillLevel), nullable=True)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Physical attributes
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Discriminator column for inheritance
    type: Mapped[str] = mapped_column(String(50))

    # Relationships as defined in ER diagram
    component_materials = relationship("ComponentMaterial", back_populates="component", cascade="all, delete-orphan")
    component_leathers = relationship("ComponentLeather", back_populates="component", cascade="all, delete-orphan")
    component_hardwares = relationship("ComponentHardware", back_populates="component", cascade="all, delete-orphan")
    component_tools = relationship("ComponentTool", back_populates="component", cascade="all, delete-orphan")

    __mapper_args__ = {
        'polymorphic_identity': 'component',
        'polymorphic_on': type
    }

    def __init__(self, **kwargs):
        """
        Initialize a Component instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_component_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Component initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Component: {str(e)}") from e

    @classmethod
    def _validate_component_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of component creation data.

        Args:
            data: Component creation data to validate

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
        # Ensure basic attributes are initialized
        if not hasattr(self, 'attributes') or self.attributes is None:
            self.attributes = {}

    def add_material(self, material_id: int, quantity: float = 1.0) -> "ComponentMaterial":
        """
        Add a material to this component.

        Args:
            material_id: ID of the material to add
            quantity: Amount of material needed

        Returns:
            The created ComponentMaterial junction object
        """
        try:
            junction = ComponentMaterial(
                component_id=self.id,
                material_id=material_id,
                quantity=quantity
            )
            self.component_materials.append(junction)
            logger.info(f"Added material {material_id} to component {self.id}")
            return junction
        except Exception as e:
            logger.error(f"Failed to add material to component: {e}")
            raise ModelValidationError(f"Failed to add material: {str(e)}")

    def add_leather(self, leather_id: int, quantity: float = 1.0) -> "ComponentLeather":
        """
        Add a leather to this component.

        Args:
            leather_id: ID of the leather to add
            quantity: Amount of leather needed

        Returns:
            The created ComponentLeather junction object
        """
        try:
            junction = ComponentLeather(
                component_id=self.id,
                leather_id=leather_id,
                quantity=quantity
            )
            self.component_leathers.append(junction)
            logger.info(f"Added leather {leather_id} to component {self.id}")
            return junction
        except Exception as e:
            logger.error(f"Failed to add leather to component: {e}")
            raise ModelValidationError(f"Failed to add leather: {str(e)}")

    def add_hardware(self, hardware_id: int, quantity: int = 1) -> "ComponentHardware":
        """
        Add a hardware item to this component.

        Args:
            hardware_id: ID of the hardware to add
            quantity: Number of hardware items needed

        Returns:
            The created ComponentHardware junction object
        """
        try:
            junction = ComponentHardware(
                component_id=self.id,
                hardware_id=hardware_id,
                quantity=quantity
            )
            self.component_hardwares.append(junction)
            logger.info(f"Added hardware {hardware_id} to component {self.id}")
            return junction
        except Exception as e:
            logger.error(f"Failed to add hardware to component: {e}")
            raise ModelValidationError(f"Failed to add hardware: {str(e)}")

    def add_tool(self, tool_id: int) -> "ComponentTool":
        """
        Add a tool to this component.

        Args:
            tool_id: ID of the tool to add

        Returns:
            The created ComponentTool junction object
        """
        try:
            junction = ComponentTool(
                component_id=self.id,
                tool_id=tool_id
            )
            self.component_tools.append(junction)
            logger.info(f"Added tool {tool_id} to component {self.id}")
            return junction
        except Exception as e:
            logger.error(f"Failed to add tool to component: {e}")
            raise ModelValidationError(f"Failed to add tool: {str(e)}")

    def __repr__(self) -> str:
        """
        String representation of the Component.

        Returns:
            Detailed component representation
        """
        return (
            f"<Component(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.component_type.name if self.component_type else 'None'})>"
        )


class PatternComponent(Base, TimestampMixin, ValidationMixin):
    """
    Pattern-specific component junction table with enhanced attributes.

    This corresponds to the PatternComponent entity in the ER diagram,
    which serves as a junction between Pattern and Component.
    """
    __tablename__ = 'pattern_components'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign keys
    pattern_id: Mapped[int] = mapped_column(Integer, ForeignKey('patterns.id'), nullable=False)
    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), nullable=False)

    # Attributes
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    pattern = relationship("Pattern", back_populates="components")
    component = relationship("Component")

    def __init__(self, **kwargs):
        """
        Initialize a PatternComponent instance with validation.

        Args:
            **kwargs: Keyword arguments for pattern component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_pattern_component_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PatternComponent initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PatternComponent: {str(e)}") from e

    @classmethod
    def _validate_pattern_component_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate pattern component data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'pattern_id', 'Pattern ID is required')
        validate_not_empty(data, 'component_id', 'Component ID is required')

        # Validate quantity if provided
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Initializes default values and performs any necessary setup.
        """
        # Initialize dimensions if not provided
        if not hasattr(self, 'dimensions') or self.dimensions is None:
            self.dimensions = {}

    def __repr__(self) -> str:
        """
        String representation of the PatternComponent.

        Returns:
            Detailed pattern component representation
        """
        return (
            f"<PatternComponent(id={self.id}, "
            f"pattern_id={self.pattern_id}, "
            f"component_id={self.component_id}, "
            f"quantity={self.quantity})>"
        )


class ProjectComponent(Base, TimestampMixin, ValidationMixin):
    """
    Project-specific component junction table with enhanced attributes.

    This corresponds to the ProjectComponent entity in the ER diagram,
    which serves as a junction between Project and Component.
    """
    __tablename__ = 'project_components'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign keys
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), nullable=False)
    picking_list_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('picking_list_items.id'),
                                                                nullable=True)

    # Attributes
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="components")
    component = relationship("Component")
    picking_list_item = relationship("PickingListItem", back_populates="project_component")

    def __init__(self, **kwargs):
        """
        Initialize a ProjectComponent instance with validation.

        Args:
            **kwargs: Keyword arguments for project component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_project_component_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ProjectComponent initialization failed: {e}")
            raise ModelValidationError(f"Failed to create ProjectComponent: {str(e)}") from e

    @classmethod
    def _validate_project_component_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate project component data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'project_id', 'Project ID is required')
        validate_not_empty(data, 'component_id', 'Component ID is required')

        # Validate quantity if provided
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )

    def mark_complete(self) -> None:
        """
        Mark the project component as complete.
        """
        self.is_complete = True
        logger.info(f"Project component {self.id} marked as complete")

    def __repr__(self) -> str:
        """
        String representation of the ProjectComponent.

        Returns:
            Detailed project component representation
        """
        return (
            f"<ProjectComponent(id={self.id}, "
            f"project_id={self.project_id}, "
            f"component_id={self.component_id}, "
            f"quantity={self.quantity}, "
            f"complete={self.is_complete})>"
        )


# Junction tables for relationships from ER diagram
class ComponentMaterial(Base):
    """
    Junction table linking Component to Material with quantity.
    This corresponds to the ComponentMaterial entity in the ER diagram.
    """
    __tablename__ = 'component_materials'

    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), primary_key=True)
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey('materials.id'), primary_key=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Relationships
    component = relationship("Component", back_populates="component_materials")
    material = relationship("Material", back_populates="component_materials")

    def __init__(self, **kwargs):
        """
        Initialize a ComponentMaterial instance with validation.

        Args:
            **kwargs: Keyword arguments

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate
            self._validate_data(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"ComponentMaterial initialization failed: {e}")
            raise ModelValidationError(f"Failed to create component material: {str(e)}") from e

    @classmethod
    def _validate_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate junction data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        validate_not_empty(data, 'component_id', 'Component ID is required')
        validate_not_empty(data, 'material_id', 'Material ID is required')

        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )


class ComponentLeather(Base):
    """
    Junction table linking Component to Leather with quantity.
    This corresponds to the ComponentLeather entity in the ER diagram.
    """
    __tablename__ = 'component_leathers'

    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), primary_key=True)
    leather_id: Mapped[int] = mapped_column(Integer, ForeignKey('leathers.id'), primary_key=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Relationships
    component = relationship("Component", back_populates="component_leathers")
    leather = relationship("Leather", back_populates="component_leathers")

    def __init__(self, **kwargs):
        """
        Initialize a ComponentLeather instance with validation.

        Args:
            **kwargs: Keyword arguments

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate
            self._validate_data(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"ComponentLeather initialization failed: {e}")
            raise ModelValidationError(f"Failed to create component leather: {str(e)}") from e

    @classmethod
    def _validate_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate junction data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        validate_not_empty(data, 'component_id', 'Component ID is required')
        validate_not_empty(data, 'leather_id', 'Leather ID is required')

        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )


class ComponentHardware(Base):
    """
    Junction table linking Component to Hardware with quantity.
    This corresponds to the ComponentHardware entity in the ER diagram.
    """
    __tablename__ = 'component_hardwares'

    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), primary_key=True)
    hardware_id: Mapped[int] = mapped_column(Integer, ForeignKey('hardwares.id'), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    component = relationship("Component", back_populates="component_hardwares")
    hardware = relationship("Hardware", back_populates="component_hardwares")

    def __init__(self, **kwargs):
        """
        Initialize a ComponentHardware instance with validation.

        Args:
            **kwargs: Keyword arguments

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate
            self._validate_data(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"ComponentHardware initialization failed: {e}")
            raise ModelValidationError(f"Failed to create component hardware: {str(e)}") from e

    @classmethod
    def _validate_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate junction data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        validate_not_empty(data, 'component_id', 'Component ID is required')
        validate_not_empty(data, 'hardware_id', 'Hardware ID is required')

        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )


class ComponentTool(Base):
    """
    Junction table linking Component to Tool.
    This corresponds to the ComponentTool entity in the ER diagram.
    """
    __tablename__ = 'component_tools'

    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), primary_key=True)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey('tools.id'), primary_key=True)

    # Relationships
    component = relationship("Component", back_populates="component_tools")
    tool = relationship("Tool", back_populates="component_tools")

    def __init__(self, **kwargs):
        """
        Initialize a ComponentTool instance with validation.

        Args:
            **kwargs: Keyword arguments

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate
            self._validate_data(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"ComponentTool initialization failed: {e}")
            raise ModelValidationError(f"Failed to create component tool: {str(e)}") from e

    @classmethod
    def _validate_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate junction data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        validate_not_empty(data, 'component_id', 'Component ID is required')
        validate_not_empty(data, 'tool_id', 'Tool ID is required')


# Register models for circular import resolution
register_lazy_import('Component', 'database.models.components', 'Component')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('PatternComponent', 'database.models.components', 'PatternComponent')  # Added registration
register_lazy_import('ComponentMaterial', 'database.models.components', 'ComponentMaterial')
register_lazy_import('ComponentLeather', 'database.models.components', 'ComponentLeather')
register_lazy_import('ComponentHardware', 'database.models.components', 'ComponentHardware')
register_lazy_import('ComponentTool', 'database.models.components', 'ComponentTool')