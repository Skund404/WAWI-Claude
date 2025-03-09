# database/models/picking_list_item.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError


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
    quantity_picked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    component = relationship("Component", back_populates="picking_list_items")
    material = relationship("Material", back_populates="picking_list_items")

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

    def pick(self, quantity: int) -> None:
        """
        Record picked quantity.

        Args:
            quantity: Quantity picked
        """
        if quantity <= 0:
            raise ValueError("Picked quantity must be positive")

        self.quantity_picked += quantity

        # Update inventory - simplified version
        # In a full implementation, this would use a service to update inventory
        if self.material_id and hasattr(self, 'material') and self.material and hasattr(self.material,
                                                                                        'inventory') and self.material.inventory:
            self.material.inventory.update_quantity(-quantity)