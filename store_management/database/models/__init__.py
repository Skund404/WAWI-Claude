# database/models/__init__.py
"""
Initialization and import management for database models.

This module ensures all models are imported and registered correctly,
resolving potential circular import issues.
"""

import logging
from utils.circular_import_resolver import (
    CircularImportResolver,
    register_lazy_import,
    lazy_import
)
from .customer import Customer

logger = logging.getLogger(__name__)

# Only directly import the base components that don't have dependencies
from .base import Base, ModelValidationError
from .enums import (
    LeatherType, MaterialType, OrderStatus, ProjectStatus,
    PaymentStatus, ComponentType
)

# Register lazy imports for potentially circular dependencies
register_lazy_import("database.models.transaction.BaseTransaction", "database.models.transaction", "BaseTransaction")
register_lazy_import("database.models.transaction.MaterialTransaction", "database.models.transaction", "MaterialTransaction")
register_lazy_import("database.models.transaction.LeatherTransaction", "database.models.transaction", "LeatherTransaction")
register_lazy_import("database.models.transaction.HardwareTransaction", "database.models.transaction", "HardwareTransaction")

# Define initial exports for backward compatibility
__all__ = [
    'Base', 'ModelValidationError',
    'LeatherType', 'MaterialType', 'OrderStatus', 'ProjectStatus',
    'PaymentStatus', 'ComponentType'
]

# Import new customer-related models and enums
from .customer import Customer
from .enums import (
    CustomerStatus,
    CustomerTier,
    CustomerSource
)

# Import all models after dependencies are registered
from .components import Component, PatternComponent, ProjectComponent
from .hardware import Hardware
from .inventory import Inventory
from .leather import Leather
from .material import Material
from .transaction import MaterialTransaction
from .order import Order, OrderItem
from .part import Part
from .pattern import Pattern
from .product import Product
from .production import Production
from .project import Project
from .sales import Sales
from .shopping_list import ShoppingList, ShoppingListItem
from .storage import Storage
from .supplier import Supplier

# Extend __all__ with additional imports
__all__.extend([
    'Customer',
    'CustomerStatus',
    'CustomerTier',
    'CustomerSource',
    'Component', 'PatternComponent', 'ProjectComponent',
    'Hardware', 'Inventory', 'Leather', 'Material',
    'MaterialTransaction', 'Order', 'OrderItem',
    'Part', 'Pattern', 'Product', 'Production',
    'Project', 'Sales', 'ShoppingList', 'ShoppingListItem',
    'Storage', 'Supplier'
])

# Add logging to help debug import issues
logger.debug("database.models package initialization complete")