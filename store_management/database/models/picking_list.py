# database/models/picking_list.py
"""
Comprehensive Picking List Models for Leatherworking Management System

This module defines the PickingList and PickingListItem models with extensive
validation, relationship management, and circular import resolution.

Implements the PickingList and PickingListItem entities from the ER diagram
with all their relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    PickingListStatus,
    TransactionType,
    InventoryStatus
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin,
    apply_mixins  # Added import for apply_mixins
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
register_lazy_import('Sales', 'database.models.sales', 'Sales')
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('Component', 'database.models.components', 'Component')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')


class PickingList(Base, apply_mixins(TimestampMixin, ValidationMixin, TrackingMixin)):  # Updated to use apply_mixins
    """
    PickingList model representing material and hardware picking lists for sales orders.

    This implements the PickingList entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'picking_lists'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # References to related entities
    sales_id: Mapped[int] = mapped_column(Integer, ForeignKey('sales.id'), nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True, index=True)

    # Status and tracking
    status: Mapped[PickingListStatus] = mapped_column(
        Enum(PickingListStatus),
        nullable=False,
        default=PickingListStatus.DRAFT
    )

    # Timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    picking_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Renamed from metadata

    # Relationships
    sales = relationship("Sales", back_populates="picking_list")
    project = relationship("Project", back_populates="picking_lists")
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """
        Initialize a PickingList instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for picking list attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Handle metadata rename if present
            if 'metadata' in kwargs:
                kwargs['picking_metadata'] = kwargs.pop('metadata')

            # Set created_at if not provided
            if 'created_at' not in kwargs:
                kwargs['created_at'] = datetime.utcnow()

            # Validate input data
            self._validate_picking_list_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingList initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PickingList: {str(e)}") from e

    @classmethod
    def _validate_picking_list_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of picking list creation data.

        Args:
            data: Picking list creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'sales_id', 'Sales ID is required')

        # Validate picking list status if provided
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                PickingListStatus,
                'status'
            )

        # Validate priority if provided
        if 'priority' in data and data['priority'] is not None:
            if not isinstance(data['priority'], int) or data['priority'] < 0:
                raise ValidationError("Priority must be a non-negative integer", "priority")

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize metadata if not provided
        if not hasattr(self, 'picking_metadata') or self.picking_metadata is None:
            self.picking_metadata = {}

        # Ensure tracking ID is set
        if not hasattr(self, 'tracking_id') or not self.tracking_id:
            self.generate_tracking_id()

    def add_item(self, item: 'PickingListItem') -> None:
        """
        Add an item to the picking list.

        Args:
            item: Picking list item to add
        """
        if not hasattr(self, 'items'):
            self.items = []

        self.items.append(item)
        logger.info(f"Added item to picking list {self.id}")

    def mark_as_in_progress(self, assigned_to: Optional[str] = None) -> None:
        """
        Mark the picking list as in progress.

        Args:
            assigned_to: Optional name of person assigned to this picking list
        """
        self.status = PickingListStatus.IN_PROGRESS

        if assigned_to:
            self.assigned_to = assigned_to

        logger.info(f"PickingList {self.id} marked as in progress" +
                    (f", assigned to {assigned_to}" if assigned_to else ""))

    def mark_as_completed(self, create_transactions: bool = True) -> List[Optional['Transaction']]:
        """
        Mark the picking list as completed and optionally create inventory transactions.

        Args:
            create_transactions: Whether to create inventory transactions

        Returns:
            List of created transactions (if create_transactions is True)
        """
        try:
            self.status = PickingListStatus.COMPLETED
            self.completed_at = datetime.utcnow()

            transactions = []

            # Create inventory transactions if requested
            if create_transactions:
                transactions = self._create_inventory_transactions()

            logger.info(f"PickingList {self.id} marked as completed")
            return transactions

        except Exception as e:
            logger.error(f"Error completing picking list: {e}")
            raise ModelValidationError(f"Failed to complete picking list: {str(e)}")

    def _create_inventory_transactions(self) -> List[Optional['Transaction']]:
        """
        Create inventory transactions for all picked items.

        Returns:
            List of created transactions
        """
        try:
            transactions = []

            # Import transaction creation function
            create_transaction = lazy_import('database.models.transaction', 'create_transaction')

            # Process each item with a picked quantity
            if hasattr(self, 'items'):
                for item in self.items:
                    if item.quantity_picked > 0:
                        # Determine item type and ID
                        if item.material_id is not None:
                            item_type = 'material'
                            item_id = item.material_id
                        elif item.leather_id is not None:
                            item_type = 'leather'
                            item_id = item.leather_id
                        elif item.hardware_id is not None:
                            item_type = 'hardware'
                            item_id = item.hardware_id
                        else:
                            # Skip if no direct item reference
                            continue

                        # Create transaction for picked items (negative - items leaving inventory)
                        transaction = create_transaction(
                            item_type=item_type,
                            item_id=item_id,
                            quantity=item.quantity_picked,
                            transaction_type=TransactionType.USAGE,
                            is_addition=False,  # Reduction from inventory
                            project_id=self.project_id,
                            notes=f"Picked for sales order {self.sales_id}"
                        )

                        if transaction:
                            transactions.append(transaction)

            return transactions

        except Exception as e:
            logger.error(f"Error creating inventory transactions: {e}")
            raise ModelValidationError(f"Failed to create inventory transactions: {str(e)}")

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancel the picking list.

        Args:
            reason: Optional reason for cancellation
        """
        self.status = PickingListStatus.CANCELLED

        if reason:
            if self.notes:
                self.notes += f"\n\nCancelled: {reason}"
            else:
                self.notes = f"Cancelled: {reason}"

        logger.info(f"PickingList {self.id} cancelled" + (f": {reason}" if reason else ""))

    def get_completion_percentage(self) -> float:
        """
        Calculate the completion percentage of the picking list.

        Returns:
            Percentage of items picked
        """
        if not hasattr(self, 'items') or not self.items:
            return 0.0

        total_ordered = sum(item.quantity_ordered for item in self.items)

        if total_ordered == 0:
            return 0.0

        total_picked = sum(item.quantity_picked for item in self.items)

        return (total_picked / total_ordered) * 100.0

    def to_dict(self, exclude_fields: Optional[List[str]] = None, include_items: bool = False) -> Dict[str, Any]:
        """
        Convert picking list to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude
            include_items: Whether to include picking list items

        Returns:
            Dictionary representation of the picking list
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
                elif isinstance(value, PickingListStatus):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add computed fields
        result['completion_percentage'] = self.get_completion_percentage()

        # Add items if requested
        if include_items and hasattr(self, 'items') and self.items:
            result['items'] = [item.to_dict() for item in self.items]

        return result

    def __repr__(self) -> str:
        """
        String representation of the PickingList.

        Returns:
            Detailed picking list representation
        """
        return (
            f"<PickingList(id={self.id}, "
            f"sales_id={self.sales_id}, "
            f"status={self.status.name if self.status else 'None'}, "
            f"items={len(self.items) if hasattr(self, 'items') else 0})>"
        )


class PickingListItem(Base, apply_mixins(TimestampMixin, ValidationMixin)):
    """
    PickingListItem model representing an item in a picking list.

    This implements the PickingListItem entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'picking_list_items'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    picking_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('picking_lists.id'), nullable=False, index=True)

    # References to different item types - only one should be set per the ER diagram
    component_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('components.id'), nullable=True)
    material_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('materials.id'), nullable=True)
    leather_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leathers.id'), nullable=True)
    hardware_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('hardwares.id'), nullable=True)

    # Quantities
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_picked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    component = relationship("Component", foreign_keys=[component_id])
    material = relationship("Material", foreign_keys=[material_id])
    leather = relationship("Leather", foreign_keys=[leather_id])
    hardware = relationship("Hardware", foreign_keys=[hardware_id])
    project_component = relationship("ProjectComponent", back_populates="picking_list_item")

    def __init__(self, **kwargs):
        """
        Initialize a PickingListItem instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for picking list item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Set quantity_picked to 0 if not provided
            if 'quantity_picked' not in kwargs:
                kwargs['quantity_picked'] = 0

            # Validate input data
            self._validate_picking_list_item_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingListItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PickingListItem: {str(e)}") from e

    @classmethod
    def _validate_picking_list_item_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of picking list item creation data.

        Args:
            data: Picking list item creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'picking_list_id', 'Picking list ID is required')
        validate_not_empty(data, 'quantity_ordered', 'Quantity ordered is required')

        # Validate quantities
        for field in ['quantity_ordered', 'quantity_picked']:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=(field == 'quantity_picked'),  # Allow zero for picked quantity
                    message=f"{field.replace('_', ' ').title()} must be {'non-negative' if field == 'quantity_picked' else 'positive'}"
                )

        # Validate that quantity_picked doesn't exceed quantity_ordered
        if 'quantity_picked' in data and 'quantity_ordered' in data:
            if data['quantity_picked'] > data['quantity_ordered']:
                raise ValidationError(
                    "Picked quantity cannot exceed ordered quantity",
                    "quantity_picked"
                )

        # Validate that at least one item type is specified
        if not any([
            data.get('component_id'),
            data.get('material_id'),
            data.get('leather_id'),
            data.get('hardware_id')
        ]):
            raise ValidationError(
                "At least one item type (component, material, leather, or hardware) must be specified",
                "item_reference"
            )

        # Ensure mutually exclusive item types
        item_fields = ['component_id', 'material_id', 'leather_id', 'hardware_id']
        specified_items = sum(1 for field in item_fields if data.get(field) is not None)

        if specified_items > 1:
            raise ValidationError(
                "Only one item type (component, material, leather, or hardware) can be specified per picking list item",
                "item_reference"
            )

    def update_picked_quantity(self, quantity: int) -> None:
        """
        Update the quantity picked.

        Args:
            quantity: New picked quantity

        Raises:
            ModelValidationError: If quantity is invalid
        """
        try:
            # Validate quantity
            if quantity < 0:
                raise ValidationError("Picked quantity cannot be negative")

            if quantity > self.quantity_ordered:
                raise ValidationError("Picked quantity cannot exceed ordered quantity")

            # Update quantity
            self.quantity_picked = quantity

            logger.info(f"PickingListItem {self.id} picked quantity updated to {self.quantity_picked}")

        except Exception as e:
            logger.error(f"Error updating picked quantity: {e}")
            raise ModelValidationError(f"Failed to update picked quantity: {str(e)}")

    def is_fully_picked(self) -> bool:
        """
        Check if the item is fully picked.

        Returns:
            True if quantity_picked equals quantity_ordered
        """
        return self.quantity_picked >= self.quantity_ordered

    def get_item_name(self) -> str:
        """
        Get the name of the item.

        Returns:
            Name of the referenced item or description if not available
        """
        if self.item_description:
            return self.item_description

        if self.component_id is not None and self.component:
            return f"Component: {getattr(self.component, 'name', 'Unknown')}"
        elif self.material_id is not None and self.material:
            return f"Material: {getattr(self.material, 'name', 'Unknown')}"
        elif self.leather_id is not None and self.leather:
            return f"Leather: {getattr(self.leather, 'name', 'Unknown')}"
        elif self.hardware_id is not None and self.hardware:
            return f"Hardware: {getattr(self.hardware, 'name', 'Unknown')}"
        else:
            return "Unknown item"

    def get_item_type(self) -> str:
        """
        Get the type of item.

        Returns:
            String indicating the item type
        """
        if self.component_id is not None:
            return "component"
        elif self.material_id is not None:
            return "material"
        elif self.leather_id is not None:
            return "leather"
        elif self.hardware_id is not None:
            return "hardware"
        else:
            return "unknown"

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert picking list item to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the picking list item
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        # Build the dictionary
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                result[column.name] = getattr(self, column.name)

        # Add computed fields
        result['item_name'] = self.get_item_name()
        result['item_type'] = self.get_item_type()
        result['is_fully_picked'] = self.is_fully_picked()

        return result

    def __repr__(self) -> str:
        """
        String representation of the PickingListItem.

        Returns:
            Detailed picking list item representation
        """
        return (
            f"<PickingListItem(id={self.id}, "
            f"picking_list_id={self.picking_list_id}, "
            f"item={self.get_item_name()}, "
            f"ordered={self.quantity_ordered}, "
            f"picked={self.quantity_picked})>"
        )


# Register for lazy import resolution
register_lazy_import('PickingList', 'database.models.picking_list', 'PickingList')
register_lazy_import('PickingListItem', 'database.models.picking_list', 'PickingListItem')