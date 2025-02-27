"""
Compatibility module for service interfaces.

This module provides compatibility wrappers and aliases for services
that may be using old import patterns. It helps transition from older
naming conventions to the new interface-based approach.
"""

import logging
from typing import Any, Dict, Optional, Type

# Import all interfaces
try:
    from .material_service import IMaterialService as MaterialService
    from .order_service import IOrderService as OrderService
    from .project_service import IProjectService as ProjectService
    from .inventory_service import IInventoryService as InventoryService
    from .storage_service import IStorageService as StorageService
    from .pattern_service import IPatternService as PatternService
    from .hardware_service import IHardwareService as HardwareService
    from .supplier_service import ISupplierService as SupplierService
    from .shopping_list_service import IShoppingListService as ShoppingListService

    # Also import the actual interfaces
    from .material_service import IMaterialService
    from .order_service import IOrderService
    from .project_service import IProjectService
    from .inventory_service import IInventoryService
    from .storage_service import IStorageService
    from .pattern_service import IPatternService
    from .hardware_service import IHardwareService
    from .supplier_service import ISupplierService
    from .shopping_list_service import IShoppingListService

    # Import enum types
    from .material_service import MaterialType
    from .order_service import OrderStatus, PaymentStatus
    from .project_service import ProjectType, SkillLevel
    from .storage_service import StorageLocationType, StorageCapacityStatus
    from .pattern_service import PatternStatus
    from .hardware_service import HardwareType, HardwareMaterial
    from .supplier_service import SupplierStatus
    from .shopping_list_service import ShoppingListStatus

    # Log successful import
    logging.info("Successfully loaded service interface compatibility aliases")

except ImportError as e:
    logging.error(f"Failed to load service interface compatibility aliases: {e}")

# Export all names to be accessible when importing from this module
__all__ = [
    # Interface aliases (old naming convention)
    'MaterialService',
    'OrderService',
    'ProjectService',
    'InventoryService',
    'StorageService',
    'PatternService',
    'HardwareService',
    'SupplierService',
    'ShoppingListService',

    # Actual interfaces (new naming convention)
    'IMaterialService',
    'IOrderService',
    'IProjectService',
    'IInventoryService',
    'IStorageService',
    'IPatternService',
    'IHardwareService',
    'ISupplierService',
    'IShoppingListService',

    # Enum types
    'MaterialType',
    'OrderStatus',
    'PaymentStatus',
    'ProjectType',
    'SkillLevel',
    'StorageLocationType',
    'StorageCapacityStatus',
    'PatternStatus',
    'HardwareType',
    'HardwareMaterial',
    'SupplierStatus',
    'ShoppingListStatus'
]