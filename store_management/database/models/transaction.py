from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/transaction.py
"""
Transaction models for tracking various types of transactions in the leatherworking application.
"""

from sqlalchemy import Column, Integer, Float, DateTime, String, Enum, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Any, Dict, List, Optional, Union
import uuid
from datetime import datetime
import enum
import logging

from database.models.base import Base, ModelValidationError, metadata
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from database.models.enums import (
    TransactionType,
    InventoryAdjustmentType,
    InventoryStatus,
    MaterialType
)
from utils.circular_import_resolver import (
    register_lazy_import
)
from utils.enhanced_model_validator import (
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('MaterialInventory', 'database.models.material_inventory', 'MaterialInventory')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('LeatherInventory', 'database.models.leather_inventory', 'LeatherInventory')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('HardwareInventory', 'database.models.hardware_inventory', 'HardwareInventory')
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('Purchase', 'database.models.purchase', 'Purchase')

from sqlalchemy.orm import declarative_base
TransactionBase = declarative_base()
TransactionBase.metadata = metadata
TransactionBase.metadata = metadata
TransactionBase.metadata = metadata

class Transaction(TransactionBase):
    """
    Base Transaction model representing inventory adjustments and movements.
    """
    __tablename__ = 'transactions'

    # Core attributes
    id: Mapped[int] = mapped_column(primary_key=True)

    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType),
        nullable=False,
        index=True
    )
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_addition: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Transaction metadata
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transaction_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Linked records
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        index=True
    )
    purchase_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("purchases.id"),
        nullable=True,
        index=True
    )

    # Relationships
    project = relationship("Project", back_populates="transactions")
    purchase = relationship("Purchase", back_populates="transactions")

    def __init__(self, **kwargs):
        """
        Initialize a Transaction instance with comprehensive validation.
        """
        try:
            # Set default transaction date if not provided
            if 'transaction_date' not in kwargs:
                kwargs['transaction_date'] = datetime.utcnow()

            # Validate input data
            validation_errors = self.validate(kwargs)
            if validation_errors:
                raise ModelValidationError(
                    "Transaction validation failed",
                    validation_errors
                )

            # Initialize base model
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"Transaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Transaction: {str(e)}")

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate transaction data.

        Args:
            data: Dictionary of transaction attributes

        Returns:
            Dictionary of validation errors by field
        """
        errors = {}

        # Validate required fields
        required_fields = ['transaction_type', 'quantity']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.setdefault(field, []).append(f"{field} is required")

        # Validate transaction type
        if 'transaction_type' in data:
            # Convert string to enum if necessary
            if isinstance(data['transaction_type'], str):
                try:
                    data['transaction_type'] = TransactionType[data['transaction_type'].upper()]
                except KeyError:
                    errors.setdefault('transaction_type', []).append(
                        f"Invalid transaction type: {data['transaction_type']}"
                    )
            elif not isinstance(data['transaction_type'], TransactionType):
                errors.setdefault('transaction_type', []).append(
                    "Transaction type must be a valid TransactionType enum"
                )

        # Validate quantity
        if 'quantity' in data:
            try:
                quantity = float(data['quantity'])
                if quantity <= 0:
                    errors.setdefault('quantity', []).append("Quantity must be a positive number")
            except (ValueError, TypeError):
                errors.setdefault('quantity', []).append("Quantity must be a valid number")

        return errors

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert transaction to a dictionary representation.
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        # Special handling for dates and enums
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert datetime to ISO format
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                # Convert enum to string
                elif isinstance(value, enum.Enum):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        return result

    def __repr__(self) -> str:
        """
        String representation of the Transaction.
        """
        return (
            f"<{self.__class__.__name__}(id={self.id}, "
            f"type={self.transaction_type.name if hasattr(self.transaction_type, 'name') else 'Unknown'}, "
            f"quantity={self.quantity}, "
            f"is_addition={self.is_addition})>"
        )

    def reverse(self) -> 'Transaction':
        """
        Create a reversal transaction that undoes this transaction.
        """
        # Create basic reversal data
        reversal_data = {
            'transaction_type': TransactionType.REVERSAL,
            'quantity': self.quantity,
            'is_addition': not self.is_addition,
            'notes': f"Reversal of transaction {self.id}",
            'reference_number': str(self.id),
            'reference_type': 'transaction_reversal',
            'project_id': self.project_id,
            'purchase_id': self.purchase_id
        }

        # Fall back to standard transaction for base class
        return Transaction(**reversal_data)


class MaterialTransaction(Transaction):
    """
    Transaction model for material inventory movements.
    """
    __tablename__ = 'material_transactions'

    # Link to parent table
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)

    # Material-specific references
    material_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False,
        index=True
    )
    material_inventory_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("material_inventories.id"),
        nullable=True,
        index=True
    )

    # Relationships
    material = relationship("Material", back_populates="transactions")
    material_inventory = relationship("MaterialInventory", back_populates="transactions")

    def __init__(self, **kwargs):
        """
        Initialize a MaterialTransaction instance with comprehensive validation.
        """
        try:
            # Validate material-specific data
            self._validate_material_transaction_data(kwargs)

            # Initialize base transaction
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"MaterialTransaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create MaterialTransaction: {str(e)}")

    @classmethod
    def _validate_material_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate material transaction specific data.
        """
        # Ensure we have at least one identifier
        if not data.get('material_id'):
            raise ValueError("Material ID is required")

    def reverse(self) -> 'MaterialTransaction':
        """
        Create a reversal transaction for MaterialTransaction.
        """
        # Create basic reversal data
        reversal_data = {
            'transaction_type': TransactionType.REVERSAL,
            'quantity': self.quantity,
            'is_addition': not self.is_addition,
            'notes': f"Reversal of material transaction {self.id}",
            'reference_number': str(self.id),
            'reference_type': 'material_transaction_reversal',
            'project_id': self.project_id,
            'purchase_id': self.purchase_id,
            'material_id': self.material_id,
            'material_inventory_id': self.material_inventory_id
        }

        return MaterialTransaction(**reversal_data)


