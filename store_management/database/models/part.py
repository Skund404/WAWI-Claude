# store_management/database/models/part.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import InventoryStatus


class Part(Base):
    """Part model"""
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True)
    description = Column(String)
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0.0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="parts")
    recipe_items = relationship("RecipeItem", back_populates="part", lazy="dynamic")
    transactions = relationship("InventoryTransaction", back_populates="part", lazy="dynamic")

    def __repr__(self):
        return f"<Part(id={self.id}, name='{self.name}')>"


