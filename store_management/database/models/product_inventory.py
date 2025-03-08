from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/product_inventory.py
"""
Comprehensive Product Inventory Model for Leatherworking Management System

This module defines the ProductInventory model with extensive validation,
relationship management, and circular import resolution.

Implements the ProductInventory entity from the ER diagram with all its
relationships and attributes for tracking finished product inventory.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    InventoryStatus,
    TransactionType,
    InventoryAdjustmentType,
    StorageLocationType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
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
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Storage', 'database.models.storage', 'Storage')

from sqlalchemy.orm import declarative_base
ProductInventoryBase = declarative_base()
ProductInventoryBase.metadata = metadata
ProductInventoryBase.metadata = metadata


class ProductInventory(ProductInventoryBase):
    """
    ProductInventory model representing inventory of finished products.

    This implements the ProductInventory entity from the ER diagram with comprehensive
    attributes and methods for tracking finished product inventory.
    """
    __tablename__ = 'product_inventories'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False, index=True)

    # Inventory details
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        nullable=False,
        default=InventoryStatus.IN_STOCK
    )

    # Storage information
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('storages.id'), nullable=True)
    location_type: Mapped[Optional[StorageLocationType]] = mapped_column(
        Enum(StorageLocationType),
        nullable=True
    )

    # Inventory management thresholds
    reorder_point: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reorder_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # SKU and batch tracking
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Quality tracking
    quality_check_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    quality_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    quality_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Transaction tracking
    last_count_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_movement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="inventory_items")
    storage = relationship("Storage", back_populates="product_inventories")

    def __init__(self, **kwargs):
        """
        Initialize a ProductInventory instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for inventory attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_product_inventory_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ProductInventory initialization failed: {e}")
            raise ModelValidationError(f"Failed to create ProductInventory: {str(e)}") from e

    @classmethod
    def _validate_product_inventory_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of product inventory creation data.

        Args:
            data: Inventory creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'product_id', 'Product ID is required')

        # Validate quantity
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=True,
                message="Quantity cannot be negative"
            )

        # Validate thresholds
        for field in ['reorder_point', 'reorder_quantity', 'max_quantity']:
            if field in data and data[field] is not None:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=False,
                    message=f"{field.replace('_', ' ').title()} must be a positive number"
                )

        # Validate inventory status
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                InventoryStatus,
                'status'
            )

        # Validate location type if provided
        if 'location_type' in data and data['location_type'] is not None:
            ModelValidator.validate_enum(
                data['location_type'],
                StorageLocationType,
                'location_type'
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize metadata if not provided
        if not hasattr(self, 'metadata') or self.metadata is None:
            self.metadata = {}

        # Update status based on quantity
        self._update_status()

        # Set tracking dates for new inventory
        if not hasattr(self, 'last_count_date') or self.last_count_date is None:
            self.last_count_date = datetime.utcnow()

        # Set SKU if not provided but product is available
        if (not hasattr(self, 'sku') or not self.sku) and hasattr(self, 'product') and self.product:
            self.sku = getattr(self.product, 'sku', None)

        # Ensure tracking ID is set
        if not hasattr(self, 'tracking_id') or not self.tracking_id:
            self.generate_tracking_id()

    def _update_status(self) -> None:
        """
        Update the inventory status based on quantity and thresholds.
        """
        if not hasattr(self, 'quantity'):
            return

        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif hasattr(self, 'reorder_point') and self.reorder_point is not None and self.quantity <= self.reorder_point:
            self.status = InventoryStatus.LOW_STOCK
        elif hasattr(self, 'max_quantity') and self.max_quantity is not None and self.quantity >= self.max_quantity:
            self.status = InventoryStatus.ON_ORDER
        else:
            self.status = InventoryStatus.IN_STOCK

        logger.debug(f"Updated status for product inventory {self.id} to {self.status}")

    def update_quantity(self, change: int, notes: Optional[str] = None) -> int:
        """
        Update the quantity of the inventory item.

        Args:
            change: Amount to add (positive) or remove (negative)
            notes: Optional notes about the change

        Returns:
            The new quantity

        Raises:
            ModelValidationError: If the resulting quantity would be negative
        """
        try:
            # Validate change amount
            if not isinstance(change, int):
                raise ValidationError("Quantity change must be an integer")

            # Calculate new quantity
            new_quantity = self.quantity + change

            # Validate new quantity
            if new_quantity < 0:
                raise ValidationError(
                    f"Cannot reduce quantity by {abs(change)} as it would result in negative inventory")

            # Update quantity and dates
            self.quantity = new_quantity
            self.last_movement_date = datetime.utcnow()

            # Add note if provided
            if notes:
                if self.notes:
                    self.notes += f"\n\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} - Quantity changed by {change}: {notes}"
                else:
                    self.notes = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} - Quantity changed by {change}: {notes}"

            # Update status based on new quantity
            self._update_status()

            logger.info(f"Updated quantity for product inventory {self.id} by {change} to {self.quantity}")
            return self.quantity

        except Exception as e:
            logger.error(f"Error updating quantity: {e}")
            raise ModelValidationError(f"Failed to update quantity: {str(e)}")

    def needs_reorder(self) -> bool:
        """
        Check if the inventory item needs to be reordered.

        Returns:
            True if quantity is at or below reorder point
        """
        if not hasattr(self, 'reorder_point') or self.reorder_point is None:
            return False

        return self.quantity <= self.reorder_point

    def perform_quality_check(self, passed: bool, notes: Optional[str] = None) -> None:
        """
        Perform a quality check on the inventory.

        Args:
            passed: Whether the inventory passed quality check
            notes: Optional notes about the quality check
        """
        try:
            self.quality_check_date = datetime.utcnow()
            self.quality_check_passed = passed

            if notes:
                self.quality_notes = notes

            # Update status if quality check failed
            if not passed:
                self.status = InventoryStatus.DISCONTINUED

            logger.info(f"Quality check performed for product inventory {self.id}: {'Passed' if passed else 'Failed'}")

        except Exception as e:
            logger.error(f"Error performing quality check: {e}")
            raise ModelValidationError(f"Failed to perform quality check: {str(e)}")

    def count_inventory(self, actual_quantity: int, notes: Optional[str] = None) -> None:
        """
        Update inventory based on physical count.

        Args:
            actual_quantity: Actual counted quantity
            notes: Optional notes about the count

        Raises:
            ModelValidationError: If count is negative
        """
        try:
            # Validate quantity
            if actual_quantity < 0:
                raise ValidationError("Counted quantity cannot be negative")

            # Calculate difference
            difference = actual_quantity - self.quantity

            # Update quantity
            if difference != 0:
                adjustment_note = f"Inventory count adjustment: from {self.quantity} to {actual_quantity}"
                if notes:
                    adjustment_note += f" - {notes}"

                self.update_quantity(difference, adjustment_note)

            # Update count date regardless of change
            self.last_count_date = datetime.utcnow()

            logger.info(f"Completed inventory count for product inventory {self.id}")

        except Exception as e:
            logger.error(f"Error performing inventory count: {e}")
            raise ModelValidationError(f"Failed to perform inventory count: {str(e)}")

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert product inventory to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the product inventory
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
                # Convert enum to string
                elif isinstance(value, (InventoryStatus, StorageLocationType)):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add product name if available
        if hasattr(self, 'product') and self.product:
            result['product_name'] = getattr(self.product, 'name', None)

        # Add storage location name if available
        if hasattr(self, 'storage') and self.storage:
            result['storage_name'] = getattr(self.storage, 'name', None)

        # Add needs_reorder flag
        result['needs_reorder'] = self.needs_reorder()

        return result

    def __repr__(self) -> str:
        """
        String representation of the ProductInventory.

        Returns:
            Detailed product inventory representation
        """
        return (
            f"<ProductInventory(id={self.id}, "
            f"product_id={self.product_id}, "
            f"quantity={self.quantity}, "
            f"status={self.status.name if hasattr(self, 'status') and self.status else 'None'})>"
        )


def initialize_relationships() -> None:
    """
    Initialize relationships between Product and ProductInventory models.

    This function resolves potential circular dependencies by setting up
    the relationship properties after all models have been loaded.
    """
    try:
        # Import models directly to avoid circular import issues
        from database.models.product import Product
        from database.models.storage import Storage

        # Ensure Product has a relationship to ProductInventory
        if not hasattr(Product, 'inventory_items') or Product.inventory_items is None:
            Product.inventory_items = relationship(
                'ProductInventory',
                back_populates='product',
                cascade='all, delete-orphan'
            )

        # Ensure Storage has a relationship to ProductInventory
        if not hasattr(Storage, 'product_inventories') or Storage.product_inventories is None:
            Storage.product_inventories = relationship(
                'ProductInventory',
                back_populates='storage'
            )

        logger.info("ProductInventory relationships initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing ProductInventory relationships: {e}")


# Register for lazy import resolution
register_lazy_import('ProductInventory', 'database.models.product_inventory', 'ProductInventory')