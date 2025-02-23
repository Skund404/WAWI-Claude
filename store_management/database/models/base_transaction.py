# database/models/base_transaction.py

from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any

from .base import BaseModel
from .enums import TransactionType


class BaseTransaction(BaseModel):
    """
    Base class for all transaction models.

    Provides common fields and functionality for tracking inventory changes.

    Attributes:
        id (int): Primary key
        transaction_type (TransactionType): Type of transaction (purchase, use, etc.)
        notes (str): Optional notes about the transaction
        timestamp (datetime): When the transaction occurred
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    notes = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, transaction_type: TransactionType, notes: Optional[str] = None):
        """
        Initialize a new transaction.

        Args:
            transaction_type: Type of inventory transaction
            notes: Optional notes about the transaction
        """
        self.transaction_type = transaction_type
        self.notes = notes

    def __repr__(self) -> str:
        """Return string representation of the transaction."""
        return (f"<{self.__class__.__name__}(id={self.id}, "
                f"type={self.transaction_type}, timestamp={self.timestamp})>")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert transaction to dictionary representation.

        Returns:
            Dictionary containing transaction data
        """
        return {
            'id': self.id,
            'transaction_type': self.transaction_type.name,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }