from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
database/sqlalchemy/core/register_managers.py
Registers specialized managers for models.
"""


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
