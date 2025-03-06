# database/models/purchase.py
"""
Purchase Model

This module defines the Purchase model which implements
the Purchase entity from the ER diagram.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import PurchaseStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Supplier = lazy_import('database.models.supplier', 'Supplier')

# Register lazy imports
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier', 'Supplier')


class Purchase(Base):
    """
    Purchase model representing orders from suppliers.
    This corresponds to the Purchase entity in the ER diagram.
    """
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.PENDING)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)

    # Metadata
    reference_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

    def __init__(self, supplier_id: int, status: PurchaseStatus = PurchaseStatus.PENDING,
                 total_amount: float = 0.0, reference_number: Optional[str] = None,
                 notes: Optional[str] = None, **kwargs):
        """
        Initialize a Purchase instance.

        Args:
            supplier_id: ID of the supplier
            status: Purchase status
            total_amount: Total purchase amount
            reference_number: Reference number for the purchase
            notes: Additional notes
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'supplier_id': supplier_id,
                'status': status,
                'total_amount': total_amount,
                'reference_number': reference_number,
                'notes': notes,
                'created_at': datetime.utcnow()
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Purchase initialization failed: {e}")
            raise ModelValidationError(f"Failed to create purchase: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate purchase creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'supplier_id', 'Supplier ID is required')

        # Validate amount
        if 'total_amount' in data:
            validate_positive_number(
                data,
                'total_amount',
                allow_zero=True,
                message="Total amount cannot be negative"
            )

    def update_total(self) -> None:
        """
        Update the total amount based on purchase items.
        """
        try:
            self.total_amount = sum(item.price * item.quantity for item in self.items)
            logger.info(f"Purchase {self.id} total updated to {self.total_amount}")
        except Exception as e:
            logger.error(f"Error updating purchase total: {e}")
            raise ModelValidationError(f"Failed to update purchase total: {str(e)}") from e

    def mark_as_delivered(self) -> None:
        """
        Mark the purchase as delivered.
        """
        try:
            self.status = PurchaseStatus.DELIVERED
            logger.info(f"Purchase {self.id} marked as delivered")
        except Exception as e:
            logger.error(f"Error marking purchase as delivered: {e}")
            raise ModelValidationError(f"Failed to update purchase status: {str(e)}") from e

    def __repr__(self) -> str:
        """String representation of the purchase."""
        return f"<Purchase(id={self.id}, supplier_id={self.supplier_id}, total={self.total_amount}, status={self.status})>"


# Final registration
register_lazy_import('database.models.purchase.Purchase', 'database.models.purchase', 'Purchase')