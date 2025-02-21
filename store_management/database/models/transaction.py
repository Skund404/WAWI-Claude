# File: store_management/database/sqlalchemy/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base
from store_management.database.sqlalchemy.models.enums import TransactionType


class InventoryTransaction(Base):
    """
    Transaction model for tracking part inventory changes.

    Attributes:
        id (int): Unique identifier for the transaction
        part_id (int): Foreign key to the part involved
        quantity_change (float): Change in quantity (positive or negative)
        transaction_type (TransactionType): Type of transaction
        notes (str): Additional notes about the transaction
        created_at (datetime): Timestamp of transaction creation
    """
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    quantity_change = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    part = relationship("Part", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction {self.id} - Part: {self.part_id}, Change: {self.quantity_change}>"


class LeatherTransaction(Base):
    """
    Transaction model for tracking leather inventory changes.

    Attributes:
        id (int): Unique identifier for the transaction
        leather_id (int): Foreign key to the leather involved
        area_change (float): Change in area (positive or negative)
        transaction_type (TransactionType): Type of transaction
        notes (str): Additional notes about the transaction
        wastage (float): Area lost during transaction
        created_at (datetime): Timestamp of transaction creation
    """
    __tablename__ = 'leather_transactions'

    id = Column(Integer, primary_key=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=False)
    area_change = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    notes = Column(String)
    wastage = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    leather = relationship("Leather", back_populates="transactions")

    def __repr__(self):
        return f"<LeatherTransaction {self.id} - Leather: {self.leather_id}, Change: {self.area_change}>"