"""
database/models/picking_list.py - Picking list and item models
"""
from database.models.base import Base, BaseModel
from datetime import datetime
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from typing import Any, Dict, List, Optional


class PickingListStatus(enum.Enum):
    """Status values for picking lists"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PickingList(Base, BaseModel):
    """Model representing a picking list"""
    __tablename__ = 'picking_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship with items
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PickingList {self.id}: {self.name}>"


class PickingListItem(Base, BaseModel):
    """Model representing an item in a picking list"""
    __tablename__ = 'picking_list_items'

    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    required_quantity = Column(Float, nullable=False)
    picked_quantity = Column(Float, default=0.0)
    unit = Column(String(20), default='pcs')
    storage_location = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    is_picked = Column(Boolean, default=False)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    material = relationship("Material")

    def __repr__(self):
        return f"<PickingListItem {self.id}: {self.material_id} ({self.picked_quantity}/{self.required_quantity})>"