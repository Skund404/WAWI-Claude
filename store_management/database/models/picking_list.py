# database/models/picking_list.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Enum, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import PickingListStatus, TransactionType


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
    sales: Mapped["Sales"] = relationship(back_populates="picking_list")
    items: Mapped[List["PickingListItem"]] = relationship(back_populates="picking_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a PickingList instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate picking list data."""
        pass  # Basic validation is handled by type annotations

    def update_status(self, new_status: PickingListStatus, user: Optional[str] = None,
                      notes: Optional[str] = None) -> None:
        """
        Update the picking list status and handle inventory implications.

        Args:
            new_status: New picking list status
            user: User making the status change
            notes: Optional notes about the status change
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        if user:
            self.updated_by = user

        # Update completion date if completed
        if new_status == PickingListStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()

            # When completing a picking list, verify that all items are picked
            if not self.is_complete():
                self.status = old_status
                raise ModelValidationError("Cannot complete picking list: not all items have been fully picked")

        # Add notes about status change
        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note

        # Handle canceled picking lists by returning items to inventory
        if new_status == PickingListStatus.CANCELLED and old_status != PickingListStatus.CANCELLED:
            self._return_picked_items_to_inventory(user)

    def is_complete(self) -> bool:
        """Check if all items have been picked."""
        if not self.items:
            return False

        return all(item.is_fully_picked() for item in self.items)

    def _return_picked_items_to_inventory(self, user: Optional[str] = None) -> None:
        """
        Return all picked items to inventory when a picking list is canceled.

        Args:
            user: User who canceled the picking list
        """
        for item in self.items:
            if item.quantity_picked > 0:
                try:
                    item.return_to_inventory(
                        quantity=item.quantity_picked,
                        user=user,
                        reason="Picking list canceled"
                    )
                except ValueError as e:
                    # Log error but continue with other items
                    error_note = f"[ERROR] Failed to return item {item.id} to inventory: {str(e)}"
                    if self.notes:
                        self.notes += f"\n{error_note}"
                    else:
                        self.notes = error_note