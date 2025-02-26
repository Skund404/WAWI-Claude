# database/__init__.py

import logging
from typing import Callable, Optional

from sqlalchemy.orm import declarative_base

from database.initialize import initialize_database
from database.models.base import Base, BaseModel
from database.models.components import Component, PatternComponent, ProjectComponent
from database.models.enums import LeatherType, MaterialType, OrderStatus, ProjectStatus
from utils.circular_import_resolver import CircularImportResolver

logger = logging.getLogger(__name__)

Base = declarative_base()

try:
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
    CircularImportResolver.register_pending_import(__name__, e)