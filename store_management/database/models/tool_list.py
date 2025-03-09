# database/models/tool_list.py
from sqlalchemy import Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ToolListStatus


class ToolList(AbstractBase, ValidationMixin):
    """
    ToolList represents a list of tools needed for a project.

    Attributes:
        project_id: Foreign key to the project
        status: Tool list status
    """
    __tablename__ = 'tool_lists'

    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    status: Mapped[ToolListStatus] = mapped_column(Enum(ToolListStatus), nullable=False, default=ToolListStatus.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tool_list")
    items = relationship("ToolListItem", back_populates="tool_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a ToolList instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate tool list data."""
        pass  # Basic validation is handled by type annotations

    def update_status(self, new_status: ToolListStatus, notes: Optional[str] = None) -> None:
        """
        Update the tool list status.

        Args:
            new_status: New tool list status
            notes: Optional notes about the status change
        """
        old_status = self.status
        self.status = new_status

        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note