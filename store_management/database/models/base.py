# database/models/base.py
"""
Comprehensive base model for SQLAlchemy models with advanced relationship
and validation strategies.

This module provides a foundational framework for database models in the
leatherworking management system, implementing advanced features like:
- Circular import resolution
- Dynamic relationship management
- Comprehensive validation
- Logging and error tracking
"""

import enum
import uuid
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable, Union

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    declared_attr,
    relationship,
    Session
)
from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    Column
)
from sqlalchemy.exc import SQLAlchemyError

# Import circular import resolver and core utilities
from utils.circular_import_resolver import (
    CircularImportResolver,
    lazy_import,
    register_lazy_import
)

# Import mixins
from .mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin
)

# Setup logging
logger = logging.getLogger(__name__)

# Type variable for generic model typing
T = TypeVar('T')


class ModelValidationError(Exception):
    """
    Custom exception for comprehensive model validation errors.
    Provides detailed error tracking and reporting.
    """

    def __init__(self, message: str, errors: Optional[Dict[str, List[str]]] = None):
        """
        Initialize validation error with optional detailed error mapping.

        Args:
            message: Primary error message
            errors: Dictionary of field-specific validation errors
        """
        super().__init__(message)
        self.errors = errors or {}

    def __str__(self) -> str:
        """
        Generate a comprehensive error string.

        Returns:
            Detailed error representation
        """
        base_message = super().__str__()
        if self.errors:
            error_details = "\n".join([
                f"{field}: {', '.join(field_errors)}"
                for field, field_errors in self.errors.items()
            ])
            return f"{base_message}\n\nValidation Errors:\n{error_details}"
        return base_message


class BaseModelMetaclass(DeclarativeBase.__class__):
    """
    Advanced metaclass for resolving inheritance conflicts,
    tracking model registrations, and managing relationships.
    """
    # Centralized registries
    _registered_models: Dict[str, Type] = {}
    _relationship_initializers: Dict[str, List[Callable]] = {}
    _validation_strategies: Dict[str, Callable] = {}

    def __new__(mcs, name, bases, attrs):
        """
        Custom metaclass method to apply advanced model configuration.

        Args:
            name: Name of the class being created
            bases: Base classes
            attrs: Class attributes and methods

        Returns:
            Configured model class
        """
        # Skip base classes
        if name in ['Base', 'BaseModel', 'DeclarativeBase']:
            return super().__new__(mcs, name, bases, attrs)

        # Create the class using SQLAlchemy's metaclass behavior
        new_class = super().__new__(mcs, name, bases, attrs)

        # Skip registration for abstract classes
        if attrs.get('__abstract__', False):
            return new_class

        # Generate full path for the model
        full_path = f"{new_class.__module__}.{new_class.__name__}"

        try:
            # Log model registration
            logger.debug(f"Registering model: {full_path}")

            # Store potential relationship initializers
            if hasattr(new_class, 'initialize_relationships'):
                mcs._relationship_initializers[full_path] = [
                    getattr(new_class, 'initialize_relationships')
                ]

            # Store validation strategies if defined
            if hasattr(new_class, 'validate'):
                mcs._validation_strategies[full_path] = getattr(new_class, 'validate')

        except Exception as e:
            logger.error(f"Error registering model {full_path}: {e}")

        return new_class

    @classmethod
    def initialize_all_model_relationships(cls):
        """
        Dynamically initialize relationships for all registered models.
        """
        logger.info("Initializing relationships for all models")

        try:
            # Dynamically import models to avoid circular imports
            from .sales import Sales
            from .sales_item import SalesItem
            from .customer import Customer
            from .product import Product
            from .pattern import Pattern
            from .components import Component
            from .picking_list import PickingList
            from .project import Project
            from .supplier import Supplier

            # Define comprehensive relationship configurations
            cls._define_comprehensive_relationships(
                Sales, SalesItem, Customer, Product,
                Pattern, Component, PickingList, Project, Supplier
            )

            logger.info("All model relationships initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing model relationships: {e}")

    @classmethod
    def _define_comprehensive_relationships(
            cls,
            Sales, SalesItem, Customer, Product,
            Pattern, Component, PickingList, Project, Supplier
    ):
        """
        Centralized method for defining complex model relationships.
        """
        # Sales relationships
        if hasattr(Sales, 'items'):
            Sales.items = relationship(
                SalesItem,
                back_populates='sale',
                cascade='all, delete-orphan'
            )

        if hasattr(Sales, 'customer'):
            Sales.customer = relationship(
                Customer,
                back_populates='sales_records'
            )

        # Customer relationships
        if hasattr(Customer, 'sales_records'):
            Customer.sales_records = relationship(
                Sales,
                back_populates='customer'
            )

        # Product relationships
        if hasattr(Product, 'sales_items'):
            Product.sales_items = relationship(
                SalesItem,
                back_populates='product'
            )

        # Add more comprehensive relationship definitions as needed
        # This method allows for centralized, flexible relationship management


class Base(DeclarativeBase, metaclass=BaseModelMetaclass):
    """
    Enhanced base model with comprehensive utility methods for
    database entities in the leatherworking management system.
    """
    # Shared metadata configuration
    metadata = MetaData()

    # Table configuration for flexibility
    __table_args__ = {
        'extend_existing': True,
        'sqlite_autoincrement': True
    }

    # Core primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Unique identifier for tracking
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    @classmethod
    def initialize_relationships(cls):
        """
        Placeholder method for model-specific relationship initialization.
        Can be overridden in subclasses to define complex relationships.
        """
        pass

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from class name.
        Convert CamelCase or PascalCase to snake_case and pluralize.
        """
        # Convert camelCase or PascalCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Pluralize with simple approach
        return f"{s2}s" if not s2.endswith('s') else s2

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """
        Generic validation method that can be overridden by subclasses.

        Args:
            data: Dictionary of model attributes to validate

        Returns:
            bool: Whether the data is valid
        """
        return all(value is not None for value in data.values())

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model instance
        """
        exclude_fields = exclude_fields or []
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    def soft_delete(self) -> None:
        """
        Perform a soft delete by marking the record as deleted.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        logger.info(f"Soft deleted {self.__class__.__name__} with ID {self.id}")

    def restore(self) -> None:
        """
        Restore a soft-deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
        logger.info(f"Restored {self.__class__.__name__} with ID {self.id}")


def initialize_all_model_relationships():
    """
    Global function to initialize all model relationships.
    Serves as a centralized entry point for relationship configuration.
    """
    BaseModelMetaclass.initialize_all_model_relationships()