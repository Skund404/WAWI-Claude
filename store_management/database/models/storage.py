# database/models/storage.py
from typing import Dict, Any, Optional

from database.models.base import Base
from database.models.enums import StorageLocationType
from database.models.leather import Leather
from database.models.hardware import Hardware
from database.models.material import Material
from database.models.product import Product

from sqlalchemy import Column, Enum, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from utils.validators import validate_not_empty


class Storage(Base):
    """
    Model representing storage locations for materials with robust
    capacity and relationship management.
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

    # Relationships with explicit configuration
    leathers = relationship(
        "Leather",
        back_populates="storage",
        lazy='dynamic',
        cascade='save-update, merge'
    )
    hardwares = relationship(
        "Hardware",
        back_populates="storage",
        lazy='dynamic',
        cascade='save-update, merge'
    )
    materials = relationship(
        "Material",
        back_populates="storage",
        lazy='dynamic',
        cascade='save-update, merge'
    )
    products = relationship(
        "Product",
        back_populates="storage",
        lazy='dynamic',
        cascade='save-update, merge'
    )
    parts = relationship(
        "Part",
        back_populates="storage",
        lazy='dynamic',
        cascade='save-update, merge'
    )

    def __init__(self, **kwargs):
        """
        Initialize a Storage instance with robust validation.

        Args:
            **kwargs: Keyword arguments with storage attributes

        Raises:
            ValueError: If validation fails for any field
            TypeError: If invalid data types are provided
        """
        try:
            self._validate_creation(kwargs)
            super().__init__(**kwargs)
        except (ValueError, TypeError) as e:
            self._handle_initialization_error(e, kwargs)

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation for storage creation data.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
            TypeError: If data types are incorrect
        """
        if not isinstance(data, dict):
            raise TypeError("Input must be a dictionary")

        validate_not_empty(data, 'name', 'Storage name is required')
        validate_not_empty(data, 'location_type', 'Storage location type is required')

        # Additional custom validations
        if 'capacity' in data:
            try:
                capacity = data['capacity']
                if not isinstance(capacity, (int, type(None))):
                    raise ValueError("Capacity must be an integer or None")
                if capacity is not None and capacity < 0:
                    raise ValueError("Capacity cannot be negative")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid capacity: {str(e)}")

    def _handle_initialization_error(self, error: Exception, data: Dict[str, Any]) -> None:
        """
        Handle initialization errors with detailed logging.

        Args:
            error (Exception): The caught exception
            data (dict): The input data that caused the error

        Raises:
            ValueError: Re-raises the original error with additional context
        """
        error_context = {
            'input_data': data,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }

        # Log the error (replace with your logging mechanism)
        print(f"Storage Initialization Error: {error_context}")

        # Re-raise with more context
        raise ValueError(f"Failed to create Storage: {str(error)}") from error

    def mark_as_full(self, is_full: bool = True) -> None:
        """
        Mark the storage location as full or not full with validation.

        Args:
            is_full (bool): Whether the storage location is full

        Raises:
            TypeError: If is_full is not a boolean
        """
        if not isinstance(is_full, bool):
            raise TypeError("is_full must be a boolean value")

        self.is_full = is_full

    def check_capacity(self, new_items_count: int = 0) -> bool:
        """
        Check if the storage location has capacity for new items.

        Args:
            new_items_count (int): Number of new items to check capacity for

        Returns:
            bool: True if there is capacity, False otherwise

        Raises:
            TypeError: If new_items_count is not an integer
        """
        if not isinstance(new_items_count, int):
            raise TypeError("new_items_count must be an integer")

        # If no capacity is set, consider it unlimited
        if self.capacity is None:
            return True

        # Dynamically count current items across all relationships
        try:
            current_count = (
                    self.leathers.count() +
                    self.hardwares.count() +
                    self.materials.count() +
                    self.products.count() +
                    self.parts.count()
            )

            return (current_count + new_items_count) <= self.capacity
        except SQLAlchemyError as e:
            print(f"Error checking storage capacity: {e}")
            return False

    def __repr__(self) -> str:
        """
        Detailed string representation of the storage location.

        Returns:
            str: Comprehensive string representation
        """
        return (
            f"<Storage(id={self.id}, name='{self.name}', "
            f"type={self.location_type}, "
            f"capacity={self.capacity or 'Unlimited'}, "
            f"is_full={self.is_full})>"
        )