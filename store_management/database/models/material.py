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
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Register lazy import to avoid circular dependency
register_lazy_import('database.models.transaction.MaterialTransaction', 'database.models.transaction')


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

    transactions = relationship(
        "MaterialTransaction",
        primaryjoin="Material.id == MaterialTransaction.material_id",
        viewonly=False,
        cascade='all, delete-orphan'
    )
    project_components = relationship(
        "ProjectComponent",
        primaryjoin="Material.id == ProjectComponent.material_id",
        viewonly=True
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


