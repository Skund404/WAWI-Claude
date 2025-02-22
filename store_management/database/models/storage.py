"""
File: database/models/storage.py
Storage model definition.
Represents physical storage locations in the system.
"""
from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship

from database.models.base import Base


class Storage(Base):
    """
    Storage model represents physical storage locations for products.
    """
    __tablename__ = 'storage'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    capacity = Column(Float, default=0.0)
    current_usage = Column(Float, default=0.0)

    # Relationships - uncomment and adjust based on your actual relationships
    # products = relationship("Product", back_populates="storage")

    def __repr__(self):
        """String representation of the Storage model."""
        return f"<Storage {self.location} - {self.current_usage}/{self.capacity}>"