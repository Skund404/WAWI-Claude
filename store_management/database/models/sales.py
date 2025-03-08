# database/models/sales.py
"""
Enhanced Sales Model for Leatherworking Management System

Represents sales transactions with comprehensive tracking,
validation, and relationship management.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.sql import sqltypes
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import SaleStatus, PaymentStatus
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    register_lazy_import,
    lazy_import
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


class Sales(Base, apply_mixins(TimestampMixin, ValidationMixin, CostingMixin)):
    """
    Sales model representing a complete sales transaction in the system.

    Tracks comprehensive details of sales, including status,
    payment, and associated entities.
    """
    __tablename__ = 'sales'

    # Primary key (explicitly defined)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

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

    # Status tracking - use sqltypes.Enum explicitly to avoid potential conflicts
    status: Mapped[SaleStatus] = mapped_column(
        sqltypes.Enum(SaleStatus),
        default=SaleStatus.QUOTE_REQUEST,
        nullable=False
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        sqltypes.Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )

    # Additional fields
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        default=lambda: Sales._generate_reference_number()
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

    @classmethod
    def _generate_reference_number(cls) -> str:
        """
        Generate a unique reference number for the sale.

        Returns:
            str: Unique reference number
        """
        # Use UUID to generate a unique reference number
        # Prefix with 'S-' for Sales and truncate to 50 characters
        return f"S-{str(uuid.uuid4())[:8]}"

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

    # ... (rest of the methods remain the same as in the previous version)


def initialize_relationships():
    """
    Initialize relationships for Sales model.

    This method is used by the centralized relationship initialization process.
    """
    logger.info("Initializing Sales relationships...")
    from utils.circular_import_resolver import register_relationship

    # Define relationships to register
    relationships = {
        'items': {
            'secondary': 'SalesItem',
            'back_populates': 'sale',
            'cascade': 'all, delete-orphan',
            'lazy': 'selectin'
        },
        'customer': {
            'secondary': 'Customer',
            'back_populates': 'sales_records',
            'lazy': 'selectin'
        }
    }

    # Register each relationship
    for rel_name, rel_config in relationships.items():
        register_relationship('Sales', rel_name, rel_config)

    logger.info("Sales relationships registered successfully")


# Register for lazy import resolution
register_lazy_import('Sales', 'database.models.sales', 'Sales')