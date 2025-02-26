# gui/inventory/__init__.py
"""
Package for inventory-related view components of the leatherworking store management system.
"""

from .hardware_inventory import HardwareInventoryView
from .product_inventory import ProductInventoryView

__all__ = ['HardwareInventoryView', 'ProductInventoryView']