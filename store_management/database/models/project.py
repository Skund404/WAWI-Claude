# database/models/project.py
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ProjectType, ProjectStatus


class Project(AbstractBase, ValidationMixin):
    """
    Project represents a production job, typically tied to a customer order.

    Attributes:
        name: Project name
        description: Detailed description
        type: Project type
        status: Project status
        start_date: Planned or actual start date
        end_date: Planned or actual end date
        sales_id: Optional foreign key to the sales order
    """
    __tablename__ = 'projects'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    type: Mapped[ProjectType] = mapped_column(Enum(ProjectType), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNED)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sales.id'), nullable=True)

    # Relationships
    sales = relationship("Sales", back_populates="projects")
    components = relationship("ProjectComponent", back_populates="project", cascade="all, delete-orphan")
    tool_list = relationship("ToolList", back_populates="project", uselist=False)

    def __init__(self, **kwargs):
        """Initialize a Project instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate project data."""
        if not self.name:
            raise ModelValidationError("Project name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Project name cannot exceed 255 characters")

        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ModelValidationError("End date cannot be before start date")

    def update_status(self, new_status: ProjectStatus, notes: Optional[str] = None) -> None:
        """
        Update the project status and add notes.

        Args:
            new_status: New project status
            notes: Optional notes about the status change
        """
        old_status = self.status
        self.status = new_status

        # Update related dates based on status
        if (new_status == ProjectStatus.IN_PROGRESS and not self.start_date):
            self.start_date = datetime.now()
        elif (new_status == ProjectStatus.COMPLETED and not self.end_date):
            self.end_date = datetime.now()

        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note