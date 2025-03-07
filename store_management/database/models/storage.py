# database/models/storage.py
"""
Comprehensive Storage Model for Leatherworking Management System

This module defines the Storage model with extensive validation,
relationship management, and circular import resolution.

Implements the Storage entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import StorageLocationType
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
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
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Material', 'database.models.material', 'Material')


class Storage(Base, TimestampMixin, ValidationMixin, TrackingMixin):
    """
    Storage model representing storage locations for leatherworking items.

    This implements the Storage entity with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'storages'

    # Basic attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Location attributes
    location_type: Mapped[StorageLocationType] = mapped_column(Enum(StorageLocationType), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    row: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    shelf: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Capacity properties
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_full: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    leathers = relationship("Leather", back_populates="storage")
    products = relationship("Product", back_populates="storage")
    hardware_items = relationship("Hardware", back_populates="storage")
    material_items = relationship("Material", back_populates="storage")

    def __init__(self, **kwargs):
        """
        Initialize a Storage instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for storage attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_storage_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Storage initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Storage: {str(e)}") from e

    @classmethod
    def _validate_storage_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of storage creation data.

        Args:
            data: Storage creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Storage name is required')
        validate_not_empty(data, 'location_type', 'Storage location type is required')

        # Validate location type
        if 'location_type' in data:
            ModelValidator.validate_enum(
                data['location_type'],
                StorageLocationType,
                'location_type'
            )

        # Validate capacity
        if 'capacity' in data and data['capacity'] is not None:
            validate_positive_number(
                data,
                'capacity',
                allow_zero=True,
                message="Capacity must be a non-negative number"
            )

    def _validate_instance(self) -> None:
        """
        Perform additional validation after instance creation.

        Raises:
            ValidationError: If instance validation fails
        """
        # Validate storage details
        if self.capacity is not None and self.capacity < 0:
            raise ValidationError(
                "Capacity cannot be negative",
                "capacity"
            )

        # Validate full status - check if capacity is exceeded
        self._check_and_update_full_status()

    def mark_as_full(self, is_full: bool = True) -> None:
        """
        Mark the storage location as full or not full with validation.

        Args:
            is_full: Whether the storage location is full

        Raises:
            ModelValidationError: If marking as full fails
        """
        try:
            # Validate input
            if not isinstance(is_full, bool):
                raise ModelValidationError("is_full must be a boolean value")

            # Update full status
            self.is_full = is_full

            logger.info(
                f"Storage {self.id} {'marked as full' if is_full else 'marked as not full'}"
            )

        except Exception as e:
            logger.error(f"Marking storage full status failed: {e}")
            raise ModelValidationError(f"Cannot update storage full status: {str(e)}")

    def _check_and_update_full_status(self) -> None:
        """
        Check if storage is full based on current contents and update status.
        """
        if self.capacity is None:
            # Unlimited capacity
            return

        # Count current items
        current_count = self._count_stored_items()

        # Update full status
        if current_count >= self.capacity and not self.is_full:
            self.is_full = True
            logger.info(f"Storage {self.id} automatically marked as full")
        elif current_count < self.capacity and self.is_full:
            self.is_full = False
            logger.info(f"Storage {self.id} automatically marked as not full")

    def _count_stored_items(self) -> int:
        """
        Count the total number of items in this storage location.

        Returns:
            Total count of stored items
        """
        count = 0

        # Safely count each relationship
        if hasattr(self, 'leathers') and self.leathers:
            count += len(self.leathers)

        if hasattr(self, 'products') and self.products:
            count += len(self.products)

        if hasattr(self, 'hardware_items') and self.hardware_items:
            count += len(self.hardware_items)

        if hasattr(self, 'material_items') and self.material_items:
            count += len(self.material_items)

        return count

    def check_capacity(self, new_items_count: int = 0) -> bool:
        """
        Check if the storage location has capacity for new items.

        Args:
            new_items_count: Number of new items to check capacity for

        Returns:
            True if there is capacity, False otherwise

        Raises:
            ModelValidationError: If capacity check fails
        """
        try:
            # Validate input
            if not isinstance(new_items_count, int) or new_items_count < 0:
                raise ModelValidationError("new_items_count must be a non-negative integer")

            # If no capacity is set, consider it unlimited
            if self.capacity is None:
                return True

            # Count current items
            current_count = self._count_stored_items()

            # Check if new items would exceed capacity
            return (current_count + new_items_count) <= self.capacity

        except Exception as e:
            logger.error(f"Capacity check failed: {e}")
            raise ModelValidationError(f"Cannot check storage capacity: {str(e)}")

    def generate_storage_code(self) -> str:
        """
        Generate a unique storage location code.

        Returns:
            Generated storage code
        """
        try:
            # Take first 3 letters of location type (uppercase)
            type_part = self.location_type.name[:3].upper()

            # Take first 3 letters of name (uppercase)
            name_part = ''.join(c for c in self.name if c.isalnum())[:3].upper()

            # Append additional location details
            location_parts = [
                self.section or 'N',
                self.row or 'N',
                self.shelf or 'N',
                self.bin or 'N'
            ]
            location_code = '-'.join(location_parts)

            # Append last 4 digits of ID
            id_part = str(self.id).zfill(4)[-4:]

            return f"{type_part}-{name_part}-{location_code}-{id_part}"
        except Exception as e:
            logger.error(f"Storage code generation failed: {e}")
            raise ModelValidationError(f"Cannot generate storage code: {str(e)}")

    def add_notes(self, notes: str) -> None:
        """
        Add notes to the storage location.

        Args:
            notes: Notes to add
        """
        try:
            if not notes:
                return

            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            note_entry = f"[{timestamp}] {notes}"

            if self.notes:
                self.notes = f"{self.notes}\n\n{note_entry}"
            else:
                self.notes = note_entry

            logger.debug(f"Added notes to storage {self.id}")

        except Exception as e:
            logger.error(f"Failed to add notes: {e}")
            raise ModelValidationError(f"Cannot add notes: {str(e)}")

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Handle special types
                if isinstance(value, StorageLocationType):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add computed fields
        result['storage_code'] = self.generate_storage_code()
        result['current_items'] = self._count_stored_items()
        result['available_capacity'] = None if self.capacity is None else max(0,
                                                                              self.capacity - result['current_items'])

        return result

    def __repr__(self) -> str:
        """
        String representation of the Storage.

        Returns:
            Detailed storage representation
        """
        item_count = self._count_stored_items()
        capacity_str = 'Unlimited' if self.capacity is None else str(self.capacity)

        return (
            f"<Storage(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.location_type.name if self.location_type else 'None'}, "
            f"capacity={capacity_str}, "
            f"is_full={self.is_full}, "
            f"items={item_count})>"
        )


# Register for lazy import resolution
register_lazy_import('Storage', 'database.models.storage', 'Storage')