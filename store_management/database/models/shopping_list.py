"""
File: database/models/shopping_list.py
Shopping list model definitions.
Represents shopping lists and their items.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime

from database.models.base import Base


class ShoppingList(Base):
    """
    ShoppingList model representing lists of items to purchase.
    """
    __tablename__ = 'shopping_lists'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    date_required = Column(DateTime, nullable=True)
    is_complete = Column(Boolean, default=False)
    created_by = Column(String(100), nullable=True)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # Relationships - uncomment and adjust based on your actual relationships
    # items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the ShoppingList model."""
        return f"<ShoppingList(id={self.id}, name='{self.name}', is_complete={self.is_complete})>"


class ShoppingListItem(Base):
    """
    ShoppingListItem model representing individual items in a shopping list.
    """
    __tablename__ = 'shopping_list_items'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)
    description = Column(String(255), nullable=True)
    quantity = Column(Float, default=1.0)
    estimated_price = Column(Float, nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    is_purchased = Column(Boolean, default=False)
    purchase_date = Column(DateTime, nullable=True)
    purchase_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # shopping_list = relationship("ShoppingList", back_populates="items")
    # part = relationship("Part")
    # leather = relationship("Leather")
    # supplier = relationship("Supplier")

    def __repr__(self):
        """String representation of the ShoppingListItem model."""
        return f"<ShoppingListItem(id={self.id}, list_id={self.shopping_list_id}, purchased={self.is_purchased})>"