# database/models/transaction.py
"""
Comprehensive Transaction Models for Leatherworking Management System

This module defines transaction models for tracking inventory movements
and material flows throughout the system, providing an audit trail for
all inventory changes with comprehensive validation and relationship management.

While not explicitly in the ER diagram, these models provide the backbone
for maintaining accurate inventory records and supporting the integrity
of the inventory management subsystem.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type, Tuple, cast

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    TransactionType,
    InventoryAdjustmentType,
    InventoryStatus
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
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


class Transaction(Base, TimestampMixin, ValidationMixin, TrackingMixin):
    """
    Base Transaction model representing inventory adjustments and movements.

    Implements single-table inheritance for different transaction types, providing
    a comprehensive audit trail for all inventory changes in the system.
    """
    __tablename__ = 'transactions'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

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
    reference_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

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

    # Single-table inheritance discriminator
    transaction_class: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="transactions")
    purchase = relationship("Purchase", back_populates="transactions")

    __mapper_args__ = {
        'polymorphic_on': transaction_class,
        'polymorphic_identity': 'transaction'
    }

    def __init__(self, **kwargs):
        """
        Initialize a Transaction instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for transaction attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Set default transaction class if not provided
            if 'transaction_class' not in kwargs:
                kwargs['transaction_class'] = self.__class__.__name__.lower()

            # Set transaction date if not provided
            if 'transaction_date' not in kwargs:
                kwargs['transaction_date'] = datetime.utcnow()

            # Validate input data
            self._validate_transaction_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Transaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Transaction: {str(e)}") from e

    @classmethod
    def _validate_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of transaction creation data.

        Args:
            data: Transaction creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'transaction_type', 'Transaction type is required')
        validate_not_empty(data, 'quantity', 'Quantity is required')

        # Validate transaction type
        if 'transaction_type' in data:
            ModelValidator.validate_enum(
                data['transaction_type'],
                TransactionType,
                'transaction_type'
            )

        # Validate quantity
        if 'quantity' in data:
            validate_positive_number(
                data,
                'quantity',
                allow_zero=False,
                message="Quantity must be greater than zero"
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize metadata if not provided
        if not hasattr(self, 'metadata') or self.metadata is None:
            self.metadata = {}

        # Ensure tracking ID is set
        if not hasattr(self, 'tracking_id') or not self.tracking_id:
            self.generate_tracking_id()

    def reverse(self) -> 'Transaction':
        """
        Create a reversal transaction that undoes this transaction.

        Returns:
            A new transaction that reverses this one
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

        # Create specific reversal based on transaction type
        if isinstance(self, MaterialTransaction):
            return MaterialTransaction(
                material_id=self.material_id,
                material_inventory_id=self.material_inventory_id,
                **reversal_data
            )
        elif isinstance(self, LeatherTransaction):
            return LeatherTransaction(
                leather_id=self.leather_id,
                leather_inventory_id=self.leather_inventory_id,
                **reversal_data
            )
        elif isinstance(self, HardwareTransaction):
            return HardwareTransaction(
                hardware_id=self.hardware_id,
                hardware_inventory_id=self.hardware_inventory_id,
                **reversal_data
            )
        else:
            # Fall back to generic transaction
            return Transaction(**reversal_data)

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert transaction to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the transaction
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

        Returns:
            Detailed transaction representation
        """
        return (
            f"<{self.__class__.__name__}(id={self.id}, "
            f"type={self.transaction_type.name if hasattr(self.transaction_type, 'name') else 'Unknown'}, "
            f"quantity={self.quantity}, "
            f"is_addition={self.is_addition})>"
        )


class MaterialTransaction(Transaction):
    """
    Transaction model for material inventory movements.
    Tracks changes to material quantities and provides an audit trail.
    """
    __tablename__ = 'material_transactions'

    # Link to parent transaction
    id: Mapped[int] = mapped_column(ForeignKey('transactions.id'), primary_key=True)

    # Material-specific references
    material_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("materials.id"),
        nullable=True,
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

    __mapper_args__ = {
        'polymorphic_identity': 'materialtransaction',
        'inherit_condition': id == Transaction.id
    }

    def __init__(self, **kwargs):
        """
        Initialize a MaterialTransaction instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for transaction attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate material-specific data
            self._validate_material_transaction_data(kwargs)

            # Initialize base transaction
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"MaterialTransaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create MaterialTransaction: {str(e)}") from e

    @classmethod
    def _validate_material_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate material transaction specific data.

        Args:
            data: Transaction data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Ensure we have at least one identifier
        if not data.get('material_id') and not data.get('material_inventory_id'):
            raise ValidationError("Either material_id or material_inventory_id is required")


class LeatherTransaction(Transaction):
    """
    Transaction model for leather inventory movements.
    Tracks changes to leather quantities and provides an audit trail.
    """
    __tablename__ = 'leather_transactions'

    # Link to parent transaction
    id: Mapped[int] = mapped_column(ForeignKey('transactions.id'), primary_key=True)

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

    __mapper_args__ = {
        'polymorphic_identity': 'leathertransaction',
        'inherit_condition': id == Transaction.id
    }

    def __init__(self, **kwargs):
        """
        Initialize a LeatherTransaction instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for transaction attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Set area_sqft to match quantity if not provided
            if 'area_sqft' not in kwargs and 'quantity' in kwargs:
                kwargs['area_sqft'] = kwargs['quantity']

            # Validate leather-specific data
            self._validate_leather_transaction_data(kwargs)

            # Initialize base transaction
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"LeatherTransaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create LeatherTransaction: {str(e)}") from e

    @classmethod
    def _validate_leather_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate leather transaction specific data.

        Args:
            data: Transaction data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'leather_id', 'Leather ID is required')

        # Validate area if provided
        if 'area_sqft' in data and data['area_sqft'] is not None:
            validate_positive_number(
                data,
                'area_sqft',
                allow_zero=False,
                message="Area must be a positive number"
            )


