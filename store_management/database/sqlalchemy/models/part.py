# File: store_management/database/sqlalchemy/models/part.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base
from store_management.database.sqlalchemy.models.enums import InventoryStatus


class Part(Base):
    """
    Part model representing inventory items.

    Attributes:
        id (int): Unique identifier for the part
        name (str): Name of the part
        description (str): Detailed description of the part
        stock_level (float): Current stock level of the part
        min_stock_level (float): Minimum stock level threshold
        unit_price (float): Price per unit
        supplier_id (int): Foreign key to the supplier
        status (InventoryStatus): Current inventory status
        created_at (datetime): Timestamp of record creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    stock_level = Column(Float, default=0)
    min_stock_level = Column(Float, default=0)
    unit_price = Column(Float)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="parts")
    transactions = relationship("InventoryTransaction", back_populates="part")

    def __repr__(self):
        return f"<Part(id={self.id}, name='{self.name}', stock_level={self.stock_level})>"