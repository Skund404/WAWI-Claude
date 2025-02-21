# File: store_management/database/sqlalchemy/models/product.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from store_management.database.sqlalchemy.base import Base


class Product(Base):
    """
    Product model representing items that can be stored and manufactured.

    Attributes:
        id (int): Unique identifier for the product
        name (str): Name of the product
        description (str): Detailed description of the product
        category (str): Product category
        unit_price (float): Price per unit
        storage_id (int): Foreign key to the storage location
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    unit_price = Column(Float)
    storage_id = Column(Integer, ForeignKey('storage.id'))

    # Relationships
    storage = relationship("Storage", back_populates="products")
    recipes = relationship("Recipe", back_populates="product")

    def __repr__(self):
        return f"<Product {self.name}>"