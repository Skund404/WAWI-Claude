# database/models/tool_checkout.py
"""
This module defines the ToolCheckout model for the leatherworking application.

It is used to track tool checkouts, returns, and manage the availability of tools.
"""
import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin


class ToolCheckout(AbstractBase, ValidationMixin):
    """
    Model for tracking tool checkouts.

    Used to record who has checked out tools, when they're due back,
    and the condition of tools before and after checkout.
    """
    __tablename__ = 'tool_checkouts'
    __table_args__ = {"extend_existing": True}

    # Foreign key relationship to Tool
    tool_id: Mapped[int] = mapped_column(
        ForeignKey("tools.id", name="fk_checkout_tool", ondelete="CASCADE"),
        nullable=False
    )

    # Checkout information
    checked_out_by: Mapped[str] = mapped_column(String(100), nullable=False)
    checked_out_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    returned_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    # Status and notes
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="checked_out")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Project association (optional)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", name="fk_checkout_project", ondelete="SET NULL"),
        nullable=True
    )

    # Condition information
    condition_before: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    condition_after: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    tool = relationship(
        "Tool",
        back_populates="checkouts",
        lazy="selectin"
    )

    project = relationship(
        "Project",
        back_populates="tool_checkouts",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a ToolCheckout instance with validation.

        Args:
            **kwargs: Keyword arguments for ToolCheckout initialization
        """
        # Set default values
        if "checked_out_date" not in kwargs:
            kwargs["checked_out_date"] = datetime.datetime.now()

        if "status" not in kwargs:
            kwargs["status"] = "checked_out"

        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate checkout record data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Tool ID validation
        if not self.tool_id or not isinstance(self.tool_id, int):
            raise ModelValidationError("Tool ID must be a valid integer")

        # User validation
        if not self.checked_out_by or not isinstance(self.checked_out_by, str):
            raise ModelValidationError("Checked out by must be a non-empty string")

        # Date validation
        if not self.checked_out_date:
            raise ModelValidationError("Checkout date is required")

        if self.returned_date and self.checked_out_date > self.returned_date:
            raise ModelValidationError("Return date cannot be before checkout date")

        # Project ID validation
        if self.project_id is not None and not isinstance(self.project_id, int):
            raise ModelValidationError("Project ID must be a valid integer or None")

        return self

    def update_status(self):
        """Update status based on dates."""
        if self.status == "returned":
            return

        now = datetime.datetime.now()
        if self.due_date and now > self.due_date:
            self.status = "overdue"
        else:
            self.status = "checked_out"

    def is_overdue(self) -> bool:
        """Check if the checkout is overdue.

        Returns:
            True if overdue, False otherwise
        """
        if self.status == "returned":
            return False

        if not self.due_date:
            return False

        return self.due_date < datetime.datetime.now()

    def days_overdue(self) -> Optional[int]:
        """Calculate days overdue.

        Returns:
            Number of days overdue, or None if not overdue
        """
        if not self.is_overdue():
            return None

        delta = datetime.datetime.now() - self.due_date
        return delta.days