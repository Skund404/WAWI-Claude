# database/models/__init__.py
"""
Database models package for the leatherworking store management system.

This package contains all SQLAlchemy ORM models used in the application.
"""

# Base classes first
from database.models.base import Base, BaseModel

# Enums next
from database.models.enums import (
    OrderStatus, MaterialType, LeatherType, MaterialQualityGrade,
    InventoryStatus, ProjectType, SkillLevel, ProjectStatus,
    SupplierStatus, StorageLocationType, MeasurementUnit,
    Priority, TransactionType, QualityCheckStatus, PaymentStatus
)

# Independent models with no foreign keys
from database.models.supplier import Supplier
from database.models.storage import Storage

# Models that depend on suppliers
from database.models.material import Material, MaterialTransaction
from database.models.part import Part
from database.models.leather import Leather
from database.models.hardware import Hardware
from database.models.product import Product

# Models that depend on material-related models
from database.models.pattern import Pattern
from database.models.project import Project, ProjectComponent
from database.models.order import Order, OrderItem
from database.models.shopping_list import ShoppingList, ShoppingListItem

__all__ = [
    'Base',
    'BaseModel',
    'OrderStatus',
    'MaterialType',
    'LeatherType',
    'MaterialQualityGrade',
    'InventoryStatus',
    'ProjectType',
    'SkillLevel',
    'ProjectStatus',
    'SupplierStatus',
    'StorageLocationType',
    'MeasurementUnit',
    'Priority',
    'TransactionType',
    'QualityCheckStatus',
    'PaymentStatus',
    'Supplier',
    'Storage',
    'Material',
    'MaterialTransaction',
    'Part',
    'Leather',
    'Hardware',
    'Product',
    'Pattern',
    'Project',
    'ProjectComponent',
    'Order',
    'OrderItem',
    'ShoppingList',
    'ShoppingListItem',
]