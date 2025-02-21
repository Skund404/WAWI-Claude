# File: store_management/database/sqlalchemy/models/leather.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base
from store_management.database.sqlalchemy.models.enums import InventoryStatus


class Leather(Base):
    """
    Leather model representing leather inventory items.

    Attributes:
        id (int): Unique identifier for the leather
        name (str): Name or identifier of the leather
        type (str): Type or category of leather
        color (str): Color of the leather
        total_area (float): Total area of the leather
        available_area (float): Currently available area
        unit_price (float): Price per square unit
        supplier_id (int): Foreign key to the supplier
        status (InventoryStatus): Current inventory status
        notes (str): Additional notes about the leather
        created_at (datetime): Timestamp of record creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = 'leathers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String)
    color = Column(String)
    total_area = Column(Float, default=0)
    available_area = Column(Float, default=0)
    unit_price = Column(Float)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier")
    transactions = relationship("LeatherTransaction", back_populates="leather")

    def __repr__(self):
        return f"<Leather {self.name} - {self.available_area} sq units>"