# store_management/database/models/supplier.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from .base import Base


class Supplier(Base):
    """Supplier model"""
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # String-based relationships
    parts = relationship("Part", back_populates="supplier", lazy="dynamic")
    leathers = relationship("Leather", back_populates="supplier", lazy="dynamic")
    orders = relationship("Order", back_populates="supplier", lazy="dynamic")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}')>"