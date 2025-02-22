# Path: database/models/product.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Product(BaseModel):
    """
    Represents a product in the inventory management system.

    Attributes:
        id (int): Unique identifier for the product
        name (str): Name of the product
        description (str): Detailed description of the product
        sku (str): Stock Keeping Unit identifier
        quantity (float): Current quantity in stock
        unit (str): Unit of measurement
        storage_id (int): Foreign key to the storage location
        supplier_id (int): Foreign key to the supplier of the product
        cost_price (float): Cost price of the product
        selling_price (float): Selling price of the product
        created_at (DateTime): Timestamp of product creation

        storage (relationship): Storage location of the product
        supplier (relationship): Supplier of the product
        recipes (relationship): Recipes for creating this product
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    sku = Column(String(50), unique=True, nullable=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String(20), nullable=True)
    storage_id = Column(Integer, ForeignKey('storage.id'), nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    cost_price = Column(Float, nullable=True)
    selling_price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    storage = relationship('Storage', back_populates='products')
    supplier = relationship('Supplier', back_populates='products')
    recipes = relationship('Recipe', back_populates='product')

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}', quantity={self.quantity})>"

    @property
    def total_value(self):
        """
        Calculate the total value of the product in stock.

        Returns:
            float: Total value of the product (quantity * cost price)
        """
        return self.quantity * (self.cost_price or 0)

    def get_primary_recipe(self):
        """
        Get the primary (first) recipe for this product.

        Returns:
            Recipe or None: The first recipe for the product, or None if no recipes exist
        """
        return self.recipes[0] if self.recipes else None

    def calculate_production_cost(self):
        """
        Calculate the total production cost based on the first recipe.

        Returns:
            float: Total production cost, or 0 if no recipe exists
        """
        primary_recipe = self.get_primary_recipe()
        return primary_recipe.calculate_total_cost() if primary_recipe else 0