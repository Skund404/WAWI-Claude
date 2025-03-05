# database/models/sales.py
"""
Enhanced Sales Model with Standard SQLAlchemy Relationship Approach

This module defines the Sales model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Date, Float, Boolean, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Order', 'database.models.order')
register_lazy_import('Product', 'database.models.product')
register_lazy_import('Customer', 'database.models.customer')

# Setup logger
logger = logging.getLogger(__name__)


class Sales(Base):
    """
    Enhanced Sales model with comprehensive validation and relationship management.

    Represents sales transactions with advanced tracking
    and relationship configuration.
    """
    __tablename__ = 'sales'

    # Sale details
    sale_date = Column(Date, default=date.today, nullable=False)
    amount = Column(Float, default=0.0, nullable=False)

    # Status and payment tracking
    is_paid = Column(Boolean, default=False, nullable=False)
    payment_date = Column(Date, nullable=True)

    # Additional sale information
    notes = Column(Text, nullable=True)
    reference_number = Column(String(50), unique=True, nullable=True)

    # Foreign keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Relationships with standard SQLAlchemy approach
    order = relationship("Order", back_populates="sales", lazy="lazy")
    product = relationship("Product", back_populates="sales", lazy="lazy")
    customer = relationship("Customer", back_populates="sales", lazy="lazy")

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate payment date
        if self.is_paid and not self.payment_date:
            raise ValidationError(
                "Payment date is required when sale is marked as paid",
                "payment_date"
            )

        # Validate payment date consistency
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

        # Validate relationships
        if self.product and not hasattr(self.product, 'id'):
            raise ValidationError("Invalid product reference", "product")

        if self.order and not hasattr(self.order, 'id'):
            raise ValidationError("Invalid order reference", "order")

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
            f"product='{self.product.name if self.product else 'None'}')>"
        )


# Register this class for lazy imports by others
register_lazy_import('Sales', 'database.models.sales')