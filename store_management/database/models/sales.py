# database/models/sales.py
"""
Enhanced Sales Model with Robust Relationship Configuration

This module defines the Sales model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import date, datetime
from typing import Dict, Any, Optional

from sqlalchemy import Date, Float, Boolean, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.customer import Customer
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Order', 'database.models.order', 'Order')
register_lazy_import('Product', 'database.models.product', 'Product')

class Sales(Base):
    """
    Enhanced Sales model with comprehensive validation and relationship management.

    Represents sales transactions with advanced tracking
    and relationship configuration.
    """
    __tablename__ = 'sales'

    # Sale details
    sale_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Status and payment tracking
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Additional sale information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)

    # Foreign keys with explicitly configured relationships
    order_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships with careful configuration
    order: Mapped[Optional["Order"]] = relationship(
        "Order",
        back_populates="sales",
        lazy="selectin",
        foreign_keys=[order_id]
    )

    product: Mapped[Optional["Product"]] = relationship(
        "Product",
        back_populates="sales",
        lazy="selectin",
        foreign_keys=[product_id]
    )

    customer: Mapped[Optional[Customer]] = relationship(
        Customer,
        back_populates="sales",
        lazy="selectin",
        foreign_keys=[customer_id]
    )

    def __init__(self, **kwargs):
        """
        Initialize a Sales instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for sales attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Pre-validate input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization validation
            self._validate_instance()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Sales initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Sales: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate sales creation data.

        Args:
            data (Dict[str, Any]): Sales creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate amount
        if 'amount' in data:
            validate_positive_number(
                data,
                'amount',
                message="Sale amount must be a non-negative number"
            )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate payment date consistency
        if self.is_paid and not self.payment_date:
            raise ValidationError(
                "Payment date is required when sale is marked as paid",
                "payment_date"
            )

        if self.payment_date:
            if self.payment_date < self.sale_date:
                raise ValidationError(
                    "Payment date cannot be earlier than sale date",
                    "payment_date"
                )

            if self.payment_date > date.today():
                raise ValidationError(
                    "Payment date cannot be in the future",
                    "payment_date"
                )

    def mark_as_paid(self, payment_date: Optional[date] = None) -> None:
        """
        Mark the sale as paid.

        Args:
            payment_date (Optional[date]): Date of payment. Defaults to today if not provided.

        Raises:
            ModelValidationError: If payment marking fails
        """
        try:
            # Use today's date if no payment date provided
            if payment_date is None:
                payment_date = date.today()

            # Validate payment date
            if payment_date < self.sale_date:
                raise ValidationError(
                    "Payment date cannot be earlier than sale date",
                    "payment_date"
                )

            # Update payment status
            self.is_paid = True
            self.payment_date = payment_date

            logger.info(
                f"Sale {self.id} marked as paid. "
                f"Payment date: {payment_date}"
            )

        except Exception as e:
            logger.error(f"Payment marking failed: {e}")
            raise ModelValidationError(f"Cannot mark sale as paid: {str(e)}")

        def calculate_tax(self, tax_rate: float = 0.08) -> float:
            """
            Calculate tax for the sale.

            Args:
                tax_rate (float): Tax rate as a decimal (default 8%)

            Returns:
                float: Calculated tax amount
            """
            try:
                # Validate tax rate
                validate_positive_number(
                    {'tax_rate': tax_rate},
                    'tax_rate',
                    message="Tax rate must be a non-negative number"
                )

                # Calculate tax
                tax_amount = self.amount * tax_rate
                return round(tax_amount, 2)

            except Exception as e:
                logger.error(f"Tax calculation failed: {e}")
                raise ModelValidationError(f"Cannot calculate tax: {str(e)}")

        def generate_reference_number(self) -> str:
            """
            Generate a unique reference number for the sale.

            Returns:
                str: Generated reference number
            """
            try:
                # Use sale date and order of creation
                date_part = self.sale_date.strftime("%Y%m%d")
                id_part = str(self.id).zfill(6)

                return f"SALE-{date_part}-{id_part}"
            except Exception as e:
                logger.error(f"Reference number generation failed: {e}")
                raise ModelValidationError(f"Cannot generate reference number: {str(e)}")

        def calculate_total_with_tax(self, tax_rate: float = 0.08) -> float:
            """
            Calculate the total sale amount including tax.

            Args:
                tax_rate (float): Tax rate as a decimal (default 8%)

            Returns:
                float: Total sale amount including tax
            """
            try:
                tax_amount = self.calculate_tax(tax_rate)
                total_with_tax = self.amount + tax_amount
                return round(total_with_tax, 2)
            except Exception as e:
                logger.error(f"Total with tax calculation failed: {e}")
                raise ModelValidationError(f"Cannot calculate total with tax: {str(e)}")

        def __repr__(self) -> str:
            """
            Provide a comprehensive string representation of the sale.

            Returns:
                str: Detailed sale representation
            """
            return (
                f"<Sales(id={self.id}, "
                f"amount=${self.amount}, "
                f"sale_date={self.sale_date}, "
                f"paid={self.is_paid}, "
                f"customer='{self.customer.full_name() if self.customer else 'None'}')>"
            )

    # Register this class for lazy imports by others
    register_lazy_import('Sales', 'database.models.sales', 'Sales')