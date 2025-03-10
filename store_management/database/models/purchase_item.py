# database/models/purchase_item.py
from datetime import datetime
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Any, Dict, List, Optional, Union
from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import TransactionType


class PurchaseItem(AbstractBase, ValidationMixin):
    """
    PurchaseItem represents an individual item line in a purchase order.

    Attributes:
        purchase_id: Foreign key to the purchase
        item_type: Type discriminator ('material', 'tool')
        item_id: Foreign key to the item
        quantity: Quantity purchased
        price: Price per unit
        received_quantity: Quantity already received
    """
    __tablename__ = 'purchase_items'

    purchase_id: Mapped[int] = mapped_column(Integer, ForeignKey('purchases.id'), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    received_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0"
    )

    # Relationships
    purchase: Mapped["Purchase"] = relationship(back_populates="items")

    # Dynamic relationships based on item_type
    material = relationship(
        "Material",
        primaryjoin="and_(PurchaseItem.item_id==Material.id, PurchaseItem.item_type=='material')",
        foreign_keys="[PurchaseItem.item_id]",
        overlaps="inventory",
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

    def receive(self, quantity: float, user: Optional[str] = None, notes: Optional[str] = None) -> None:
        """
        Record receipt of purchased items and update inventory.

        Args:
            quantity: Quantity received
            user: User recording the receipt
            notes: Optional notes about the receipt

        Raises:
            ValueError: If quantity is invalid or exceeds ordered quantity
        """
        if quantity <= 0:
            raise ValueError("Received quantity must be positive")

        if self.received_quantity + quantity > self.quantity:
            raise ValueError(
                f"Cannot receive {quantity} units; only {self.quantity - self.received_quantity} remaining to receive")

        # Record receipt
        self.received_quantity += quantity
        self.updated_at = datetime.now()
        if user:
            self.updated_by = user

        # Update inventory with proper transaction tracking
        self._update_inventory(quantity, user, notes)

    def _update_inventory(self, quantity: float, user: Optional[str] = None, notes: Optional[str] = None) -> None:
        """
        Update inventory for received items.

        Args:
            quantity: Quantity received
            user: User recording the receipt
            notes: Optional notes about the receipt
        """
        item = None
        if self.item_type == 'material' and hasattr(self, 'material') and self.material:
            item = self.material
        elif self.item_type == 'tool' and hasattr(self, 'tool') and self.tool:
            item = self.tool

        if item and hasattr(item, 'inventory'):
            # Create inventory record if it doesn't exist
            from database.models.inventory import Inventory
            from database.models.enums import InventoryStatus

            if not item.inventory:
                item.inventory = Inventory(
                    item_type=self.item_type,
                    item_id=self.item_id,
                    quantity=0,
                    status=InventoryStatus.OUT_OF_STOCK,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    created_by=user,
                    updated_by=user
                )

            # Prepare notes for transaction
            transaction_notes = f"Received from purchase #{self.purchase_id}"
            if notes:
                transaction_notes += f" - {notes}"

            # If cost is provided, update unit cost based on weighted average
            if self.price > 0:
                current_quantity = item.inventory.quantity
                current_value = current_quantity * (item.inventory.unit_cost or 0)
                new_value = quantity * self.price

                if current_quantity + quantity > 0:
                    new_unit_cost = (current_value + new_value) / (current_quantity + quantity)
                    item.inventory.unit_cost = new_unit_cost

            # Update inventory quantity with transaction tracking
            item.inventory.update_quantity(
                change=quantity,
                transaction_type=TransactionType.PURCHASE,
                reference_type='purchase',
                reference_id=self.purchase_id,
                notes=transaction_notes
            )

    def is_fully_received(self) -> bool:
        """Check if this item has been fully received."""
        return self.received_quantity >= self.quantity

    def get_remaining_quantity(self) -> float:
        """Get the remaining quantity to receive."""
        return max(0, self.quantity - self.received_quantity)

    def get_receipt_percentage(self) -> float:
        """Get the receipt completion percentage."""
        if self.quantity <= 0:
            return 100.0
        return min(100.0, (self.received_quantity / self.quantity) * 100)