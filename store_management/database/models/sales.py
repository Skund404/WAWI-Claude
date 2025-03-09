# database/models/sales.py
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError, CostingMixin
from database.models.enums import SaleStatus, PaymentStatus


class Sales(AbstractBase, ValidationMixin, CostingMixin):
    """
    Sales represents a customer purchase.

    Attributes:
        customer_id: Foreign key to the customer
        total_amount: Total sale amount
        status: Sale status
        payment_status: Payment status
        notes: Additional notes
    """
    __tablename__ = 'sales'

    customer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('customers.id'), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), nullable=False, default=SaleStatus.DRAFT)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False,
                                                          default=PaymentStatus.PENDING)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment tracking
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Shipping information
    shipping_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SalesItem", back_populates="sales", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="sales")
    picking_list = relationship("PickingList", back_populates="sales", uselist=False)

    def __init__(self, **kwargs):
        """Initialize a Sales instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate sales data."""
        if self.total_amount < 0:
            raise ModelValidationError("Total amount cannot be negative")

        if self.amount_paid < 0:
            raise ModelValidationError("Amount paid cannot be negative")

        if self.amount_paid > self.total_amount:
            raise ModelValidationError("Amount paid cannot exceed total amount")

    def update_total_amount(self) -> None:
        """Recalculate the total amount based on the linked sales items."""
        if not hasattr(self, 'items') or not self.items:
            self.total_amount = 0.0
            return

        self.total_amount = sum(item.price * item.quantity for item in self.items)

    def update_status(self, new_status: SaleStatus, notes: Optional[str] = None) -> None:
        """
        Update the sales status and add notes.

        Args:
            new_status: New sales status
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

    def update_payment_status(self, new_status: PaymentStatus, amount: Optional[float] = None) -> None:
        """
        Update the payment status and record payment if applicable.

        Args:
            new_status: New payment status
            amount: Optional payment amount
        """
        old_status = self.payment_status
        self.payment_status = new_status

        if amount is not None and amount > 0:
            self.amount_paid += amount
            self.payment_date = datetime.now()

            # Update payment status based on amount
            if self.amount_paid >= self.total_amount:
                self.payment_status = PaymentStatus.PAID
            elif self.amount_paid > 0:
                self.payment_status = PaymentStatus.PARTIALLY_PAID