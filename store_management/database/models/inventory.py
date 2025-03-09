# database/models/inventory.py
"""
This module defines the Inventory model for the leatherworking application.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, AuditMixin, ModelValidationError, TrackingMixin, ValidationMixin
from database.models.enums import InventoryAdjustmentType, InventoryStatus, TransactionType


class Inventory(AbstractBase, ValidationMixin, AuditMixin, TrackingMixin):
    """
    Unified inventory tracking for all item types with enhanced movement tracking.

    Attributes:
        item_type: Type discriminator ('material', 'product', 'tool')
        item_id: Foreign key to the corresponding item
        quantity: Current quantity in stock
        status: Inventory status
        min_stock_level: Threshold for low stock warning
        reorder_point: Quantity at which to reorder
        reorder_quantity: Standard quantity to reorder
        storage_location: Physical storage location
        location_details: Additional location information (aisle, shelf, bin, etc.)
        last_count_date: Date of last physical inventory count
        last_movement_date: Date of last inventory movement
        transaction_history: Log of recent transactions (limited entries kept in model)
        unit_cost: Current unit cost for valuation
        notes: Additional notes about the inventory item
    """
    __tablename__ = 'inventory'
    __table_args__ = (
        UniqueConstraint('item_type', 'item_id', name='uix_inventory_item'),
        {"extend_existing": True}
    )

    # Basic attributes
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus), nullable=False)

    # Enhanced inventory management fields
    min_stock_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reorder_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reorder_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    storage_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    last_count_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_movement_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Store recent transactions in the model (limited history)
    transaction_history: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    unit_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships - maintain compatibility with ER diagram
    material = relationship(
        "Material",
        primaryjoin="and_(Inventory.item_id==Material.id, Inventory.item_type=='material')",
        foreign_keys="[Inventory.item_id]",
        back_populates="inventory",
        uselist=False,
        lazy="selectin"
    )

    product = relationship(
        "Product",
        primaryjoin="and_(Inventory.item_id==Product.id, Inventory.item_type=='product')",
        foreign_keys="[Inventory.item_id]",
        back_populates="inventory",
        uselist=False,
        lazy="selectin"
    )

    tool = relationship(
        "Tool",
        primaryjoin="and_(Inventory.item_id==Tool.id, Inventory.item_type=='tool')",
        foreign_keys="[Inventory.item_id]",
        back_populates="inventory",
        uselist=False,
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize an Inventory instance with validation.

        Args:
            **kwargs: Keyword arguments for Inventory initialization
        """
        if 'transaction_history' not in kwargs:
            kwargs['transaction_history'] = []

        super().__init__(**kwargs)

        # Set default status based on quantity
        if 'status' not in kwargs:
            self._update_status()

        # Initialize location_details if not provided
        if not self.location_details:
            self.location_details = {}

        self.validate()

    def validate(self) -> None:
        """
        Validate inventory data.

        Raises:
            ModelValidationError: If validation fails
        """
        if self.quantity < 0:
            raise ModelValidationError("Inventory quantity cannot be negative")

        if not self.item_type:
            raise ModelValidationError("Item type must be specified")

        if self.item_type not in ('material', 'product', 'tool'):
            raise ModelValidationError("Invalid item type")

        if self.min_stock_level is not None and self.min_stock_level < 0:
            raise ModelValidationError("Minimum stock level cannot be negative")

        if self.reorder_point is not None and self.reorder_point < 0:
            raise ModelValidationError("Reorder point cannot be negative")

        if self.reorder_quantity is not None and self.reorder_quantity <= 0:
            raise ModelValidationError("Reorder quantity must be positive")

        return self

    def _update_status(self) -> None:
        """
        Update inventory status based on current quantity and thresholds.
        """
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.min_stock_level is not None and self.quantity <= self.min_stock_level:
            self.status = InventoryStatus.LOW_STOCK
        elif self.reorder_point is not None and self.quantity <= self.reorder_point:
            self.status = InventoryStatus.PENDING_REORDER
        else:
            self.status = InventoryStatus.IN_STOCK

    def update_quantity(self, change: float, transaction_type: TransactionType,
                        reference_type: Optional[str] = None, reference_id: Optional[int] = None,
                        notes: Optional[str] = None) -> None:
        """
        Update inventory quantity and status with transaction tracking.

        Args:
            change: The amount to add (positive) or subtract (negative)
            transaction_type: Type of transaction causing the quantity change
            reference_type: Type of reference document (e.g., 'purchase', 'sales')
            reference_id: ID of the reference document
            notes: Optional notes about the transaction
        """
        if self.quantity + change < 0:
            raise ModelValidationError(f"Cannot reduce quantity by {abs(change)} as only {self.quantity} available")

        previous_quantity = self.quantity
        self.quantity += change
        self.last_movement_date = datetime.now()
        self.updated_at = datetime.now()

        # Update status based on new quantity
        self._update_status()

        # Record the transaction
        transaction = {
            'date': datetime.now().isoformat(),
            'previous_quantity': previous_quantity,
            'new_quantity': self.quantity,
            'change': change,
            'transaction_type': transaction_type.name,
            'reference_type': reference_type,
            'reference_id': reference_id,
            'notes': notes
        }

        # Keep the 10 most recent transactions in the history
        if not self.transaction_history:
            self.transaction_history = []

        self.transaction_history.append(transaction)
        if len(self.transaction_history) > 10:
            self.transaction_history = self.transaction_history[-10:]

    def record_adjustment(self, quantity_change: float, adjustment_type: InventoryAdjustmentType,
                          reason: str, authorized_by: Optional[str] = None) -> None:
        """
        Record a manual inventory adjustment.

        Args:
            quantity_change: The amount to adjust (positive or negative)
            adjustment_type: Type of adjustment
            reason: Reason for the adjustment
            authorized_by: Person who authorized the adjustment
        """
        self.update_quantity(
            change=quantity_change,
            transaction_type=TransactionType.ADJUSTMENT,
            reference_type='adjustment',
            notes=f"Type: {adjustment_type.name}, Reason: {reason}, Auth: {authorized_by}"
        )

    def transfer_location(self, new_location: str, new_details: Optional[Dict[str, Any]] = None,
                          notes: Optional[str] = None) -> None:
        """
        Transfer inventory to a new storage location.

        Args:
            new_location: New storage location
            new_details: New location details (will be merged with existing)
            notes: Optional notes about the transfer
        """
        old_location = self.storage_location
        old_details = self.location_details or {}

        self.storage_location = new_location
        self.updated_at = datetime.now()

        if new_details:
            # Merge new details with existing details
            if not self.location_details:
                self.location_details = {}
            self.location_details.update(new_details)

        # Record the transaction
        transaction = {
            'date': datetime.now().isoformat(),
            'transaction_type': TransactionType.TRANSFER.name,
            'from_location': old_location,
            'to_location': new_location,
            'from_details': old_details,
            'to_details': self.location_details,
            'notes': notes
        }

        if not self.transaction_history:
            self.transaction_history = []

        self.transaction_history.append(transaction)
        if len(self.transaction_history) > 10:
            self.transaction_history = self.transaction_history[-10:]

    def record_physical_count(self, counted_quantity: float, adjustment_notes: Optional[str] = None,
                              counted_by: Optional[str] = None) -> None:
        """
        Record a physical inventory count and adjust as needed.

        Args:
            counted_quantity: The actual quantity counted
            adjustment_notes: Notes about any discrepancy
            counted_by: Person who performed the count
        """
        quantity_difference = counted_quantity - self.quantity

        if quantity_difference != 0:
            adjustment_type = (InventoryAdjustmentType.FOUND if quantity_difference > 0
                               else InventoryAdjustmentType.LOST)

            self.record_adjustment(
                quantity_change=quantity_difference,
                adjustment_type=adjustment_type,
                reason=f"Physical count adjustment. {adjustment_notes or ''}",
                authorized_by=counted_by
            )

        self.last_count_date = datetime.now()
        self.updated_at = datetime.now()

    def calculate_value(self) -> float:
        """
        Calculate the current value of this inventory item.

        Returns:
            float: The calculated value (quantity * unit_cost)
        """
        if self.unit_cost is None:
            return 0.0
        return self.quantity * self.unit_cost

    def needs_reorder(self) -> bool:
        """
        Check if this item needs to be reordered based on reorder point.

        Returns:
            bool: True if the item needs to be reordered, False otherwise
        """
        if self.reorder_point is None:
            return False
        return self.quantity <= self.reorder_point

    def days_since_last_count(self) -> Optional[int]:
        """
        Calculate days since last physical count.

        Returns:
            Optional[int]: Days since last count, or None if never counted
        """
        if self.last_count_date is None:
            return None
        delta = datetime.now() - self.last_count_date
        return delta.days

    def days_since_last_movement(self) -> Optional[int]:
        """
        Calculate days since last movement.

        Returns:
            Optional[int]: Days since last movement, or None if no movement recorded
        """
        if self.last_movement_date is None:
            return None
        delta = datetime.now() - self.last_movement_date
        return delta.days