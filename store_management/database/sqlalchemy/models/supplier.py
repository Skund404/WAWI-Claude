# File: store_management/database/sqlalchemy/models/supplier.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base


class Supplier(Base):
    """
    Supplier model representing external suppliers.

    Attributes:
        id (int): Unique identifier for the supplier
        name (str): Name of the supplier
        contact_name (str): Name of the primary contact
        email (str): Contact email address
        phone (str): Contact phone number
        address (str): Supplier's physical address
        rating (float): Supplier performance rating
        notes (str): Additional notes about the supplier
        created_at (datetime): Timestamp of record creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    rating = Column(Float, default=0.0)
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parts = relationship("Part", back_populates="supplier")
    orders = relationship("Order", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier {self.name}>"