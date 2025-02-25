# path: database/models/transaction.py
"""
Transaction models for the leatherworking store management application.

This module defines the database models for inventory transactions,
which track changes to material and part quantities.
"""

import enum
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

# Import base classes without causing circular dependencies
from database.models.base import Base, BaseModel
from database.models.enums import TransactionType


class BaseTransaction(Base, BaseModel):
    """
    Base model for inventory transactions.

    This is the foundation for specific transaction types like
    InventoryTransaction and LeatherTransaction.
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Discriminator column for polymorphic identity
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'transaction',
        'polymorphic_on': type
    }

    def __init__(self, transaction_type: TransactionType, notes: Optional[str] = None):
        """
        Initialize a new transaction.

        Args:
            transaction_type: Type of the transaction
            notes: Optional notes about the transaction
        """
        self.transaction_type = transaction_type
        self.notes = notes

    def __repr__(self) -> str:
        """
        Return a string representation of the transaction.

        Returns:
            str: String representation with id and type
        """
        return f"<Transaction(id={self.id}, type={self.transaction_type})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the transaction to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the transaction
        """
        result = super().to_dict()

        # Convert enum values to strings
        if isinstance(self.transaction_type, TransactionType):
            result['transaction_type'] = self.transaction_type.value

        return result


class InventoryTransaction(BaseTransaction):
    """
    Transaction for inventory parts.

    This model represents transactions affecting the quantities of
    inventory parts like buckles, rivets, etc.
    """
    __tablename__ = 'inventory_transactions'

    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=False)
    quantity_change = Column(Integer, nullable=False)

    # Relationship to the affected part
    part = relationship("Part", backref="transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'inventory_transaction',
    }

    def __init__(self, part_id: int, quantity_change: int,
                 transaction_type: TransactionType, notes: Optional[str] = None):
        """
        Initialize a new inventory transaction.

        Args:
            part_id: ID of the part affected
            quantity_change: Amount to change the quantity by (positive or negative)
            transaction_type: Type of the transaction
            notes: Optional notes about the transaction
        """
        super().__init__(transaction_type, notes)
        self.part_id = part_id
        self.quantity_change = quantity_change

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the transaction to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the transaction
        """
        result = super().to_dict()

        # Add part_id
        result['part_id'] = self.part_id
        result['quantity_change'] = self.quantity_change

        return result


class LeatherTransaction(BaseTransaction):
    """
    Transaction for leather inventory.

    This model represents transactions affecting the areas of
    leather materials, with additional tracking for wastage.
    """
    __tablename__ = 'leather_transactions'

    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=False)
    area_change = Column(Float, nullable=False)  # in square feet or square meters
    wastage = Column(Float, default=0.0)  # wastage during cutting

    # Relationship to the affected leather
    leather = relationship("Leather", backref="transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'leather_transaction',
    }

    def __init__(self, leather_id: int, area_change: float,
                 transaction_type: TransactionType, notes: Optional[str] = None,
                 wastage: float = 0.0):
        """
        Initialize a new leather transaction.

        Args:
            leather_id: ID of the leather affected
            area_change: Amount to change the area by (positive or negative)
            transaction_type: Type of the transaction
            notes: Optional notes about the transaction
            wastage: Amount of leather wasted during cutting
        """
        super().__init__(transaction_type, notes)
        self.leather_id = leather_id
        self.area_change = area_change
        self.wastage = wastage

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the transaction to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the transaction
        """
        result = super().to_dict()

        # Add leather-specific fields
        result['leather_id'] = self.leather_id
        result['area_change'] = self.area_change
        result['wastage'] = self.wastage

        return result

    def net_area_change(self) -> float:
        """
        Calculate the net area change including wastage.

        Returns:
            float: Net area change
        """
        return self.area_change - self.wastage