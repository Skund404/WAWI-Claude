# database/models/part.py

import logging
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from typing import List, Optional, Dict, Any


from .base import BaseModel
from .transaction import InventoryTransaction

logger = logging.getLogger(__name__)


class Part(BaseModel):
    """
    Model for parts/components inventory.
    """

    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    quantity = Column(Float, default=0)
    unit = Column(String(20), nullable=False)
    minimum_stock = Column(Float, default=0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))

    # Relationships
    transactions = relationship("InventoryTransaction", back_populates="part",
                                cascade="all, delete-orphan")
    supplier = relationship("Supplier", back_populates="parts")