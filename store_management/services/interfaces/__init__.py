"""
Interfaces for all services used in the application.

This module exports all service interfaces to make them accessible
with simplified imports like `from services.interfaces import IMaterialService`.

Note: We use explicit imports rather than wildcard imports to avoid circular dependencies.
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Type

# Try to import the circular import resolver
try:
    from utils.circular_import_resolver import (
        CircularImportResolver,
        register_lazy_import,
        resolve_lazy_import
    )
    resolver_available = True
except ImportError:
    logging.warning("CircularImportResolver not available. Using direct imports.")
    resolver_available = False

    # Create placeholder functions
    def register_lazy_import(import_path, loader_func=None):
        pass

    def resolve_lazy_import(import_path):
        return None


# Dictionary mapping interface names to their import paths
INTERFACES = {
    'IBaseService': 'services.interfaces.base_service.IBaseService',
    'IMaterialService': 'services.interfaces.material_service.IMaterialService',
    'MaterialType': 'services.interfaces.material_service.MaterialType',
    'IOrderService': 'services.interfaces.order_service.IOrderService',
    'OrderStatus': 'services.interfaces.order_service.OrderStatus',
    'PaymentStatus': 'services.interfaces.order_service.PaymentStatus',
    'IProjectService': 'services.interfaces.project_service.IProjectService',
    'ProjectType': 'services.interfaces.project_service.ProjectType',
    'SkillLevel': 'services.interfaces.project_service.SkillLevel',
    'IInventoryService': 'services.interfaces.inventory_service.IInventoryService',
    'IStorageService': 'services.interfaces.storage_service.IStorageService',
    'StorageLocationType': 'services.interfaces.storage_service.StorageLocationType',
    'StorageCapacityStatus': 'services.interfaces.storage_service.StorageCapacityStatus',
    'IPatternService': 'services.interfaces.pattern_service.IPatternService',
    'PatternStatus': 'services.interfaces.pattern_service.PatternStatus',
    'IHardwareService': 'services.interfaces.hardware_service.IHardwareService',
    'HardwareType': 'services.interfaces.hardware_service.HardwareType',
    'HardwareMaterial': 'services.interfaces.hardware_service.HardwareMaterial',
    'ISupplierService': 'services.interfaces.supplier_service.ISupplierService',
    'SupplierStatus': 'services.interfaces.supplier_service.SupplierStatus',
    'IShoppingListService': 'services.interfaces.shopping_list_service.IShoppingListService',
    'ShoppingListStatus': 'services.interfaces.shopping_list_service.ShoppingListStatus',
}


# Register all interfaces for lazy imports if the resolver is available
if resolver_available:
    for name, path in INTERFACES.items():
        register_lazy_import(path)


# Direct imports for the interfaces - using try/except for each to avoid
# one bad import breaking everything
try:
    from .base_service import IBaseService
except ImportError as e:
    logging.warning(f"Failed to import IBaseService: {e}")
    IBaseService = None

try:
    from .material_service import IMaterialService, MaterialType
except ImportError as e:
    logging.warning(f"Failed to import IMaterialService: {e}")
    IMaterialService = None
    MaterialType = None

try:
    from .order_service import IOrderService, OrderStatus, PaymentStatus
except ImportError as e:
    logging.warning(f"Failed to import IOrderService: {e}")
    IOrderService = None
    OrderStatus = None
    PaymentStatus = None

try:
    from .project_service import IProjectService, ProjectType, SkillLevel
except ImportError as e:
    logging.warning(f"Failed to import IProjectService: {e}")
    IProjectService = None
    ProjectType = None
    SkillLevel = None

try:
    from .inventory_service import IInventoryService
except ImportError as e:
    logging.warning(f"Failed to import IInventoryService: {e}")
    IInventoryService = None

try:
    from .storage_service import IStorageService, StorageLocationType, StorageCapacityStatus
except ImportError as e:
    logging.warning(f"Failed to import IStorageService: {e}")
    IStorageService = None
    StorageLocationType = None
    StorageCapacityStatus = None

try:
    from .pattern_service import IPatternService, PatternStatus
except ImportError as e:
    logging.warning(f"Failed to import IPatternService: {e}")
    IPatternService = None
    PatternStatus = None

try:
    from .hardware_service import IHardwareService, HardwareType, HardwareMaterial
except ImportError as e:
    logging.warning(f"Failed to import IHardwareService: {e}")
    IHardwareService = None
    HardwareType = None
    HardwareMaterial = None

try:
    from .supplier_service import ISupplierService, SupplierStatus
except ImportError as e:
    logging.warning(f"Failed to import ISupplierService: {e}")
    ISupplierService = None
    SupplierStatus = None

try:
    from .shopping_list_service import IShoppingListService, ShoppingListStatus
except ImportError as e:
    logging.warning(f"Failed to import IShoppingListService: {e}")
    IShoppingListService = None
    ShoppingListStatus = None

# Import compatibility module for backward compatibility
try:
    from . import compatibility

    # Add compatibility aliases for services that use old naming conventions
    # This provides backward compatibility for code that imports MaterialService
    # instead of IMaterialService
    MaterialService = compatibility.MaterialService
    OrderService = compatibility.OrderService
    ProjectService = compatibility.ProjectService
    InventoryService = compatibility.InventoryService
    StorageService = compatibility.StorageService
    PatternService = compatibility.PatternService
    HardwareService = compatibility.HardwareService
    SupplierService = compatibility.SupplierService
    ShoppingListService = compatibility.ShoppingListService

    logging.info("Backward compatibility aliases loaded")
except ImportError as e:
    logging.warning(f"Failed to import compatibility module: {e}")
    # If the compatibility module failed to load, provide minimalist compatibility
    MaterialService = IMaterialService if 'IMaterialService' in locals() else None
    OrderService = IOrderService if 'IOrderService' in locals() else None
    ProjectService = IProjectService if 'IProjectService' in locals() else None
    InventoryService = IInventoryService if 'IInventoryService' in locals() else None
    StorageService = IStorageService if 'IStorageService' in locals() else None
    PatternService = IPatternService if 'IPatternService' in locals() else None
    HardwareService = IHardwareService if 'IHardwareService' in locals() else None
    SupplierService = ISupplierService if 'ISupplierService' in locals() else None
    ShoppingListService = IShoppingListService if 'IShoppingListService' in locals() else None

# Lazy getters for interfaces that might have circular dependencies
def get_interface(name: str) -> Optional[Type]:
    """
    Get an interface class by name.

    Args:
        name: Name of the interface to retrieve

    Returns:
        The interface class or None if not found
    """
    # First check if the interface is already imported directly
    if name in globals() and globals()[name] is not None:
        return globals()[name]

    # Then try lazy loading
    if name not in INTERFACES:
        logging.error(f"Unknown interface: {name}")
        return None

    path = INTERFACES[name]

    try:
        if resolver_available:
            # Try to use the resolver
            return resolve_lazy_import(path)
        else:
            # Fall back to standard import
            module_path, class_name = path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logging.error(f"Failed to retrieve interface {name}: {e}")
        return None


# Add getter methods for each interface to the module globals
for name in INTERFACES:
    # Create a dynamic getter function that captures the name properly
    globals()[f"get_{name}"] = (lambda n=name: lambda: get_interface(n))()


# Define what gets imported with "from services.interfaces import *"
__all__ = list(INTERFACES.keys()) + [f"get_{name}" for name in INTERFACES.keys()] + [
    # Add backward compatibility aliases to __all__
    'MaterialService',
    'OrderService',
    'ProjectService',
    'InventoryService',
    'StorageService',
    'PatternService',
    'HardwareService',
    'SupplierService',
    'ShoppingListService'
]