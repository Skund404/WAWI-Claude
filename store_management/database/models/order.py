# database/models/order.py
"""
Path: database/models/order.py
Order and OrderItem models defining the core order management functionality.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional, Dict, Any

from database.models.base import BaseModel
from database.models.enums import OrderStatus, PaymentStatus


class Order(BaseModel):
    """
    Order model representing customer orders in the system.

    Attributes:
        number (str): Unique order number
        customer_name (str): Name of the customer
        status (OrderStatus): Current order status
        payment_status (PaymentStatus): Current payment status
        total_amount (float): Total order amount
        notes (str): Additional order notes
        items (List[OrderItem]): List of order items
    """
    __tablename__ = 'orders'

    number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(100), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    notes = Column(String(500))

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize an order with the given attributes."""
        super().__init__(**kwargs)
        self.update_total()

    def update_total(self) -> None:
        """Recalculate and update the total order amount."""
        self.total_amount = sum(item.total_price for item in self.items)

    def add_item(self, item: 'OrderItem') -> None:
        """
        Add an item to the order.

        Args:
            item: OrderItem to add
        """
        self.items.append(item)
        self.update_total()

    def remove_item(self, item: 'OrderItem') -> None:
        """
        Remove an item from the order.

        Args:
            item: OrderItem to remove
        """
        self.items.remove(item)
        self.update_total()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert order to dictionary including related items.

        Returns:
            dict: Dictionary representation of the order
        """
        data = super().to_dict()
        data.update({
            'items': [item.to_dict() for item in self.items],
            'status': self.status.value if self.status else None,
            'payment_status': self.payment_status.value if self.payment_status else None
        })
        return data


class OrderItem(BaseModel):
    """
    OrderItem model representing individual items within an order.

    Attributes:
        order_id (int): Foreign key to parent order
        product_name (str): Name of the product
        quantity (int): Quantity ordered
        unit_price (float): Price per unit
        total_price (float): Total price for this item
    """
    __tablename__ = 'order_items'

    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")

    def __init__(self, **kwargs):
        """Initialize an order item with the given attributes."""
        super().__init__(**kwargs)
        self.update_total_price()

    def update_total_price(self) -> None:
        """Calculate and update the total price for this item."""
        self.total_price = self.quantity * self.unit_price

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert order item to dictionary.

        Returns:
            dict: Dictionary representation of the order item
        """
        data = super().to_dict()
        data.update({
            'order_id': self.order_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        })
        return data