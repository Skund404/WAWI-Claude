# database/models/tool_maintenance.py
"""
This module defines the ToolMaintenance model for the leatherworking application.

It is used to track maintenance activities performed on tools, including
routine maintenance, repairs, and inspections.
"""
import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin


class ToolMaintenance(AbstractBase, ValidationMixin):
    """
    Model for tracking tool maintenance activities.

    Used to record all maintenance performed on tools, including scheduled
    maintenance, repairs, and inspections.
    """
    __tablename__ = 'tool_maintenance'
    __table_args__ = {"extend_existing": True}

    # Foreign key relationship to Tool
    tool_id: Mapped[int] = mapped_column(
        ForeignKey("tools.id", name="fk_maintenance_tool", ondelete="CASCADE"),
        nullable=False
    )

    # Maintenance information
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    maintenance_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    performed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Completed")

    # Maintenance details
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Next maintenance
    maintenance_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in days
    next_maintenance_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    # Condition tracking
    condition_before: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    condition_after: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    tool = relationship(
        "Tool",
        back_populates="maintenance_records",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a ToolMaintenance instance with validation.

        Args:
            **kwargs: Keyword arguments for ToolMaintenance initialization
        """
        # Set default values
        if "maintenance_date" not in kwargs:
            kwargs["maintenance_date"] = datetime.datetime.now()

        if "status" not in kwargs:
            kwargs["status"] = "Completed"

        # Calculate next maintenance date if interval provided
        if "maintenance_interval" in kwargs and kwargs["maintenance_interval"] and "maintenance_date" in kwargs:
            interval = kwargs["maintenance_interval"]
            date = kwargs["maintenance_date"]
            kwargs["next_maintenance_date"] = date + datetime.timedelta(days=interval)

        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate maintenance record data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Tool ID validation
        if not self.tool_id or not isinstance(self.tool_id, int):
            raise ModelValidationError("Tool ID must be a valid integer")

        # Maintenance type validation
        if not self.maintenance_type or not isinstance(self.maintenance_type, str):
            raise ModelValidationError("Maintenance type must be a non-empty string")

        # Date validation
        if not self.maintenance_date:
            raise ModelValidationError("Maintenance date is required")

        # Cost validation
        if self.cost is not None and self.cost < 0:
            raise ModelValidationError("Maintenance cost cannot be negative")

        # Interval validation
        if self.maintenance_interval is not None and self.maintenance_interval < 0:
            raise ModelValidationError("Maintenance interval cannot be negative")

        return self