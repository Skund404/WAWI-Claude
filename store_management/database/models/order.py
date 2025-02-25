# database/models/order.py
"""
Order model module for the leatherworking store management system.

Defines models for Order and OrderItem.
"""

import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import OrderStatus, PaymentStatus


class Order(Base, BaseModel):
    """
    Represents an order in the system.

    An order can contain multiple order items.
    """
    __tablename__ = 'orders'

    order_number = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    delivery_date = Column(DateTime, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="orders")

    def __repr__(self) -> str:
        """String representation of the Order model."""
        return f"<Order id={self.id}, number='{self.order_number}', status={self.status.name}>"

    def to_dict(self, include_items: bool = False) -> Dict[str, Any]:
        """
        Convert order to dictionary representation.

        Args:
            include_items (bool): Whether to include order items

        Returns:
            dict: Dictionary representation of the order
        """
        result = super().to_dict()
        result['status'] = self.status.name
        result['payment_status'] = self.payment_status.name
        result['order_date'] = self.order_date.isoformat() if self.order_date else None
        result['delivery_date'] = self.delivery_date.isoformat() if self.delivery_date else None

        if include_items:
            result['items'] = [item.to_dict() for item in self.items]

        return result

    def calculate_total(self) -> float:
        """
        Calculate the total order amount based on items.

        Returns:
            float: The calculated total amount
        """
        total = sum(item.get_total() for item in self.items)
        self.total_amount = total
        return total


class OrderItem(Base, BaseModel):
    """
    Represents an individual item within an order.
    """
    __tablename__ = 'order_items'

    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    description = Column(String(255), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self) -> str:
        """String representation of the OrderItem model."""
        return f"<OrderItem id={self.id}, order_id={self.order_id}, quantity={self.quantity}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert order item to dictionary representation.

        Returns:
            dict: Dictionary representation of the order item
        """
        result = super().to_dict()
        if self.product:
            result['product_name'] = self.product.name
        return result

    def get_total(self) -> float:
        """
        Calculate the total price for this item.

        Returns:
            float: Total price (quantity * unit_price)
        """
        return self.quantity * self.unit_price