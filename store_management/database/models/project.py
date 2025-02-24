# Path: database/models/project.py
"""
Comprehensive Project model with robust metaclass handling.
"""

from sqlalchemy import Column, String, Float, Enum as SQLAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional, Any

from .model_metaclass import BaseModel
from .enums import ProjectStatus, ProjectType, SkillLevel
from .mixins import TimestampMixin, ValidationMixin, CostingMixin
from .interfaces import IProject


class Project(BaseModel, IProject):
    """
    Comprehensive Project model representing a project in the system.

    Combines multiple mixins and implements project-specific functionality.
    """
    __tablename__ = 'projects'

    # Model-specific columns
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    project_type: Mapped[ProjectType] = mapped_column(SQLAEnum(ProjectType))
    skill_level: Mapped[SkillLevel] = mapped_column(SQLAEnum(SkillLevel))
    status: Mapped[ProjectStatus] = mapped_column(
        SQLAEnum(ProjectStatus),
        default=ProjectStatus.PLANNING
    )
    estimated_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    material_budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    components: Mapped[List['ProjectComponent']] = relationship(
        "ProjectComponent",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    tasks: Mapped[List['ProjectTask']] = relationship(
        "ProjectTask",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    # Mixin methods (explicitly add to ensure compatibility)
    def update_timestamp(self):
        """Update timestamp for the project."""
        from datetime import datetime
        self.updated_at = datetime.utcnow()

    def validate_required_fields(self, data, required_fields):
        """
        Validate required fields.

        Args:
            data (dict): Data to validate
            required_fields (list): Fields that must be present

        Returns:
            bool: True if all required fields are present
        """
        return all(field in data and data[field] is not None for field in required_fields)

    def calculate_labor_cost(self, hours, rate=50.0):
        """
        Calculate labor cost.

        Args:
            hours (float): Number of labor hours
            rate (float, optional): Hourly rate. Defaults to 50.0.

        Returns:
            float: Total labor cost
        """
        return hours * rate

    def __init__(self,
                 name: str,
                 project_type: ProjectType,
                 skill_level: SkillLevel,
                 description: Optional[str] = None,
                 estimated_hours: float = 0.0,
                 material_budget: float = 0.0):
        """
        Initialize a Project instance.

        Args:
            name (str): Name of the project.
            project_type (ProjectType): Type of the project.
            skill_level (SkillLevel): Skill level required.
            description (Optional[str], optional): Project description.
            estimated_hours (float, optional): Estimated project duration.
            material_budget (float, optional): Budget for materials.

        Raises:
            ValueError: If material budget is negative.
        """
        self.name = name
        self.project_type = project_type
        self.skill_level = skill_level
        self.description = description
        self.estimated_hours = estimated_hours
        self.material_budget = material_budget
        self.status = ProjectStatus.PLANNING
        self.components = []
        self.tasks = []

        # Validate initialization
        if material_budget < 0:
            raise ValueError("Material budget cannot be negative")

    def calculate_complexity(self) -> float:
        """
        Calculate project complexity based on various factors.

        Returns:
            float: Complexity score of the project.
        """
        complexity = 0
        complexity += len(self.components) * 0.5
        complexity += len(self.tasks) * 0.3

        # Adjust complexity based on skill level
        skill_multipliers = {
            SkillLevel.BEGINNER: 1.0,
            SkillLevel.INTERMEDIATE: 1.5,
            SkillLevel.ADVANCED: 2.0,
            SkillLevel.EXPERT: 2.5
        }
        complexity *= skill_multipliers.get(self.skill_level, 1.0)

        return round(complexity, 2)

    def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of the project.

        Returns:
            float: Total project cost.
        """
        # Calculate material costs from components
        material_cost = sum(component.calculate_cost() for component in self.components)

        # Add labor cost
        labor_cost = self.estimated_hours * 50  # Assuming $50 per hour

        return material_cost + labor_cost

    def update_status(self, new_status: ProjectStatus) -> None:
        """
        Update the project status.

        Args:
            new_status (ProjectStatus): New status to set for the project.
        """
        self.status = new_status

    def validate(self) -> bool:
        """
        Validate project attributes.

        Returns:
            bool: True if project is valid, False otherwise.
        """
        # Comprehensive validation
        if not self.name or len(self.name) > 100:
            return False
        if self.estimated_hours < 0:
            return False
        if self.material_budget < 0:
            return False
        return True

    def to_dict(self, exclude_fields: Optional[list[str]] = None) -> dict:
        """
        Convert Project to dictionary representation.

        Args:
            exclude_fields (Optional[list[str]], optional): Fields to exclude.

        Returns:
            dict: Dictionary of project attributes.
        """
        exclude_fields = exclude_fields or []

        # Base dictionary
        project_dict = {
            'id': getattr(self, 'id', None),
            'name': self.name,
            'description': self.description,
            'project_type': self.project_type.value if self.project_type else None,
            'skill_level': self.skill_level.value if self.skill_level else None,
            'status': self.status.value if self.status else None,
            'estimated_hours': self.estimated_hours,
            'material_budget': self.material_budget,
        }

        # Add computed fields if not excluded
        if 'complexity' not in exclude_fields:
            project_dict['complexity'] = self.calculate_complexity()

        if 'total_cost' not in exclude_fields:
            project_dict['total_cost'] = self.calculate_total_cost()

        # Optional: Add relationships
        if 'components' not in exclude_fields and hasattr(self, 'components'):
            project_dict['components'] = [
                component.to_dict() for component in self.components
            ]

        if 'tasks' not in exclude_fields and hasattr(self, 'tasks'):
            project_dict['tasks'] = [
                task.to_dict() for task in self.tasks
            ]

        return project_dict