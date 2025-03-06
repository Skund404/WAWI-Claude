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
    lazy_import,
    resolve_lazy_relationships
)

# Setup logger
logger = logging.getLogger(__name__)

# Only directly import the base components that don't have dependencies
from .base import Base, ModelValidationError
from .enums import (
    LeatherType, MaterialType, OrderStatus, ProjectStatus,
    PaymentStatus, ComponentType
)

# Define initial exports for backward compatibility
__all__ = [
    'Base', 'ModelValidationError',
    'LeatherType', 'MaterialType', 'OrderStatus', 'ProjectStatus',
    'PaymentStatus', 'ComponentType'
]

# Register lazy imports for potentially circular dependencies
register_lazy_import("Transaction", "database.models.transaction", "BaseTransaction")
register_lazy_import("MaterialTransaction", "database.models.transaction", "MaterialTransaction")
register_lazy_import("LeatherTransaction", "database.models.transaction", "LeatherTransaction")
register_lazy_import("HardwareTransaction", "database.models.transaction", "HardwareTransaction")

# Import customer-related models and enums
from .customer import Customer
from .enums import (
    CustomerStatus,
    CustomerTier,
    CustomerSource
)

# Extend initial exports
__all__.extend([
    'Customer',
    'CustomerStatus',
    'CustomerTier',
    'CustomerSource'
])

# Import models after dependencies are registered
from .components import Component, PatternComponent, ProjectComponent
from .hardware import Hardware
from .inventory import Inventory
from .leather import Leather
from .material import Material
from .order import Order, setup_relationships as setup_order_relationships
from .order_item import OrderItem, setup_relationships as setup_order_item_relationships
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
    'Component', 'PatternComponent', 'ProjectComponent',
    'Hardware', 'Inventory', 'Leather', 'Material',
    'Order', 'OrderItem', 'Part', 'Pattern', 'Product',
    'Production', 'Project', 'Sales', 'ShoppingList',
    'ShoppingListItem', 'Storage', 'Supplier'
])


def initialize_models():
    """
    Initialize model relationships and perform any necessary setup.
    """
    logger.info("Initializing model relationships")

    # Call setup relationships for order and order_item
    setup_order_relationships()
    setup_order_item_relationships()

    # Resolve any lazy relationships
    resolve_lazy_relationships()


# Initialize models when the module is imported
initialize_models()

# Add logging to help debug import issues
logger.debug("database.models package initialization complete")