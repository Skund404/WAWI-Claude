# Path: database/models/__init__.py
# Import all models to ensure they're registered with SQLAlchemy

from .storage import Storage
from .part import Part
from .leather import Leather
from .order import Order, OrderItem
from .product import Product
from .recipe import Recipe, RecipeItem
from .shopping_list import ShoppingList, ShoppingListItem
from .supplier import Supplier
from .transaction import InventoryTransaction, LeatherTransaction
from .enums import (
    InventoryStatus,
    ProductionStatus,
    TransactionType,
    OrderStatus,
    PaymentStatus
)

# List of all model classes for easy reference
__all__ = [
    'Storage', 'Part', 'Leather', 'Order', 'OrderItem',
    'Product', 'Recipe', 'RecipeItem', 'ShoppingList',
    'ShoppingListItem', 'Supplier', 'InventoryTransaction',
    'LeatherTransaction', 'InventoryStatus', 'ProductionStatus',
    'TransactionType', 'OrderStatus', 'PaymentStatus'
]