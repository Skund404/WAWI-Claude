# store_management/database/models/transaction.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import TransactionType


class InventoryTransaction(Base):
    """Transaction for part inventory changes"""
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Float, nullable=False)
    notes = Column(String)
    reference = Column(String)  # Could be order number, production order number, etc.
    transaction_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    part = relationship("Part", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction(id={self.id}, part_id={self.part_id})>"


class LeatherTransaction(Base):
    """Transaction for leather inventory changes"""
    __tablename__ = 'leather_transactions'

    id = Column(Integer, primary_key=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    area = Column(Float, nullable=False)  # in square feet
    wastage = Column(Float, default=0.0)  # Wastage tracking
    notes = Column(String)
    reference = Column(String)
    transaction_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    leather = relationship("Leather", back_populates="transactions")

    def __repr__(self):
        return f"<LeatherTransaction(id={self.id}, leather_id={self.leather_id})>"