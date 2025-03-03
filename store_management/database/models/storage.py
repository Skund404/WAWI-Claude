# database/models/storage.py
from database.models.base import Base
from database.models.enums import StorageLocationType
from sqlalchemy import Column, Enum, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from utils.validators import validate_not_empty


class Storage(Base):
    """
    Model representing storage locations for materials.
    """
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

    # Relationships
    leathers = relationship("Leather", back_populates="storage")
    hardware = relationship("Hardware", back_populates="storage")
    materials = relationship("Material", back_populates="storage")
    products = relationship("Product", back_populates="storage")

    def __init__(self, **kwargs):
        """Initialize a Storage instance with validation.

        Args:
            **kwargs: Keyword arguments with storage attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate storage data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'name', 'Storage name is required')
        validate_not_empty(data, 'location_type', 'Storage location type is required')

    def mark_as_full(self, is_full=True):
        """Mark the storage location as full or not full.

        Args:
            is_full (bool): Whether the storage location is full
        """
        self.is_full = is_full

    def check_capacity(self, new_items_count=0):
        """Check if the storage location has capacity for new items.

        Args:
            new_items_count (int): Number of new items to check capacity for

        Returns:
            bool: True if there is capacity, False otherwise
        """
        if self.capacity is None:
            return True

        current_count = 0
        if self.leathers:
            current_count += len(self.leathers)
        if self.hardware:
            current_count += len(self.hardware)
        if self.materials:
            current_count += len(self.materials)
        if self.products:
            current_count += len(self.products)

        return (current_count + new_items_count) <= self.capacity

    def __repr__(self):
        """String representation of the storage location.

        Returns:
            str: String representation
        """
        return f"<Storage(id={self.id}, name='{self.name}', type={self.location_type})>"