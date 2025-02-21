# File: store_management/database/sqlalchemy/models/storage.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from store_management.database.sqlalchemy.base import Base


class Storage(Base):
    """
    Storage model representing storage locations.

    Attributes:
        id (int): Unique identifier for the storage location
        location (str): Specific location or name of the storage
        description (str): Detailed description of the storage
        capacity (float): Total capacity of the storage
        current_usage (float): Current usage of the storage
    """
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    location = Column(String, nullable=False, unique=True)
    description = Column(String)
    capacity = Column(Float, default=0)
    current_usage = Column(Float, default=0)

    # Relationships
    products = relationship("Product", back_populates="storage")

    def __repr__(self):
        return f"<Storage {self.location} - {self.current_usage}/{self.capacity}>"