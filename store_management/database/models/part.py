"""
File: database/models/part.py
Part model definition.
Represents inventory parts in the system.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from database.models.base import Base


class Part(Base):
    """
    Part model representing inventory parts in the system.
    """
    __tablename__ = 'parts'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    stock_level = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=0)
    price = Column(Float, default=0.0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Relationships - uncomment and adjust as needed
    # supplier = relationship("Supplier", back_populates="parts")

    def __repr__(self):
        """String representation of the Part model."""
        return f"<Part(id={self.id}, name='{self.name}', stock_level={self.stock_level})>"