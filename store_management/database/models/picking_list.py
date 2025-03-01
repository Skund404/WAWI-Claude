# models/picking_list.py
from datetime import datetime
from database.models.base import Base, BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
import enum


class PickingListStatus(enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PickingList(Base, BaseModel):
    """Model representing a picking list for project materials."""

    __tablename__ = 'picking_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notes = Column(Text)
    priority = Column(Integer, default=0)  # 0=normal, 1=high, 2=urgent
    assigned_to = Column(String(100))

    # Relationships
    project = relationship("Project", back_populates="picking_lists")
    order = relationship("Order", back_populates="picking_lists")
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")


class PickingListItem(Base, BaseModel):
    """Model representing an item in a picking list."""

    __tablename__ = 'picking_list_items'

    id = Column(Integer, primary_key=True)
    picking_list_id = Column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    hardware_id = Column(Integer, ForeignKey('hardware.id'), nullable=True)
    storage_location_id = Column(Integer, ForeignKey('storage.id'), nullable=True)

    item_type = Column(String(50), nullable=False)  # leather, hardware, thread, etc.
    name = Column(String(100), nullable=False)
    description = Column(Text)
    quantity_required = Column(Float, nullable=False)
    quantity_picked = Column(Float, default=0)
    unit = Column(String(20), default="piece")
    notes = Column(Text)
    is_picked = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)  # For custom sorting

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    material = relationship("Material")
    hardware = relationship("Hardware")
    storage_location = relationship("Storage")