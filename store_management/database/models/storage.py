# File: store_management/database/sqlalchemy/models/storage.py
"""
Storage model definition for the Store Management System.

This module defines the Storage model representing storage locations
where products can be stored.
"""

from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.orm import relationship
from store_management.database.sqlalchemy.base import Base

# Remove any self-referential imports
# Do NOT import Storage from itself

class Storage(Base):
    """
    Storage model representing locations where products can be stored.

    Attributes:
        id (int): Unique identifier for the storage location.
        location (str): Specific location identifier.
        description (str, optional): Description of the storage location.
        capacity (float, optional): Total capacity of the storage location.
        current_usage (float, optional): Current usage of the storage location.
    """
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    location = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    capacity = Column(Float, default=0.0)
    current_usage = Column(Float, default=0.0)

    def __repr__(self):
        """
        String representation of the Storage instance.

        Returns:
            str: Representation of the storage location with ID and location.
        """
        return f"<Storage(id={self.id}, location='{self.location}')>"