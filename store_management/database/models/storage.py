# database/models/storage.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Storage(Base):
    """
    SQLAlchemy model representing a storage location.

    Attributes:
        id (int): Unique identifier for the storage location.
        name (str): Name of the storage location.
        description (str): Description of the storage location.
        capacity (float): Total capacity of the storage location.
        current_occupancy (float): Current occupancy of the storage location.
        location (str): Physical location of the storage.
        type (str): Type of storage (warehouse, shelf, etc.).
        status (str): Current status of the storage location.
        created_at (datetime): Timestamp when the storage was created.
        updated_at (datetime): Timestamp of the last update.
    """
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    capacity = Column(Float, default=0.0)
    current_occupancy = Column(Float, default=0.0)
    location = Column(String, nullable=True)
    type = Column(String, nullable=True)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def occupancy_percentage(self) -> float:
        """
        Calculate the occupancy percentage of the storage location.

        Returns:
            float: Percentage of storage capacity in use, or 0 if capacity is 0.
        """
        if self.capacity and self.capacity > 0:
            return (self.current_occupancy / self.capacity) * 100
        return 0.0

    def __repr__(self) -> str:
        """
        String representation of the Storage model.

        Returns:
            str: A string showing key details of the storage location.
        """
        return (f"<Storage(id={self.id}, name='{self.name}', "
                f"location='{self.location}', "
                f"occupancy={self.occupancy_percentage():.2f}%)>")