# Path: services/interfaces/compatibility.py
"""
Compatibility module for service interfaces.

This module provides aliases for service interfaces to maintain compatibility
with different parts of the application.
"""

import logging

# Import service interfaces
try:
    # services/compatibility.py
    """
    Compatibility module providing aliases for service interfaces to maintain 
    backward compatibility with existing code.
    """

    # Import interfaces using direct paths to avoid circular imports
    from .interfaces.hardware_service import IHardwareService as HardwareService
    from .interfaces.inventory_service import IInventoryService as InventoryService
    from .interfaces.material_service import IMaterialService as MaterialService
    from .interfaces.sale_service import ISaleService as OrderService
    from .interfaces.pattern_service import IPatternService as PatternService
    from .interfaces.project_service import IProjectService as ProjectService
    from .interfaces.shopping_list_service import IShoppingListService as ShoppingListService
    from .interfaces.storage_service import IStorageService as StorageService
    from .interfaces.supplier_service import ISupplierService as SupplierService

    # Import type definitions for backward compatibility
    from .interfaces.material_service import MaterialType
    from .interfaces.sale_service import SaleStatus, PaymentStatus
    from .interfaces.pattern_service import PatternStatus
    from .interfaces.project_service import ProjectType, SkillLevel
    from .interfaces.shopping_list_service import ShoppingListStatus
    from .interfaces.storage_service import StorageLocationType, StorageCapacityStatus
    from .interfaces.supplier_service import SupplierStatus

    logging.info("Loaded service interface compatibility aliases")
except ImportError as e:
    logging.error(f"Failed to load service interface compatibility aliases: {e}")