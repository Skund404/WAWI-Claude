from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase

class BaseModel:
    pass

class TimestampMixin:
    pass

class ValidationMixin:
    pass

class OrderStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'


class PaymentStatus(Enum):
    UNPAID = 'unpaid'
    PAID = 'paid'
    REFUNDED = 'refunded'


Base = declarative_base()


class MaterialType(Enum):
    """
    Enumeration of material types.
    """
    LEATHER = 'leather'
    THREAD = 'thread'
    HARDWARE = 'hardware'
    FABRIC = 'fabric'
    OTHER = 'other'


class MaterialQualityGrade(Enum):
    """
    Enumeration of material quality grades.
    """
    PREMIUM = 'premium'
    STANDARD = 'standard'
    ECONOMY = 'economy'


class Material(BaseModel, Base):
    """
    Represents a material in the inventory system.

    Attributes:
        id (int): Unique identifier for the material
        name (str): Name of the material
        material_type (MaterialType): Type of material
        quality_grade (MaterialQualityGrade): Quality grade of the material
        stock (float): Current stock quantity
        minimum_stock (float): Minimum stock threshold
        unit_price (float): Price per unit
        supplier_id (int): ID of the supplier
        description (str): Optional description of the material
        created_at (DateTime): Timestamp of record creation
        updated_at (DateTime): Timestamp of last update
    """
    __tablename__ = 'materials'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    material_type = Column(SQLAEnum(MaterialType), nullable=False)
    quality_grade = Column(SQLAEnum(MaterialQualityGrade), nullable=False)
    stock = Column(Float, default=0.0, nullable=False)
    minimum_stock = Column(Float, default=0.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    supplier_id = Column(Integer, nullable=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @inject(MaterialService)
    def __repr__(self):
        """
        String representation of the Material instance.

        Returns:
            str: Formatted string with material details
        """
        return (
            f"<Material(id={self.id}, name='{self.name}', type={self.material_type}, stock={self.stock})>"
        )

    @inject(MaterialService)
    def update_stock(self, quantity_change: float) -> None:
        """
        Update the stock quantity.

        Args:
            quantity_change (float): Quantity to add or subtract

        Raises:
            ValueError: If stock would become negative
        """
        new_stock = self.stock + quantity_change
        if new_stock < 0:
            raise ValueError(
                f'Insufficient stock. Cannot reduce stock below 0.')
        self.stock = new_stock

    @inject(MaterialService)
    def is_low_stock(self) -> bool:
        """
        Check if the material is below its minimum stock threshold.

        Returns:
            bool: True if stock is below minimum, False otherwise
        """
        return self.stock <= self.minimum_stock

    @inject(MaterialService)
    def to_dict(self, exclude_fields=None):
        """
        Convert material to dictionary representation.

        Args:
            exclude_fields (list, optional): Fields to exclude from the dictionary

        Returns:
            dict: Dictionary representation of the material
        """
        exclude_fields = exclude_fields or []
        material_dict = {'id': self.id, 'name': self.name, 'material_type':
                         self.material_type.value, 'quality_grade': self.quality_grade.
                         value, 'stock': self.stock, 'minimum_stock': self.minimum_stock,
                         'unit_price': self.unit_price, 'supplier_id': self.supplier_id,
                         'description': self.description, 'created_at': self.created_at,
                         'updated_at': self.updated_at}
        for field in exclude_fields:
            material_dict.pop(field, None)
        return material_dict