class LeatherTransaction(Transaction):
    """
    Transaction model for leather inventory movements.
    """
    __tablename__ = 'leather_transactions'

    # Link to parent table
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)

    # Leather-specific attributes
    area_sqft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Leather-specific references
    leather_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("leathers.id"),
        nullable=False,
        index=True
    )
    leather_inventory_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("leather_inventories.id"),
        nullable=True,
        index=True
    )

    # Relationships
    leather = relationship("Leather", back_populates="transactions")
    leather_inventory = relationship("LeatherInventory", back_populates="transactions")

    def __init__(self, **kwargs):
        """
        Initialize a LeatherTransaction instance with comprehensive validation.
        """
        try:
            # Set area_sqft to match quantity if not provided
            if 'area_sqft' not in kwargs and 'quantity' in kwargs:
                kwargs['area_sqft'] = kwargs['quantity']

            # Validate leather-specific data
            self._validate_leather_transaction_data(kwargs)

            # Initialize base transaction
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"LeatherTransaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create LeatherTransaction: {str(e)}")

    @classmethod
    def _validate_leather_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate leather transaction specific data.
        """
        # Validate required fields
        if not data.get('leather_id'):
            raise ValueError("Leather ID is required")

        # Validate area if provided
        if 'area_sqft' in data and data['area_sqft'] is not None:
            try:
                area = float(data['area_sqft'])
                if area <= 0:
                    raise ValueError("Area must be a positive number")
            except (ValueError, TypeError):
                raise ValueError("Area must be a valid number")

    def reverse(self) -> 'LeatherTransaction':
        """
        Create a reversal transaction for LeatherTransaction.
        """
        # Create basic reversal data
        reversal_data = {
            'transaction_type': TransactionType.REVERSAL,
            'quantity': self.quantity,
            'is_addition': not self.is_addition,
            'notes': f"Reversal of leather transaction {self.id}",
            'reference_number': str(self.id),
            'reference_type': 'leather_transaction_reversal',
            'project_id': self.project_id,
            'purchase_id': self.purchase_id,
            'leather_id': self.leather_id,
            'leather_inventory_id': self.leather_inventory_id,
            'area_sqft': self.area_sqft
        }

        return LeatherTransaction(**reversal_data)


class HardwareTransaction(Transaction):
    """
    Transaction model for hardware inventory movements.
    """
    __tablename__ = 'hardware_transactions'

    # Link to parent table
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)

    # Hardware-specific references
    hardware_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hardwares.id"),
        nullable=False,
        index=True
    )
    hardware_inventory_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("hardware_inventories.id"),
        nullable=True,
        index=True
    )

    # Relationships
    hardware = relationship("Hardware", back_populates="transactions")
    hardware_inventory = relationship("HardwareInventory", back_populates="transactions")

    def __init__(self, **kwargs):
        """
        Initialize a HardwareTransaction instance with comprehensive validation.
        """
        try:
            # Validate hardware-specific data
            self._validate_hardware_transaction_data(kwargs)

            # Initialize base transaction
            super().__init__(**kwargs)

        except Exception as e:
            logger.error(f"HardwareTransaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create HardwareTransaction: {str(e)}")

    @classmethod
    def _validate_hardware_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate hardware transaction specific data.
        """
        # Validate required fields
        if not data.get('hardware_id'):
            raise ValueError("Hardware ID is required")

    def reverse(self) -> 'HardwareTransaction':
        """
        Create a reversal transaction for HardwareTransaction.
        """
        # Create basic reversal data
        reversal_data = {
            'transaction_type': TransactionType.REVERSAL,
            'quantity': self.quantity,
            'is_addition': not self.is_addition,
            'notes': f"Reversal of hardware transaction {self.id}",
            'reference_number': str(self.id),
            'reference_type': 'hardware_transaction_reversal',
            'project_id': self.project_id,
            'purchase_id': self.purchase_id,
            'hardware_id': self.hardware_id,
            'hardware_inventory_id': self.hardware_inventory_id
        }

        return HardwareTransaction(**reversal_data)


# Register for lazy import resolution
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')
register_lazy_import('MaterialTransaction', 'database.models.transaction', 'MaterialTransaction')
register_lazy_import('LeatherTransaction', 'database.models.transaction', 'LeatherTransaction')
register_lazy_import('HardwareTransaction', 'database.models.transaction', 'HardwareTransaction')