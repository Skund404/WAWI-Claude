# Path: services/interfaces/compatibility.py
"""
Compatibility module for service interfaces.

This module provides aliases for service interfaces to maintain compatibility
with different parts of the application.
"""

import logging

# Import service interfaces
try:
    from .material_service import IMaterialService
    from .material_service import IMaterialService as MaterialService  # Alias

    from .order_service import IOrderService
    from .order_service import IOrderService as OrderService  # Alias

    from .project_service import IProjectService
    from .project_service import IProjectService as ProjectService  # Alias

    from .inventory_service import IInventoryService
    from .inventory_service import IInventoryService as InventoryService  # Alias

    from .storage_service import IStorageService
    from .storage_service import IStorageService as StorageService  # Alias

    from .pattern_service import IPatternService
    from .pattern_service import IPatternService as PatternService  # Alias

    from .hardware_service import IHardwareService
    from .hardware_service import IHardwareService as HardwareService  # Alias

    from .supplier_service import ISupplierService
    from .supplier_service import ISupplierService as SupplierService  # Alias

    from .shopping_list_service import IShoppingListService
    from .shopping_list_service import IShoppingListService as ShoppingListService  # Alias

    logging.info("Loaded service interface compatibility aliases")
except ImportError as e:
    logging.error(f"Failed to load service interface compatibility aliases: {e}")