class HardwareTransaction(Transaction):
    """
    Transaction model for hardware inventory movements.
    Tracks changes to hardware quantities and provides an audit trail.
    """
    __tablename__ = 'hardware_transactions'

    # Link to parent transaction
    id: Mapped[int] = mapped_column(ForeignKey('transactions.id'), primary_key=True)

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

    __mapper_args__ = {
        'polymorphic_identity': 'hardwaretransaction',
        'inherit_condition': id == Transaction.id
    }

    def __init__(self, **kwargs):
        """
        Initialize a HardwareTransaction instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for transaction attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate hardware-specific data
            self._validate_hardware_transaction_data(kwargs)

            # Initialize base transaction
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"HardwareTransaction initialization failed: {e}")
            raise ModelValidationError(f"Failed to create HardwareTransaction: {str(e)}") from e

    @classmethod
    def _validate_hardware_transaction_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate hardware transaction specific data.

        Args:
            data: Transaction data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'hardware_id', 'Hardware ID is required')


# Helper functions for transaction management

def create_transaction(
        item_type: str,
        item_id: int,
        quantity: float,
        transaction_type: Union[str, TransactionType],
        is_addition: bool = True,
        inventory_id: Optional[int] = None,
        project_id: Optional[int] = None,
        purchase_id: Optional[int] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
) -> Transaction:
    """
    Create a transaction for a specific item type.

    Args:
        item_type: Type of item ("material", "leather", "hardware")
        item_id: ID of the specific item
        quantity: Amount involved in the transaction
        transaction_type: Type of transaction
        is_addition: Whether this is an addition or reduction
        inventory_id: Optional ID of the specific inventory record
        project_id: Optional project ID to associate with the transaction
        purchase_id: Optional purchase ID to associate with the transaction
        notes: Optional notes about the transaction
        metadata: Optional additional transaction metadata

    Returns:
        The created transaction object

    Raises:
        ModelValidationError: If transaction creation fails
        ValueError: If item type is not supported
    """
    try:
        # Normalize transaction type
        if isinstance(transaction_type, str):
            try:
                transaction_type = TransactionType[transaction_type.upper()]
            except KeyError:
                raise ValidationError(f"Invalid transaction type: {transaction_type}")

        # Prepare common transaction data
        transaction_data = {
            'transaction_type': transaction_type,
            'quantity': quantity,
            'is_addition': is_addition,
            'notes': notes,
            'project_id': project_id,
            'purchase_id': purchase_id,
            'metadata': metadata or {}
        }

        # Create transaction based on item type
        item_type = item_type.lower()

        if item_type == 'material':
            transaction = MaterialTransaction(
                material_id=item_id,
                material_inventory_id=inventory_id,
                **transaction_data
            )
        elif item_type == 'leather':
            transaction = LeatherTransaction(
                leather_id=item_id,
                leather_inventory_id=inventory_id,
                **transaction_data
            )
        elif item_type == 'hardware':
            transaction = HardwareTransaction(
                hardware_id=item_id,
                hardware_inventory_id=inventory_id,
                **transaction_data
            )
        else:
            raise ValueError(f"Unsupported item type: {item_type}")

        return transaction

    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        if isinstance(e, (ValidationError, ValueError)):
            raise ModelValidationError(str(e))
        raise ModelValidationError(f"Failed to create transaction: {str(e)}")


def get_transactions_by_project(project_id: int, session) -> List[Transaction]:
    """
    Retrieve all transactions associated with a project.

    Args:
        project_id: ID of the project
        session: Database session

    Returns:
        List of transactions for the project

    Raises:
        ModelValidationError: If retrieval fails
    """
    try:
        validate_not_empty({'project_id': project_id}, 'project_id', 'Project ID is required')

        from sqlalchemy import select
        query = select(Transaction).where(Transaction.project_id == project_id)
        return session.execute(query).scalars().all()

    except Exception as e:
        logger.error(f"Error getting transactions for project {project_id}: {e}")
        raise ModelValidationError(f"Failed to retrieve project transactions: {str(e)}")


def get_transactions_by_item(
        item_type: str,
        item_id: int,
        session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
) -> List[Transaction]:
    """
    Retrieve transactions for a specific inventory item.

    Args:
        item_type: Type of item ("material", "leather", "hardware")
        item_id: ID of the specific item
        session: Database session
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        List of transactions for the item

    Raises:
        ModelValidationError: If retrieval fails
        ValueError: If item type is not supported
    """
    try:
        validate_not_empty({'item_id': item_id}, 'item_id', 'Item ID is required')
        validate_not_empty({'item_type': item_type}, 'item_type', 'Item type is required')

        from sqlalchemy import select, and_

        # Create query based on item type
        item_type = item_type.lower()

        if item_type == 'material':
            query = select(MaterialTransaction).where(MaterialTransaction.material_id == item_id)
        elif item_type == 'leather':
            query = select(LeatherTransaction).where(LeatherTransaction.leather_id == item_id)
        elif item_type == 'hardware':
            query = select(HardwareTransaction).where(HardwareTransaction.hardware_id == item_id)
        else:
            raise ValueError(f"Unsupported item type: {item_type}")

        # Add date filters if provided
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)

        # Execute query
        return session.execute(query).scalars().all()

    except Exception as e:
        logger.error(f"Error getting transactions for {item_type} {item_id}: {e}")
        if isinstance(e, ValueError):
            raise ModelValidationError(str(e))
        raise ModelValidationError(f"Failed to retrieve item transactions: {str(e)}")


# Register for lazy import resolution
register_lazy_import('Transaction', 'database.models.transaction', 'Transaction')
register_lazy_import('MaterialTransaction', 'database.models.transaction', 'MaterialTransaction')
register_lazy_import('LeatherTransaction', 'database.models.transaction', 'LeatherTransaction')
register_lazy_import('HardwareTransaction', 'database.models.transaction', 'HardwareTransaction')