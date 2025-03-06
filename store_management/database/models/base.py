# database/models/base.py
"""
Comprehensive base model for SQLAlchemy models with advanced utility methods.
"""

from .model_metaclass import BaseModelInterface
import enum
import uuid
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr, relationship
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy import event
from sqlalchemy.orm import Mapper

# Import mixins
from .mixins import TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin

# Setup logging
logger = logging.getLogger(__name__)

# Create a single, shared metadata instance
metadata = MetaData()

T = TypeVar('T')


class ModelValidationError(Exception):
    """Custom exception for model validation errors."""
    pass


class BaseModelMetaclass(DeclarativeBase.__class__):
    """
    Custom metaclass to resolve inheritance conflicts and track model registrations.
    """
    # Class-level dictionary to track registered models with full paths
    _registered_models: Dict[str, Type] = {}
    _relationship_initializers: Dict[str, List[Callable]] = {}

    def __new__(mcs, name, bases, attrs):
        """
        Custom metaclass method to apply interface validation and mixin application.
        """
        # Skip base classes
        if name in ['Base', 'BaseModel', 'DeclarativeBase']:
            return super().__new__(mcs, name, bases, attrs)

        # Create the class using SQLAlchemy's metaclass behavior
        new_class = super().__new__(mcs, name, bases, attrs)

        # Skip registration for abstract classes
        if attrs.get('__abstract__', False):
            return new_class

        # Generate full path for the model with module and class name
        full_path = f"{new_class.__module__}.{new_class.__name__}"

        try:
            # Log model registration
            logger.debug(f"Registering model: {full_path}")

            # Store potential relationship initializers
            if hasattr(new_class, 'initialize_relationships'):
                mcs._relationship_initializers[full_path] = [
                    getattr(new_class, 'initialize_relationships')
                ]

        except Exception as e:
            logger.error(f"Error registering model {full_path}: {e}")

        return new_class

    @classmethod
    def initialize_all_model_relationships(cls):
        """
        Initialize relationships for all registered models.
        """
        logger.info("Initializing relationships for all models")

        try:
            # Dynamically import models to avoid circular imports
            from .sales import Sales
            from .sales_item import SalesItem
            from .customer import Customer
            from .product import Product
            from .project import Project
            from .picking_list import PickingList
            from .pattern import Pattern
            from .component import Component
            from .supplier import Supplier

            # Define key relationships
            cls._define_customer_relationships(Customer, Sales)
            cls._define_sales_relationships(Sales, SalesItem, PickingList, Project)
            cls._define_product_relationships(Product, Sales, Pattern)
            cls._define_project_relationships(Project, Sales, PickingList)
            cls._define_component_relationships(Component, Pattern)
            cls._define_supplier_relationships(Supplier)

            logger.info("All model relationships initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing model relationships: {e}")

    @classmethod
    def _define_customer_relationships(cls, Customer, Sales):
        """Define relationships for Customer model."""
        if hasattr(Customer, 'sales'):
            Customer.sales = relationship(
                Sales,
                back_populates='customer',
                cascade='all, delete-orphan'
            )

    @classmethod
    def _define_sales_relationships(cls, Sales, SalesItem, PickingList, Project):
        """Define relationships for Sales model."""
        if hasattr(Sales, 'items'):
            Sales.items = relationship(
                SalesItem,
                back_populates='sale',
                cascade='all, delete-orphan'
            )

        if hasattr(Sales, 'picking_list'):
            Sales.picking_list = relationship(
                PickingList,
                back_populates='sale',
                uselist=False
            )

        if hasattr(Sales, 'project'):
            Sales.project = relationship(
                Project,
                back_populates='sale',
                uselist=False
            )

    @classmethod
    def _define_product_relationships(cls, Product, Sales, Pattern):
        """Define relationships for Product model."""
        if hasattr(Product, 'sales_items'):
            Product.sales_items = relationship(
                Sales,
                back_populates='product'
            )

        if hasattr(Product, 'patterns'):
            Product.patterns = relationship(
                Pattern,
                secondary='product_patterns',
                back_populates='products'
            )

    @classmethod
    def _define_project_relationships(cls, Project, Sales, PickingList):
        """Define relationships for Project model."""
        if hasattr(Project, 'sale'):
            Project.sale = relationship(
                Sales,
                back_populates='project'
            )

        if hasattr(Project, 'picking_lists'):
            Project.picking_lists = relationship(
                PickingList,
                back_populates='project'
            )

    @classmethod
    def _define_component_relationships(cls, Component, Pattern):
        """Define relationships for Component model."""
        if hasattr(Component, 'patterns'):
            Component.patterns = relationship(
                Pattern,
                secondary='pattern_components',
                back_populates='components'
            )

    @classmethod
    def _define_supplier_relationships(cls, Supplier):
        """Define relationships for Supplier model."""
        # Define relationships for materials, leather, hardware, tools
        pass


class Base(DeclarativeBase, metaclass=BaseModelMetaclass):
    """
    Enhanced base model with comprehensive utility methods.
    """
    # Use the shared metadata
    metadata = metadata

    # Table configuration
    __table_args__ = {
        'extend_existing': True,  # Allow redefining tables
        'sqlite_autoincrement': True
    }

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Unique identifier
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    @classmethod
    def initialize_relationships(cls):
        """
        Placeholder method for model-specific relationship initialization.
        Can be overridden in subclasses.
        """
        pass

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from class name.
        Convert CamelCase to snake_case and pluralize.
        """
        # Convert camelCase or PascalCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Pluralize (simple approach)
        return f"{s2}s" if not s2.endswith('s') else s2

    # ... (rest of the existing Base class methods remain the same)


def initialize_all_model_relationships():
    """
    Global function to initialize all model relationships.
    """
    BaseModelMetaclass.initialize_all_model_relationships()