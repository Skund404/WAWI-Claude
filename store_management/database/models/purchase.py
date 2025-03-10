# database/models/purchase.py
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import PurchaseStatus, TransactionType


class Purchase(AbstractBase, ValidationMixin):
    """
    Purchase represents an order placed with a supplier.

    Attributes:
        supplier_id: Foreign key to the supplier
        total_amount: Total purchase amount
        status: Purchase status
        notes: Additional notes
        order_date: When the order was placed
        expected_delivery: Expected delivery date
        delivery_date: Actual delivery date
        purchase_order_number: PO number for reference
        invoice_number: Invoice number for reference
    """
    __tablename__ = 'purchases'
    __table_args__ = {'extend_existing': True}

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
    supplier: Mapped["Supplier"] = relationship(back_populates="purchases")
    items: Mapped[List["PurchaseItem"]] = relationship(back_populates="purchase", cascade="all, delete-orphan")

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

    def update_status(self, new_status: PurchaseStatus, user: Optional[str] = None,
                      notes: Optional[str] = None) -> None:
        """
        Update the purchase status and handle inventory implications.

        Args:
            new_status: New purchase status
            user: User making the status change
            notes: Optional notes about the status change
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        if user:
            self.updated_by = user

        # Update related dates based on status
        if new_status == PurchaseStatus.ORDERED and not self.order_date:
            self.order_date = datetime.now()
        elif new_status == PurchaseStatus.DELIVERED and not self.delivery_date:
            self.delivery_date = datetime.now()

        # Add notes about status change
        if notes:
            status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
            if self.notes:
                self.notes += f"\n{status_note}"
            else:
                self.notes = status_note

    def receive_items(self, receipt_data: Dict[int, float], user: Optional[str] = None,
                      notes: Optional[str] = None) -> None:
        """
        Record receipt of multiple items at once.

        Args:
            receipt_data: Dictionary mapping purchase_item_id to received quantity
            user: User recording the receipt
            notes: Optional notes about the receipt

        Raises:
            ValueError: If any items cannot be received
        """
        errors = []

        # First validate all quantities to ensure the operation is atomic
        for item_id, quantity in receipt_data.items():
            try:
                item = next((item for item in self.items if item.id == item_id), None)
                if not item:
                    errors.append(f"Item {item_id} not found in this purchase")
                    continue

                if quantity <= 0:
                    errors.append(f"Item {item_id}: Received quantity must be positive")

                if item.received_quantity + quantity > item.quantity:
                    errors.append(f"Item {item_id}: Cannot receive more than ordered quantity")
            except Exception as e:
                errors.append(f"Item {item_id}: {str(e)}")

        if errors:
            raise ValueError(f"Cannot receive items: {'; '.join(errors)}")

        # If validation passes, process all receipts
        receipt_date = datetime.now()
        receipt_note = f"Bulk receipt on {receipt_date.strftime('%Y-%m-%d %H:%M')}"
        if notes:
            receipt_note += f": {notes}"

        for item_id, quantity in receipt_data.items():
            item = next((item for item in self.items if item.id == item_id), None)
            if item:
                item.receive(quantity, user, receipt_note)

        # Check if all items have been fully received
        if all(item.received_quantity >= item.quantity for item in self.items):
            self.update_status(PurchaseStatus.RECEIVED, user, "All items received")
        else:
            self.update_status(PurchaseStatus.PARTIALLY_RECEIVED, user, "Some items received")

    def get_receipt_status(self) -> Dict[str, Any]:
        """
        Get the receipt status of this purchase.

        Returns:
            Dict containing receipt statistics and status
        """
        total_items = len(self.items) if self.items else 0
        if total_items == 0:
            return {
                'status': 'EMPTY',
                'total_items': 0,
                'received_items': 0,
                'completion_percentage': 0,
                'items_detail': []
            }

        received_items = sum(1 for item in self.items if item.received_quantity >= item.quantity)

        items_detail = [
            {
                'id': item.id,
                'item_type': item.item_type,
                'item_id': item.item_id,
                'ordered': item.quantity,
                'received': item.received_quantity,
                'remaining': item.quantity - item.received_quantity,
                'completion_percentage': (item.received_quantity / item.quantity * 100) if item.quantity > 0 else 0
            }
            for item in self.items
        ]

        return {
            'status': self.status.name,
            'total_items': total_items,
            'received_items': received_items,
            'completion_percentage': (received_items / total_items * 100) if total_items > 0 else 0,
            'items_detail': items_detail
        }