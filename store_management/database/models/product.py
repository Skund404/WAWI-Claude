# database/models/product.py
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from typing import List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError, CostingMixin
from database.models.relationship_tables import product_pattern_table


class Product(AbstractBase, ValidationMixin, CostingMixin):
    """
    Product represents a finished good available for sale.

    Attributes:
        name: Product name
        description: Detailed description
        price: Retail price
        is_active: Whether the product is active in catalog
    """
    __tablename__ = 'products'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    patterns = relationship(
        "Pattern",
        secondary="product_patterns",
        back_populates="products"
    )

    sales_items = relationship("SalesItem", back_populates="product")

    # Fixed inventory relationship with proper foreign key annotation
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Product.id==Inventory.item_id, Inventory.item_type=='product')",
        foreign_keys="[Inventory.item_id]",
        back_populates="product",
        uselist=False
    )

    def __init__(self, **kwargs):
        """Initialize a Product instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate product data."""
        if not self.name:
            raise ModelValidationError("Product name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Product name cannot exceed 255 characters")

        if self.price < 0:
            raise ModelValidationError("Product price cannot be negative")

    def calculate_profit(self) -> Optional[float]:
        """Calculate profit amount per unit."""
        if not self.cost_price:
            return None
        return self.price - self.cost_price

    def calculate_margin_percentage(self) -> Optional[float]:
        """Calculate margin percentage."""
        if not self.cost_price or self.price <= 0:
            return None
        return ((self.price - self.cost_price) / self.price) * 100