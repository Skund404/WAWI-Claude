# database/models/product.py
"""
Product model module for the leatherworking store management system.

Defines the Product class for tracking products.
"""

from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, Enum, Boolean
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import MaterialType


class Product(Base, BaseModel):
    """
    Represents a product in the leatherworking store.

    Attributes:
        name (str): Name of the product
        description (str, optional): Detailed description of the product
        price (float): Selling price of the product
        stock_quantity (int): Number of items in stock
        category (MaterialType): Category of the product
        weight (float, optional): Weight of the product
    """
    __tablename__ = 'product'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    stock_quantity = Column(Integer, nullable=False, default=0)
    category = Column(Enum(MaterialType), nullable=True)
    weight = Column(Float, nullable=True)
    sku = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    storage_id = Column(Integer, ForeignKey('storage.id'), nullable=True)
    storage = relationship("Storage", back_populates="products")

    def __repr__(self) -> str:
        """
        String representation of the Product model.

        Returns:
            str: A string showing product details
        """
        return f"<Product id={self.id}, name='{self.name}', stock={self.stock_quantity}>"

    def to_dict(self, include_order_items: bool = False) -> Dict[str, Any]:
        """
        Convert product to dictionary representation.

        Args:
            include_order_items (bool): Whether to include order item
            Returns:
            dict: Dictionary representation of the product
        """
        result = super().to_dict()

        if self.category:
            result['category'] = self.category.name

        if include_order_items:
            result['order_items'] = [item.to_dict() for item in self.order_items]

        return result

    def update_stock(self, quantity_change: int) -> None:
        """
        Update product stock quantity.

        Args:
            quantity_change: Amount to change the stock by

        Raises:
            ValueError: If resulting stock would be negative
        """
        new_quantity = self.stock_quantity + quantity_change
        if new_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")

        self.stock_quantity = new_quantity