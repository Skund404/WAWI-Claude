# File: store_management/database/sqlalchemy/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base
from store_management.database.sqlalchemy.models.enums import OrderStatus, PaymentStatus


class Order(Base):
    """
    Purchase order model representing orders in the system.

    Attributes:
        id (int): Unique identifier for the order
        order_number (str): Unique order number
        supplier_id (int): Foreign key to the supplier
        order_date (datetime): Date of order creation
        expected_delivery_date (datetime): Expected delivery date
        total_amount (float): Total order amount
        status (OrderStatus): Current order status
        payment_status (PaymentStatus): Current payment status
        is_paid (bool): Whether the order is fully paid
        notes (str): Additional notes about the order
        created_at (datetime): Timestamp of record creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery_date = Column(DateTime)
    total_amount = Column(Float, default=0.0)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    is_paid = Column(Boolean, default=False)
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(Base):
    """
    Individual items within an order.

    Attributes:
        id (int): Unique identifier for the order item
        order_id (int): Foreign key to the parent order
        part_id (int): Foreign key to the part
        quantity (float): Quantity of the part ordered
        unit_price (float): Price per unit
        total_price (float): Total price for this item
        notes (str): Additional notes about the item
    """
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    notes = Column(String)

    # Relationships
    order = relationship("Order", back_populates="items")
    part = relationship("Part")

    def __repr__(self):
        return f"<OrderItem {self.id} - Part: {self.part_id}, Qty: {self.quantity}>"