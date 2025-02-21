# store_management/database/models/shopping_list.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class ShoppingList(Base):
    """Shopping list model"""
    __tablename__ = 'shopping_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ShoppingList(id={self.id}, name='{self.name}')>"


class ShoppingListItem(Base):
    """Shopping list item model"""
    __tablename__ = 'shopping_list_items'

    id = Column(Integer, primary_key=True)
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'))
    leather_id = Column(Integer, ForeignKey('leathers.id'))
    quantity = Column(Float)
    purchased = Column(Boolean, default=False)
    purchase_date = Column(DateTime)
    purchase_price = Column(Float)

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    part = relationship("Part")
    leather = relationship("Leather")

    def __repr__(self):
        return f"<ShoppingListItem(id={self.id}, shopping_list_id={self.shopping_list_id})>"