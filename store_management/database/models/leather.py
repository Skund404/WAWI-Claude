# database/models/leather.py
"""
Leather model for the leatherworking store management application.

This module defines the database model for leather materials, including
validation, quantity management, and value calculation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base, BaseModel
from database.models.enums import InventoryStatus, LeatherType, MaterialQualityGrade, MaterialType, TransactionType
from utils.validators import validate_not_empty, validate_positive_number
from utils.logger import get_logger

logger = get_logger(__name__)


class Leather(Base, BaseModel):
    """
    Model representing leather materials in inventory.

    Attributes:
        id (int): Primary key
        name (str): Name of the leather
        description (str): Detailed description
        leather_type (LeatherType): Type of leather (full grain, top grain, etc.)
        tannage (str): Tanning method (vegetable, chrome, etc.)
        thickness_mm (float): Thickness in millimeters
        size_sqft (float): Size in square feet
        grade (MaterialQualityGrade): Quality grade of the leather
        color (str): Color of the leather
        finish (str): Surface finish description
        supplier_id (int): Foreign key to supplier
        supplier (Supplier): Relationship to the supplier
        cost_per_sqft (float): Cost per square foot
        unit_price (float): Unit price for GUI display purposes
        status (InventoryStatus): Current inventory status
        quantity (int): Current quantity in inventory
        location (str): Storage location
        date_added (datetime): Date when added to inventory
        last_updated (datetime): Last update timestamp
        notes (str): Additional notes
        deleted (bool): Soft delete flag
    """
    __tablename__ = "leathers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Leather-specific attributes
    leather_type = Column(Enum(LeatherType), nullable=False, index=True)
    tannage = Column(String(50), nullable=True)
    thickness_mm = Column(Float, nullable=True)
    size_sqft = Column(Float, nullable=True)
    grade = Column(Enum(MaterialQualityGrade), nullable=False, index=True)
    color = Column(String(50), nullable=True, index=True)
    finish = Column(String(100), nullable=True)

    # Inventory and cost attributes
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="leathers")
    cost_per_sqft = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=True)  # For GUI display
    status = Column(Enum(InventoryStatus), nullable=False, default=InventoryStatus.IN_STOCK, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    location = Column(String(100), nullable=True)

    # Tracking attributes
    date_added = Column(DateTime, nullable=False, default=func.current_timestamp())
    last_updated = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    notes = Column(Text, nullable=True)
    deleted = Column(Boolean, nullable=False, default=False, index=True)

    # Relationships
    transactions = relationship("LeatherTransaction", back_populates="leather", cascade="all, delete-orphan")
    project_components = relationship("ProjectComponent", back_populates="leather")

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a Leather instance with validation.

        Args:
            **kwargs: Keyword arguments with leather attributes

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Creating new Leather instance with args: {kwargs}")

        # Validate required fields
        self._validate_fields(kwargs)

        # Auto-calculate unit price if not provided but cost_per_sqft is
        if 'unit_price' not in kwargs and 'cost_per_sqft' in kwargs and kwargs['cost_per_sqft'] is not None:
            kwargs['unit_price'] = kwargs['cost_per_sqft']

        # Call parent init after validation
        super().__init__(**kwargs)

        logger.info(f"Created new Leather: {self.name} ({self.leather_type.name if self.leather_type else 'Unknown'})")

    def _validate_fields(self, kwargs: Dict[str, Any]) -> None:
        """
        Validate leather fields before initialization or update.

        Args:
            kwargs: Dictionary of field values to validate

        Raises:
            ValueError: If validation fails
        """
        if 'name' in kwargs:
            validate_not_empty(kwargs['name'], 'name')

        if 'leather_type' in kwargs and kwargs['leather_type'] is None:
            raise ValueError("Leather type cannot be None")

        if 'grade' in kwargs and kwargs['grade'] is None:
            raise ValueError("Leather grade cannot be None")

        if 'thickness_mm' in kwargs and kwargs['thickness_mm'] is not None:
            validate_positive_number(kwargs['thickness_mm'], 'thickness_mm')

        if 'size_sqft' in kwargs and kwargs['size_sqft'] is not None:
            validate_positive_number(kwargs['size_sqft'], 'size_sqft')

        if 'cost_per_sqft' in kwargs and kwargs['cost_per_sqft'] is not None:
            validate_positive_number(kwargs['cost_per_sqft'], 'cost_per_sqft')

        if 'unit_price' in kwargs and kwargs['unit_price'] is not None:
            validate_positive_number(kwargs['unit_price'], 'unit_price')

        if 'quantity' in kwargs:
            validate_positive_number(kwargs['quantity'], 'quantity', allow_zero=True)

    def update(self, **kwargs: Any) -> 'Leather':
        """
        Update leather attributes with validation.

        Args:
            **kwargs: Keyword arguments with leather attributes to update

        Returns:
            Leather: Self reference

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Updating Leather ID {self.id} ({self.name}) with: {kwargs}")

        # Validate fields before update
        self._validate_fields(kwargs)

        # Auto-update unit_price if cost_per_sqft is updated
        if 'cost_per_sqft' in kwargs and kwargs['cost_per_sqft'] is not None and 'unit_price' not in kwargs:
            kwargs['unit_price'] = kwargs['cost_per_sqft']

        # Track changes for logging
        changes = {}
        for key, value in kwargs.items():
            if hasattr(self, key) and getattr(self, key) != value:
                changes[key] = {
                    'old': getattr(self, key),
                    'new': value
                }

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Log changes
        if changes:
            logger.info(f"Updated Leather ID {self.id} ({self.name}): {changes}")

        return self

    def soft_delete(self) -> None:
        """
        Soft delete the leather item.
        """
        logger.info(f"Soft deleting Leather ID {self.id} ({self.name})")
        self.deleted = True
        self.status = InventoryStatus.DISCONTINUED

    def restore(self) -> None:
        """
        Restore a soft-deleted leather item.
        """
        logger.info(f"Restoring previously deleted Leather ID {self.id} ({self.name})")
        self.deleted = False
        self.status = InventoryStatus.IN_STOCK

    def adjust_quantity(self, area_change: float, transaction_type: TransactionType,
                        notes: Optional[str] = None, wastage: float = 0.0) -> None:
        """
        Adjust the leather area and create a transaction record.

        Args:
            area_change: Amount to change area by (positive or negative square feet)
            transaction_type: Type of transaction
            notes: Additional notes for the transaction
            wastage: Amount of leather wasted during cutting

        Raises:
            ValueError: If resulting area would be negative
        """
        from database.models.transaction import LeatherTransaction

        if self.size_sqft is None:
            logger.error(f"Cannot adjust Leather ID {self.id} area: size_sqft is None")
            raise ValueError("Cannot adjust area on leather with no size_sqft value")

        new_size = self.size_sqft + area_change
        if new_size < 0:
            logger.error(f"Cannot adjust Leather ID {self.id} area to {new_size}")
            raise ValueError(f"Cannot adjust area to {new_size}. Current area: {self.size_sqft}")

        # Create transaction record
        transaction = LeatherTransaction(
            leather_id=self.id,
            area_change=area_change,
            transaction_type=transaction_type,
            notes=notes,
            wastage=wastage
        )

        # Update size
        old_size = self.size_sqft
        self.size_sqft = new_size

        # Update status if needed
        if new_size == 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif new_size <= 5:  # Arbitrary low threshold
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

        logger.info(
            f"Adjusted Leather ID {self.id} ({self.name}) area from {old_size} to {new_size} ({transaction_type.name})")

        # Add transaction to relationship
        self.transactions.append(transaction)

    def calculate_total_value(self) -> float:
        """
        Calculate the total value of this leather inventory.

        Returns:
            float: Total value (size_sqft * cost_per_sqft)
        """
        if self.size_sqft is None or self.cost_per_sqft is None:
            return 0.0

        return self.size_sqft * self.cost_per_sqft

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert leather object to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the leather
        """
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.leather_type.value if self.leather_type else None,  # Naming to match GUI expectations
            'leather_type': self.leather_type.value if self.leather_type else None,
            'tannage': self.tannage,
            'thickness': self.thickness_mm,  # Naming to match GUI expectations
            'thickness_mm': self.thickness_mm,
            'size_sqft': self.size_sqft,
            'grade': self.grade.value if self.grade else None,
            'quality_grade': self.grade.value if self.grade else None,  # Naming to match GUI expectations
            'color': self.color,
            'finish': self.finish,
            'supplier_id': self.supplier_id,
            'cost_per_sqft': self.cost_per_sqft,
            'unit_price': self.unit_price or self.cost_per_sqft,  # Provide unit price for GUI
            'status': self.status.value if self.status else None,
            'quantity': self.quantity,
            'location': self.location,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'notes': self.notes,
            'total_value': self.calculate_total_value(),
            'material_type': MaterialType.LEATHER.value
        }
        return result

    def __repr__(self) -> str:
        """String representation of the leather.

        Returns:
            str: String representation
        """
        return (
            f"Leather(id={self.id}, name='{self.name}', type={self.leather_type.name if self.leather_type else 'None'}, "
            f"grade={self.grade.name if self.grade else 'None'}, size={self.size_sqft}, status={self.status.name if self.status else 'None'})")