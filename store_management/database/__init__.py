# database/__init__.py

import logging
from typing import Callable, Optional

from utils.circular_import_resolver import CircularImportResolver

logger = logging.getLogger(__name__)

# First, import Base from models.base
from database.models.base import Base
# Define BaseModel as an alias for Base
BaseModel = Base

from database.initialize import initialize_database

try:
    # Import models after Base and BaseModel are defined
    from database.models.components import Component, PatternComponent, ProjectComponent
    from database.models.enums import LeatherType, MaterialType, OrderStatus, ProjectStatus
    from database.models.hardware import Hardware
    from database.models.leather import Leather
    from database.models.material import Material, MaterialTransaction
    from database.models.order import Order, OrderItem
    from database.models.part import Part
    from database.models.pattern import Pattern
    from database.models.product import Product
    from database.models.project import Project, ProjectComponent
    from database.models.shopping_list import ShoppingList, ShoppingListItem
    from database.models.storage import Storage
    from database.models.supplier import Supplier
except ImportError as e:
    # Use the correct method for circular import resolution
    CircularImportResolver.register_lazy_import(__name__, e)