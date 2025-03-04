# database/models/leather.py
from database.models.base import Base
from database.models.enums import LeatherType, MaterialQualityGrade, InventoryStatus, TransactionType
from sqlalchemy import Column, Enum, Float, String, Text, Boolean, Integer, ForeignKey  # Add Integer and ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional
from utils.validators import validate_not_empty, validate_positive_number


class Leather(Base):
    """
    Model representing leather materials.
    """
    __tablename__ = 'leathers'
    # Leather specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    leather_type = Column(Enum(LeatherType), nullable=False)
    tannage = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    finish = Column(String(50), nullable=True)
    grade = Column(Enum(MaterialQualityGrade), nullable=True)

    thickness_mm = Column(Float, nullable=True)
    size_sqft = Column(Float, nullable=True)
    area_available_sqft = Column(Float, nullable=True)

    cost_per_sqft = Column(Float, default=0.0, nullable=False)
    price_per_sqft = Column(Float, default=0.0, nullable=False)

    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id"), nullable=True)

    # Relationships
    transactions = relationship("LeatherTransaction", back_populates="leather", cascade="all, delete-orphan")
    supplier = relationship("Supplier", back_populates="leathers")
    storage = relationship("Storage", back_populates="leathers")
    project_components = relationship(
        "ProjectComponent",
        primaryjoin="and_(foreign(Leather.id) == remote(ProjectComponent.material_id), "
                    "ProjectComponent.type == 'project_component')",
        viewonly=True,

    )
    project_component_id = Column(Integer, ForeignKey('components.id'), nullable=True)

    def __init__(self, **kwargs):
        """Initialize a Leather instance with validation.

        Args:
            **kwargs: Keyword arguments with leather attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate leather data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'name', 'Leather name is required')
        validate_not_empty(data, 'leather_type', 'Leather type is required')

        if 'thickness_mm' in data:
            validate_positive_number(data, 'thickness_mm')
        if 'size_sqft' in data:
            validate_positive_number(data, 'size_sqft')
        if 'area_available_sqft' in data:
            validate_positive_number(data, 'area_available_sqft')
        if 'cost_per_sqft' in data:
            validate_positive_number(data, 'cost_per_sqft')
        if 'price_per_sqft' in data:
            validate_positive_number(data, 'price_per_sqft')

    def adjust_area(self, area_change: float, transaction_type: TransactionType, notes: Optional[str] = None):
        """Adjust available leather area and record the transaction.

        Args:
            area_change: Amount to adjust in square feet (positive for addition, negative for reduction)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ValueError: If resulting area would be negative
        """
        # Validate the adjustment
        if self.area_available_sqft + area_change < 0:
            raise ValueError(
                f"Cannot reduce area below zero. Current: {self.area_available_sqft}, Change: {area_change}")

        # Update the area
        old_area = self.area_available_sqft
        self.area_available_sqft += area_change

        # Update status if needed
        if self.area_available_sqft <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.area_available_sqft <= 1.0:  # Example threshold for low stock
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

        # Create transaction record
        # Implementation would depend on your transaction model

    def __repr__(self):
        """String representation of the leather.

        Returns:
            str: String representation
        """
        return f"<Leather(id={self.id}, name='{self.name}', type={self.leather_type}, area={self.area_available_sqft} sqft)>"