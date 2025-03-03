# database/models/material.py
"""
Material and MaterialTransaction models for tracking materials in the inventory system.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import MaterialType, TransactionType, InventoryStatus


class Material(Base):
    """
    Represents a material in the inventory system.
    """
    __tablename__ = 'materials'

    # Specific material attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[MaterialType] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Inventory tracking
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[InventoryStatus] = mapped_column(nullable=False, default=InventoryStatus.IN_STOCK)

    # Optional material-specific attributes
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thickness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    transactions: Mapped[list['MaterialTransaction']] = relationship(
        'MaterialTransaction',
        back_populates='material',
        cascade='all, delete-orphan'
    )

    @classmethod
    def _validate_creation(cls, data):
        """
        Validate material creation data.

        Args:
            data (dict): Material creation data

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        if not data.get('name'):
            raise ValueError("Material name is required")

        if 'material_type' not in data:
            raise ValueError("Material type is required")

        # Validate quantity
        quantity = data.get('quantity', 0.0)
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        # Validate price if provided
        price = data.get('price')
        if price is not None and price < 0:
            raise ValueError("Price cannot be negative")

    def _validate_instance(self):
        """
        Additional instance-level validation.
        """
        if self.quantity < 0:
            raise ValueError("Quantity cannot become negative")


class MaterialTransaction(Base):
    """
    Represents a transaction (purchase, usage, adjustment) for a material.
    """
    __tablename__ = 'material_transactions'

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key to material
    material_id: Mapped[int] = mapped_column(ForeignKey('materials.id'), nullable=False)

    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    material: Mapped[Material] = relationship('Material', back_populates='transactions')

    @classmethod
    def _validate_creation(cls, data):
        """
        Validate material transaction creation data.

        Args:
            data (dict): Transaction creation data

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        if 'material_id' not in data:
            raise ValueError("Material ID is required")

        if 'transaction_type' not in data:
            raise ValueError("Transaction type is required")

        # Validate quantity
        quantity = data.get('quantity', 0)
        if quantity <= 0:
            raise ValueError("Transaction quantity must be positive")

    def _validate_instance(self):
        """
        Additional instance-level validation.
        """
        if self.quantity <= 0:
            raise ValueError("Transaction quantity must be positive")