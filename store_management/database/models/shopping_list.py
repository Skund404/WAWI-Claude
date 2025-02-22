# database/models/shopping_list.py
"""
Models for shopping list and shopping list items.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from .supplier import Supplier


class ShoppingList(BaseModel):
    """
    Represents a shopping list with multiple items.
    """
    __tablename__ = 'shopping_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=True)

    # Relationship with shopping list items
    items = relationship('ShoppingListItem', back_populates='shopping_list', cascade='all, delete-orphan')


class ShoppingListItem(BaseModel):
    """
    Represents an individual item in a shopping list.
    """
    __tablename__ = 'shopping_list_items'

    id = Column(Integer, primary_key=True)
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'), nullable=False)
    product_id = Column(Integer, nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)
    notes = Column(String(255), nullable=True)

    # Relationships
    shopping_list = relationship('ShoppingList', back_populates='items')
    supplier = relationship('Supplier', backref='shopping_list_items_alt')  # Use a different backref name