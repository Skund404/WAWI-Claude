from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

"""
Order model definition with support for order items.
"""


class Order(BaseModel):
    """
    Represents a customer order in the system.

    Attributes:
        id (int): Primary key for the order.
        order_number (str): Unique order identifier.
        status (OrderStatus): Current status of the order.
        payment_status (PaymentStatus): Payment status of the order.
        customer_name (str): Name of the customer.
        total_amount (float): Total order amount.
        created_at (datetime): Timestamp of order creation.
        updated_at (datetime): Timestamp of last order update.
        items (list): List of order items associated with this order.
    """
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    customer_name = Column(String(100))
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                         onupdate=datetime.utcnow)
    items = relationship('OrderItem', back_populates='order',
                           cascade='all, delete-orphan', lazy='subquery')

    @inject(MaterialService)
    def __init__(self, order_number: str, customer_name: str = None):
        """
        Initialize an Order.

        Args:
            order_number (str): Unique order identifier.
            customer_name (str, optional): Name of the customer. Defaults to None.
        """
        self.order_number = order_number
        self.customer_name = customer_name

    @inject(MaterialService)
    def __repr__(self) -> str:
        """
        String representation of the Order.

        Returns:
            str: Formatted string describing the order.
        """
        return (
            f"<Order(id={self.id}, order_number='{self.order_number}', status={self.status}, total_amount={self.total_amount})>"
        )

    @inject(MaterialService)
    def calculate_total_amount(self) -> float:
        """
        Calculate the total amount of the order based on items.

        Returns:
            float: Total order amount.
        """
        self.total_amount = sum(item.calculate_total_price() for item in
                                 self.items)
        return self.total_amount

    @inject(MaterialService)
    def add_item(self, order_item: OrderItem) -> None:
        """
        Add an item to the order.

        Args:
            order_item (OrderItem): OrderItem to be added to the order.
        """
        order_item.order = self
        self.items.append(order_item)
        self.calculate_total_amount()

    @inject(MaterialService)
    def remove_item(self, order_item: OrderItem) -> None:
        """
        Remove an item from the order.

        Args:
            order_item (OrderItem): OrderItem to be removed from the order.
        """
        if order_item in self.items:
            self.items.remove(order_item)
            self.calculate_total_amount()

    @inject(MaterialService)
    def update_status(self, new_status: OrderStatus) -> None:
        """
        Update the order status.

        Args:
            new_status (OrderStatus): New status to set for the order.
        """
        self.status = new_status

    @inject(MaterialService)
    def update_payment_status(self, new_payment_status: PaymentStatus) -> None:
        """
        Update the payment status of the order.

        Args:
            new_payment_status (PaymentStatus): New payment status to set.
        """
        self.payment_status = new_payment_status

    @inject(MaterialService)
    def to_dict(self, include_items: bool = False) -> dict:
        """
        Convert Order to dictionary representation.

        Args:
            include_items (bool, optional): Whether to include order items. Defaults to False.

        Returns:
            dict: Dictionary containing Order attributes.
        """
        order_dict = {'id': self.id, 'order_number': self.order_number,
                      'status': self.status.value if self.status else None,
                      'payment_status': self.payment_status.value if self.
                      payment_status else None, 'customer_name': self.customer_name,
                      'total_amount': self.total_amount, 'created_at': self.
                      created_at.isoformat() if self.created_at else None,
                      'updated_at': self.updated_at.isoformat() if self.updated_at else
                      None}
        if include_items:
            order_dict['items'] = [item.to_dict() for item in self.items]
        return order_dict