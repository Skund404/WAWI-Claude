# database/models/material.py
from database.models.base import Base
from database.models.enums import InventoryStatus, MaterialType, MeasurementUnit
from sqlalchemy import Column, Enum, Float, String, Text, Boolean
from sqlalchemy.orm import relationship
from typing import Optional
from utils.validators import validate_not_empty, validate_positive_number


class Material(Base):
    """
    Model representing general materials used in leatherworking projects.
    """
    # Material specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    material_type = Column(Enum(MaterialType), nullable=False)
    brand = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)

    quantity = Column(Float, default=0.0, nullable=False)
    min_quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(Enum(MeasurementUnit), nullable=False, default=MeasurementUnit.PIECE)

    cost_per_unit = Column(Float, default=0.0, nullable=False)
    price_per_unit = Column(Float, default=0.0, nullable=False)

    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    transactions = relationship("MaterialTransaction", back_populates="material", cascade="all, delete-orphan")
    project_components = relationship("ProjectComponent", back_populates="material")

    def __init__(self, **kwargs):
        """Initialize a Material instance with validation.

        Args:
            **kwargs: Keyword arguments with material attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate material data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'name', 'Material name is required')
        validate_not_empty(data, 'material_type', 'Material type is required')

        if 'quantity' in data:
            validate_positive_number(data, 'quantity')
        if 'min_quantity' in data:
            validate_positive_number(data, 'min_quantity')
        if 'cost_per_unit' in data:
            validate_positive_number(data, 'cost_per_unit')
        if 'price_per_unit' in data:
            validate_positive_number(data, 'price_per_unit')

    def adjust_quantity(self, quantity_change: float, transaction_type, notes: Optional[str] = None):
        """Adjust material quantity and record the transaction.

        Args:
            quantity_change: Amount to adjust (positive for addition, negative for reduction)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ValueError: If resulting quantity would be negative
        """
        # Validate the adjustment
        if self.quantity + quantity_change < 0:
            raise ValueError(f"Cannot reduce quantity below zero. Current: {self.quantity}, Change: {quantity_change}")

        # Update the quantity
        old_quantity = self.quantity
        self.quantity += quantity_change

        # Update status if needed
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.min_quantity:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

        # Create transaction record
        # Implementation would depend on your transaction model

    def __repr__(self):
        """String representation of the material.

        Returns:
            str: String representation
        """
        return f"<Material(id={self.id}, name='{self.name}', type={self.material_type}, status={self.status})>"