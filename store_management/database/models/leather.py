# store_management/database/models/leather.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import InventoryStatus


class Leather(Base):
    """Leather model"""
    __tablename__ = 'leathers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True)
    type = Column(String)
    color = Column(String)
    thickness = Column(Float)
    area = Column(Float, default=0.0)  # in square feet
    min_area = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)  # per square foot
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="leathers")
    recipe_items = relationship("RecipeItem", back_populates="leather", lazy="dynamic")
    transactions = relationship("LeatherTransaction", back_populates="leather", lazy="dynamic")

    def __repr__(self):
        return f"<Leather(id={self.id}, name='{self.name}')>"