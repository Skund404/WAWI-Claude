from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/project.py
"""
Comprehensive Project Model for Leatherworking Management System

Implements the Project entity from the ER diagram with advanced
relationship management, validation, and business logic.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    ProjectStatus,
    ProjectType,
    SkillLevel,
    MaterialType,
    ComponentType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    apply_mixins
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
register_lazy_import('Sales', 'database.models.sales', 'Sales')
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('PickingList', 'database.models.picking_list', 'PickingList')
register_lazy_import('ToolList', 'database.models.tool_list', 'ToolList')
register_lazy_import('Production', 'database.models.production', 'Production')

from sqlalchemy.orm import declarative_base
ProjectBase = declarative_base()
ProjectBase.metadata = metadata
ProjectBase.metadata = metadata

class Project(ProjectBase):
    """
    Project model representing a comprehensive leatherworking project.

    Implements detailed tracking of project lifecycle,
    relationships, and business logic.
    """
    __tablename__ = 'projects'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Core project attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Project classification and metadata
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType),
        nullable=False
    )
    skill_level: Mapped[Optional[SkillLevel]] = mapped_column(
        Enum(SkillLevel),
        nullable=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        default=ProjectStatus.INITIAL_CONSULTATION,
        nullable=False
    )

    # Temporal tracking
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Time and effort tracking
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Financial tracking
    material_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    labor_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overhead_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # External relationships
    sales_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('sales.id'),
        nullable=True
    )
    pattern_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('patterns.id'),
        nullable=True
    )

    # Additional metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Renamed to project_metadata to avoid conflicts with SQLAlchemy's metadata
    project_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships with lazy loading and circular import resolution
    sale: Mapped[Optional['Sales']] = relationship(
        "Sales",
        back_populates="project",
        lazy="selectin"
    )

    pattern: Mapped[Optional['Pattern']] = relationship(
        "Pattern",
        lazy="selectin"
    )

    components: Mapped[List['ProjectComponent']] = relationship(
        "ProjectComponent",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    picking_lists: Mapped[List['PickingList']] = relationship(
        "PickingList",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    tool_list: Mapped[Optional['ToolList']] = relationship(
        "ToolList",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan"
    )

    production_records: Mapped[List['Production']] = relationship(
        "Production",
        back_populates="project",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Project instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for project attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Handle metadata rename if present
            if 'metadata' in kwargs:
                kwargs['project_metadata'] = kwargs.pop('metadata')

            # Validate and filter input data
            self._validate_project_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Project initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Project: {str(e)}") from e

    @classmethod
    def _validate_project_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of project creation data.

        Args:
            data (Dict[str, Any]): Project creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Project name is required')
        validate_not_empty(data, 'project_type', 'Project type is required')

        # Validate project type
        if 'project_type' in data:
            cls._validate_project_type(data['project_type'])

        # Validate skill level if provided
        if 'skill_level' in data and data['skill_level']:
            cls._validate_skill_level(data['skill_level'])

        # Validate time-related fields
        cls._validate_project_dates(data)

        # Validate cost-related fields
        cls._validate_project_costs(data)

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Set start date for active projects
        if self.status not in [
            ProjectStatus.INITIAL_CONSULTATION,
            ProjectStatus.DESIGN_PHASE
        ] and not self.start_date:
            self.start_date = datetime.utcnow()

        # Initialize costs if not provided
        if not hasattr(self, 'material_cost'):
            self.material_cost = 0.0
        if not hasattr(self, 'labor_cost'):
            self.labor_cost = 0.0
        if not hasattr(self, 'overhead_cost'):
            self.overhead_cost = 0.0

        # Initialize project_metadata if not provided
        if not hasattr(self, 'project_metadata') or self.project_metadata is None:
            self.project_metadata = {}

    @classmethod
    def _validate_project_type(cls, project_type: Union[str, ProjectType]) -> ProjectType:
        """
        Validate project type.

        Args:
            project_type: Project type to validate

        Returns:
            Validated ProjectType

        Raises:
            ValidationError: If project type is invalid
        """
        if isinstance(project_type, str):
            try:
                return ProjectType[project_type.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid project type. Must be one of {[t.name for t in ProjectType]}",
                    "project_type"
                )

        if not isinstance(project_type, ProjectType):
            raise ValidationError("Invalid project type", "project_type")

        return project_type

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
    def _validate_project_dates(cls, data: Dict[str, Any]) -> None:
        """
        Validate project dates to ensure logical consistency.

        Args:
            data (Dict[str, Any]): Project data containing date information

        Raises:
            ValidationError: If date validation fails
        """
        start_date = data.get('start_date')
        due_date = data.get('due_date')
        completion_date = data.get('completion_date')

        # Check date consistency
        if start_date and due_date and start_date > due_date:
            raise ValidationError(
                "Start date cannot be later than due date",
                "start_date"
            )

        if completion_date:
            if start_date and completion_date < start_date:
                raise ValidationError(
                    "Completion date cannot be earlier than start date",
                    "completion_date"
                )

            if due_date and completion_date > due_date:
                raise ValidationError(
                    "Completion date cannot be later than due date",
                    "completion_date"
                )

    @classmethod
    def _validate_project_costs(cls, data: Dict[str, Any]) -> None:
        """
        Validate project cost-related fields.

        Args:
            data (Dict[str, Any]): Project data containing cost information

        Raises:
            ValidationError: If cost validation fails
        """
        cost_fields = ['material_cost', 'labor_cost', 'overhead_cost']

        for field in cost_fields:
            if field in data and data[field] is not None:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

    def add_component(
            self,
            component,
            quantity: float = 1.0,
            component_type: Optional[ComponentType] = None
    ) -> None:
        """
        Add a component to the project.

        Args:
            component: Component to add
            quantity: Quantity of the component
            component_type: Optional component type specification
        """
        # Lazy import to avoid circular dependencies
        ProjectComponent = lazy_import('database.models.components', 'ProjectComponent')

        # Create project component
        project_component = ProjectComponent(
            project_id=self.id,
            component_id=component.id,
            quantity=quantity,
            component_type=component_type or ComponentType.OTHER
        )

        if project_component not in self.components:
            self.components.append(project_component)
            logger.info(f"Component {component.id} added to Project {self.id}")

    def update_status(self, new_status: Union[str, ProjectStatus]) -> None:
        """
        Update the project status with comprehensive validation.

        Args:
            new_status: New status for the project

        Raises:
            ModelValidationError: If status update fails
        """
        try:
            # Validate new status
            if isinstance(new_status, str):
                new_status = self._validate_project_type(new_status)

            # Update status
            self.status = new_status

            # Handle date updates based on status
            if new_status == ProjectStatus.COMPLETED and not self.completion_date:
                self.completion_date = datetime.utcnow()
            elif new_status in [ProjectStatus.INITIAL_CONSULTATION, ProjectStatus.DESIGN_PHASE]:
                self.start_date = None

            logger.info(f"Project {self.id} status updated to {new_status.name}")

        except Exception as e:
            logger.error(f"Status update failed for project {self.id}: {e}")
            raise ModelValidationError(f"Cannot update project status: {e}")

    def calculate_total_cost(self) -> float:
        """
        Calculate and update the total project cost.

        Returns:
            float: Total project cost
        """
        try:
            total_cost = self.material_cost + self.labor_cost + self.overhead_cost
            self.total_cost = total_cost
            return total_cost
        except Exception as e:
            logger.error(f"Total cost calculation failed for project {self.id}: {e}")
            raise ModelValidationError(f"Cannot calculate project total cost: {e}")

    def create_tool_list(self) -> 'ToolList':
        """
        Create a tool list for the project.

        Returns:
            ToolList: The created tool list
        """
        # Lazy import to avoid circular dependencies
        ToolList = lazy_import('database.models.tool_list', 'ToolList')

        if self.tool_list:
            logger.debug(f"Tool list already exists for project ID {self.id}")
            return self.tool_list

        try:
            tool_list = ToolList(project_id=self.id)
            self.tool_list = tool_list
            logger.debug(f"Created tool list for project ID {self.id}")
            return tool_list
        except Exception as e:
            logger.error(f"Tool list creation failed for project {self.id}: {e}")
            raise ModelValidationError(f"Cannot create tool list: {e}")

    def __repr__(self) -> str:
        """
        String representation of the project.

        Returns:
            str: Detailed project representation
        """
        return (
            f"<Project("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type={self.project_type.name}, "
            f"status={self.status.name}"
            f")>"
        )


def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing Project relationships")
    try:
        # Import necessary models
        from database.models.sales import Sales
        from database.models.pattern import Pattern
        from database.models.components import ProjectComponent
        from database.models.picking_list import PickingList
        from database.models.tool_list import ToolList
        from database.models.production import Production

        # Ensure relationships are properly configured
        logger.info("Project relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Project relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('Project', 'database.models.project', 'Project')