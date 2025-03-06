# services/interfaces/__init__.py
from utils.circular_import_resolver import register_lazy_import, resolve_lazy_import
import logging
import sys
from typing import Any, Dict, List, Optional, Type

# Define module paths for services
MODULE_PATHS = {
    "IBaseService": "services.interfaces.base_service",
    "IHardwareService": "services.interfaces.hardware_service",
    "IInventoryService": "services.interfaces.inventory_service",
    "IMaterialService": "services.interfaces.material_service",
    "MaterialType": "services.interfaces.material_service",
    "IOrderService": "services.interfaces.order_service",
    "OrderStatus": "services.interfaces.order_service",
    "PaymentStatus": "services.interfaces.order_service",
    "IPatternService": "services.interfaces.pattern_service",
    "PatternStatus": "services.interfaces.pattern_service",
    "IProjectService": "services.interfaces.project_service",
    "ProjectType": "services.interfaces.project_service",
    "SkillLevel": "services.interfaces.project_service",
    "IShoppingListService": "services.interfaces.shopping_list_service",
    "ShoppingListStatus": "services.interfaces.shopping_list_service",
    "IStorageService": "services.interfaces.storage_service",
    "StorageCapacityStatus": "services.interfaces.storage_service",
    "StorageLocationType": "services.interfaces.storage_service",
    "ISupplierService": "services.interfaces.supplier_service",
    "SupplierStatus": "services.interfaces.supplier_service"
}

# Register lazy imports to break circular dependencies
for name, module_path in MODULE_PATHS.items():
    register_lazy_import(
        target_name=name,
        module_path=module_path,
        class_name=name
    )

# Add a function to resolve lazy imports
def resolve_lazy_import_safe(import_path):
    """Resolve a lazily imported module or class."""
    try:
        return resolve_lazy_import(import_path)
    except ImportError as e:
        logging.warning(f"Failed to resolve lazy import {import_path}: {e}")
        return None

# Export all interfaces and types as lambda functions for lazy loading
INTERFACES = {name: lambda n=name: resolve_lazy_import_safe(n) for name in MODULE_PATHS}

# Import from compatibility module if needed
try:
    from ..compatibility import *
except ImportError as e:
    logging.warning(f"Failed to import compatibility module: {e}")

# Optionally, export specific interfaces for direct import
__all__ = list(INTERFACES.keys())