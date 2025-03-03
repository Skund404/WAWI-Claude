# database/models/transaction.py
from database.models.base import Base
from database.models.enums import TransactionType
from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from typing import Optional


class BaseTransaction(Base):
    """
    Base model for all transaction types.
    """
    # Base transaction fields
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    is_addition = Column(Boolean, default=True, nullable=False)

    # Single-table inheritance discriminator
    transaction_class = Column(String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': transaction_class,
        'polymorphic_identity': 'base_transaction'
    }

    def __init__(self, transaction_type: TransactionType, quantity: float,
                 is_addition: bool = True, notes: Optional[str] = None, **kwargs):
        """Initialize a new transaction.

        Args:
            transaction_type: Type of the transaction
            quantity: Amount being transacted
            is_addition: Whether this is an addition or reduction
            notes: Optional notes about the transaction
        """
        kwargs.update({
            'transaction_type': transaction_type,
            'quantity': quantity,
            'is_addition': is_addition,
            'notes': notes
        })

        # Validate transaction data before creating
        self._validate_creation(kwargs)

        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate transaction data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        if 'transaction_type' not in data:
            raise ValueError("Transaction type is required")

        if 'quantity' not in data:
            raise ValueError("Quantity is required")

        if data.get('quantity', 0) <= 0:
            raise ValueError("Quantity must be greater than zero")


class MaterialTransaction(BaseTransaction):
    """
    Model for transactions involving generic materials.
    """
    # Foreign keys
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)

    # Relationships
    material = relationship("Material", back_populates="transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'material_transaction'
    }

    def __init__(self, material_id: int, **kwargs):
        """Initialize a material transaction.

        Args:
            material_id: ID of the material being transacted
        """
        kwargs.update({
            'material_id': material_id
        })
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate material transaction data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        super()._validate_creation(data)

        if 'material_id' not in data:
            raise ValueError("Material ID is required")


class LeatherTransaction(BaseTransaction):
    """
    Model for transactions involving leather.
    """
    # Leather-specific fields
    area_sqft = Column(Float, nullable=True)

    # Foreign keys
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    leather = relationship("Leather", back_populates="transactions")
    project = relationship("Project", back_populates="leather_transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'leather_transaction'
    }

    def __init__(self, leather_id: int, **kwargs):
        """Initialize a leather transaction.

        Args:
            leather_id: ID of the leather being transacted
        """
        kwargs.update({
            'leather_id': leather_id,
            'area_sqft': kwargs.get('quantity')  # Set area_sqft to match quantity for consistency
        })
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate leather transaction data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        super()._validate_creation(data)

        if 'leather_id' not in data:
            raise ValueError("Leather ID is required")


class HardwareTransaction(BaseTransaction):
    """
    Model for transactions involving hardware.
    """
    # Foreign keys
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    hardware = relationship("Hardware", back_populates="transactions")
    project = relationship("Project", back_populates="hardware_transactions")

    __mapper_args__ = {
        'polymorphic_identity': 'hardware_transaction'
    }

    def __init__(self, hardware_id: int, **kwargs):
        """Initialize a hardware transaction.

        Args:
            hardware_id: ID of the hardware being transacted
        """
        kwargs.update({
            'hardware_id': hardware_id
        })
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate hardware transaction data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        super()._validate_creation(data)

        if 'hardware_id' not in data:
            raise ValueError("Hardware ID is required")