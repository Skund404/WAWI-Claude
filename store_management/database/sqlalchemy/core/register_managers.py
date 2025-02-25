# database/sqlalchemy/core/register_managers.py
"""
Registers specialized managers for models.

This module provides a centralized location for registering
specialized manager classes for different model types.
"""

from typing import Type

from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

from core.managers.manager_factory import register_specialized_manager

# Import model and manager classes
from models.storage import Storage
from models.product import Product
from models.supplier import Supplier
from models.part import Part
from models.leather import Leather
from models.project import Project
from models.order import Order
from models.shopping_list import ShoppingList

from core.managers.storage_manager import StorageManager
from core.managers.product_manager import ProductManager
from core.managers.supplier_manager import SupplierManager
from core.managers.part_manager import PartManager
from core.managers.leather_manager import LeatherManager
from core.managers.recipe_manager import RecipeManager
from core.managers.order_manager import OrderManager
from core.managers.shopping_list_manager import ShoppingListManager


def register_all_specialized_managers():
    """
    Register all specialized managers for models.

    This function should be called during application initialization
    to set up specialized managers for different model types.
    """
    # Register specialized managers for each model
    register_specialized_manager(Storage, StorageManager)
    register_specialized_manager(Product, ProductManager)
    register_specialized_manager(Supplier, SupplierManager)
    register_specialized_manager(Part, PartManager)
    register_specialized_manager(Leather, LeatherManager)
    register_specialized_manager(Project, RecipeManager)
    register_specialized_manager(Order, OrderManager)
    register_specialized_manager(ShoppingList, ShoppingListManager)