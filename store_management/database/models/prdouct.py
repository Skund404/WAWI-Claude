# store_management/database/models/product.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Product(Base):
    """Product model"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True)
    description = Column(String)
    price = Column(Float, default=0.0)
    storage_id = Column(Integer, ForeignKey('storage.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    storage = relationship("Storage", back_populates="products")
    recipes = relationship("Recipe", back_populates="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"