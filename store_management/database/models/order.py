# database/models/order.py
"""
Enhanced Order Model with Advanced Relationship and Validation Strategies

This module defines the Order model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import OrderStatus, PaymentStatus
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
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
register_lazy_import('database.models.order.OrderItem', 'database.models.order')
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier')
register_lazy_import('database.models.sales.Sales', 'database.models.sales')

# Lazy load model classes to prevent circular imports
OrderItem = lazy_import("database.models.order", "OrderItem")
Supplier = lazy_import("database.models.supplier", "Supplier")
Sales = lazy_import("database.models.sales", "Sales")


class Order(Base):
    """
    Enhanced Order model with comprehensive validation and relationship management.

    Represents a customer order with advanced tracking and relationship configuration.
    """
    __tablename__ = 'orders'

    # Order identification and customer details
    order_number = Column(String(50), unique=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)

    # Temporal tracking
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    shipping_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(Enum(OrderStatus), default=OrderStatus.QUOTE_REQUEST, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    # Financial tracking
    subtotal = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    shipping_cost = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)

    # Additional details
    shipping_address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Foreign keys with lazy import support
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Relationships configured to avoid circular imports
    items = relationship(
        "OrderItem",
        back_populates="order",
        lazy='select',
        cascade="all, delete-orphan"
    )

    sales = relationship(
        "Sales",
        back_populates="order",
        lazy='select'
    )

    supplier = relationship(
        "Supplier",
        back_populates="orders",
        lazy='select'
    )

    def __init__(self, **kwargs):
        """
        Initialize an Order instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for order attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Calculate total if not already set
            if 'total' not in kwargs and 'subtotal' in kwargs:
                self.calculate_total()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Order initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Order: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate order creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Order creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'customer_name', 'Customer name is required')

        # Validate numeric fields
        numeric_fields = [
            'subtotal', 'tax', 'shipping_cost', 'total'
        ]

        for field in numeric_fields:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} must be a non-negative number"
                )

        # Validate order and payment status
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                OrderStatus,
                'status'
            )

        if 'payment_status' in data:
            ModelValidator.validate_enum(
                data['payment_status'],
                PaymentStatus,
                'payment_status'
            )

        # Validate email if provided
        if 'customer_email' in data and data['customer_email']:
            try:
                ModelValidator.validate_email(data['customer_email'])
            except ValidationError as e:
                raise ValidationError("Invalid email format", "customer_email")

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate order total
        self._validate_order_total()

        # Validate relationships
        if self.supplier and not hasattr(self.supplier, 'id'):
            raise ValidationError("Invalid supplier reference", "supplier")

    def _validate_order_total(self) -> None:
        """
        Validate that the order total matches the calculated total.

        Raises:
            ValidationError: If total calculation is inconsistent
        """
        calculated_total = (
                self.subtotal +
                self.tax +
                self.shipping_cost
        )

        # Allow small floating-point discrepancies
        if abs(calculated_total - self.total) > 0.01:
            logger.warning(
                f"Order total mismatch. "
                f"Calculated: {calculated_total}, Stored: {self.total}"
            )
            self.total = calculated_total

    def calculate_total(self) -> float:
        """
        Calculate the order total based on subtotal, tax, and shipping cost.

        Returns:
            float: Calculated total cost
        """
        try:
            self.total = self.subtotal + self.tax + self.shipping_cost
            return self.total
        except Exception as e:
            logger.error(f"Total calculation failed: {e}")
            raise ModelValidationError(f"Order total calculation failed: {str(e)}")

    def update_status(self, new_status: OrderStatus) -> None:
        """
        Update the order status with validation and tracking.

        Args:
            new_status (OrderStatus): The new status to set

        Raises:
            ModelValidationError: If status update is invalid
        """
        try:
            # Validate status transition
            self._validate_status_transition(new_status)

            # Update status
            self.status = new_status

            # Update related timestamps
            if new_status == OrderStatus.SHIPPED:
                self.shipping_date = datetime.utcnow()
            elif new_status == OrderStatus.DELIVERED:
                self.delivery_date = datetime.utcnow()

            logger.info(f"Order {self.id} status updated to {new_status}")

        except Exception as e:
            logger.error(f"Order status update failed: {e}")
            raise ModelValidationError(f"Cannot update order status: {str(e)}")

    def _validate_status_transition(self, new_status: OrderStatus) -> None:
        """
        Validate order status transitions.

        Args:
            new_status (OrderStatus): Proposed new status

        Raises:
            ModelValidationError: If status transition is invalid
        """
        # Example of a basic status transition validation
        invalid_transitions = {
            OrderStatus.QUOTE_REQUEST: [OrderStatus.DELIVERED],
            OrderStatus.CANCELLED: [
                OrderStatus.IN_PRODUCTION,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED
            ]
        }

        if self.status in invalid_transitions:
            forbidden_statuses = invalid_transitions[self.status]
            if new_status in forbidden_statuses:
                raise ModelValidationError(
                    f"Cannot transition from {self.status} to {new_status}"
                )

    def apply_payment(self, payment_amount: float) -> None:
        """
        Apply a payment to the order.

        Args:
            payment_amount (float): Amount of payment received

        Raises:
            ModelValidationError: If payment application fails
        """
        try:
            # Validate payment amount
            validate_positive_number(
                {'payment': payment_amount},
                'payment',
                message="Payment amount must be a positive number"
            )

            # Calculate remaining balance
            remaining_balance = self.total - payment_amount

            # Update payment status
            if remaining_balance <= 0:
                self.payment_status = PaymentStatus.PAID
            elif remaining_balance > 0:
                self.payment_status = PaymentStatus.PARTIALLY_PAID

            logger.info(
                f"Payment of {payment_amount} applied to Order {self.id}. "
                f"Remaining balance: {remaining_balance}"
            )

        except Exception as e:
            logger.error(f"Payment application failed: {e}")
            raise ModelValidationError(f"Cannot apply payment: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the order.

        Returns:
            str: Detailed order representation
        """
        return (
            f"<Order(id={self.id}, "
            f"order_number='{self.order_number}', "
            f"customer='{self.customer_name}', "
            f"status={self.status}, "
            f"total={self.total}, "
            f"payment_status={self.payment_status})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.order.Order', 'database.models.order')