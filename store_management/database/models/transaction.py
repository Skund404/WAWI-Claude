"""
File: database/models/transaction.py
Transaction model definitions.
Represents inventory transactions for parts and leather.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
import datetime
import enum

from database.models.base import Base


class TransactionType(enum.Enum):
    """Enumeration for transaction types."""
    PURCHASE = "purchase"
    PRODUCTION = "production"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    WASTAGE = "wastage"
    TRANSFER = "transfer"


class InventoryTransaction(Base):
    """
    InventoryTransaction model representing transactions for parts inventory.
    """
    __tablename__ = 'inventory_transactions'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    quantity_change = Column(Integer, nullable=False)  # Can be positive or negative
    transaction_type = Column(String(20), default=TransactionType.ADJUSTMENT.value)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    notes = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # part = relationship("Part", back_populates="transactions")
    # order = relationship("Order")

    def __repr__(self):
        """String representation of the InventoryTransaction model."""
        return f"<InventoryTransaction(id={self.id}, part_id={self.part_id}, change={self.quantity_change})>"


class LeatherTransaction(Base):
    """
    LeatherTransaction model representing transactions for leather inventory.
    """
    __tablename__ = 'leather_transactions'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    area_change = Column(Float, nullable=False)  # Can be positive or negative
    transaction_type = Column(String(20), default=TransactionType.ADJUSTMENT.value)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    wastage = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # leather = relationship("Leather", back_populates="transactions")
    # order = relationship("Order")

    def __repr__(self):
        """String representation of the LeatherTransaction model."""
        return f"<LeatherTransaction(id={self.id}, leather_id={self.leather_id}, change={self.area_change})>"