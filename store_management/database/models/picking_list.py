# database/models/picking_list.py
from database.models.base import Base
from database.models.enums import PickingListStatus
from sqlalchemy import Column, Enum, String, Text, Boolean, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class PickingList(Base):
    """
    Model representing a picking list for order fulfillment.
    """
    # PickingList specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT, nullable=False)

    creation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    completion_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="picking_lists")
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")
    user = relationship("User", back_populates="assigned_picking_lists")

    def __init__(self, **kwargs):
        """Initialize a PickingList instance with validation.

        Args:
            **kwargs: Keyword arguments with picking list attributes

        Raises:
            ValueError: If validation fails for any field
        """
        # Validate picking list data
        if 'name' not in kwargs or not kwargs['name']:
            raise ValueError("Picking list name is required")

        super().__init__(**kwargs)

    def mark_as_completed(self):
        """Mark the picking list as completed."""
        if self.status != PickingListStatus.COMPLETED:
            self.status = PickingListStatus.COMPLETED
            self.completion_date = datetime.utcnow()

    def mark_as_in_progress(self):
        """Mark the picking list as in progress."""
        if self.status != PickingListStatus.IN_PROGRESS:
            self.status = PickingListStatus.IN_PROGRESS

    def cancel(self):
        """Cancel the picking list."""
        if self.status != PickingListStatus.CANCELLED:
            self.status = PickingListStatus.CANCELLED

    def all_items_picked(self):
        """Check if all items in the picking list have been picked.

        Returns:
            bool: True if all items are picked
        """
        if not self.items:
            return False

        return all(item.is_picked for item in self.items)

    def __repr__(self):
        """Model representing an item in a picking list"""
        return f"<PickingList(id={self.id}, name='{self.name}', status={self.status})>"


class PickingListItem(Base):
    """
    Model representing an item in a picking list.
    """
    # PickingListItem specific fields
    quantity_required = Column(Float, default=1.0, nullable=False)
    quantity_picked = Column(Float, default=0.0, nullable=False)

    is_picked = Column(Boolean, default=False, nullable=False)
    picked_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys
    picking_list_id = Column(Integer, ForeignKey("picking_lists.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storage.id"), nullable=True)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    product = relationship("Product", uselist=False, viewonly=True)
    material = relationship("Material", uselist=False, viewonly=True)
    leather = relationship("Leather", uselist=False, viewonly=True)
    hardware = relationship("Hardware", uselist=False, viewonly=True)
    storage = relationship("Storage", uselist=False, viewonly=True)

    def __init__(self, **kwargs):
        """Initialize a PickingListItem instance with validation.

        Args:
            **kwargs: Keyword arguments with picking list item attributes

        Raises:
            ValueError: If validation fails for any field
        """
        # Validate picking list item data
        if 'picking_list_id' not in kwargs:
            raise ValueError("Picking list ID is required")

        if 'quantity_required' in kwargs and kwargs['quantity_required'] <= 0:
            raise ValueError("Quantity required must be greater than zero")

        # Ensure at least one item reference is provided
        if not any(key in kwargs for key in ['product_id', 'material_id', 'leather_id', 'hardware_id']):
            raise ValueError("At least one of product_id, material_id, leather_id, or hardware_id must be specified")

        super().__init__(**kwargs)

    def mark_as_picked(self, quantity=None):
        """Mark the item as picked.

        Args:
            quantity (float, optional): The quantity picked. If not provided, will use quantity_required.
        """
        if quantity is not None:
            self.quantity_picked = quantity
        else:
            self.quantity_picked = self.quantity_required

        self.is_picked = True
        self.picked_at = datetime.utcnow()

    def reset_picked_status(self):
        """Reset the picked status of the item."""
        self.is_picked = False
        self.quantity_picked = 0
        self.picked_at = None

    def __repr__(self):
        """String representation of the picking list item."""
        item_type = "Unknown"
        item_id = None

        if self.product_id:
            item_type = "Product"
            item_id = self.product_id
        elif self.material_id:
            item_type = "Material"
            item_id = self.material_id
        elif self.leather_id:
            item_type = "Leather"
            item_id = self.leather_id
        elif self.hardware_id:
            item_type = "Hardware"
            item_id = self.hardware_id

        return f"<PickingListItem(id={self.id}, type={item_type}, item_id={item_id}, picked={self.is_picked})>"