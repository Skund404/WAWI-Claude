# database/sqlalchemy/core/register_managers.py
"""
database/sqlalchemy/core/register_managers.py
Registers specialized managers for models.
"""

from database.sqlalchemy.models_file import (
    Storage, Product, Supplier, Part, Leather, Project, ProjectComponent, Order, OrderItem,
    ShoppingList, ShoppingListItem
)
from database.sqlalchemy.core.manager_factory import register_specialized_manager
from database.sqlalchemy.core.specialized.storage_manager import StorageManager
from database.sqlalchemy.core.specialized.product_manager import ProductManager
from database.sqlalchemy.core.specialized.supplier_manager import SupplierManager
from database.sqlalchemy.core.specialized.part_manager import PartManager
from database.sqlalchemy.core.specialized.leather_manager import LeatherManager
from database.sqlalchemy.core.specialized.recipe_manager import PatternManager
from database.sqlalchemy.core.specialized.order_manager import OrderManager
from database.sqlalchemy.core.specialized.shopping_list_manager import ShoppingListManager


def register_all_specialized_managers():
    """
    Register all specialized managers for models.

    This should be called during application initialization.
    """
    register_specialized_manager(Storage, StorageManager)
    register_specialized_manager(Product, ProductManager)
    register_specialized_manager(Supplier, SupplierManager)
    register_specialized_manager(Part, PartManager)
    register_specialized_manager(Leather, LeatherManager)
    register_specialized_manager(Project, RecipeManager)
    register_specialized_manager(Order, OrderManager)
    register_specialized_manager(ShoppingList, ShoppingListManager)