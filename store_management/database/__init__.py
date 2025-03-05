# database/__init__.py

import logging
from typing import Callable, Optional

from utils.circular_import_resolver import CircularImportResolver, register_lazy_import

logger = logging.getLogger(__name__)

# First, import Base from models.base
from database.models.base import Base

# Define BaseModel as an alias for Base
BaseModel = Base

from database.initialize import initialize_database

try:
    # Import transaction models directly from the main transaction module
    from database.models.transaction import (
        BaseTransaction,
        HardwareTransaction,
        LeatherTransaction,
        MaterialTransaction
    )

    # Then import the rest of the models
    from database.models.components import Component, PatternComponent, ProjectComponent
    from database.models.enums import LeatherType, MaterialType, OrderStatus, ProjectStatus
    from database.models.hardware import Hardware
    from database.models.leather import Leather
    from database.models.material import Material
    from database.models.order import Order, OrderItem
    from database.models.part import Part
    from database.models.pattern import Pattern
    from database.models.product import Product
    from database.models.project import Project
    from database.models.shopping_list import ShoppingList, ShoppingListItem
    from database.models.storage import Storage
    from database.models.supplier import Supplier

except ImportError as e:
    # Log the import error and continue
    logger.error(f"Import error in database module: {e}")

# Register lazy imports for transaction models
register_lazy_import("database.models.transaction.HardwareTransaction", "database.models.transaction", "HardwareTransaction")
register_lazy_import("database.models.transaction.LeatherTransaction", "database.models.transaction", "LeatherTransaction")
register_lazy_import("database.models.transaction.MaterialTransaction", "database.models.transaction", "MaterialTransaction")
register_lazy_import("database.models.transaction.BaseTransaction", "database.models.transaction", "BaseTransaction")

# Optional: Register lazy imports for other models if needed
register_lazy_import("database.models.hardware.Hardware", "database.models.hardware", "Hardware")
register_lazy_import("database.models.leather.Leather", "database.models.leather", "Leather")
register_lazy_import("database.models.material.Material", "database.models.material", "Material")

# Add logging to help debug import issues
logger.debug("database package initialization complete")