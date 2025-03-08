# database/models/purchase_item.py
"""
Comprehensive Purchase Item Model for Leatherworking Management System

This module defines the PurchaseItem model with extensive validation,
relationship management, and circular import resolution.

Implements the PurchaseItem entity from the ER diagram with all its
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
    TransactionType,
    InventoryStatus,
    MaterialType,
    LeatherType,
    HardwareType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin
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
register_lazy_import('Purchase', 'database.models.purchase', 'Purchase')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Tool', 'database.models.tool', 'Tool')
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')


class PurchaseItem(Base, TimestampMixin, ValidationMixin, CostingMixin):
    """
    PurchaseItem model representing items in a purchase order.

    This implements the PurchaseItem entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'purchase_items'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(Integer, ForeignKey('purchases.id'), nullable=False, index=True)

    # Quantity and pricing
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Reference to purchasable items - only one should be set per the ER diagram
    material_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('materials.id'), nullable=True)
    leather_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leathers.id'), nullable=True)
    hardware_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('hardwares.id'), nullable=True)
    tool_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tools.id'), nullable=True)

    # Item description and details
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    item_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status tracking
    is_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    received_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    received_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships - following the ER diagram
    purchase = relationship("Purchase", back_populates="items")
    material = relationship("Material", lazy="select")
    leather = relationship("Leather", lazy="select")
    hardware = relationship("Hardware", lazy="select")
    tool = relationship("Tool", lazy="select")

    # Transaction relationship for inventory updates
    transactions = relationship("Transaction", lazy="select")

    def __init__(self, **kwargs):
        """
        Initialize a PurchaseItem instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for purchase item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Calculate total price if not provided
            if 'price' in kwargs and 'quantity' in kwargs and 'total_price' not in kwargs:
                kwargs['total_price'] = kwargs['price'] * kwargs['quantity']

            # Validate input data
            self._validate_purchase_item_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PurchaseItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PurchaseItem: {str(e)}") from e

    @classmethod
    def _validate_purchase_item_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of purchase item creation data.

        Args:
            data: Purchase item creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'purchase_id', 'Purchase ID is required')
        validate_not_empty(data, 'quantity', 'Quantity is required')
        validate_not_empty(data, 'price', 'Price is required')

        # Validate quantity and price
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be a positive number"
            )

        if 'price' in data:
            validate_positive_number(
                data,
                'price',
                allow_zero=False,
                message="Price must be a positive number"
            )

        if 'total_price' in data and data['total_price'] is not None:
            validate_positive_number(
                data,
                'total_price',
                allow_zero=False,
                message="Total price must be a positive number"
            )

        # Validate that at least one item type is specified
        if not any([
            data.get('material_id'),
            data.get('leather_id'),
            data.get('hardware_id'),
            data.get('tool_id')
        ]):
            raise ValidationError(
                "At least one item type (material, leather, hardware, or tool) must be specified",
                "item_reference"
            )

        # Ensure mutually exclusive item types
        item_fields = ['material_id', 'leather_id', 'hardware_id', 'tool_id']
        specified_items = sum(1 for field in item_fields if data.get(field) is not None)

        if specified_items > 1:
            raise ValidationError(
                "Only one item type (material, leather, hardware, or tool) can be specified per purchase item",
                "item_reference"
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Calculate total price if not set
        if not hasattr(self, 'total_price') or self.total_price is None:
            self.total_price = self.price * self.quantity

        # Initialize received quantity if not set
        if not hasattr(self, 'received_quantity') or self.received_quantity is None:
            self.received_quantity = 0

        # Initialize metadata if not provided
        if not hasattr(self, 'metadata') or self.metadata is None:
            self.metadata = {}

    def mark_as_received(self,
                         received_quantity: Optional[int] = None,
                         received_date: Optional[datetime] = None,
                         create_transaction: bool = True,
                         notes: Optional[str] = None) -> Optional['Transaction']:
        """
        Mark this purchase item as received and optionally create an inventory transaction.

        Args:
            received_quantity: The quantity received (defaults to ordered quantity)
            received_date: The date received (defaults to current date/time)
            create_transaction: Whether to create an inventory transaction
            notes: Optional notes about the receipt

        Returns:
            Created transaction if create_transaction is True, otherwise None

        Raises:
            ModelValidationError: If receipt processing fails
        """
        try:
            # Validate received quantity
            actual_quantity = received_quantity if received_quantity is not None else self.quantity

            if actual_quantity <= 0:
                raise ValidationError("Received quantity must be greater than zero")

            if actual_quantity > self.quantity:
                logger.warning(
                    f"Received quantity ({actual_quantity}) exceeds ordered quantity ({self.quantity})"
                )

            # Update receipt information
            self.is_received = True
            self.received_quantity = actual_quantity
            self.received_date = received_date or datetime.utcnow()

            # Create inventory transaction if requested
            if create_transaction:
                return self._create_receipt_transaction(actual_quantity, notes)

            return None

        except Exception as e:
            logger.error(f"Failed to mark purchase item as received: {e}")
            raise ModelValidationError(f"Receipt processing failed: {str(e)}")

    def _create_receipt_transaction(self, quantity: int, notes: Optional[str] = None) -> 'Transaction':
        """
        Create an inventory transaction for this purchase receipt.

        Args:
            quantity: The quantity received
            notes: Optional notes about the receipt

        Returns:
            The created transaction

        Raises:
            ModelValidationError: If transaction creation fails
        """
        try:
            # Import transaction function
            create_transaction = lazy_import('database.models.transaction', 'create_transaction')

            # Determine item type and ID
            if self.material_id is not None:
                item_type = 'material'
                item_id = self.material_id
            elif self.leather_id is not None:
                item_type = 'leather'
                item_id = self.leather_id
            elif self.hardware_id is not None:
                item_type = 'hardware'
                item_id = self.hardware_id
            elif self.tool_id is not None:
                item_type = 'tool'
                item_id = self.tool_id
            else:
                raise ValidationError("No item reference found for transaction creation")

            # Create the transaction
            transaction = create_transaction(
                item_type=item_type,
                item_id=item_id,
                quantity=quantity,
                transaction_type=TransactionType.PURCHASE,
                is_addition=True,
                purchase_id=self.purchase_id,
                notes=notes or f"Receipt of purchase item {self.id}",
                metadata={
                    'purchase_item_id': self.id,
                    'purchase_id': self.purchase_id,
                    'price_per_unit': self.price,
                    'total_price': self.price * quantity
                }
            )

            return transaction

        except Exception as e:
            logger.error(f"Failed to create receipt transaction: {e}")
            raise ModelValidationError(f"Transaction creation failed: {str(e)}")

    def get_item_details(self) -> Dict[str, Any]:
        """
        Get details about the referenced item.

        Returns:
            Dictionary with item details
        """
        item_details = {
            'name': self.get_item_name(),
            'type': self.get_item_type(),
            'price': self.price,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'received': self.is_received,
            'description': self.description
        }

        # Add item-specific attributes if available
        if self.material_id is not None and self.material:
            item_details.update({
                'material_type': getattr(self.material, 'material_type', None),
                'unit': getattr(self.material, 'unit', None)
            })
        elif self.leather_id is not None and self.leather:
            item_details.update({
                'leather_type': getattr(self.leather, 'leather_type', None),
                'thickness': getattr(self.leather, 'thickness_mm', None),
                'area': getattr(self.leather, 'size_sqft', None)
            })
        elif self.hardware_id is not None and self.hardware:
            item_details.update({
                'hardware_type': getattr(self.hardware, 'hardware_type', None),
                'material': getattr(self.hardware, 'material', None),
                'finish': getattr(self.hardware, 'finish', None)
            })
        elif self.tool_id is not None and self.tool:
            item_details.update({
                'tool_type': getattr(self.tool, 'tool_type', None)
            })

        return item_details

    def get_item_type(self) -> str:
        """
        Get the type of item referenced by this purchase item.

        Returns:
            String indicating the item type
        """
        if self.material_id is not None:
            return "material"
        elif self.leather_id is not None:
            return "leather"
        elif self.hardware_id is not None:
            return "hardware"
        elif self.tool_id is not None:
            return "tool"
        else:
            return "unknown"

    def get_item_name(self) -> str:
        """
        Get the name of the purchased item.

        Returns:
            Name of the referenced item or description if not available
        """
        if self.material_id is not None and self.material:
            return f"Material: {self.material.name}"
        elif self.leather_id is not None and self.leather:
            return f"Leather: {self.leather.name}"
        elif self.hardware_id is not None and self.hardware:
            return f"Hardware: {self.hardware.name}"
        elif self.tool_id is not None and self.tool:
            return f"Tool: {self.tool.name}"
        else:
            return self.description or "Unknown item"

    def calculate_total(self) -> float:
        """
        Calculate the total price for this item.

        Returns:
            Total price (quantity * price)
        """
        return self.quantity * self.price

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert purchase item to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the purchase item
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        # Build the dictionary
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert datetime to ISO format
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                # Handle other special types here if needed
                else:
                    result[column.name] = value

        # Add computed or related values
        result['item_name'] = self.get_item_name()
        result['item_type'] = self.get_item_type()

        return result

    def __repr__(self) -> str:
        """
        String representation of the PurchaseItem.

        Returns:
            Detailed purchase item representation
        """
        return (
            f"<PurchaseItem(id={self.id}, "
            f"purchase_id={self.purchase_id}, "
            f"item={self.get_item_name()}, "
            f"quantity={self.quantity}, "
            f"price={self.price})>"
        )


# Register for lazy import resolution
register_lazy_import('PurchaseItem', 'database.models.purchase_item', 'PurchaseItem')