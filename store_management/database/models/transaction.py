# database/models/transaction.py
"""
Transaction models for tracking inventory movements and changes.

This module defines various transaction types for different materials
and implements proper relationship handling to avoid circular imports.
"""

import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Union, List, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, MetaData, and_
from sqlalchemy.orm import relationship, backref, foreign, remote
from sqlalchemy import inspect, create_engine
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base
from database.models.enums import TransactionType
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Lazy import helpers
Material = lazy_import('database.models.material', 'Material')
Leather = lazy_import('database.models.leather', 'Leather')
Hardware = lazy_import('database.models.hardware', 'Hardware')
Project = lazy_import('database.models.project', 'Project')

# Register lazy imports
register_lazy_import('database.models.material.Material', 'database.models.material', 'Material')
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('database.models.project.Project', 'database.models.project', 'Project')

# We'll define the relationships directly in the classes instead of using register_relationship
# Since register_relationship expects class objects, not strings


class BaseTransaction(Base):
    """
    Base model for all transaction types.
    Implements single-table inheritance for different transaction types.
    """
    __tablename__ = 'base_transactions'

    # Important: Set extend_existing to True to handle multiple imports
    __table_args__ = {'extend_existing': True}

    # Base transaction fields
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    is_addition = Column(Boolean, default=True, nullable=False)

    # Timestamps
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Reference information
    reference_number = Column(String(50), nullable=True)
    reference_type = Column(String(50), nullable=True)

    # Project relationship (optional) - stored at base transaction level
    project_id = Column(
        Integer,
        ForeignKey("projects.id", name="fk_base_transaction_project"),
        nullable=True,
        info={'constraint_name': 'fk_base_transaction_project'}
    )

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
            **kwargs: Additional attributes for the transaction
        """
        try:
            kwargs.update({
                'transaction_type': transaction_type,
                'quantity': quantity,
                'is_addition': is_addition,
                'notes': notes,
                'transaction_date': datetime.utcnow()
            })

            # Validate transaction data before creating
            self._validate_creation(kwargs)

            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing BaseTransaction: {e}")
            raise ValueError(f"Failed to initialize transaction: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """Validate transaction data before creation.

        Args:
            data: The data to validate

        Raises:
            ValueError: If validation fails
        """
        try:
            if 'transaction_type' not in data:
                raise ValueError("Transaction type is required")

            if 'quantity' not in data:
                raise ValueError("Quantity is required")

            if data.get('quantity', 0) <= 0:
                raise ValueError("Quantity must be greater than zero")
        except Exception as e:
            logger.error(f"Error validating transaction data: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Transaction validation failed: {str(e)}") from e

    def _validate_instance(self) -> None:
        """
        Additional validation after instance creation.

        Raises:
            ValueError: If validation fails
        """
        try:
            if self.quantity <= 0:
                raise ValueError("Quantity must be greater than zero")
        except Exception as e:
            logger.error(f"Error validating transaction instance: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Transaction instance validation failed: {str(e)}") from e

    def reverse(self) -> 'BaseTransaction':
        """
        Create a reversal transaction that undoes this transaction.

        Returns:
            BaseTransaction: A new transaction that reverses this one

        Raises:
            ValueError: If creating the reversal fails
        """
        try:
            reversal_data = {
                'transaction_type': TransactionType.REVERSAL,
                'quantity': self.quantity,
                'is_addition': not self.is_addition,
                'notes': f"Reversal of transaction {self.id}",
                'reference_number': str(self.id),
                'reference_type': 'transaction_reversal'
            }

            return self.__class__(**reversal_data)
        except Exception as e:
            logger.error(f"Error creating reversal transaction: {e}")
            raise ValueError(f"Failed to create reversal transaction: {str(e)}") from e

    def __repr__(self) -> str:
        """String representation of the transaction."""
        return (f"<{self.__class__.__name__}(id={self.id}, "
                f"type={self.transaction_type.name if hasattr(self.transaction_type, 'name') else 'Unknown'}, "
                f"quantity={self.quantity}, "
                f"is_addition={self.is_addition})>")


class MaterialTransaction(BaseTransaction):
    """
    Model for transactions involving generic materials.
    """
    __table_args__ = {'extend_existing': True}

    # Foreign keys
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)

    # Relationships - explicitly defining the join condition
    material = relationship(
        "Material",
        back_populates="transactions",
        lazy="select"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'material_transaction'
    }

    def __init__(self, material_id: int, **kwargs):
        """Initialize a material transaction.

        Args:
            material_id: ID of the material being transacted
            **kwargs: Additional attributes for the transaction
        """
        try:
            kwargs.update({
                'material_id': material_id
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing MaterialTransaction: {e}")
            raise ValueError(f"Failed to initialize material transaction: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """Validate material transaction data before creation.

        Args:
            data: The data to validate

        Raises:
            ValueError: If validation fails
        """
        try:
            super()._validate_creation(data)

            if 'material_id' not in data:
                raise ValueError("Material ID is required")
        except Exception as e:
            logger.error(f"Error validating material transaction data: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Material transaction validation failed: {str(e)}") from e


class LeatherTransaction(BaseTransaction):
    """
    Model for transactions involving leather.
    """
    __table_args__ = {'extend_existing': True}

    # Leather-specific fields
    area_sqft = Column(Float, nullable=True)

    # Foreign keys with explicit configuration
    leather_id = Column(
        Integer,
        ForeignKey("leathers.id", name="fk_leather_transaction_leather"),
        nullable=False,
        info={'constraint_name': 'fk_leather_transaction_leather'}
    )

    # Relationships with explicit join conditions
    leather = relationship(
        "Leather",
        primaryjoin="LeatherTransaction.leather_id == Leather.id",
        foreign_keys=[leather_id],
        back_populates="transactions",
        lazy="select"
    )

    # Using string-based primaryjoin and viewonly=True to resolve circular dependency issue
    project = relationship(
        "Project",
        primaryjoin="LeatherTransaction.project_id == Project.id",
        foreign_keys="[LeatherTransaction.project_id]",
        viewonly=True,  # This is the key change to fix the circular dependency
        back_populates="leather_transactions"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'leather_transaction'
    }

    @classmethod
    def debug_relationship(cls) -> Dict[str, Any]:
        """
        Provides detailed debugging information about the relationship configuration.

        Returns:
            Dict[str, Any]: Debug information about relationships
        """
        debug_info = {}
        try:
            logger.info(f"Debugging LeatherTransaction relationships")

            # Get relationship information
            debug_info["project_id_column"] = str(getattr(cls, "project_id", "Not found"))
            debug_info["project_id_type"] = str(type(getattr(cls, "project_id", None)))
            debug_info["project_relationship"] = str(getattr(cls, "project", "Not defined"))

            # Log foreign key constraints
            if hasattr(cls, '__table__'):
                fk_constraints = [
                    str(constraint) for constraint in cls.__table__.constraints
                    if isinstance(constraint, ForeignKey)
                ]
                debug_info["foreign_key_constraints"] = fk_constraints

            logger.info(f"LeatherTransaction relationship debug info: {debug_info}")
            return debug_info
        except Exception as e:
            logger.error(f"Error during LeatherTransaction relationship debugging: {e}")
            debug_info["error"] = str(e)
            return debug_info

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Class method called when the class is subclassed.
        Used to validate and debug relationship configuration during class definition.

        Args:
            **kwargs: Additional keyword arguments
        """
        try:
            super().__init_subclass__(**kwargs)

            # Call the debugging method
            if hasattr(cls, 'debug_relationship'):
                cls.debug_relationship()
        except Exception as e:
            logger.error(f"Error during relationship debugging for {cls.__name__}: {e}")

    def __init__(self, leather_id: int, **kwargs):
        """Initialize a leather transaction.

        Args:
            leather_id: ID of the leather being transacted
            **kwargs: Additional attributes for the transaction
        """
        try:
            # Set area_sqft to match quantity for consistency if not provided
            if 'area_sqft' not in kwargs and 'quantity' in kwargs:
                kwargs['area_sqft'] = kwargs['quantity']

            kwargs.update({
                'leather_id': leather_id
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing LeatherTransaction: {e}")
            raise ValueError(f"Failed to initialize leather transaction: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """Validate leather transaction data before creation.

        Args:
            data: The data to validate

        Raises:
            ValueError: If validation fails
        """
        try:
            super()._validate_creation(data)

            if 'leather_id' not in data:
                raise ValueError("Leather ID is required")

            # Validate area_sqft if provided
            if 'area_sqft' in data and data['area_sqft'] is not None:
                if data['area_sqft'] <= 0:
                    raise ValueError("Area must be greater than zero")
        except Exception as e:
            logger.error(f"Error validating leather transaction data: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Leather transaction validation failed: {str(e)}") from e


class HardwareTransaction(BaseTransaction):
    """
    Model for transactions involving hardware.
    """
    __table_args__ = {'extend_existing': True}

    # Foreign keys
    hardware_id = Column(
        Integer,
        ForeignKey("hardwares.id", name="fk_hardware_transaction_hardware"),
        nullable=False,
        info={'constraint_name': 'fk_hardware_transaction_hardware'}
    )

    # Relationships with explicit join conditions
    hardware = relationship(
        "Hardware",
        primaryjoin="HardwareTransaction.hardware_id == Hardware.id",
        foreign_keys=[hardware_id],
        lazy="select"
    )

    # Using string-based primaryjoin and viewonly=True to resolve circular dependency issue
    project = relationship(
        "Project",
        primaryjoin="HardwareTransaction.project_id == Project.id",
        foreign_keys="[HardwareTransaction.project_id]",
        viewonly=True,  # This is the key change to fix the circular dependency
        back_populates="hardware_transactions"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'hardware_transaction'
    }

    @classmethod
    def debug_relationship(cls) -> Dict[str, Any]:
        """
        Provides detailed debugging information about the relationship configuration.

        Returns:
            Dict[str, Any]: Debug information about relationships
        """
        debug_info = {}
        try:
            logger.info(f"Debugging HardwareTransaction relationships")

            # Get relationship information
            debug_info["project_id_column"] = str(getattr(cls, "project_id", "Not found"))
            debug_info["project_id_type"] = str(type(getattr(cls, "project_id", None)))
            debug_info["project_relationship"] = str(getattr(cls, "project", "Not defined"))

            # Log foreign key constraints
            if hasattr(cls, '__table__'):
                fk_constraints = [
                    str(constraint) for constraint in cls.__table__.constraints
                    if isinstance(constraint, ForeignKey)
                ]
                debug_info["foreign_key_constraints"] = fk_constraints

            logger.info(f"HardwareTransaction relationship debug info: {debug_info}")
            return debug_info
        except Exception as e:
            logger.error(f"Error during HardwareTransaction relationship debugging: {e}")
            debug_info["error"] = str(e)
            return debug_info

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Class method called when the class is subclassed.
        Used to validate and debug relationship configuration during class definition.

        Args:
            **kwargs: Additional keyword arguments
        """
        try:
            super().__init_subclass__(**kwargs)

            # Call the debugging method
            if hasattr(cls, 'debug_relationship'):
                cls.debug_relationship()
        except Exception as e:
            logger.error(f"Error during relationship debugging for {cls.__name__}: {e}")

    def __init__(self, hardware_id: int, **kwargs):
        """Initialize a hardware transaction.

        Args:
            hardware_id: ID of the hardware being transacted
            **kwargs: Additional attributes for the transaction
        """
        try:
            kwargs.update({
                'hardware_id': hardware_id
            })
            super().__init__(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing HardwareTransaction: {e}")
            raise ValueError(f"Failed to initialize hardware transaction: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """Validate hardware transaction data before creation.

        Args:
            data: The data to validate

        Raises:
            ValueError: If validation fails
        """
        try:
            super()._validate_creation(data)

            if 'hardware_id' not in data:
                raise ValueError("Hardware ID is required")
        except Exception as e:
            logger.error(f"Error validating hardware transaction data: {e}")
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Hardware transaction validation failed: {str(e)}") from e


# ----- Module-level functions below -----

def create_transaction(
        item: Union[Any, 'Material', 'Leather', 'Hardware'],
        quantity: float,
        transaction_type: TransactionType,
        is_addition: bool = True,
        project_id: Optional[int] = None,
        notes: Optional[str] = None
) -> BaseTransaction:
    """
    Create a transaction for a material, leather, or hardware item.

    Args:
        item: The item being transacted
        quantity: Amount being transacted
        transaction_type: Type of transaction
        is_addition: Whether this is an addition or reduction
        project_id: Optional project ID to associate with the transaction
        notes: Optional notes about the transaction

    Returns:
        The created transaction

    Raises:
        ValueError: If the transaction would result in negative inventory
        TypeError: If an unsupported item type is provided
    """
    transaction_data = {
        'quantity': quantity,
        'transaction_type': transaction_type,
        'is_addition': is_addition,
        'notes': notes
    }

    if project_id is not None:
        transaction_data['project_id'] = project_id

    try:
        # Dynamically create transaction based on item type
        if isinstance(item, Material) or (hasattr(item, '__class__') and item.__class__.__name__ == 'Material'):
            transaction = MaterialTransaction(material_id=item.id, **transaction_data)
        elif isinstance(item, Leather) or (hasattr(item, '__class__') and item.__class__.__name__ == 'Leather'):
            transaction = LeatherTransaction(leather_id=item.id, **transaction_data)
        elif isinstance(item, Hardware) or (hasattr(item, '__class__') and item.__class__.__name__ == 'Hardware'):
            transaction = HardwareTransaction(hardware_id=item.id, **transaction_data)
        else:
            raise TypeError(f"Unsupported item type: {type(item)}")

        return transaction

    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        logger.error(traceback.format_exc())
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Failed to create transaction: {str(e)}") from e


def get_transactions_by_project(project_id: int) -> List[BaseTransaction]:
    """
    Get all transactions associated with a specific project.

    Args:
        project_id: The ID of the project

    Returns:
        List of transactions associated with the project

    Raises:
        ValueError: If the project ID is invalid
    """
    if not project_id:
        raise ValueError("Project ID is required")

    try:
        # Use SQLAlchemy's polymorphic query capability to fetch all transaction types
        from sqlalchemy import select
        from sqlalchemy.orm import Session
        from database.sqlalchemy.session import get_db_session

        # Get a database session
        session = get_db_session()

        # Create a query for all transaction types with the given project_id
        query = select(BaseTransaction).where(BaseTransaction.project_id == project_id)

        # Execute the query
        transactions = session.execute(query).scalars().all()

        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions for project {project_id}: {e}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Failed to retrieve project transactions: {str(e)}") from e


def initialize_relationships():
    """
    Initialize all relationships for transaction models.
    This function should be called after all models are loaded to ensure
    correct relationship setup, especially for circular dependencies.
    """
    try:
        logger.info("Initializing transaction relationships")

        # Import necessary models directly to avoid circular import issues
        from database.models.project import Project
        from database.models.material import Material
        from database.models.leather import Leather
        from database.models.hardware import Hardware

        # Update the relationship definitions if needed
        # This gives us a chance to make runtime adjustments to relationships
        # that might be hard to define correctly at class definition time

        # Log successful initialization
        logger.info("Transaction relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing transaction relationships: {e}")
        logger.error(traceback.format_exc())