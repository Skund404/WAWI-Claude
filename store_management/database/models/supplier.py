# Path: database/models/supplier.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Supplier(BaseModel):
    """
    Represents a supplier in the inventory management system.

    Attributes:
        id (int): Unique identifier for the supplier
        name (str): Name of the supplier
        contact_person (str): Primary contact person at the supplier
        email (str): Email address of the supplier
        phone (str): Phone number of the supplier
        address (str): Physical address of the supplier
        rating (float): Supplier performance rating
        created_at (DateTime): Timestamp of supplier record creation

        parts (relationship): Inventory parts supplied by this supplier
        products (relationship): Products supplied by this supplier
        orders (relationship): Orders placed with this supplier
        shopping_list_items (relationship): Shopping list items associated with this supplier
        leather_materials (relationship): Leather materials supplied by this supplier
    """
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(200), nullable=True)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    parts = relationship('Part', back_populates='supplier')
    products = relationship('Product', back_populates='supplier')
    orders = relationship('Order', back_populates='supplier')
    shopping_list_items = relationship('ShoppingListItem', back_populates='supplier')
    leather_materials = relationship('Leather', back_populates='supplier')

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', rating={self.rating})>"

    @property
    def total_parts(self):
        """
        Calculate the total number of parts from this supplier.

        Returns:
            int: Number of parts supplied
        """
        return len(self.parts)

    @property
    def total_products(self):
        """
        Calculate the total number of products from this supplier.

        Returns:
            int: Number of products supplied
        """
        return len(self.products)

    @property
    def total_leather_materials(self):
        """
        Calculate the total number of leather materials from this supplier.

        Returns:
            int: Number of leather materials supplied
        """
        return len(self.leather_materials)

    @property
    def total_orders(self):
        """
        Calculate the total number of orders from this supplier.

        Returns:
            int: Number of orders
        """
        return len(self.orders)

    def get_performance_metrics(self):
        """
        Calculate supplier performance metrics.

        Returns:
            dict: Dictionary containing performance metrics
        """
        return {
            'total_orders': self.total_orders,
            'rating': self.rating,
            'total_parts_supplied': self.total_parts,
            'total_products_supplied': self.total_products
        }