# database/models/picking_list.py
"""
Enhanced PickingList Model with Advanced Relationship and Validation Strategies

This module defines the PickingList and PickingListItem models with comprehensive
validation, relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, String, Text, Boolean, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import PickingListStatus
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    register_relationship
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)
from utils.enhanced_relationship_strategy import (
    RelationshipConfiguration,
    RelationshipLoadingStrategy
)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('database.models.order.Order', 'database.models.order')
register_lazy_import('database.models.user.User', 'database.models.user')
register_lazy_import('database.models.product.Product', 'database.models.product')
register_lazy_import('database.models.material.Material', 'database.models.material')
register_lazy_import('database.models.leather.Leather', 'database.models.leather')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware')
register_lazy_import('database.models.storage.Storage', 'database.models.storage')

# Lazy load model classes to prevent circular imports
Order = lazy_import("database.models.order", "Order")
User = lazy_import("database.models.user", "User")
Product = lazy_import("database.models.product", "Product")
Material = lazy_import("database.models.material", "Material")
Leather = lazy_import("database.models.leather", "Leather")
Hardware = lazy_import("database.models.hardware", "Hardware")
Storage = lazy_import("database.models.storage", "Storage")

# Setup logger
logger = logging.getLogger(__name__)


class PickingList(Base):
    """
    Enhanced PickingList model with comprehensive validation and relationship management.

    Represents a picking list for order fulfillment with advanced tracking
    and relationship configuration.
    """
    __tablename__ = 'picking_lists'

    # PickingList specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT, nullable=False)

    creation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    completion_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys with explicit support for circular imports
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Comprehensive relationships with advanced configuration
    order = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingList',
        target_model='database.models.order.Order',
        relationship_name='order',
        back_populates='picking_lists',
        loading_strategy=RelationshipLoadingStrategy.LAZY
    )

    user = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingList',
        target_model='database.models.user.User',
        relationship_name='user',
        back_populates='assigned_picking_lists',
        loading_strategy=RelationshipLoadingStrategy.LAZY
    )

    items = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingList',
        target_model='database.models.picking_list.PickingListItem',
        relationship_name='items',
        back_populates='picking_list',
        cascade="all, delete-orphan",
        loading_strategy=RelationshipLoadingStrategy.SELECTIN
    )

    def __init__(self, **kwargs):
        """
        Initialize a PickingList instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for picking list attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingList initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PickingList: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate picking list creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): PickingList creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Picking list name is required')

        # Validate status
        if 'status' in data and data['status']:
            ModelValidator.validate_enum(
                data['status'],
                PickingListStatus,
                'status'
            )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate relationships
        if self.order and not hasattr(self.order, 'id'):
            raise ValidationError("Invalid order reference", "order")

        if self.user and not hasattr(self.user, 'id'):
            raise ValidationError("Invalid user reference", "user")

        # Validate status transitions
        if self.status == PickingListStatus.COMPLETED and not self.all_items_picked():
            raise ValidationError(
                "Cannot mark picking list as completed if not all items are picked",
                "status"
            )

    def mark_as_completed(self) -> None:
        """
        Mark the picking list as completed with validation.

        Raises:
            ModelValidationError: If status change is invalid
        """
        try:
            # Validate all items are picked
            if not self.all_items_picked():
                raise ModelValidationError(
                    "Cannot complete picking list with unpicked items"
                )

            # Change status if not already completed
            if self.status != PickingListStatus.COMPLETED:
                self.status = PickingListStatus.COMPLETED
                self.completion_date = datetime.utcnow()

                logger.info(f"PickingList {self.id} marked as completed")

        except Exception as e:
            logger.error(f"Completing picking list failed: {e}")
            raise ModelValidationError(f"Cannot complete picking list: {str(e)}")

    def mark_as_in_progress(self) -> None:
        """
        Mark the picking list as in progress with validation.

        Raises:
            ModelValidationError: If status change is invalid
        """
        try:
            # Change status if not already in progress
            if self.status != PickingListStatus.IN_PROGRESS:
                self.status = PickingListStatus.IN_PROGRESS

                logger.info(f"PickingList {self.id} marked as in progress")

        except Exception as e:
            logger.error(f"Marking picking list as in progress failed: {e}")
            raise ModelValidationError(f"Cannot mark picking list as in progress: {str(e)}")

    def cancel(self) -> None:
        """
        Cancel the picking list with validation.

        Raises:
            ModelValidationError: If cancellation is invalid
        """
        try:
            # Change status if not already cancelled
            if self.status != PickingListStatus.CANCELLED:
                self.status = PickingListStatus.CANCELLED

                logger.info(f"PickingList {self.id} cancelled")

        except Exception as e:
            logger.error(f"Cancelling picking list failed: {e}")
            raise ModelValidationError(f"Cannot cancel picking list: {str(e)}")

    def all_items_picked(self) -> bool:
        """
        Check if all items in the picking list have been picked.

        Returns:
            bool: True if all items are picked, False otherwise
        """
        if not self.items:
            return False

        return all(item.is_picked for item in self.items)

    def generate_picking_list_code(self) -> str:
        """
        Generate a unique picking list code.

        Returns:
            str: Generated picking list code
        """
        try:
            # Use creation date and ID to create unique code
            date_part = self.creation_date.strftime('%Y%m%d')

            # Take first 3 letters of name (uppercase)
            name_part = ''.join(c for c in self.name if c.isalnum())[:3].upper()

            # Append last 4 digits of ID
            id_part = str(self.id).zfill(4)[-4:]

            return f"{name_part}-{date_part}-{id_part}"
        except Exception as e:
            logger.error(f"Picking list code generation failed: {e}")
            raise ModelValidationError(f"Cannot generate picking list code: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the picking list.

        Returns:
            str: Detailed picking list representation
        """
        return (
            f"<PickingList(id={self.id}, "
            f"name='{self.name}', "
            f"status={self.status}, "
            f"items={len(self.items or [])})>"
        )


class PickingListItem(Base):
    """
    Enhanced PickingListItem model with comprehensive validation and relationship management.

    Represents an individual item in a picking list with advanced tracking
    and relationship configuration.
    """
    __tablename__ = 'picking_list_items'

    # PickingListItem specific fields
    quantity_required = Column(Float, default=1.0, nullable=False)
    quantity_picked = Column(Float, default=0.0, nullable=False)

    is_picked = Column(Boolean, default=False, nullable=False)
    picked_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys with explicit support for circular imports
    picking_list_id = Column(Integer, ForeignKey("picking_lists.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id"), nullable=True)

    # Comprehensive relationships with advanced configuration
    picking_list = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingListItem',
        target_model='database.models.picking_list.PickingList',
        relationship_name='picking_list',
        back_populates='items',
        loading_strategy=RelationshipLoadingStrategy.LAZY
    )

    product = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingListItem',
        target_model='database.models.product.Product',
        relationship_name='product',
        loading_strategy=RelationshipLoadingStrategy.LAZY,
        uselist=False,
        viewonly=True
    )

    material = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingListItem',
        target_model='database.models.material.Material',
        relationship_name='material',
        loading_strategy=RelationshipLoadingStrategy.LAZY,
        uselist=False,
        viewonly=True
    )

    leather = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingListItem',
        target_model='database.models.leather.Leather',
        relationship_name='leather',
        loading_strategy=RelationshipLoadingStrategy.LAZY,
        uselist=False,
        viewonly=True
    )

    hardware = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingListItem',
        target_model='database.models.hardware.Hardware',
        relationship_name='hardware',
        loading_strategy=RelationshipLoadingStrategy.LAZY,
        uselist=False,
        viewonly=True
    )

    storage = RelationshipConfiguration.configure_relationship(
        source_model='database.models.picking_list.PickingListItem',
        target_model='database.models.storage.Storage',
        relationship_name='storage',
        loading_strategy=RelationshipLoadingStrategy.LAZY,
        uselist=False,
        viewonly=True
    )

    def __init__(self, **kwargs):
        """
        Initialize a PickingListItem instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for picking list item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingListItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PickingListItem: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate picking list item creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): PickingListItem creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate picking list reference
        if 'picking_list_id' not in data:
            raise ValidationError("Picking list ID is required", "picking_list_id")

        # Validate quantities
        if 'quantity_required' in data:
            validate_positive_number(
                data,
                'quantity_required',
                message="Quantity required must be greater than zero"
            )

        # Ensure at least one item reference is provided
        if not any(key in data for key in ['product_id', 'material_id', 'leather_id', 'hardware_id']):
            raise ValidationError(
                "At least one of product_id, material_id, leather_id, or hardware_id must be specified",
                "item_reference"
            )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate quantities
        if self.quantity_picked > self.quantity_required:
            raise ValidationError(
                "Picked quantity cannot exceed required quantity",
                "quantity_picked"
            )

        # Validate item references
        item_references = [
            ('product', self.product),
            ('material', self.material),
            ('leather', self.leather),
            ('hardware', self.hardware)
        ]

        for ref_name, ref_obj in item_references:
            if ref_obj and not hasattr(ref_obj, 'id'):
                raise ValidationError(f"Invalid {ref_name} reference", f"{ref_name}_id")

    def mark_as_picked(self, quantity: Optional[float] = None) -> None:
        """
        Mark the item as picked with comprehensive validation.

        Args:
            quantity (Optional[float]): The quantity picked.
                                        If not provided, will use quantity_required.

        Raises:
            ModelValidationError: If marking as picked fails
        """
        try:
            # Validate and set quantity
            if quantity is None:
                quantity = self.quantity_required
            else:
                # Validate input quantity
                validate_positive_number(
                    {'quantity': quantity},
                    'quantity',
                    message="Picked quantity must be a positive number"
                )

                # Ensure quantity does not exceed required quantity
                if quantity > self.quantity_required:
                    raise ModelValidationError(
                        f"Cannot pick more than required. "
                        f"Required: {self.quantity_required}, Attempted: {quantity}"
                    )

            # Update picking details
            self.quantity_picked = quantity
            self.is_picked = True
            self.picked_at = datetime.utcnow()

            logger.info(
                f"PickingListItem {self.id} marked as picked. "
                f"Quantity: {quantity}"
            )

        except Exception as e:
            logger.error(f"Marking picking list item as picked failed: {e}")
            raise ModelValidationError(f"Cannot mark item as picked: {str(e)}")

    def reset_picked_status(self) -> None:
        """
        Reset the picked status of the item with validation.

        Raises:
            ModelValidationError: If resetting status fails
        """
        try:
            # Check if item is already unpicked
            if not self.is_picked:
                logger.info(f"PickingListItem {self.id} is already unpicked")
                return

            # Reset picking details
            self.is_picked = False
            self.quantity_picked = 0.0
            self.picked_at = None

            logger.info(f"PickingListItem {self.id} picking status reset")

        except Exception as e:
            logger.error(f"Resetting picking list item status failed: {e}")
            raise ModelValidationError(f"Cannot reset item picking status: {str(e)}")

    def generate_item_code(self) -> str:
        """
        Generate a unique item code for the picking list item.

        Returns:
            str: Generated item code
        """
        try:
            # Determine item type and ID
            item_type = "UNK"
            item_id = "0000"

            if self.product_id:
                item_type = "PRD"
                item_id = str(self.product_id).zfill(4)[-4:]
            elif self.material_id:
                item_type = "MAT"
                item_id = str(self.material_id).zfill(4)[-4:]
            elif self.leather_id:
                item_type = "LTH"
                item_id = str(self.leather_id).zfill(4)[-4:]
            elif self.hardware_id:
                item_type = "HRD"
                item_id = str(self.hardware_id).zfill(4)[-4:]

            # Append last 4 digits of picking list item ID
            item_code_part = str(self.id).zfill(4)[-4:]

            return f"{item_type}-{item_id}-{item_code_part}"
        except Exception as e:
            logger.error(f"Item code generation failed: {e}")
            raise ModelValidationError(f"Cannot generate item code: {str(e)}")

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the picking list item.

        Returns:
            str: Detailed picking list item representation
        """
        item_type = "Unknown"
        item_id = None

        if self.product_id:
            item_type = "Product"
            item_id = self.product_id
        elif self.material_id:
            item_type = "Material"
            item_id = self.material_id
        elif self.leather_id:
            item_type = "Leather"
            item_id = self.leather_id
        elif self.hardware_id:
            item_type = "Hardware"
            item_id = self.hardware_id

        return (
            f"<PickingListItem(id={self.id}, "
            f"type={item_type}, "
            f"item_id={item_id}, "
            f"picked={self.is_picked}, "
            f"quantity_picked={self.quantity_picked})>"
        )


# Final registration for lazy imports
register_lazy_import('database.models.picking_list.PickingList', 'database.models.picking_list')
register_lazy_import('database.models.picking_list.PickingListItem', 'database.models.picking_list')