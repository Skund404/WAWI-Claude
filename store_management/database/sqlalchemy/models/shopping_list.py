# File: store_management/database/sqlalchemy/models/shopping_list.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base


class ShoppingList(Base):
    """
    Shopping List model for tracking items to be purchased.

    Attributes:
        id (int): Unique identifier for the shopping list
        name (str): Name or description of the shopping list
        created_at (datetime): Timestamp of list creation
        updated_at (datetime): Timestamp of last update
        is_completed (bool): Whether the shopping list is completed
        total_estimated_cost (float): Total estimated cost of items
    """
    __tablename__ = 'shopping_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    total_estimated_cost = Column(Float, default=0.0)

    # Relationships
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ShoppingList {self.name} - {'Completed' if self.is_completed else 'Pending'}>"


class ShoppingListItem(Base):
    """
    Individual items within a shopping list.

    Attributes:
        id (int): Unique identifier for the shopping list item
        shopping_list_id (int): Foreign key to the parent shopping list
        part_id (int): Foreign key to the part (optional)
        leather_id (int): Foreign key to the leather (optional)
        quantity (float): Quantity of the item to be purchased
        estimated_price (float): Estimated price of the item
        is_purchased (bool): Whether the item has been purchased
        supplier_id (int): Foreign key to the supplier
        purchase_date (datetime): Date of purchase
        actual_price (float): Actual price paid
        notes (str): Additional notes about the item
    """
    __tablename__ = 'shopping_list_items'

    id = Column(Integer, primary_key=True)
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'))
    leather_id = Column(Integer, ForeignKey('leathers.id'))
    quantity = Column(Float, nullable=False)
    estimated_price = Column(Float)
    is_purchased = Column(Boolean, default=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    purchase_date = Column(DateTime)
    actual_price = Column(Float)
    notes = Column(String)

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    part = relationship("Part")
    leather = relationship("Leather")
    supplier = relationship("Supplier")

    def __repr__(self):
        item_type = "Part" if self.part_id else "Leather" if self.leather_id else "Unknown"
        item_id = self.part_id or self.leather_id
        return f"<ShoppingListItem {self.id} - {item_type}: {item_id}, Qty: {self.quantity}, {'Purchased' if self.is_purchased else 'Pending'}>"