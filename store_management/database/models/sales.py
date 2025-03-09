# database/models/sales.py
"""
This module defines the Sales model for the leatherworking application.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, CostingMixin, ModelValidationError, ValidationMixin
from database.models.enums import PaymentStatus, SaleStatus


class Sales(AbstractBase, ValidationMixin, CostingMixin):
    """
    Sales model representing a sale transaction.

    A sale can have multiple sales items and can be associated with a customer.
    It can also generate picking lists and projects.
    """
    __tablename__ = 'sales'
    __table_args__ = {"extend_existing": True}

    # Basic attributes
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus),
        nullable=False,
        default=SaleStatus.QUOTE_REQUEST
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING
    )

    # Foreign keys
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    customer = relationship(
        "Customer",
        back_populates="sales",
        lazy="selectin"
    )

    sales_items = relationship(
        "SalesItem",
        back_populates="sales",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Break the circular dependency using string-based primaryjoin
    projects = relationship(
        "Project",
        primaryjoin="Sales.id==Project.sales_id",
        lazy="selectin",
        viewonly=True  # Use viewonly to break circular references
    )

    # These will be implemented later
    # picking_lists = relationship(
    #     "PickingList",
    #     back_populates="sales",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )

    def __init__(self, **kwargs):
        """
        Initialize a Sales instance with validation.

        Args:
            **kwargs: Keyword arguments for Sales initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate sales data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Total amount validation
        if self.total_amount < 0:
            raise ModelValidationError("Total amount cannot be negative")

        # Status validation
        if not self.status:
            raise ModelValidationError("Sales status must be specified")

        # Payment status validation
        if not self.payment_status:
            raise ModelValidationError("Payment status must be specified")

        return self

    def calculate_total(self) -> float:
        """
        Calculate the total amount based on sales items.

        Returns:
            float: The calculated total amount
        """
        total = sum(item.price * item.quantity for item in self.sales_items) if self.sales_items else 0
        self.total_amount = total
        return total