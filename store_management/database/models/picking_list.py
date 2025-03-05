"""
database/models/picking_list.py - SQLAlchemy model for picking lists and picking list items.

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
    register_relationship,
    register_class_alias
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Register class aliases to handle cross-module references
register_class_alias('database.models.project', 'ProjectComponent', 'database.models.components', 'ProjectComponent')

# Register lazy imports to resolve circular dependencies
register_lazy_import('database.models.order', 'Order')
register_lazy_import('database.models.product', 'Product')
register_lazy_import('database.models.project', 'Project')
register_lazy_import('database.models.material', 'Material')
register_lazy_import('database.models.leather', 'Leather')
register_lazy_import('database.models.hardware', 'Hardware')
register_lazy_import('database.models.storage', 'Storage')
register_lazy_import('database.models.user', 'User')

# Set up logger
logger = logging.getLogger(__name__)


class PickingList(Base):
    """
    Enhanced PickingList model with comprehensive validation and relationship management.

    Represents a picking list for order fulfillment with advanced tracking capabilities.
    """
    __tablename__ = 'picking_lists'

    # Primary key
    id = Column(Integer, primary_key=True)

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    creation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    completion_date = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    # Using simple string-based relationships to avoid circular import issues
    order = relationship("Order", backref="picking_lists")
    project = relationship("Project", backref="picking_lists")
    assigned_to = relationship("User", backref="assigned_picking_lists")

    # One-to-many relationship with items
    items = relationship(
        "PickingListItem",
        back_populates="picking_list",
        cascade="all, delete-orphan",
        lazy="selectin"
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
            # Validate required fields
            if 'name' not in kwargs or not kwargs['name']:
                raise ValidationError("Picking list name is required", "name")

            # Validate status if provided
            if 'status' in kwargs and kwargs['status'] is not None:
                if not isinstance(kwargs['status'], PickingListStatus):
                    if isinstance(kwargs['status'], str):
                        try:
                            kwargs['status'] = PickingListStatus[kwargs['status']]
                        except KeyError:
                            raise ValidationError(f"Invalid status value: {kwargs['status']}", "status")
                    else:
                        raise ValidationError(f"Invalid status type: {type(kwargs['status'])}", "status")

            # Initialize base model
            super().__init__(**kwargs)

            logger.debug(f"Created PickingList: {self.name} with ID {self.id}")

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingList initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PickingList: {str(e)}") from e

    def mark_as_completed(self) -> None:
        """
        Mark the picking list as completed with validation.

        Sets the status to COMPLETED and records the completion date.

        Raises:
            ModelValidationError: If all items are not picked
        """
        try:
            # Validate all items are picked
            if not self.all_items_picked():
                raise ModelValidationError("Cannot complete picking list with unpicked items")

            # Update status and completion date
            self.status = PickingListStatus.COMPLETED
            self.completion_date = datetime.utcnow()

            logger.info(f"PickingList {self.id} marked as completed")

        except Exception as e:
            logger.error(f"Error marking picking list as completed: {e}")
            raise ModelValidationError(f"Cannot complete picking list: {str(e)}")

    def mark_as_in_progress(self) -> None:
        """
        Mark the picking list as in progress.

        Updates the status to IN_PROGRESS.
        """
        try:
            self.status = PickingListStatus.IN_PROGRESS
            logger.info(f"PickingList {self.id} marked as in progress")
        except Exception as e:
            logger.error(f"Error marking picking list as in progress: {e}")
            raise ModelValidationError(f"Cannot update picking list status: {str(e)}")

    def cancel(self) -> None:
        """
        Cancel the picking list.

        Updates the status to CANCELLED.
        """
        try:
            self.status = PickingListStatus.CANCELLED
            logger.info(f"PickingList {self.id} cancelled")
        except Exception as e:
            logger.error(f"Error cancelling picking list: {e}")
            raise ModelValidationError(f"Cannot cancel picking list: {str(e)}")

    def all_items_picked(self) -> bool:
        """
        Check if all items in the picking list have been picked.

        Returns:
            bool: True if all items are picked, False otherwise
        """
        if not self.items:
            return False

        return all(item.picked for item in self.items)

    def get_completion_percentage(self) -> float:
        """
        Calculate the completion percentage of the picking list.

        Returns:
            float: Percentage of items picked (0-100)
        """
        if not self.items:
            return 0.0

        total_items = len(self.items)
        picked_items = sum(1 for item in self.items if item.picked)

        return (picked_items / total_items) * 100.0

    def generate_picking_code(self) -> str:
        """
        Generate a unique picking list code.

        Returns:
            str: Generated picking list code
        """
        # Use creation date and ID to create unique code
        date_part = self.creation_date.strftime('%Y%m%d')

        # Take first 3 letters of name (uppercase)
        name_part = ''.join(c for c in self.name if c.isalnum())[:3].upper()

        # Format ID with leading zeros
        id_part = str(self.id).zfill(4)

        return f"PL-{name_part}-{date_part}-{id_part}"

    def __repr__(self) -> str:
        """
        String representation of the picking list.

        Returns:
            str: Descriptive string of the picking list
        """
        return (
            f"<PickingList(id={self.id}, "
            f"name='{self.name}', "
            f"status={self.status.name if self.status else 'None'}, "
            f"items={len(self.items) if self.items else 0})>"
        )


class PickingListItem(Base):
    """
    Enhanced PickingListItem model with comprehensive validation and relationship management.

    Represents an individual item in a picking list with detailed tracking.
    """
    __tablename__ = 'picking_list_items'

    # Primary key
    id = Column(Integer, primary_key=True)

    # Basic information
    quantity = Column(Float, default=1.0, nullable=False)
    picked = Column(Boolean, default=False, nullable=False)
    picked_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    location_info = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign keys
    picking_list_id = Column(Integer, ForeignKey("picking_lists.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storage.id"), nullable=True)

    # Relationships
    # Many-to-one relationship with picking list
    picking_list = relationship("PickingList", back_populates="items")

    # Using simple string-based relationships to avoid circular import issues
    product = relationship("Product")
    material = relationship("Material")
    leather = relationship("Leather")
    hardware = relationship("Hardware")
    storage = relationship("Storage")

    def __init__(self, **kwargs):
        """
        Initialize a PickingListItem instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for picking list item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate required fields
            if 'picking_list_id' not in kwargs:
                raise ValidationError("Picking list ID is required", "picking_list_id")

            # Validate quantity
            if 'quantity' in kwargs and kwargs['quantity'] is not None:
                if float(kwargs['quantity']) <= 0:
                    raise ValidationError("Quantity must be positive", "quantity")

            # Ensure at least one item reference is provided
            if not any(key in kwargs for key in ['product_id', 'material_id', 'leather_id', 'hardware_id']):
                raise ValidationError(
                    "At least one of product_id, material_id, leather_id, or hardware_id must be specified",
                    "item_reference"
                )

            # Initialize base model
            super().__init__(**kwargs)

            logger.debug(f"Created PickingListItem for list ID {self.picking_list_id}")

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingListItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PickingListItem: {str(e)}") from e

    def mark_as_picked(self):
        """
        Mark the item as picked.

        Sets the picked flag to True and records the picked date.
        """
        try:
            self.picked = True
            self.picked_date = datetime.utcnow()
            logger.info(f"PickingListItem {self.id} marked as picked")
        except Exception as e:
            logger.error(f"Error marking item as picked: {e}")
            raise ModelValidationError(f"Cannot mark item as picked: {str(e)}")

    def reset_picked_status(self):
        """
        Reset the picked status of the item.

        Clears the picked flag and picked date.
        """
        try:
            self.picked = False
            self.picked_date = None
            logger.info(f"PickingListItem {self.id} picking status reset")
        except Exception as e:
            logger.error(f"Error resetting picked status: {e}")
            raise ModelValidationError(f"Cannot reset picked status: {str(e)}")

    def get_item_name(self) -> str:
        """
        Get the name of the item based on its reference type.

        Returns:
            str: Name of the referenced item or 'Unknown'
        """
        if self.product_id and hasattr(self, 'product') and self.product:
            return f"Product: {self.product.name}"
        elif self.material_id and hasattr(self, 'material') and self.material:
            return f"Material: {self.material.name}"
        elif self.leather_id and hasattr(self, 'leather') and self.leather:
            return f"Leather: {self.leather.name}"
        elif self.hardware_id and hasattr(self, 'hardware') and self.hardware:
            return f"Hardware: {self.hardware.name}"
        return "Unknown Item"

    def get_item_code(self) -> str:
        """
        Generate a unique item code for the picking list item.

        Returns:
            str: Generated item code
        """
        # Determine item type
        item_type = "ITEM"
        item_id = "0000"

        if self.product_id:
            item_type = "PROD"
            item_id = str(self.product_id).zfill(4)
        elif self.material_id:
            item_type = "MATL"
            item_id = str(self.material_id).zfill(4)
        elif self.leather_id:
            item_type = "LTHR"
            item_id = str(self.leather_id).zfill(4)
        elif self.hardware_id:
            item_type = "HDWR"
            item_id = str(self.hardware_id).zfill(4)

        # Format item code with picking list ID and item ID
        return f"{item_type}-{self.picking_list_id:04d}-{item_id}-{self.id:04d}"

    def __repr__(self) -> str:
        """
        String representation of the picking list item.

        Returns:
            str: Descriptive string of the picking list item
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
            f"picked={self.picked}, "
            f"quantity={self.quantity})>"
        )