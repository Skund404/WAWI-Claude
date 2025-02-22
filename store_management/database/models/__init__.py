# Path: database/models/__init__.py
# Import the base from SQLAlchemy configuration
from database.sqlalchemy.base import Base

# Import all model classes to ensure they are loaded and registered with Base
from .order import Order, OrderItem
from .part import Part
from .leather import Leather
from .product import Product
from .recipe import Recipe, RecipeItem
from .shopping_list import ShoppingList, ShoppingListItem
from .storage import Storage
from .supplier import Supplier
from .transaction import InventoryTransaction, LeatherTransaction
from .enums import (
    InventoryStatus,
    ProductionStatus,
    TransactionType,
    OrderStatus,
    PaymentStatus
)

# List of all model classes for convenience
__all__ = [
    'Base',
    'Order', 'OrderItem',
    'Part',
    'Leather',
    'Product',
    'Recipe', 'RecipeItem',
    'ShoppingList', 'ShoppingListItem',
    'Storage',
    'Supplier',
    'InventoryTransaction', 'LeatherTransaction',
    'InventoryStatus', 'ProductionStatus',
    'TransactionType', 'OrderStatus', 'PaymentStatus'
]