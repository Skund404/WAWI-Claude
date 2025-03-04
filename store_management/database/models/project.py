# database/models/project.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import relationship, validates
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base
from database.models.enums import ProjectStatus, ProjectType, SkillLevel
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Explicit lazy imports to resolve circular dependencies
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components')
register_lazy_import('database.models.pattern.Pattern', 'database.models.pattern')

# Lazy load model classes to prevent circular imports
ProjectComponent = lazy_import("database.models.components", "ProjectComponent")
Pattern = lazy_import("database.models.pattern", "Pattern")


class Project(Base):
    """
    Model representing a leatherworking project with comprehensive
    lifecycle and relationship management.
    """
    __tablename__ = 'projects'

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
    project_metadata = Column(JSON, nullable=True)

    # Foreign keys
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)

    # Validate key attributes
    @validates('name')
    def validate_name(self, key, name):
        """Validate project name."""
        if not name or len(name) > 255:
            raise ValueError("Project name must be between 1 and 255 characters")
        return name

    @validates('due_date', 'start_date')
    def validate_dates(self, key, date):
        """Validate project dates."""
        if date and self.start_date and self.due_date:
            if key == 'due_date' and date < self.start_date:
                raise ValueError("Due date cannot be earlier than start date")
            if key == 'start_date' and date > self.due_date:
                raise ValueError("Start date cannot be later than due date")
        return date

    # Relationships with explicit configuration
    components = relationship(
        "ProjectComponent",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select"
    )

    pattern = relationship(
        "Pattern",
        back_populates="projects",
        lazy="select",
        cascade="save-update, merge"
    )

    # Add the missing production_records relationship
    production_records = relationship(
        "Production",
        back_populates="project",
        lazy="select",
        cascade="save-update, merge"
    )

    # Relationships that view existing transactions
    leather_transactions = relationship(
        "LeatherTransaction",
        back_populates="project",
        viewonly=True,
        lazy="select"
    )

    hardware_transactions = relationship(
        "HardwareTransaction",
        back_populates="project",
        viewonly=True,
        lazy="select"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Project instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for project attributes

        Raises:
            ValueError: If validation fails
            TypeError: If invalid data types are provided
        """
        try:
            # Remove any keys not in the model to prevent unexpected attribute errors
            filtered_kwargs = {k: v for k, v in kwargs.items() if hasattr(self.__class__, k)}

            super().__init__(**filtered_kwargs)

            # Set start date if not provided and project is active
            if 'start_date' not in kwargs and self.status not in [ProjectStatus.NEW, ProjectStatus.PLANNING]:
                self.start_date = datetime.utcnow()

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
        logger.error(f"Project Initialization Error: {error_context}")

        # Re-raise with more context
        raise ValueError(f"Failed to create Project: {str(error)}") from error

    def complete(self) -> None:
        """
        Mark the project as completed with comprehensive validation.

        Raises:
            ValueError: If the project cannot be completed
            RuntimeError: If completion process fails
        """
        try:
            # Validate project completion
            self._validate_project_completion()

            # Update status
            self.status = ProjectStatus.COMPLETED
            self.completion_date = datetime.utcnow()

            # Calculate final costs
            self.calculate_total_cost()

            logger.info(f"Project {self.id} successfully completed")

        except Exception as e:
            logger.error(f"Error completing project: {e}")
            raise RuntimeError(f"Failed to complete project: {str(e)}") from e

    def _validate_project_completion(self) -> None:
        """
        Validate project completion prerequisites.

        Raises:
            ValueError: If project cannot be considered complete
        """
        # Ensure all critical components are complete
        if self.components and not all(
                getattr(component, 'is_complete', False)
                for component in self.components
        ):
            raise ValueError("Not all project components are complete")

        # Validate transactions
        if (
                not all(getattr(txn, 'is_processed', False)
                        for txn in (self.leather_transactions or []))
                or not all(getattr(txn, 'is_processed', False)
                           for txn in (self.hardware_transactions or []))
        ):
            raise ValueError("Some project transactions are not processed")

    def calculate_total_cost(self) -> float:
        """
        Calculate and update the total cost of the project.

        Returns:
            float: The calculated total cost

        Raises:
            RuntimeError: If cost calculation fails
        """
        try:
            # Recalculate total cost with error handling
            self.total_cost = (
                    self.material_cost +
                    self.labor_cost +
                    self.overhead_cost
            )

            logger.debug(f"Project {self.id} total cost calculated: {self.total_cost}")
            return self.total_cost

        except Exception as e:
            logger.error(f"Error calculating project total cost: {e}")
            raise RuntimeError(f"Failed to calculate total cost: {str(e)}") from e

    def __repr__(self) -> str:
        """
        Detailed string representation of the project.

        Returns:
            str: Comprehensive string representation
        """
        return (
            f"<Project(id={self.id}, name='{self.name}', "
            f"type={self.project_type}, "
            f"status={self.status.name if self.status else 'None'}, "
            f"pattern_id={self.pattern_id})>"
        )


# Explicitly register lazy imports to ensure proper configuration
register_lazy_import('database.models.project.Project', 'database.models.project')