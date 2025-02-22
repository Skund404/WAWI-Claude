"""
File: database/models/order.py
Order model definitions.
Represents purchase orders and their items.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

from database.models.base import Base


class OrderStatus(enum.Enum):
    """Enumeration for order status values."""
    DRAFT = "draft"
    PLACED = "placed"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(enum.Enum):
    """Enumeration for payment status values."""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"


class Order(Base):
    """
    Order model representing purchase orders from suppliers.
    """
    __tablename__ = 'orders'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    date_required = Column(DateTime, nullable=True)
    date_expected = Column(DateTime, nullable=True)
    status = Column(String(20), default=OrderStatus.DRAFT.value)
    payment_status = Column(String(20), default=PaymentStatus.PENDING.value)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # supplier = relationship("Supplier", back_populates="orders")
    # items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the Order model."""
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base):
    """
    OrderItem model representing individual items in an order.
    """
    __tablename__ = 'order_items'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)
    description = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    received_quantity = Column(Integer, default=0)

    # Relationships - uncomment and adjust based on your actual relationships
    # order = relationship("Order", back_populates="items")
    # part = relationship("Part")
    # leather = relationship("Leather")

    def __repr__(self):
        """String representation of the OrderItem model."""
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity})>"