# database/models/material.py
"""
Material model module for the leatherworking store management system.

Defines classes for tracking materials and material transactions.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Enum, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, Dict, Any, List

from database.models.base import Base, BaseModel
from database.models.enums import MaterialType, MaterialQualityGrade


class Material(Base, BaseModel):
    """
    Represents a material in the store management system.

    Attributes:
        name (str): Name of the material
        material_type (MaterialType): Type of material
        supplier_id (int): Foreign key to the Supplier
        quality_grade (MaterialQualityGrade): Quality grade of the material
        current_stock (float): Current stock quantity
        minimum_stock (float): Minimum stock threshold
        unit_price (float): Price per unit
        is_active (bool): Whether the material is currently active
    """
    __tablename__ = 'material'

    name = Column(String(255), nullable=False)
    material_type = Column(Enum(MaterialType), nullable=False)
    description = Column(String(255), nullable=True)

    # Inventory tracking
    current_stock = Column(Float, default=0.0, nullable=False)
    minimum_stock = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    reorder_quantity = Column(Float, default=0.0, nullable=True)

    # Quality information
    quality_grade = Column(Enum(MaterialQualityGrade), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Relationships
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="materials")

    transactions = relationship("MaterialTransaction", back_populates="material", cascade="all, delete-orphan")
    components = relationship("ProjectComponent", back_populates="material")

    def __repr__(self) -> str:
        """
        String representation of the Material model.

        Returns:
            str: A string showing material name, type, and current stock
        """
        return f"<Material id={self.id}, name='{self.name}', type={self.material_type.name}, stock={self.current_stock}>"

    def to_dict(self, include_transactions: bool = False) -> Dict[str, Any]:
        """
        Convert material to dictionary representation.

        Args:
            include_transactions (bool): Whether to include transaction history

        Returns:
            dict: Dictionary representation of the material
        """
        result = super().to_dict()
        result['material_type'] = self.material_type.name

        if self.quality_grade:
            result['quality_grade'] = self.quality_grade.name

        if include_transactions:
            result['transactions'] = [t.to_dict() for t in self.transactions]

        return result

    def update_stock(self, quantity_change: float, transaction_type: str = "ADJUSTMENT",
                     notes: Optional[str] = None) -> None:
        """
        Update material stock with transaction tracking.

        Args:
            quantity_change: Amount to change the stock by
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ValueError: If resulting stock would be negative
        """
        new_stock = self.current_stock + quantity_change
        if new_stock < 0:
            raise ValueError("Stock quantity cannot be negative")

        self.current_stock = new_stock

        # Create transaction record
        transaction = MaterialTransaction(
            material=self,
            quantity_change=quantity_change,
            transaction_type=transaction_type,
            notes=notes
        )

        return transaction


class MaterialTransaction(Base, BaseModel):
    """
    Represents a transaction involving material stock.

    Attributes:
        material_id (int): Foreign key to the Material
        quantity_change (float): Amount of stock change
        transaction_type (str): Type of transaction (e.g., PURCHASE, USAGE, ADJUSTMENT)
        transaction_date (DateTime): Date of the transaction
        notes (str): Additional notes about the transaction
    """
    __tablename__ = 'material_transaction'

    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    quantity_change = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    transaction_date = Column(DateTime, default=func.now())
    notes = Column(String(255), nullable=True)

    # Relationships
    material = relationship("Material", back_populates="transactions")

    def __repr__(self) -> str:
        """
        String representation of the MaterialTransaction model.

        Returns:
            str: A string showing transaction details
        """
        return f"<MaterialTransaction id={self.id}, material_id={self.material_id}, change={self.quantity_change}>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert material transaction to dictionary representation.

        Returns:
            dict: Dictionary representation of the material transaction
        """
        return super().to_dict()