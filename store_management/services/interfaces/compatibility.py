# services/interfaces/compatibility.py
"""
Compatibility module for service interfaces and type aliases.

This module provides type aliases and compatibility imports for services
to support consistent usage across the application.
"""

from .base_service import IBaseService
from .hardware_service import IHardwareService, HardwareType, HardwareMaterial
from .inventory_service import IInventoryService
from .material_service import IMaterialService, MaterialType
from .order_service import IOrderService, OrderStatus, PaymentStatus
from .pattern_service import IPatternService, PatternStatus
from .project_service import IProjectService, ProjectType, SkillLevel
from .shopping_list_service import IShoppingListService, ShoppingListStatus
from .storage_service import IStorageService, StorageLocationType, StorageCapacityStatus
from .supplier_service import ISupplierService, SupplierStatus

# Type aliases for convenient imports
HardwareService = IHardwareService
InventoryService = IInventoryService
MaterialService = IMaterialService
OrderService = IOrderService
PatternService = IPatternService
ProjectService = IProjectService
ShoppingListService = IShoppingListService
StorageService = IStorageService
SupplierService = ISupplierService

# Export commonly used enums and types
__all__ = [
    'IBaseService',
    'HardwareService', 'HardwareType', 'HardwareMaterial',
    'InventoryService',
    'MaterialService', 'MaterialType',
    'OrderService', 'OrderStatus', 'PaymentStatus',
    'PatternService', 'PatternStatus',
    'ProjectService', 'ProjectType', 'SkillLevel',
    'ShoppingListService', 'ShoppingListStatus',
    'StorageService', 'StorageLocationType', 'StorageCapacityStatus',
    'SupplierService', 'SupplierStatus'
]