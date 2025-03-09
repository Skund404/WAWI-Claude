# database/models/purchase_item.py
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Union, Any

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError


class PurchaseItem(AbstractBase, ValidationMixin):
    """
    PurchaseItem represents an individual item line in a purchase order.

    Attributes:
        purchase_id: Foreign key to the purchase
        item_type: Type discriminator ('material', 'tool')
        item_id: Foreign key to the item
        quantity: Quantity purchased
        price: Price per unit
    """
    __tablename__ = 'purchase_items'

    purchase_id: Mapped[int] = mapped_column(Integer, ForeignKey('purchases.id'), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    received_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    purchase = relationship("Purchase", back_populates="items")

    # Dynamic relationships based on item_type
    material = relationship(
        "Material",
        primaryjoin="and_(PurchaseItem.item_id==Material.id, PurchaseItem.item_type=='material')",
        foreign_keys="[PurchaseItem.item_id]",
        overlaps="inventory",  # Add this line
        viewonly=True
    )
    tool = relationship(
        "Tool",
        primaryjoin="and_(PurchaseItem.item_id==Tool.id, PurchaseItem.item_type=='tool')",
        foreign_keys=[item_id],
        viewonly=True
    )

    def __init__(self, **kwargs):
        """Initialize a PurchaseItem instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate purchase item data."""
        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be positive")

        if self.price < 0:
            raise ModelValidationError("Price cannot be negative")

        if self.received_quantity < 0:
            raise ModelValidationError("Received quantity cannot be negative")

        if self.item_type not in ('material', 'tool'):
            raise ModelValidationError("Invalid item type")

    def get_subtotal(self) -> float:
        """Calculate the subtotal for this item."""
        return self.price * self.quantity

    def receive(self, quantity: float) -> None:
        """
        Record receipt of purchased items.

        Args:
            quantity: Quantity received
        """
        if quantity <= 0:
            raise ValueError("Received quantity must be positive")

        if self.received_quantity + quantity > self.quantity:
            raise ValueError("Received quantity cannot exceed ordered quantity")

        self.received_quantity += quantity

        # Update inventory - simplified version
        # In a full implementation, this would use a service to update inventory
        if self.received_quantity > 0:
            item = None
            if self.item_type == 'material' and self.material:
                item = self.material
            elif self.item_type == 'tool' and self.tool:
                item = self.tool

            if item and hasattr(item, 'inventory') and item.inventory:
                item.inventory.update_quantity(quantity)