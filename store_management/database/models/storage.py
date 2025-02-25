# database/models/storage.py
"""
Storage model module for the leatherworking store management system.

Defines the Storage class for tracking inventory storage locations.
"""

from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import StorageLocationType


class Storage(Base, BaseModel):
    """
    Storage entity representing physical storage locations for inventory.

    This class defines the storage location data model and provides methods for storage management.
    """
    __tablename__ = 'storage'

    name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=True)
    capacity = Column(Float, default=0.0)
    current_occupancy = Column(Float, default=0.0)
    type = Column(Enum(StorageLocationType), default=StorageLocationType.SHELF)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    products = relationship("Product", back_populates="storage")

    def __init__(self, name: str, location: str, capacity: float,
                 current_occupancy: float, type: StorageLocationType,
                 description: Optional[str] = None,
                 is_active: bool = True, **kwargs):
        """
        Initialize a new Storage instance.

        Args:
            name: The name of the storage location.
            location: The physical location description.
            capacity: The total capacity of the storage.
            current_occupancy: The current used capacity.
            type: The type of storage (e.g., Warehouse, Workshop, etc.).
            description: A detailed description of the storage.
            is_active: The current status of the storage.
        """
        super().__init__(**kwargs)  # Initialize the BaseModel
        self.name = name
        self.location = location
        self.capacity = capacity
        self.current_occupancy = current_occupancy
        self.type = type
        self.description = description
        self.is_active = is_active

    def __repr__(self) -> str:
        """
        Get a string representation of the storage location.

        Returns:
            A string representation of the storage location.
        """
        return f"<Storage id={self.id}, name='{self.name}', type={self.type.name}>"

    def occupancy_percentage(self) -> float:
        """
        Calculate the occupancy percentage of the storage.

        Returns:
            The occupancy percentage (0-100).
        """
        if self.capacity <= 0:
            return 0.0
        return (self.current_occupancy / self.capacity) * 100

    def is_full(self) -> bool:
        """
        Check if the storage is full.

        Returns:
            True if the storage is full, False otherwise.
        """
        return self.current_occupancy >= self.capacity

    def is_empty(self) -> bool:
        """
        Check if the storage is empty.

        Returns:
            True if the storage is empty, False otherwise.
        """
        return self.current_occupancy <= 0

    def available_capacity(self) -> float:
        """
        Calculate the available capacity.

        Returns:
            The available capacity.
        """
        return max(0, self.capacity - self.current_occupancy)

    def can_store(self, required_capacity: float) -> bool:
        """
        Check if the storage can accommodate the required capacity.

        Args:
            required_capacity: The capacity required.

        Returns:
            True if the storage can accommodate the required capacity, False otherwise.
        """
        return self.available_capacity() >= required_capacity