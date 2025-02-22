"""
File: database/models/product.py
Product model definition.
Represents finished products in the system.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from database.models.base import Base


class Product(Base):
    """
    Product model representing finished products in the system.
    """
    __tablename__ = 'products'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)
    sku = Column(String(50), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    storage_id = Column(Integer, ForeignKey('storage.id'), nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # storage = relationship("Storage", back_populates="products")
    # recipe = relationship("Recipe", back_populates="product", uselist=False)

    def __repr__(self):
        """String representation of the Product model."""
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"