# database/models/hardware.py
from database.models.base import Base
from database.models.enums import InventoryStatus, MeasurementUnit, TransactionType
from database.models.hardware_enums import HardwareFinish, HardwareMaterial, HardwareType
from sqlalchemy import Boolean, Column, Enum, Float, String
from sqlalchemy.orm import relationship
from typing import Optional
from utils.validators import validate_not_empty, validate_positive_number, validate_string


class Hardware(Base):
    """
    Model representing hardware items used in leatherworking projects.
    """
    # Define specific columns for this model (Base already has id, uuid, etc.)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    hardware_type = Column(Enum(HardwareType), nullable=False)
    material = Column(Enum(HardwareMaterial), nullable=False)
    finish = Column(Enum(HardwareFinish), nullable=True)

    quantity = Column(Float, default=0.0, nullable=False)
    min_quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(Enum(MeasurementUnit), nullable=False, default=MeasurementUnit.PIECE)

    cost_per_unit = Column(Float, default=0.0, nullable=False)
    price_per_unit = Column(Float, default=0.0, nullable=False)

    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)

    # Relationships
    transactions = relationship("InventoryTransaction", back_populates="hardware")

    def __init__(self, **kwargs):
        """Initialize a Hardware instance with validation.

        Args:
            **kwargs: Keyword arguments with hardware attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate hardware data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'name', 'Hardware name is required')
        validate_not_empty(data, 'hardware_type', 'Hardware type is required')
        validate_not_empty(data, 'material', 'Hardware material is required')

        if 'quantity' in data:
            validate_positive_number(data, 'quantity')
        if 'min_quantity' in data:
            validate_positive_number(data, 'min_quantity')
        if 'cost_per_unit' in data:
            validate_positive_number(data, 'cost_per_unit')
        if 'price_per_unit' in data:
            validate_positive_number(data, 'price_per_unit')

    def adjust_quantity(self, quantity_change: int, transaction_type: TransactionType, notes: Optional[str] = None):
        """Adjust hardware quantity and record the transaction.

        Args:
            quantity_change: Amount to adjust (positive for addition, negative for reduction)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction
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

        # Create transaction record - implementation would depend on your transaction model

    def __repr__(self):
        """String representation of the hardware.

        Returns:
            str: String representation
        """
        return f"<Hardware(id={self.id}, name='{self.name}', type={self.hardware_type}, status={self.status})>"