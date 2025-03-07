# database/models/sales.py
"""
Enhanced Sales Model for Leatherworking Management System

Represents sales transactions with comprehensive tracking,
validation, and relationship management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SaleStatus, PaymentStatus
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin
)
from utils.circular_import_resolver import (
    CircularImportResolver,
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError
)

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports to resolve potential circular dependencies
register_lazy_import('Customer', 'database.models.customer', 'Customer')
register_lazy_import('SalesItem', 'database.models.sales_item', 'SalesItem')
register_lazy_import('PickingList', 'database.models.picking_list', 'PickingList')
register_lazy_import('Project', 'database.models.project', 'Project')


class Sales(Base, TimestampMixin, ValidationMixin, CostingMixin):
    """
    Sales model representing a complete sales transaction in the system.

    Tracks comprehensive details of sales, including status,
    payment, and associated entities.
    """
    __tablename__ = 'sales'

    # Primary key inherited from Base

    # Customer relationship
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('customers.id'),
        nullable=False
    )

    # Relationships with lazy loading and circular import resolution
    customer: Mapped['Customer'] = relationship(
        "Customer",
        back_populates="sales_records",
        lazy="selectin"
    )

    # Sales details
    total_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    # Status tracking
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus),
        default=SaleStatus.QUOTE_REQUEST,
        nullable=False
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )

    # Additional fields
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True
    )

    # Related entities
    items: Mapped[List['SalesItem']] = relationship(
        "SalesItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    picking_list: Mapped[Optional['PickingList']] = relationship(
        "PickingList",
        back_populates="sale",
        uselist=False,
        cascade="all, delete-orphan"
    )

    project: Mapped[Optional['Project']] = relationship(
        "Project",
        back_populates="sale",
        uselist=False
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
            # Validate required fields
            self._validate_sales_data(kwargs)

            # Initialize the base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Sales initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Sales: {str(e)}") from e

    @classmethod
    def _validate_sales_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of sales creation data.

        Args:
            data (Dict[str, Any]): Sales creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate customer ID
        if 'customer_id' not in data or not data['customer_id']:
            raise ValidationError("Customer ID is required", "customer_id")

        # Validate status
        if 'status' in data:
            cls._validate_sale_status(data['status'])

        # Validate payment status
        if 'payment_status' in data:
            cls._validate_payment_status(data['payment_status'])

        # Validate total amount
        if 'total_amount' in data:
            cls._validate_total_amount(data['total_amount'])

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Calculate total amount if not provided
        if not hasattr(self, 'total_amount') or self.total_amount is None:
            self.calculate_total_amount()

        # Set initial statuses if not specified
        if not hasattr(self, 'status') or self.status is None:
            self.status = SaleStatus.QUOTE_REQUEST

        if not hasattr(self, 'payment_status') or self.payment_status is None:
            self.payment_status = PaymentStatus.PENDING

    @classmethod
    def _validate_sale_status(cls, status: Union[str, SaleStatus]) -> SaleStatus:
        """
        Validate and convert sale status.

        Args:
            status: Sale status to validate

        Returns:
            Validated SaleStatus

        Raises:
            ValidationError: If status is invalid
        """
        if isinstance(status, str):
            try:
                return SaleStatus[status.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid sale status. Must be one of {[s.name for s in SaleStatus]}",
                    "status"
                )

        if not isinstance(status, SaleStatus):
            raise ValidationError("Invalid sale status type", "status")

        return status

    @classmethod
    def _validate_payment_status(cls, status: Union[str, PaymentStatus]) -> PaymentStatus:
        """
        Validate and convert payment status.

        Args:
            status: Payment status to validate

        Returns:
            Validated PaymentStatus

        Raises:
            ValidationError: If status is invalid
        """
        if isinstance(status, str):
            try:
                return PaymentStatus[status.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid payment status. Must be one of {[s.name for s in PaymentStatus]}",
                    "payment_status"
                )

        if not isinstance(status, PaymentStatus):
            raise ValidationError("Invalid payment status type", "payment_status")

        return status

    @classmethod
    def _validate_total_amount(cls, amount: float) -> None:
        """
        Validate total amount.

        Args:
            amount: Total sale amount to validate

        Raises:
            ValidationError: If amount is invalid
        """
        if amount < 0:
            raise ValidationError("Total amount cannot be negative", "total_amount")

    def calculate_total_amount(self) -> float:
        """
        Calculate the total sale amount based on sales items.

        Returns:
            float: Total sale amount
        """
        try:
            # Calculate total from sales items
            if hasattr(self, 'items') and self.items:
                total = sum(item.total_price for item in self.items)
                self.total_amount = total
                logger.debug(f"Calculated total for sale ID {self.id}: {total}")
                return total

            return 0.0
        except Exception as e:
            logger.error(f"Total amount calculation failed: {e}")
            raise ModelValidationError(f"Cannot calculate sale total: {e}")

    def add_item(self, sales_item: 'SalesItem') -> None:
        """
        Add an item to the sale and update total.

        Args:
            sales_item: The SalesItem to add
        """
        if not hasattr(self, 'items'):
            self.items = []

        if sales_item not in self.items:
            self.items.append(sales_item)
            sales_item.sale = self
            self.calculate_total_amount()
            logger.debug(f"Added item to sale ID {self.id}: {sales_item}")

    def remove_item(self, sales_item: 'SalesItem') -> bool:
        """
        Remove an item from the sale and update total.

        Args:
            sales_item: The SalesItem to remove

        Returns:
            bool: True if item was removed, False if not found
        """
        if hasattr(self, 'items') and sales_item in self.items:
            self.items.remove(sales_item)
            sales_item.sale = None
            self.calculate_total_amount()
            logger.debug(f"Removed item from sale ID {self.id}: {sales_item}")
            return True
        return False

    def update_status(self, new_status: Union[str, SaleStatus]) -> None:
        """
        Update the sale status with validation.

        Args:
            new_status: New status for the sale

        Raises:
            ModelValidationError: If status update fails
        """
        try:
            validated_status = self._validate_sale_status(new_status)
            self.status = validated_status
            logger.info(f"Sale {self.id} status updated to {validated_status.name}")
        except Exception as e:
            logger.error(f"Status update failed for sale {self.id}: {e}")
            raise ModelValidationError(f"Cannot update sale status: {e}")

    def create_picking_list(self) -> 'PickingList':
        """
        Create a picking list for this sale.

        Returns:
            PickingList: The created picking list
        """
        # Lazy import to avoid circular dependencies
        PickingList = lazy_import('database.models.picking_list', 'PickingList')

        if self.picking_list:
            logger.debug(f"Picking list already exists for sale ID {self.id}")
            return self.picking_list

        try:
            picking_list = PickingList(sales_id=self.id)
            self.picking_list = picking_list
            logger.debug(f"Created picking list for sale ID {self.id}")
            return picking_list
        except Exception as e:
            logger.error(f"Picking list creation failed for sale {self.id}: {e}")
            raise ModelValidationError(f"Cannot create picking list: {e}")

    def __repr__(self) -> str:
        """
        String representation of the Sales.

        Returns:
            str: Detailed sales representation
        """
        return (
            f"Sales("
            f"id={self.id}, "
            f"customer_id={self.customer_id}, "
            f"total_amount={self.total_amount}, "
            f"status={self.status.name}, "
            f"payment_status={self.payment_status.name}"
            f")"
        )


def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing Sales relationships")
    try:
        # Import necessary models
        from database.models.sales_item import SalesItem
        from database.models.customer import Customer
        from database.models.picking_list import PickingList
        from database.models.project import Project

        # Ensure relationships are properly configured
        logger.info("Sales relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Sales relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('Sales', 'database.models.sales', 'Sales')