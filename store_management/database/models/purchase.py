# database/models/purchase.py
"""
Comprehensive Purchase Model for Leatherworking Management System

This module defines the Purchase model with extensive validation,
relationship management, and circular import resolution.

Implements the Purchase entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    PurchaseStatus,
    TransactionType
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin
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


class Purchase(Base, TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin):
    """
    Purchase model representing orders from suppliers.

    This implements the Purchase entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'purchases'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Supplier relationship
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=False, index=True)

    # Purchase details
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.PENDING)

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
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

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
        if not hasattr(self, 'metadata') or self.metadata is None:
            self.metadata = {}

        # Ensure tracking ID is set
        if not hasattr(self, 'tracking_id') or not self.tracking_id:
            self.generate_tracking_id()

    def add_item(self, item: 'PurchaseItem') -> None:
        """
        Add an item to the purchase.

        Args:
            item: Purchase item to add
        """
        if not hasattr(self, 'items'):
            self.items = []

        self.items.append(item)
        self.update_total()

    def update_total(self) -> None:
        """
        Update the total amount based on purchase items.
        """
        if hasattr(self, 'items') and self.items:
            self.total_amount = sum(item.price * item.quantity for item in self.items)
        else:
            self.total_amount = 0.0

        logger.info(f"Purchase {self.id} total updated to {self.total_amount}")

    def update_status(self, new_status: Union[str, PurchaseStatus], notes: Optional[str] = None) -> None:
        """
        Update the purchase status with validation.

        Args:
            new_status: New status for the purchase
            notes: Optional notes about the status change

        Raises:
            ValidationError: If status is invalid
        """
        # Process status value
        if isinstance(new_status, str):
            try:
                new_status = PurchaseStatus[new_status.upper()]
            except KeyError:
                raise ValidationError(f"Invalid purchase status: {new_status}", "status")

        # Validate status value
        if not isinstance(new_status, PurchaseStatus):
            raise ValidationError("Status must be a valid PurchaseStatus enum value", "status")

        # Update status
        old_status = self.status
        self.status = new_status

        # Add notes about status change
        if notes:
            existing_notes = self.notes or ""
            status_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Status changed from {old_status.name} to {new_status.name}: {notes}"
            self.notes = f"{existing_notes}\n\n{status_note}" if existing_notes else status_note

        logger.info(f"Purchase {self.id} status updated from {old_status.name} to {new_status.name}")

        # Handle status-specific updates
        if new_status == PurchaseStatus.DELIVERED and not self.delivery_date:
            self.delivery_date = datetime.utcnow()

    def mark_as_ordered(self, reference_number: Optional[str] = None) -> None:
        """
        Mark the purchase as ordered.

        Args:
            reference_number: Optional reference number for the order
        """
        if reference_number:
            self.reference_number = reference_number

        self.update_status(PurchaseStatus.PROCESSING, "Order placed with supplier")

    def mark_as_shipped(self, expected_delivery_date: Optional[datetime] = None) -> None:
        """
        Mark the purchase as shipped.

        Args:
            expected_delivery_date: Optional expected delivery date
        """
        if expected_delivery_date:
            self.expected_delivery_date = expected_delivery_date

        self.update_status(PurchaseStatus.SHIPPED, "Order shipped by supplier")

    def mark_as_delivered(self, create_transactions: bool = True) -> List[Optional['Transaction']]:
        """
        Mark the purchase as delivered and optionally create inventory transactions.

        Args:
            create_transactions: Whether to create inventory transactions for items

        Returns:
            List of created transactions (if create_transactions is True)
        """
        self.update_status(PurchaseStatus.DELIVERED, "Order received")
        self.delivery_date = datetime.utcnow()

        transactions = []

        if create_transactions and hasattr(self, 'items'):
            for item in self.items:
                if not item.is_received:
                    try:
                        # Mark the item as received
                        transaction = item.mark_as_received(
                            received_date=self.delivery_date,
                            create_transaction=True,
                            notes=f"Received as part of purchase {self.id}"
                        )

                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        logger.error(f"Error processing item {item.id} receipt: {e}")

        return transactions

    def mark_as_paid(self, payment_reference: Optional[str] = None) -> None:
        """
        Mark the purchase as paid.

        Args:
            payment_reference: Optional payment reference number
        """
        self.is_paid = True
        self.payment_date = datetime.utcnow()

        if payment_reference:
            self.payment_reference = payment_reference

        logger.info(f"Purchase {self.id} marked as paid")

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancel the purchase.

        Args:
            reason: Optional reason for cancellation
        """
        self.update_status(PurchaseStatus.CANCELLED, reason or "Purchase cancelled")

    def to_dict(self, exclude_fields: Optional[List[str]] = None, include_items: bool = False) -> Dict[str, Any]:
        """
        Convert purchase to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude
            include_items: Whether to include purchase items

        Returns:
            Dictionary representation of the purchase
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        # Special handling for dates and enums
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert datetime to ISO format
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                # Convert enum to string
                elif isinstance(value, PurchaseStatus):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add items if requested
        if include_items and hasattr(self, 'items') and self.items:
            result['items'] = [item.to_dict() for item in self.items]

        # Add supplier name if available
        if hasattr(self, 'supplier') and self.supplier:
            result['supplier_name'] = getattr(self.supplier, 'name', 'Unknown Supplier')

        return result

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


# Register for lazy import resolution
register_lazy_import('Purchase', 'database.models.purchase', 'Purchase')


