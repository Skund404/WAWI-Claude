# database/models/purchase.py
"""
Comprehensive Purchase Model for Leatherworking Management System

This module defines the Purchase model with extensive validation,
relationship management, and circular import resolution.

Implements the Purchase entity from the ER diagram with all its
relationships and attributes.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import sqltypes

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    PurchaseStatus,
    TransactionType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('PurchaseItem', 'database.models.purchase_item', 'PurchaseItem')
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')


class Purchase(Base, apply_mixins(TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin)):
    """
    Purchase model representing orders from suppliers.

    This implements the Purchase entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'purchases'

    # Explicit primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Supplier relationship
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=False, index=True)

    # Purchase details
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Use sqltypes for enum column
    status: Mapped[PurchaseStatus] = mapped_column(
        sqltypes.Enum(PurchaseStatus),
        nullable=False,
        default=PurchaseStatus.PENDING
    )

    # Date tracking
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional information
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    supplier_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment tracking
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    model_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="purchase")

    def __init__(self, **kwargs):
        """
        Initialize a Purchase instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for purchase attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Handle potential metadata renaming
            if 'metadata' in kwargs:
                kwargs['model_metadata'] = kwargs.pop('metadata')

            # Set created_at if not provided
            if 'created_at' not in kwargs:
                kwargs['created_at'] = datetime.utcnow()

            # If order_date not provided, use created_at
            if 'order_date' not in kwargs and 'created_at' in kwargs:
                kwargs['order_date'] = kwargs['created_at']

            # Validate input data
            self._validate_purchase_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Purchase initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Purchase: {str(e)}") from e

    @classmethod
    def _validate_purchase_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of purchase creation data.

        Args:
            data: Purchase creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'supplier_id', 'Supplier ID is required')

        # Validate purchase status if provided
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                PurchaseStatus,
                'status'
            )

        # Validate total amount if provided
        if 'total_amount' in data:
            validate_positive_number(
                data,
                'total_amount',
                allow_zero=True,
                message="Total amount cannot be negative"
            )

        # Validate dates if provided
        if 'expected_delivery_date' in data and data['expected_delivery_date'] is not None:
            if 'order_date' in data and data['order_date'] is not None:
                if data['expected_delivery_date'] < data['order_date']:
                    raise ValidationError("Expected delivery date cannot be before order date",
                                          "expected_delivery_date")

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize metadata if not provided
        if not hasattr(self, 'model_metadata') or self.model_metadata is None:
            self.model_metadata = {}

        # Ensure tracking ID is set
        if not hasattr(self, 'tracking_id') or not self.tracking_id:
            self.generate_tracking_id()

    def generate_tracking_id(self) -> str:
        """
        Generate a unique tracking ID for the purchase.

        Returns:
            Unique tracking ID
        """
        self.tracking_id = f"PURCH-{uuid.uuid4().hex[:8].upper()}"
        return self.tracking_id

    def __repr__(self) -> str:
        """
        String representation of the Purchase.

        Returns:
            Detailed purchase representation
        """
        return (
            f"<Purchase(id={self.id}, "
            f"supplier_id={self.supplier_id}, "
            f"total={self.total_amount}, "
            f"status={self.status.name if self.status else 'None'})>"
        )


# Optional function to initialize relationships and resolve circular imports
def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing Purchase relationships")
    try:
        # Import necessary models
        from database.models.supplier import Supplier
        from database.models.purchase_item import PurchaseItem
        from database.models.transaction import Transaction

        # Ensure relationships are properly configured
        logger.info("Purchase relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Purchase relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('Purchase', 'database.models.purchase', 'Purchase')