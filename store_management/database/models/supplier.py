"""
File: database/models/supplier.py
Supplier model definition.
Represents suppliers of parts and materials.
"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from sqlalchemy.orm import relationship

from database.models.base import Base


class Supplier(Base):
    """
    Supplier model representing vendors who supply parts and materials.
    """
    __tablename__ = 'suppliers'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)

    # Relationships - uncomment and adjust based on your actual relationships
    # parts = relationship("Part", back_populates="supplier")
    # leather = relationship("Leather", back_populates="supplier")
    # orders = relationship("Order", back_populates="supplier")

    def __repr__(self):
        """String representation of the Supplier model."""
        return f"<Supplier(id={self.id}, name='{self.name}')>"