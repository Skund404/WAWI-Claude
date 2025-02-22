"""
File: database/models/leather.py
Leather model definition.
Represents leather inventory in the system.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from database.models.base import Base


class Leather(Base):
    """
    Leather model representing leather materials in inventory.
    """
    __tablename__ = 'leather'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    color = Column(String(50), nullable=True)
    thickness = Column(Float, nullable=True)
    quality = Column(String(50), nullable=True)
    area = Column(Float, default=0.0)  # Current stock area
    min_area = Column(Float, default=0.0)  # Minimum stock area
    price_per_unit = Column(Float, default=0.0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # supplier = relationship("Supplier", back_populates="leather")
    # transactions = relationship("LeatherTransaction", back_populates="leather")

    def __repr__(self):
        """String representation of the Leather model."""
        return f"<Leather(id={self.id}, name='{self.name}', color='{self.color}', area={self.area})>"