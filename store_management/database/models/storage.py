# database/models/storage.py
"""
Enhanced Storage Model with Standard SQLAlchemy Relationship Approach

This module defines the Storage model with comprehensive validation,
relationship management, and circular import resolution.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import StorageLocationType
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
register_lazy_import('Leather', 'database.models.leather')
register_lazy_import('Product', 'database.models.product')
register_lazy_import('Part', 'database.models.part')
register_lazy_import('Hardware', 'database.models.hardware')
register_lazy_import('Material', 'database.models.material')

# Setup logger
logger = logging.getLogger(__name__)


class Storage(Base):
    """
    Enhanced Storage model with comprehensive validation and relationship management.

    Represents storage locations for materials with robust
    capacity and relationship configuration.
    """
    __tablename__ = 'storages'

    # Storage specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    location_type = Column(Enum(StorageLocationType), nullable=False)

    section = Column(String(50), nullable=True)
    row = Column(String(50), nullable=True)
    shelf = Column(String(50), nullable=True)
    bin = Column(String(50), nullable=True)

    capacity = Column(Integer, nullable=True)
    is_full = Column(Boolean, default=False, nullable=False)

    notes = Column(Text, nullable=True)

    # Relationships using standard SQLAlchemy approach
    leathers = relationship("Leather", back_populates="storage",
                            lazy="lazy", cascade="save-update, merge")

    products = relationship("Product", back_populates="storage",
                            lazy="lazy", cascade="save-update, merge")

    parts = relationship("Part", back_populates="storage",
                         lazy="lazy", cascade="save-update, merge")

    def __init__(self, **kwargs):
        """
        Initialize a Storage instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for storage attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_creation(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Storage initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Storage: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate storage creation data with comprehensive checks.

        Args:
            data (Dict[str, Any]): Storage creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Storage name is required')
        validate_not_empty(data, 'location_type', 'Storage location type is required')

        # Validate location type
        if 'location_type' in data:
            validate_not_empty(data, 'location_type', 'Storage location type is required')

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

        # Validate full status - modified to safely check related collections
        if self.is_full and self.capacity is not None:
            current_items_count = 0

            # Safely count leathers if available
            if hasattr(self, 'leathers') and callable(getattr(self.leathers, 'count', None)):
                current_items_count += self.leathers.count()

            # Safely count products if available
            if hasattr(self, 'products') and callable(getattr(self.products, 'count', None)):
                current_items_count += self.products.count()

            # Safely count parts if available
            if hasattr(self, 'parts') and callable(getattr(self.parts, 'count', None)):
                current_items_count += self.parts.count()

            if current_items_count < self.capacity:
                raise ValidationError(
                    "Storage marked as full but has available capacity",
                    "is_full"
                )

    def mark_as_full(self, is_full: bool = True) -> None:
        """
        Mark the storage location as full or not full with validation.

        Args:
            is_full (bool): Whether the storage location is full

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

    def check_capacity(self, new_items_count: int = 0) -> bool:
        """
        Check if the storage location has capacity for new items.

        Args:
            new_items_count (int): Number of new items to check capacity for

        Returns:
            bool: True if there is capacity, False otherwise

        Raises:
            ModelValidationError: If capacity check fails
        """
        try:
            # Validate input
            if not isinstance(new_items_count, int):
                raise ModelValidationError("new_items_count must be an integer")

            # If no capacity is set, consider it unlimited
            if self.capacity is None:
                return True

            # Count current items across relationships - modified to safely check collections
            current_count = 0

            # Safely count leathers if available
            if hasattr(self, 'leathers') and callable(getattr(self.leathers, 'count', None)):
                current_count += self.leathers.count()

            # Safely count products if available
            if hasattr(self, 'products') and callable(getattr(self.products, 'count', None)):
                current_count += self.products.count()

            # Safely count parts if available
            if hasattr(self, 'parts') and callable(getattr(self.parts, 'count', None)):
                current_count += self.parts.count()

            # Check if new items would exceed capacity
            return (current_count + new_items_count) <= self.capacity

        except Exception as e:
            logger.error(f"Capacity check failed: {e}")
            raise ModelValidationError(f"Cannot check storage capacity: {str(e)}")

    def generate_storage_code(self) -> str:
        """
        Generate a unique storage location code.

        Returns:
            str: Generated storage code
        """
        try:
            # Take first 3 letters of location type (uppercase)
            type_part = ''.join(c for c in self.location_type.name if c.isalnum())[:3].upper()

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

    def __repr__(self) -> str:
        """
        Provide a comprehensive string representation of the storage location.

        Returns:
            str: Detailed storage representation
        """
        # Modified to safely check related collections
        item_count = 0
        if hasattr(self, 'leathers') and callable(getattr(self.leathers, 'count', None)):
            item_count += self.leathers.count()
        if hasattr(self, 'products') and callable(getattr(self.products, 'count', None)):
            item_count += self.products.count()
        if hasattr(self, 'parts') and callable(getattr(self.parts, 'count', None)):
            item_count += self.parts.count()

        return (
            f"<Storage(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.location_type}, "
            f"capacity={self.capacity or 'Unlimited'}, "
            f"is_full={self.is_full}, "
            f"items={item_count})>"
        )


# Register this class for lazy imports by others
register_lazy_import('Storage', 'database.models.storage')