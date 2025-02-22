# Path: database/models/part.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Part(BaseModel):
    """
    Represents an inventory part in the inventory management system.

    Attributes:
        id (int): Unique identifier for the part
        name (str): Name of the part
        description (str): Detailed description of the part
        sku (str): Stock Keeping Unit identifier
        quantity (float): Current quantity in stock
        unit (str): Unit of measurement
        supplier_id (int): Foreign key to the supplier of the part
        min_stock_level (float): Minimum stock level for reordering
        cost_price (float): Cost price of the part
        created_at (DateTime): Timestamp of part creation

        supplier (relationship): Supplier of the part
        transactions (relationship): Inventory transactions for this part
    """
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    sku = Column(String(50), unique=True, nullable=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String(20), nullable=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    min_stock_level = Column(Float, default=0.0)
    cost_price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship('Supplier', back_populates='parts')
    transactions = relationship('InventoryTransaction', back_populates='part')

    def __repr__(self):
        return f"<Part(id={self.id}, name='{self.name}', sku='{self.sku}', quantity={self.quantity})>"

    @property
    def total_value(self):
        """
        Calculate the total value of the part in stock.

        Returns:
            float: Total value of the part (quantity * cost price)
        """
        return self.quantity * (self.cost_price or 0)

    def needs_reorder(self):
        """
        Check if the part needs to be reordered.

        Returns:
            bool: True if current quantity is below minimum stock level, False otherwise
        """
        return self.quantity <= self.min_stock_level