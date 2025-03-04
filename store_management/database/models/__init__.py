# database/models/__init__.py
import logging
from utils.circular_import_resolver import CircularImportResolver, register_lazy_import, lazy_import

logger = logging.getLogger(__name__)

# Only directly import the base components that don't have dependencies
from .base import Base, ModelValidationError
from .enums import LeatherType, MaterialType, OrderStatus, ProjectStatus

# Register lazy imports for potentially circular dependencies
register_lazy_import("database.models.transaction.BaseTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["BaseTransaction"]).BaseTransaction)
register_lazy_import("database.models.transaction.MaterialTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["MaterialTransaction"]).MaterialTransaction)
register_lazy_import("database.models.transaction.LeatherTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["LeatherTransaction"]).LeatherTransaction)
register_lazy_import("database.models.transaction.HardwareTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["HardwareTransaction"]).HardwareTransaction)

# Define exports for backward compatibility
__all__ = [
    'Base', 'ModelValidationError',
    'LeatherType', 'MaterialType', 'OrderStatus', 'ProjectStatus',
]

# After dependencies are registered, we can safely import
from .components import Component, PatternComponent, ProjectComponent
from .hardware import Hardware
from .inventory import Inventory
from .leather import Leather
from .material import Material
from .transaction import MaterialTransaction  # Now safe to import directly
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

# Add more items to __all__
__all__.extend([
    'Component', 'PatternComponent', 'ProjectComponent',
    'Hardware', 'Inventory', 'Leather', 'Material',
    'MaterialTransaction', 'Order', 'OrderItem',
    'Part', 'Pattern', 'Product', 'Production',
    'Project', 'Sales', 'ShoppingList', 'ShoppingListItem',
    'Storage', 'Supplier'
])

# Add logging to help debug import issues
logger.debug("database.models package initialization complete")