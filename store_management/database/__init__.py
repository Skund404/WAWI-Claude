# database/__init__.py
from store_management.database.base import BaseManager
from store_management.database.sqlalchemy.models import Base

# Explicitly import all models
from store_management.database.sqlalchemy.models import (
    Supplier,
    Part,
    Leather,
    Recipe,
    RecipeItem,
    ShoppingList,
    ShoppingListItem,
    Order,
    OrderItem
)

# Try importing Shelf from session if not in models
try:
    from store_management.database.sqlalchemy.models import Shelf
except ImportError:
    try:
        from store_management.database.sqlalchemy.session import Shelf
    except ImportError:
        try:
            from store_management.database.sqlalchemy.path.shelf import Shelf
        except ImportError:
            Shelf = None

from store_management.database.sqlalchemy.manager import DatabaseManagerSQLAlchemy

__all__ = [
    'BaseManager',
    'Base',
    'Supplier',
    'Part',
    'Leather',
    'Recipe',
    'RecipeItem',
    'ShoppingList',
    'ShoppingListItem',
    'Order',
    'OrderItem',
    'Shelf',
    'DatabaseManagerSQLAlchemy'
]