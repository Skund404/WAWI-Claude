# database/models/project.py
from database.models.base import Base
from database.models.enums import ProjectStatus, ProjectType, SkillLevel
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime


class Project(Base):
    """
    Model representing a leatherworking project.
    """
    # Project specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    project_type = Column(Enum(ProjectType), nullable=False)
    skill_level = Column(Enum(SkillLevel), nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.NEW, nullable=False)

    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)

    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    notes = Column(Text, nullable=True)
    project_metadata  = Column(JSON, nullable=True)

    # Relationships
    components = relationship("ProjectComponent", back_populates="project", cascade="all, delete-orphan")

    # Foreign keys
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)
    pattern = relationship("Pattern", back_populates="projects")

    def __init__(self, **kwargs):
        """Initialize a Project instance with validation.

        Args:
            **kwargs: Keyword arguments for project attributes

        Raises:
            ValueError: If validation fails
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

        # Set start date if not provided
        if 'start_date' not in kwargs and self.status not in [ProjectStatus.NEW, ProjectStatus.PLANNING]:
            self.start_date = datetime.utcnow()

    @classmethod
    def _validate_creation(cls, data):
        """Validate project attributes.

        Raises:
            ValueError: If any validation fails
        """
        if 'name' not in data or not data['name']:
            raise ValueError("Project name is required")

        if 'project_type' not in data:
            raise ValueError("Project type is required")

    def update_status(self, new_status: ProjectStatus):
        """Update project status with logging.

        Args:
            new_status (ProjectStatus): New status to set
        """
        old_status = self.status
        self.status = new_status

        # Update related timestamps
        if new_status == ProjectStatus.COMPLETED:
            self.completion_date = datetime.utcnow()
        elif old_status == ProjectStatus.NEW and new_status != ProjectStatus.NEW:
            if not self.start_date:
                self.start_date = datetime.utcnow()

    def complete(self):
        """Mark the project as completed."""
        self.update_status(ProjectStatus.COMPLETED)
        self.completion_date = datetime.utcnow()

    def calculate_total_cost(self):
        """Calculate and update the total cost of the project."""
        self.total_cost = self.material_cost + self.labor_cost + self.overhead_cost
        return self.total_cost


class ProjectComponent(Base):
    """
    Model representing a component of a project.
    """
    # ProjectComponent specific fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    quantity = Column(Float, default=1.0, nullable=False)
    unit_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)

    is_completed = Column(Boolean, default=False, nullable=False)

    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="components")
    material = relationship("Material", back_populates="project_components")
    leather = relationship("Leather", back_populates="project_components")
    hardware = relationship("Hardware", back_populates="project_components")

    def __init__(self, **kwargs):
        """Initialize a ProjectComponent with validation.

        Args:
            **kwargs: Keyword arguments for component attributes

        Raises:
            ValueError: If validation fails
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

        # Calculate total cost if not provided
        if 'total_cost' not in kwargs and 'unit_cost' in kwargs and 'quantity' in kwargs:
            self.total_cost = self.quantity * self.unit_cost

    @classmethod
    def _validate_creation(cls, data):
        """Validate project component attributes.

        Raises:
            ValueError: If any validation fails
        """
        if 'name' not in data or not data['name']:
            raise ValueError("Component name is required")

        if 'project_id' not in data:
            raise ValueError("Project ID is required")

        # Check that at least one of material, leather, or hardware is specified
        if not any(key in data for key in ['material_id', 'leather_id', 'hardware_id']):
            raise ValueError("At least one of material_id, leather_id, or hardware_id must be specified")