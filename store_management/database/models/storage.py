# store_management/database/models/storage.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class Storage(Base):
    """Storage location model"""
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    location = Column(String, nullable=False, unique=True)
    capacity = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="available")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # String-based relationship to avoid circular imports
    products = relationship("Product", back_populates="storage", lazy="dynamic")

    def __repr__(self):
        return f"<Storage(id={self.id}, location='{self.location}')>"