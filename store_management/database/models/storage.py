# Path: database/models/storage.py
"""
Storage model for the database.
"""
import logging
from sqlalchemy import Column, Integer, String, Float, Enum, Text
from ..base import Base
from database.base import BaseModel

logger = logging.getLogger(__name__)


class Storage(Base):
    """
    Storage model representing a storage location in the warehouse.
    """
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    capacity = Column(Float, nullable=False, default=0.0)
    current_occupancy = Column(Float, nullable=False, default=0.0)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='active')

    def __init__(self, name, location, capacity, current_occupancy, type, description, status):
        """
        Initialize a new Storage instance.

        Args:
            name: Name of the storage location
            location: Physical location
            capacity: Maximum capacity
            current_occupancy: Current used capacity
            type: Type of storage
            description: Description
            status: Status (active, inactive, etc.)
        """
        self.name = name
        self.location = location
        self.capacity = capacity
        self.current_occupancy = current_occupancy
        self.type = type
        self.description = description
        self.status = status

    def __repr__(self):
        """String representation of the storage location."""
        return f"<Storage(id={self.id}, name={self.name}, location={self.location})>"

    def occupancy_percentage(self):
        """
        Calculate the occupancy percentage.

        Returns:
            float: Occupancy percentage
        """
        if self.capacity > 0:
            return (self.current_occupancy / self.capacity) * 100
        return 0.0


logger.debug("Storage model defined")