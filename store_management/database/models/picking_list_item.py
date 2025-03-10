# database/models/picking_list_item.py
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Any, Dict, List, Optional
from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import TransactionType


class PickingListItem(AbstractBase, ValidationMixin):
    """
    PickingListItem represents an individual item in a picking list.

    Attributes:
        picking_list_id: Foreign key to the picking list
        component_id: Optional foreign key to a component
        material_id: Optional foreign key to a material
        quantity_ordered: Quantity needed
        quantity_picked: Quantity picked
    """
    __tablename__ = 'picking_list_items'

    picking_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    component_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('components.id'), nullable=True)
    material_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('materials.id'), nullable=True)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_picked: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # Relationships
    picking_list: Mapped["PickingList"] = relationship(back_populates="items")
    component: Mapped[Optional["Component"]] = relationship(back_populates="picking_list_items")
    material: Mapped[Optional["Material"]] = relationship(back_populates="picking_list_items")

    def __init__(self, **kwargs):
        """Initialize a PickingListItem instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate picking list item data."""
        if self.quantity_ordered <= 0:
            raise ModelValidationError("Quantity ordered must be positive")

        if self.quantity_picked < 0:
            raise ModelValidationError("Quantity picked cannot be negative")

        # Ensure either component or material is specified, but not both or neither
        if (self.component_id is None and self.material_id is None) or \
                (self.component_id is not None and self.material_id is not None):
            raise ModelValidationError("Either component or material must be specified, but not both")

    def is_fully_picked(self) -> bool:
        """Check if the item has been fully picked."""
        return self.quantity_picked >= self.quantity_ordered

    def pick(self, quantity: int, user: Optional[str] = None) -> None:
        """
        Record picked quantity and update inventory.

        Args:
            quantity: Quantity picked
            user: User who performed the picking

        Raises:
            ValueError: If quantity is not positive or exceeds available inventory
        """
        if quantity <= 0:
            raise ValueError("Picked quantity must be positive")

        # Calculate the remaining quantity to pick
        remaining_to_pick = self.quantity_ordered - self.quantity_picked
        if quantity > remaining_to_pick:
            raise ValueError(f"Cannot pick {quantity} units; only {remaining_to_pick} remaining to pick")

        self.quantity_picked += quantity
        self.updated_at = datetime.now()
        if user:
            self.updated_by = user

        # Update inventory
        if self.material_id and hasattr(self, 'material') and self.material and hasattr(self.material,
                                                                                        'inventory') and self.material.inventory:
            try:
                # Get reference information from the picking list
                reference_type = 'picking_list'
                reference_id = self.picking_list_id
                sales_id = self.picking_list.sales_id if hasattr(self.picking_list, 'sales_id') else None

                # Prepare notes for the inventory transaction
                notes = f"Picked for picking list #{self.picking_list_id}"
                if sales_id:
                    notes += f" (Sales #{sales_id})"

                # Update the inventory with proper transaction tracking
                self.material.inventory.update_quantity(
                    change=-quantity,
                    transaction_type=TransactionType.USAGE,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    notes=notes
                )
            except ModelValidationError as e:
                # Revert the picked quantity if inventory update fails
                self.quantity_picked -= quantity
                raise ValueError(f"Cannot pick {quantity} units: {str(e)}")

    def return_to_inventory(self, quantity: int, user: Optional[str] = None, reason: Optional[str] = None) -> None:
        """
        Return picked items to inventory.

        Args:
            quantity: Quantity to return
            user: User who performed the return
            reason: Reason for returning items

        Raises:
            ValueError: If quantity is not positive or exceeds picked quantity
        """
        if quantity <= 0:
            raise ValueError("Return quantity must be positive")

        if quantity > self.quantity_picked:
            raise ValueError(f"Cannot return {quantity} units; only {self.quantity_picked} were picked")

        self.quantity_picked -= quantity
        self.updated_at = datetime.now()
        if user:
            self.updated_by = user

        # Update inventory
        if self.material_id and hasattr(self, 'material') and self.material and hasattr(self.material,
                                                                                        'inventory') and self.material.inventory:
            notes = f"Returned to inventory from picking list #{self.picking_list_id}"
            if reason:
                notes += f" - Reason: {reason}"

            # Update the inventory with proper transaction tracking
            self.material.inventory.update_quantity(
                change=quantity,
                transaction_type=TransactionType.RETURN,
                reference_type='picking_list',
                reference_id=self.picking_list_id,
                notes=notes
            )