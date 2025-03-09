# database/models/sales_item.py
"""
This module defines the SalesItem model for the leatherworking application.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin


class SalesItem(AbstractBase, ValidationMixin):
    """
    SalesItem model representing an item in a sales transaction.

    Each sales item is associated with a product and has a quantity and price.
    """
    __tablename__ = 'sales_items'
    __table_args__ = {"extend_existing": True}

    # Basic attributes
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Foreign keys
    sales_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    sales = relationship(
        "Sales",
        back_populates="sales_items",
        lazy="selectin"
    )

    product = relationship(
        "Product",
        back_populates="sales_items",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a SalesItem instance with validation.

        Args:
            **kwargs: Keyword arguments for SalesItem initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate sales item data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Quantity validation
        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be positive")

        # Price validation
        if self.price < 0:
            raise ModelValidationError("Price cannot be negative")

        return self

    def calculate_subtotal(self) -> float:
        """
        Calculate the subtotal for this item.

        Returns:
            float: The subtotal (price * quantity)
        """
        return self.price * self.quantity