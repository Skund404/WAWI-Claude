# Path: database/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from .base import BaseModel


class OrderStatus(PyEnum):
    """
    Enum representing different statuses of an order.
    """
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class PaymentStatus(PyEnum):
    """
    Enum representing different payment statuses of an order.
    """
    UNPAID = "Unpaid"
    PARTIAL = "Partial Payment"
    PAID = "Paid"
    REFUNDED = "Refunded"


class Order(BaseModel):
    """
    Represents an order in the inventory management system.

    Attributes:
        id (int): Unique identifier for the order
        order_number (str): Unique order number
        supplier_id (int): Foreign key to the supplier of the order
        status (OrderStatus): Current status of the order
        payment_status (PaymentStatus): Payment status of the order
        total_amount (float): Total amount of the order
        order_date (DateTime): Date the order was placed
        expected_delivery_date (DateTime): Expected delivery date
        actual_delivery_date (DateTime): Actual delivery date
        notes (str): Additional notes about the order

        supplier (relationship): Supplier associated with the order
        items (relationship): Items in the order
    """
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    status = Column(String(50), nullable=False, default=OrderStatus.PENDING.value)
    payment_status = Column(String(50), nullable=False, default=PaymentStatus.UNPAID.value)
    total_amount = Column(Float, nullable=False, default=0.0)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    supplier = relationship('Supplier', back_populates='orders')
    items = relationship('OrderItem', back_populates='order',
                         cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"

    def calculate_total_amount(self):
        """
        Recalculate the total amount based on order items.

        Returns:
            float: Total amount of the order
        """
        return sum(item.total_price for item in self.items)

    def update_total_amount(self):
        """
        Update the total amount of the order based on its items.
        """
        self.total_amount = self.calculate_total_amount()


class OrderItem(BaseModel):
    """
    Represents an individual item in an order.

    Attributes:
        id (int): Unique identifier for the order item
        order_id (int): Foreign key to the parent order
        part_id (int): Foreign key to the inventory part (optional)
        leather_id (int): Foreign key to the leather material (optional)
        quantity (float): Quantity of the item ordered
        unit_price (float): Unit price of the item
        total_price (float): Total price of the item
        notes (str): Additional notes about the order item

        order (relationship): Parent order
        part (relationship): Inventory part in the order
        leather (relationship): Leather material in the order
    """
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)

    # Relationships
    order = relationship('Order', back_populates='items')
    part = relationship('Part')
    leather = relationship('Leather')

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity})>"

    def update_total_price(self):
        """
        Calculate and update the total price of the order item.
        """
        self.total_price = self.quantity * self.unit_price