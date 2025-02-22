# Path: database/models/leather.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Leather(BaseModel):
    """
    Represents a leather material in the inventory management system.

    Attributes:
        id (int): Unique identifier for the leather
        name (str): Name or description of the leather
        supplier_id (int): Foreign key to the supplier of the leather
        color (str): Color of the leather
        total_area (float): Total area of the leather
        available_area (float): Currently available area of the leather
        thickness (float): Thickness of the leather
        quality (str): Quality grade of the leather
        purchase_date (DateTime): Date of leather purchase
        cost (float): Cost of the leather
        notes (str): Additional notes about the leather

        supplier (relationship): Supplier of the leather
        transactions (relationship): Leather inventory transactions
    """
    __tablename__ = 'leather'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    color = Column(String(50), nullable=True)
    total_area = Column(Float, nullable=False, default=0.0)
    available_area = Column(Float, nullable=False, default=0.0)
    thickness = Column(Float, nullable=True)
    quality = Column(String(50), nullable=True)
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    cost = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship('Supplier', back_populates='leather_materials')
    transactions = relationship('LeatherTransaction', back_populates='leather')

    def __repr__(self):
        return f"<Leather(id={self.id}, name='{self.name}', available_area={self.available_area})>"

    @property
    def usage_percentage(self):
        """
        Calculate the percentage of leather used.

        Returns:
            float: Percentage of leather used
        """
        if self.total_area > 0:
            return ((self.total_area - self.available_area) / self.total_area) * 100
        return 0.0

    def can_fulfill_requirement(self, required_area: float) -> bool:
        """
        Check if the leather has enough available area.

        Args:
            required_area (float): Area required for a specific use

        Returns:
            bool: True if enough area is available, False otherwise
        """
        return self.available_area >= required_area