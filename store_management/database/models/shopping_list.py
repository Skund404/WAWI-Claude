# database/models/shopping_list.py
"""
Shopping list models for the leatherworking application.
With updated relationships that avoid circular dependencies.
"""

from database.models.base import Base
from database.models.enums import Priority
from sqlalchemy import Column, String, Text, Boolean, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class ShoppingList(Base):
    """
    Model representing a shopping list.
    """
    __tablename__ = 'shopping_lists'

    # Basic fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Status fields
    status = Column(String(50), default="DRAFT", nullable=False)
    priority = Column(String(50), default="MEDIUM", nullable=False)

    due_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    items = relationship("ShoppingListItem", back_populates="shopping_list", lazy="select")

    def mark_completed(self):
        """Mark the shopping list as completed."""
        self.status = "COMPLETED"
        self.completion_date = datetime.utcnow()

    def reset(self):
        """Reset the shopping list to draft status."""
        self.status = "DRAFT"
        self.completion_date = None

    def __repr__(self):
        """String representation of the shopping list."""
        return f"<ShoppingList(id={self.id}, name='{self.name}', status={self.status})>"


class ShoppingListItem(Base):
    """
    Model representing an item in a shopping list.
    """
    __tablename__ = 'shopping_list_items'

    # Shopping list item specific fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, nullable=True)
    estimated_total = Column(Float, nullable=True)

    priority = Column(String(50), default="MEDIUM", nullable=False)
    is_purchased = Column(Boolean, default=False, nullable=False)
    purchase_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardwares.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")

    # Use explicit primaryjoin for all relationships to avoid foreign key issues
    material = relationship("Material",
                            primaryjoin="ShoppingListItem.material_id==Material.id",
                            uselist=False, viewonly=True)

    leather = relationship("Leather",
                           primaryjoin="ShoppingListItem.leather_id==Leather.id",
                           uselist=False, viewonly=True)

    # This was the problematic relationship - use explicit primaryjoin
    hardware = relationship("Hardware",
                            primaryjoin="ShoppingListItem.hardware_id==Hardware.id",
                            uselist=False, viewonly=True)

    supplier = relationship("Supplier",
                            primaryjoin="ShoppingListItem.supplier_id==Supplier.id",
                            uselist=False)

    def __init__(self, **kwargs):
        """Initialize a ShoppingListItem instance with validation."""
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

        # Calculate estimated total if unit price is provided
        if 'unit_price' in kwargs and 'quantity' in kwargs and 'estimated_total' not in kwargs:
            self.estimated_total = kwargs['unit_price'] * kwargs['quantity']

    @classmethod
    def _validate_creation(cls, data):
        """Validate shopping list item attributes before saving."""
        if 'name' not in data or not data['name']:
            raise ValueError("Item name is required")

        if 'shopping_list_id' not in data or not data['shopping_list_id']:
            raise ValueError("Shopping list ID is required")

        if 'quantity' in data and data['quantity'] <= 0:
            raise ValueError("Quantity must be greater than zero")

        if 'unit_price' in data and data['unit_price'] < 0:
            raise ValueError("Unit price cannot be negative")

    def mark_purchased(self):
        """Mark the item as purchased."""
        self.is_purchased = True
        self.purchase_date = datetime.utcnow()

    def reset_purchase_status(self):
        """Reset the purchase status of the item."""
        self.is_purchased = False
        self.purchase_date = None

    def __repr__(self):
        """String representation of the shopping list item."""
        return f"<ShoppingListItem(id={self.id}, name='{self.name}', list_id={self.shopping_list_id}, purchased={self.is_purchased})>"