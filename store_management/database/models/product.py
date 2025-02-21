# File: store_management/database/models/product.py
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Product(Base):
    """
    Product model representing items that can be stored in storage locations.
    """
    __tablename__ = 'products'

    # Additional columns specific to Product
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    price = Column(Float, default=0.0)

    # Optional relationship with Storage (if needed)
    # storage_id = Column(Integer, ForeignKey('storages.id'))
    # storage = relationship('Storage', back_populates='products')

    def __repr__(self):
        """
        String representation of the Product.

        Returns:
            String with product name and ID
        """
        return f"<Product(id={self.id}, name='{self.name}')>"