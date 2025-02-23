# database\models\transaction.py
from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
from database.models.base import BaseModel
from database.models.enums import TransactionType  # Import TransactionType from enums


class BaseTransaction(BaseModel):
    """Base class for all transaction models.

    Provides common fields and functionality for tracking inventory changes.

    Attributes:
        id (int): Primary key
        transaction_type (TransactionType): Type of transaction (purchase, use, etc.)
        notes (str): Optional notes about the transaction
        timestamp (datetime): When the transaction occurred
    """
    __tablename__ = 'base_transactions'

    id = Column(Integer, primary_key=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    notes = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __mapper_args__ = {
        'polymorphic_identity': 'base_transaction',
        'polymorphic_on': transaction_type
    }

    def __init__(self, transaction_type, notes):
        """Initialize a new transaction.

        Args:
            transaction_type: Type of inventory transaction
            notes: Optional notes about the transaction
        """
        self.transaction_type = transaction_type
        self.notes = notes

    def __repr__(self):
        return f"<BaseTransaction(id={self.id}, type={self.transaction_type})>"

    def to_dict(self):
        """Convert transaction to dictionary representation.

        Returns:
            Dictionary containing transaction data
        """
        return {
            'id': self.id,
            'transaction_type': str(self.transaction_type),
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat()
        }


class InventoryTransaction(BaseTransaction):
    """Model for tracking part inventory transactions."""
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, ForeignKey('base_transactions.id'), primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    quantity_change = Column(Float, nullable=False)

    part = relationship("Part", back_populates="transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'inventory_transaction'
    }

    def __init__(self, part_id, quantity_change, transaction_type, notes):
        super().__init__(transaction_type, notes)
        self.part_id = part_id
        self.quantity_change = quantity_change

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'part_id': self.part_id,
            'quantity_change': self.quantity_change
        })
        return data


class LeatherTransaction(BaseTransaction):
    """Model for tracking leather inventory transactions."""
    __tablename__ = 'leather_transactions'

    id = Column(Integer, ForeignKey('base_transactions.id'), primary_key=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=False)
    area_change = Column(Float, nullable=False)
    wastage = Column(Float, nullable=True)

    leather = relationship("Leather", back_populates="transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'leather_transaction'
    }

    def __init__(self, leather_id, area_change, transaction_type, notes, wastage=0.0):
        super().__init__(transaction_type, notes)
        self.leather_id = leather_id
        self.area_change = area_change
        self.wastage = wastage

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'leather_id': self.leather_id,
            'area_change': self.area_change,
            'wastage': self.wastage
        })
        return data

    def net_area_change(self):
        """Calculates the net change in area, including wastage."""
        return self.area_change - (self.wastage or 0)