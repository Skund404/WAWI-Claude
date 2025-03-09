# database/models/sales_item.py
from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError


class SalesItem(AbstractBase, ValidationMixin):
    """
    SalesItem represents an individual product line in a sale.

    Attributes:
        sales_id: Foreign key to the sale
        product_id: Foreign key to the product
        quantity: Quantity sold
        price: Price per unit
    """
    __tablename__ = 'sales_items'

    sales_id: Mapped[int] = mapped_column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    sales = relationship("Sales", back_populates="items")
    product = relationship("Product", back_populates="sales_items")

    def __init__(self, **kwargs):
        """Initialize a SalesItem instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate sales item data."""
        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be positive")

        if self.price < 0:
            raise ModelValidationError("Price cannot be negative")

    def get_subtotal(self) -> float:
        """Calculate the subtotal for this item."""
        return self.price * self.quantity