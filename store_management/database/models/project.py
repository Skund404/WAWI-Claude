# database/models/project.py
"""
This module defines the Project model for the leatherworking application.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin
from database.models.enums import ProjectStatus, ProjectType


class Project(AbstractBase, ValidationMixin):
    """
    Project model representing a leatherworking project.

    Projects can be associated with a sales record and contain multiple components.
    """
    __tablename__ = 'projects'
    __table_args__ = {"extend_existing": True}

    # Basic attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[ProjectType] = mapped_column(Enum(ProjectType), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNED)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Make sales_id nullable to avoid initialization issues
    # Use string ForeignKey to avoid import-time resolution which causes circular dependency
    sales_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sales.id", name="fk_project_sales", use_alter=True, ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    project_components = relationship(
        "ProjectComponent",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Use a string reference to avoid circular import dependencies
    sales = relationship(
        "Sales",
        foreign_keys=[sales_id],
        lazy="selectin",
        # This is important to break the circular dependency during initialization
        post_update=True,
        # Back-reference without circular loading
        primaryjoin="Project.sales_id==Sales.id"
    )

    # Add the tool_list relationship to match ToolList's expectation
    tool_list = relationship(
        "ToolList",
        back_populates="project",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # picking_lists will be added later if needed

    def __init__(self, **kwargs):
        """
        Initialize a Project instance with validation.

        Args:
            **kwargs: Keyword arguments for Project initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate project data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Name validation
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Project name must be a non-empty string")

        if len(self.name) > 255:
            raise ModelValidationError("Project name cannot exceed 255 characters")

        # Type validation
        if not self.type:
            raise ModelValidationError("Project type must be specified")

        # Status validation
        if not self.status:
            raise ModelValidationError("Project status must be specified")

        # Date validation
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ModelValidationError("Project end date cannot be before start date")

        return self