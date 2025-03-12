# database/models/product.py
"""
This module defines the Product model for the leatherworking application.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from database.models.base import AbstractBase, CostingMixin, ModelValidationError, ValidationMixin
from database.models.enums import ProjectType

# Import the relationship table from the central location
from database.models.relationship_tables import product_pattern_table


class Product(AbstractBase, ValidationMixin, CostingMixin):
    """
    Product model representing items that can be sold.

    Products can be linked to one or more patterns and can be sold through sales items.
    """
    __tablename__ = 'products'
    __table_args__ = {"extend_existing": True}

    # Basic attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=expression.true())

    # Relationships
    patterns = relationship(
        "Pattern",
        secondary=product_pattern_table,
        back_populates="products",
        lazy="selectin"
    )

    sales_items = relationship(
        "SalesItem",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Inventory relationship
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Product.id==Inventory.item_id, Inventory.item_type=='product')",
        foreign_keys="[Inventory.item_id]",
        back_populates="product",
        uselist=False,
        lazy="selectin",
        overlaps="inventory"  # Add this parameter
    )

    def __init__(self, **kwargs):
        """
        Initialize a Product instance with validation.

        Args:
            **kwargs: Keyword arguments for Product initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate product data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Name validation
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Product name must be a non-empty string")

        if len(self.name) > 255:
            raise ModelValidationError("Product name cannot exceed 255 characters")

        # Description validation
        if self.description and len(self.description) > 1000:
            raise ModelValidationError("Product description cannot exceed 1000 characters")

        # Price validation
        if self.price < 0:
            raise ModelValidationError("Product price cannot be negative")

        return self

    def get_stock_level(self) -> float:
        """
        Get the current stock level for this product.

        Returns:
            float: Current quantity in stock, or 0 if no inventory record exists
        """
        if self.inventory:
            return self.inventory.quantity
        return 0.0

    def is_in_stock(self) -> bool:
        """
        Check if this product is currently in stock.

        Returns:
            bool: True if product is in stock (quantity > 0), False otherwise
        """
        return self.get_stock_level() > 0

    def update_inventory(self, change: float, transaction_type: str,
                         reference_type: Optional[str] = None,
                         reference_id: Optional[int] = None,
                         notes: Optional[str] = None) -> None:
        """
        Update the inventory for this product.

        Creates an inventory record if one doesn't exist yet.

        Args:
            change: Quantity change (positive for additions, negative for reductions)
            transaction_type: Type of transaction
            reference_type: Optional reference type (e.g., 'sales', 'production')
            reference_id: Optional reference ID
            notes: Optional notes about the transaction
        """
        from database.models.enums import InventoryStatus, TransactionType
        from database.models.inventory import Inventory

        # Create inventory record if it doesn't exist
        if not self.inventory:
            self.inventory = Inventory(
                item_type='product',
                item_id=self.id,
                quantity=0,
                status=InventoryStatus.OUT_OF_STOCK,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

        # Update the inventory
        self.inventory.update_quantity(
            change=change,
            transaction_type=TransactionType[transaction_type],
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )