# File: \database\sqlalchemy\core\specialized\__init__.py

"""
This module initializes the specialized manager package and exports the necessary classes.

It imports and exposes the specialized manager classes, allowing other parts of the
application to access these components through a single import.
"""

from .storage_manager import StorageManager
from .supplier_manager import SupplierManager
from .product_manager import ProductManager
from .part_manager import PartManager
from .leather_manager import LeatherManager
from .recipe_manager import PatternManager
from .order_manager import OrderManager
from .shopping_list_manager import ShoppingListManager

__all__ = [
"StorageManager",
"SupplierManager",
"ProductManager",
"PartManager",
"LeatherManager",
"RecipeManager",
"OrderManager",
"ShoppingListManager",
]
