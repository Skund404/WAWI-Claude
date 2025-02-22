# Path: database/models/transaction.py
from sqlalchemy import Column, Integer, Float, DateTime, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum, auto
from .base import BaseModel


class TransactionType(Enum):
    """
    Enum representing different types of inventory transactions.
    """
    PURCHASE = "Purchase"
    USAGE = "Usage"
    TRANSFER = "Transfer"
    ADJUSTMENT = "Adjustment"
    RETURN = "Return"
    PRODUCTION = "Production"
    WASTE = "Waste"


class InventoryTransaction(BaseModel):
    """
    Represents a transaction involving inventory parts.

    Attributes:
        id (int): Unique identifier for the transaction
        part_id (int): Foreign key to the inventory part
        transaction_type (TransactionType): Type of transaction
        quantity_change (float): Quantity change in the transaction
        date (DateTime): Timestamp of the transaction
        notes (str): Additional notes about the transaction

        part (relationship): Inventory part involved in the transaction
    """
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity_change = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    part = relationship('Part', back_populates='transactions')

    def __repr__(self):
        return f"<InventoryTransaction(id={self.id}, part_id={self.part_id}, type='{self.transaction_type}', quantity_change={self.quantity_change})>"


class LeatherTransaction(BaseModel):
    """
    Represents a transaction involving leather materials.

    Attributes:
        id (int): Unique identifier for the transaction
        leather_id (int): Foreign key to the leather material
        transaction_type (TransactionType): Type of transaction
        area_change (float): Area change in the transaction
        date (DateTime): Timestamp of the transaction
        notes (str): Additional notes about the transaction
        wastage (float): Wastage area during the transaction

        leather (relationship): Leather material involved in the transaction
    """
    __tablename__ = 'leather_transactions'

    id = Column(Integer, primary_key=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    area_change = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    wastage = Column(Float, default=0.0)

    # Relationships
    leather = relationship('Leather', back_populates='transactions')

    def __repr__(self):
        return f"<LeatherTransaction(id={self.id}, leather_id={self.leather_id}, type='{self.transaction_type}', area_change={self.area_change})>"

    @property
    def net_area_change(self):
        """
        Calculate the net area change, accounting for wastage.

        Returns:
            float: Net area change after subtracting wastage
        """
        return self.area_change - self.wastage