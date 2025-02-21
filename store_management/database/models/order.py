# store_management/database/models/order.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import OrderStatus, PaymentStatus


class Order(Base):
    """Purchase order model"""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String, nullable=False, unique=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    order_date = Column(DateTime, default=datetime.utcnow)
    expected_delivery = Column(DateTime)
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}')>"


class OrderItem(Base):
    """Items in a purchase order"""
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'))
    leather_id = Column(Integer, ForeignKey('leathers.id'))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    received_quantity = Column(Float, default=0.0)
    notes = Column(String)

    # Relationships
    order = relationship("Order", back_populates="items")
    part = relationship("Part")
    leather = relationship("Leather")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id})>"