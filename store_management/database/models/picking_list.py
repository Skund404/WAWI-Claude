# database/models/picking_list.py
from sqlalchemy import Column, Enum, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import PickingListStatus


class PickingList(AbstractBase, ValidationMixin):
    """
    PickingList represents a material picking list for production.

    Attributes:
        sales_id: Foreign key to the sales order
        status: Picking list status
        completed_at: When the picking was completed
    """
    __tablename__ = 'picking_lists'

    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sales.id'), nullable=True)
    status: Mapped[PickingListStatus] = mapped_column(Enum(PickingListStatus), nullable=False,
                                                      default=PickingListStatus.DRAFT)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    sales = relationship("Sales", back_populates="picking_list")
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a PickingList instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate picking list data."""
        pass  # Basic validation is handled by type annotations

    def update_status(self, new_status: PickingListStatus, notes: Optional[str] = None) -> None:
        """
        Update the picking list status.

        Args:
            new_status: New picking list status
            notes: Optional notes about the status change
        """
        old_status = self.status
        self.status = new_status

        # Update completion date if completed
        if new_status == PickingListStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()

        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note

    def is_complete(self) -> bool:
        """Check if all items have been picked."""
        if not self.items:
            return False

        return all(item.is_fully_picked() for item in self.items)