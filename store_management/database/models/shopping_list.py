# database/models/shopping_list.py
"""
Shopping list model module for the leatherworking store management system.

Defines models for ShoppingList and ShoppingListItem.
"""

import enum
import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import Priority


class ShoppingList(Base, BaseModel):
    """
    Model for shopping lists.

    A shopping list represents a collection of items that need to be purchased,
    either for specific projects or general inventory replenishment.
    """
    __tablename__ = 'shopping_list'

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    is_completed = Column(Boolean, default=False)

    # Relationships
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """
        Return a string representation of the shopping list.

        Returns:
            str: String representation with id and name
        """
        return f"<ShoppingList id={self.id}, name='{self.name}'>"

    def get_total_estimated_cost(self) -> float:
        """
        Calculate the total estimated cost of all items in the list.

        Returns:
            float: Total estimated cost
        """
        return sum(item.estimated_cost for item in self.items)

    def get_pending_items(self) -> List['ShoppingListItem']:
        """
        Get items that have not been purchased yet.

        Returns:
            List[ShoppingListItem]: List of pending items
        """
        return [item for item in self.items if not item.is_purchased]

    def get_completion_percentage(self) -> float:
        """
        Calculate the percentage of items that have been purchased.

        Returns:
            float: Completion percentage (0-100)
        """
        if not self.items:
            return 0.0

        purchased_count = sum(1 for item in self.items if item.is_purchased)
        return (purchased_count / len(self.items)) * 100


class ShoppingListItem(Base, BaseModel):
    """
    Model for items in a shopping list.

    A shopping list item represents a specific material or part that
    needs to be purchased, along with quantity and purchasing details.
    """
    __tablename__ = 'shopping_list_item'

    shopping_list_id = Column(Integer, ForeignKey('shopping_list.id'), nullable=False)
    name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    actual_cost = Column(Float, nullable=True)

    # Links to specific inventory items
    material_id = Column(Integer, ForeignKey('material.id'), nullable=True)
    part_id = Column(Integer, ForeignKey('part.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)

    # Purchase tracking
    is_purchased = Column(Boolean, default=False)
    purchase_date = Column(DateTime, nullable=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    notes = Column(Text, nullable=True)

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    material = relationship("Material", backref="shopping_list_items")
    part = relationship("Part", backref="shopping_list_items")
    leather = relationship("Leather", backref="shopping_list_items")

    def __repr__(self) -> str:
        """
        Return a string representation of the shopping list item.

        Returns:
            str: String representation with id and name
        """
        return f"<ShoppingListItem id={self.id}, name='{self.name}'>"

    def mark_as_purchased(self, actual_cost: Optional[float] = None) -> None:
        """
        Mark the item as purchased.

        Args:
            actual_cost: The actual cost of the item (optional)
        """
        self.is_purchased = True
        self.purchase_date = datetime.datetime.utcnow()

        if actual_cost is not None:
            self.actual_cost = actual_cost