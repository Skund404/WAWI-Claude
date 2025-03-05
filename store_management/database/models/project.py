# database/models/project.py
"""
Enhanced Project Model with Standard SQLAlchemy Relationship Approach

This module defines the Project model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import ProjectStatus, ProjectType, SkillLevel
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

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('ProjectComponent', 'database.models.components')
register_lazy_import('Pattern', 'database.models.pattern')
register_lazy_import('Production', 'database.models.production')
register_lazy_import('LeatherTransaction', 'database.models.transaction')
register_lazy_import('HardwareTransaction', 'database.models.transaction')

# Setup logger
logger = logging.getLogger(__name__)


class Project(Base):
    """
    Enhanced Project model with comprehensive validation and relationship management.

    Represents a leatherworking project with advanced lifecycle tracking,
    relationship configuration, and validation strategies.
    """
    __tablename__ = 'projects'

    # Core project attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Enum and status tracking
    project_type = Column(Enum(ProjectType), nullable=False)
    skill_level = Column(Enum(SkillLevel), nullable=True)
    # Changed from NEW to INITIAL_CONSULTATION which exists in the enum
    status = Column(Enum(ProjectStatus), default=ProjectStatus.INITIAL_CONSULTATION, nullable=False)

    # Temporal tracking
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)

    # Cost and time tracking
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)

    # Financial tracking
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    overhead_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    # Additional metadata
    notes = Column(Text, nullable=True)
    project_metadata = Column(JSON, nullable=True)

    # Foreign keys with lazy import support
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)

    # Relationships using standard SQLAlchemy approach
    pattern = relationship("Pattern", back_populates="projects", lazy="lazy")

    components = relationship("ProjectComponent", back_populates="project",
                              cascade="all, delete-orphan", lazy="selectin")

    production_records = relationship("Production", back_populates="project", lazy="lazy")

    # View-only relationships with transactions
    leather_transactions = relationship("LeatherTransaction", back_populates="project",
                                        lazy="lazy")

    hardware_transactions = relationship("HardwareTransaction", back_populates="project",
                                         lazy="lazy")

    def __init__(self, **kwargs):
        """
        Initialize a Project instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for project attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Set start date for active projects
            self._initialize_project_dates(kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Project initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Project: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate project creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Project creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Project name is required')
        validate_not_empty(data, 'project_type', 'Project type is required')

        # Validate project type
        if 'project_type' in data:
            ModelValidator.validate_enum(
                data['project_type'],
                ProjectType,
                'project_type'
            )

        # Validate optional numeric fields
        optional_numeric_fields = [
            'estimated_hours', 'actual_hours',
            'material_cost', 'labor_cost',
            'overhead_cost', 'total_cost'
        ]

        for field in optional_numeric_fields:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

        # Validate dates
        cls._validate_project_dates(data)

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate relationships
        if self.pattern and not hasattr(self.pattern, 'id'):
            raise ValidationError("Invalid pattern reference", "pattern")

        # Validate cost calculations
        self._validate_cost_calculation()

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
                "start_date",
                "date_order_error"
            )

        if completion_date:
            if start_date and completion_date < start_date:
                raise ValidationError(
                    "Completion date cannot be earlier than start date",
                    "completion_date",
                    "date_order_error"
                )

            if due_date and completion_date > due_date:
                raise ValidationError(
                    "Completion date cannot be later than due date",
                    "completion_date",
                    "date_order_error"
                )

    def _validate_cost_calculation(self) -> None:
        """
        Validate project cost calculations.

        Raises:
            ValidationError: If cost calculation is inconsistent
        """
        # Total cost should match sum of individual costs
        calculated_total = (
                self.material_cost +
                self.labor_cost +
                self.overhead_cost
        )

        # Allow small floating-point discrepancies
        if abs(calculated_total - self.total_cost) > 0.01:
            logger.warning(
                f"Cost calculation mismatch. "
                f"Calculated: {calculated_total}, Stored: {self.total_cost}"
            )
            self.total_cost = calculated_total

    def _initialize_project_dates(self, kwargs: Dict[str, Any]) -> None:
        """
        Initialize project dates based on status and input.

        Args:
            kwargs (Dict[str, Any]): Initialization arguments
        """
        # Set start date for active projects if not provided
        if (not self.start_date and
                self.status not in [ProjectStatus.INITIAL_CONSULTATION, ProjectStatus.DESIGN_PHASE]):
            self.start_date = datetime.utcnow()

        # Update completion date for completed projects
        if (self.status == ProjectStatus.COMPLETED and
                not self.completion_date):
            self.completion_date = datetime.utcnow()

    def calculate_total_cost(self) -> float:
        """
        Calculate and update the total project cost.

        Returns:
            float: Calculated total cost
        """
        try:
            self.total_cost = (
                    self.material_cost +
                    self.labor_cost +
                    self.overhead_cost
            )
            return self.total_cost
        except Exception as e:
            logger.error(f"Error calculating project total cost: {e}")
            raise ModelValidationError(f"Cost calculation failed: {e}")

    def complete(self) -> None:
        """
        Mark the project as completed with comprehensive validation.

        Raises:
            ModelValidationError: If project cannot be completed
        """
        try:
            # Validate project completion prerequisites
            self._validate_project_completion()

            # Update project status
            self.status = ProjectStatus.COMPLETED
            self.completion_date = datetime.utcnow()

            # Finalize costs
            self.calculate_total_cost()

            logger.info(f"Project {self.id} successfully completed")

        except Exception as e:
            logger.error(f"Project completion failed: {e}")
            raise ModelValidationError(f"Cannot complete project: {str(e)}")

    def _validate_project_completion(self) -> None:
        """
        Validate project completion prerequisites.

        Raises:
            ModelValidationError: If project cannot be completed
        """
        # Validate component completion
        if self.components:
            incomplete_components = [
                comp for comp in self.components
                if not getattr(comp, 'is_complete', False)
            ]
            if incomplete_components:
                raise ModelValidationError(
                    f"{len(incomplete_components)} project components are not complete"
                )

        # Validate transaction processing
        unprocessed_leather_txns = [
            txn for txn in self.leather_transactions
            if not getattr(txn, 'is_processed', False)
        ]
        unprocessed_hardware_txns = [
            txn for txn in self.hardware_transactions
            if not getattr(txn, 'is_processed', False)
        ]

        if unprocessed_leather_txns or unprocessed_hardware_txns:
            raise ModelValidationError(
                "Some project transactions are not processed"
            )

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the project.

        Returns:
            str: Detailed project representation
        """
        return (
            f"<Project(id={self.id}, name='{self.name}', "
            f"type={self.project_type}, "
            f"status={self.status}, "
            f"components={len(self.components)}, "
            f"total_cost={self.total_cost})>"
        )


# Register this class for lazy imports by others
register_lazy_import('Project', 'database.models.project')