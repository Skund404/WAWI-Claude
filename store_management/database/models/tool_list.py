# database/models/tool_list.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ToolListStatus, TransactionType


class ToolList(AbstractBase, ValidationMixin):
    """
    ToolList represents a list of tools needed for a project.

    Attributes:
        project_id: Foreign key to the project
        status: Tool list status
        notes: Additional notes about the tool list
    """
    __tablename__ = 'tool_lists'

    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    status: Mapped[ToolListStatus] = mapped_column(Enum(ToolListStatus), nullable=False, default=ToolListStatus.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="tool_list")
    items: Mapped[List["ToolListItem"]] = relationship(back_populates="tool_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a ToolList instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate tool list data."""
        pass  # Basic validation is handled by type annotations

    def update_status(self, new_status: ToolListStatus, user: Optional[str] = None,
                      notes: Optional[str] = None) -> None:
        """
        Update the tool list status and handle inventory implications.

        Args:
            new_status: New tool list status
            user: User making the status change
            notes: Optional notes about the status change

        Raises:
            ModelValidationError: If the status change is invalid
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        if user:
            self.updated_by = user

        # Add notes about status change
        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note

        # Handle tool checkout when moving to IN_PROGRESS
        if new_status == ToolListStatus.IN_PROGRESS and old_status != ToolListStatus.IN_PROGRESS:
            self._check_out_tools(user)

        # Handle tool return when completing or cancelling
        if (new_status == ToolListStatus.COMPLETED or new_status == ToolListStatus.CANCELLED) and \
                old_status == ToolListStatus.IN_PROGRESS:
            self._return_tools(user)

    def _check_out_tools(self, user: Optional[str] = None) -> None:
        """
        Check out tools from inventory for project use.

        Args:
            user: User checking out the tools

        Raises:
            ModelValidationError: If any tool can't be checked out
        """
        errors = []

        for item in self.items:
            try:
                item.check_out(user=user)
            except ValueError as e:
                errors.append(f"Tool #{item.tool_id}: {str(e)}")

        if errors:
            # Revert status and raise error
            self.status = ToolListStatus.DRAFT
            raise ModelValidationError(f"Cannot check out tools: {'; '.join(errors)}")

    def _return_tools(self, user: Optional[str] = None) -> None:
        """
        Return tools to inventory.

        Args:
            user: User returning the tools
        """
        for item in self.items:
            try:
                item.return_to_inventory(user=user)
            except ValueError as e:
                # Log error but continue with other items
                error_note = f"[ERROR] Failed to return tool {item.tool_id} to inventory: {str(e)}"
                if self.notes:
                    self.notes += f"\n{error_note}"
                else:
                    self.notes = error_note