# database/models/sales.py
"""
Model for sales in the leatherworking application.

This module defines the Sales model, which represents customer sales transactions
in the application. Sales can include multiple sale items linked to products.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SaleStatus, PaymentStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to avoid circular dependencies
register_lazy_import('SalesItem', 'database.models.sales_item', 'SalesItem')
register_lazy_import('Customer', 'database.models.customer', 'Customer')
register_lazy_import('PickingList', 'database.models.picking_list', 'PickingList')
register_lazy_import('Project', 'database.models.project', 'Project')


class Sales(Base):
    """Model representing a sales transaction in the application."""

    __tablename__ = 'sales'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign keys
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customer.id'), nullable=False)

    # Sale details
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), default=SaleStatus.QUOTE_REQUEST)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Additional fields
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships will be set up by initialize_relationships
    # These are just placeholders that will be properly defined later
    # Don't initialize relationship objects here to avoid circular imports

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the Sales instance.

        Args:
            **kwargs: Keyword arguments for sales attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate required fields
            required_fields = ['customer_id']
            for field in required_fields:
                if field not in kwargs or kwargs[field] is None:
                    raise ModelValidationError(f"Field '{field}' is required for Sales")

            # Ensure status and payment_status are valid enum values
            if 'status' in kwargs and isinstance(kwargs['status'], str):
                try:
                    kwargs['status'] = SaleStatus[kwargs['status']]
                except KeyError:
                    valid_statuses = ", ".join([status.name for status in SaleStatus])
                    raise ModelValidationError(
                        f"Invalid sale status: {kwargs['status']}. "
                        f"Valid values are: {valid_statuses}"
                    )

            if 'payment_status' in kwargs and isinstance(kwargs['payment_status'], str):
                try:
                    kwargs['payment_status'] = PaymentStatus[kwargs['payment_status']]
                except KeyError:
                    valid_statuses = ", ".join([status.name for status in PaymentStatus])
                    raise ModelValidationError(
                        f"Invalid payment status: {kwargs['payment_status']}. "
                        f"Valid values are: {valid_statuses}"
                    )

            # Call parent constructor
            super().__init__(**kwargs)
            logger.debug(
                f"Sales created: ID={self.id}, customer_id={self.customer_id}, total_amount={self.total_amount}")
        except Exception as e:
            if not isinstance(e, ModelValidationError):
                logger.error(f"Error creating Sales: {str(e)}")
                raise ModelValidationError(f"Failed to create Sales: {str(e)}")
            raise

    def calculate_total(self) -> float:
        """
        Calculate the total sale amount based on items.

        Returns:
            float: The total sale amount
        """
        # Use lazy import to avoid circular imports
        SalesItem = lazy_import('database.models.sales_item', 'SalesItem')

        if hasattr(self, 'items'):
            total = sum(item.price * item.quantity for item in self.items)
            self.total_amount = total
            logger.debug(f"Calculated total for sale ID {self.id}: {self.total_amount}")
            return total
        return 0.0

    def add_item(self, sales_item: Any) -> None:
        """
        Add an item to the sale and update total.

        Args:
            sales_item: The SalesItem to add
        """
        if not hasattr(self, 'items'):
            # Initialize items list if not already done
            self.items = []

        if sales_item not in self.items:
            self.items.append(sales_item)
            self.calculate_total()
            logger.debug(f"Added item to sale ID {self.id}: {sales_item}")

    def remove_item(self, sales_item: Any) -> bool:
        """
        Remove an item from the sale and update total.

        Args:
            sales_item: The SalesItem to remove

        Returns:
            bool: True if item was removed, False if not found
        """
        if hasattr(self, 'items') and sales_item in self.items:
            self.items.remove(sales_item)
            self.calculate_total()
            logger.debug(f"Removed item from sale ID {self.id}: {sales_item}")
            return True
        return False

    def create_picking_list(self) -> Any:
        """
        Create a picking list for this sale.

        Returns:
            PickingList: The created picking list
        """
        # Import here to avoid circular imports
        PickingList = lazy_import('database.models.picking_list', 'PickingList')

        if hasattr(self, 'picking_list') and self.picking_list:
            logger.debug(f"Picking list already exists for sale ID {self.id}")
            return self.picking_list

        picking_list = PickingList(sales_id=self.id)
        if not hasattr(self, 'picking_list'):
            self.picking_list = None
        self.picking_list = picking_list
        logger.debug(f"Created picking list for sale ID {self.id}")
        return picking_list

    def __repr__(self) -> str:
        """String representation of the Sales."""
        return f"Sales(id={self.id}, customer_id={self.customer_id}, total_amount={self.total_amount}, status={self.status.name})"


def initialize_relationships() -> None:
    """
    Set up relationships to avoid circular imports.
    This function is called after all models are imported.
    """
    logger.debug("Initializing Sales relationships")
    try:
        # Import models - using lazy_import to avoid issues
        SalesItem = lazy_import('database.models.sales_item', 'SalesItem')
        Customer = lazy_import('database.models.customer', 'Customer')
        PickingList = lazy_import('database.models.picking_list', 'PickingList')
        Project = lazy_import('database.models.project', 'Project')

        # Set up relationships if not already done
        if not hasattr(Sales, 'items') or Sales.items is None:
            Sales.items = relationship("SalesItem", back_populates="sale", cascade="all, delete-orphan")
            logger.debug("Set up Sales.items relationship")

        if not hasattr(Sales, 'customer') or Sales.customer is None:
            Sales.customer = relationship("Customer", back_populates="sales")
            logger.debug("Set up Sales.customer relationship")

        if not hasattr(Sales, 'picking_list') or Sales.picking_list is None:
            Sales.picking_list = relationship("PickingList", back_populates="sale", uselist=False,
                                              cascade="all, delete-orphan")
            logger.debug("Set up Sales.picking_list relationship")

        if not hasattr(Sales, 'project') or Sales.project is None:
            Sales.project = relationship("Project", back_populates="sale", uselist=False)
            logger.debug("Set up Sales.project relationship")

        logger.info("Sales relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Sales relationships: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())