# database/models/part.py
from database.models.base import Base
from database.models.enums import InventoryStatus
from sqlalchemy import Column, Enum, String, Text, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from utils.validators import validate_not_empty, validate_positive_number


class Part(Base):
    """
    Model representing individual parts used in leatherworking projects.
    """
    # Part specific fields
    name = Column(String(255), nullable=False, index=True)
    part_number = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)

    dimensions = Column(String(100), nullable=True)  # Format: "LxWxH"
    weight = Column(Float, nullable=True)

    quantity = Column(Integer, default=0, nullable=False)
    min_quantity = Column(Integer, default=0, nullable=False)

    cost = Column(Float, default=0.0, nullable=False)
    msrp = Column(Float, default=0.0, nullable=False)

    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storage.id"), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="parts")
    supplier = relationship("Supplier", back_populates="parts")
    storage = relationship("Storage", back_populates="parts")

    def __init__(self, **kwargs):
        """Initialize a Part instance with validation.

        Args:
            **kwargs: Keyword arguments with part attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate part data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'name', 'Part name is required')

        if 'quantity' in data:
            validate_positive_number(data, 'quantity', allow_zero=True)
        if 'min_quantity' in data:
            validate_positive_number(data, 'min_quantity', allow_zero=True)
        if 'cost' in data:
            validate_positive_number(data, 'cost', allow_zero=True)
        if 'msrp' in data:
            validate_positive_number(data, 'msrp', allow_zero=True)

    def adjust_quantity(self, quantity_change):
        """Adjust the part quantity.

        Args:
            quantity_change (int): The quantity to add (positive) or remove (negative)

        Raises:
            ValueError: If the resulting quantity would be negative
        """
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            raise ValueError(f"Cannot adjust quantity to {new_quantity}. Current quantity is {self.quantity}.")

        self.quantity = new_quantity

        # Update status
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= self.min_quantity:
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK

    def __repr__(self):
        """String representation of the part.

        Returns:
            str: String representation
        """
        return f"<Part(id={self.id}, name='{self.name}', quantity={self.quantity}, status={self.status})>"