# database/models/project.py
from sqlalchemy import Column, String, Float, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database.models.base import Base, BaseModel
from database.models.base import ModelValidationError
from database.models.enums import ProjectType, ProjectStatus, SkillLevel
from database.models.mixins import TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class Project(Base, BaseModel, TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin):
    """
    Represents a leatherworking project with comprehensive tracking and validation.

    Attributes:
        id (str): Unique identifier for the project
        name (str): Project name
        description (str): Detailed project description
        project_type (ProjectType): Type of project (e.g., BAG, WALLET)
        skill_level (SkillLevel): Skill level required for the project
        status (ProjectStatus): Current status of the project
        start_date (datetime): Project start date
        end_date (datetime): Project completion date
        estimated_hours (float): Estimated project duration
        actual_hours (float): Actual project duration
        is_completed (bool): Whether the project is completed
        metadata (dict): Additional project metadata
    """
    __tablename__ = 'projects'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False)
    skill_level = Column(Enum(SkillLevel), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)

    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)

    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    is_completed = Column(Boolean, default=False)

    metadata = Column(JSON, nullable=True)

    # Relationships
    components = relationship('ProjectComponent', back_populates='project', cascade='all, delete-orphan')
    materials = relationship('Material', secondary='project_materials', back_populates='projects')

    def __init__(self, **kwargs):
        """
        Initialize a Project instance with validation.

        Args:
            **kwargs: Keyword arguments for project attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            super().__init__(**kwargs)
            self.validate()
        except Exception as e:
            logger.error(f"Project initialization error: {str(e)}")
            raise ModelValidationError(f"Invalid project data: {str(e)}")

    def validate(self):
        """
        Validate project attributes.

        Raises:
            ModelValidationError: If any validation fails
        """
        if not self.name or len(self.name) < 2:
            raise ModelValidationError("Project name must be at least 2 characters long")

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ModelValidationError("Start date cannot be after end date")

        if self.estimated_hours is not None and self.estimated_hours < 0:
            raise ModelValidationError("Estimated hours cannot be negative")

        if self.actual_hours is not None and self.actual_hours < 0:
            raise ModelValidationError("Actual hours cannot be negative")

    def update_status(self, new_status: ProjectStatus):
        """
        Update project status with logging.

        Args:
            new_status (ProjectStatus): New status to set
        """
        old_status = self.status
        self.status = new_status
        logger.info(f"Project {self.id} status changed from {old_status} to {new_status}")

    def complete(self):
        """
        Mark the project as completed.
        """
        if not self.is_completed:
            self.is_completed = True
            self.end_date = datetime.utcnow()
            self.update_status(ProjectStatus.COMPLETED)
            logger.info(f"Project {self.id} marked as completed")

    def __repr__(self):
        """
        String representation of the Project.

        Returns:
            str: Project details
        """
        return (f"<Project(id={self.id}, name='{self.name}', "
                f"type={self.project_type}, status={self.status})>")


class ProjectComponent(Base, BaseModel, TimestampMixin):
    """
    Represents a component within a project.

    Attributes:
        project_id (str): ID of the parent project
        name (str): Component name
        description (str): Component description
        quantity (float): Quantity of the component
        material_id (str): ID of the associated material
    """
    __tablename__ = 'project_components'

    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    material_id = Column(String, ForeignKey('materials.id'), nullable=True)

    project = relationship('Project', back_populates='components')
    material = relationship('Material')

    def __init__(self, **kwargs):
        """
        Initialize a ProjectComponent with validation.

        Args:
            **kwargs: Keyword arguments for component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            super().__init__(**kwargs)
            self.validate()
        except Exception as e:
            logger.error(f"Project component initialization error: {str(e)}")
            raise ModelValidationError(f"Invalid project component data: {str(e)}")

    def validate(self):
        """
        Validate project component attributes.

        Raises:
            ModelValidationError: If any validation fails
        """
        if not self.name or len(self.name) < 2:
            raise ModelValidationError("Component name must be at least 2 characters long")

        if self.quantity <= 0:
            raise ModelValidationError("Component quantity must be positive")