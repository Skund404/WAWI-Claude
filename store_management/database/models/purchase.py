# database/models/purchase.py
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import PurchaseStatus


class Purchase(AbstractBase, ValidationMixin):
    """
    Purchase represents an order placed with a supplier.

    Attributes:
        supplier_id: Foreign key to the supplier
        total_amount: Total purchase amount
        status: Purchase status
        notes: Additional notes
    """
    __tablename__ = 'purchases'

    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Order tracking
    order_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Reference information
    purchase_order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a Purchase instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate purchase data."""
        if self.total_amount < 0:
            raise ModelValidationError("Total amount cannot be negative")

    def update_total_amount(self) -> None:
        """Recalculate the total amount based on the linked purchase items."""
        if not hasattr(self, 'items') or not self.items:
            self.total_amount = 0.0
            return

        self.total_amount = sum(item.price * item.quantity for item in self.items)

    def update_status(self, new_status: PurchaseStatus, notes: Optional[str] = None) -> None:
        """
        Update the purchase status and add notes.

        Args:
            new_status: New purchase status
            notes: Optional notes about the status change
        """
        old_status = self.status
        self.status = new_status

        # Update related dates based on status
        if new_status == PurchaseStatus.ORDERED and not self.order_date:
            self.order_date = datetime.now()
        elif new_status == PurchaseStatus.DELIVERED and not self.delivery_date:
            self.delivery_date = datetime.now()

        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note