# Update services/interfaces/__init__.py

from utils.circular_import_resolver import register_lazy_import, resolve_lazy_import
import logging
import sys
from typing import Any, Dict, List, Optional, Type


# Register lazy imports to break circular dependencies
register_lazy_import(".base_service.IBaseService")
register_lazy_import(".hardware_service.IHardwareService")
register_lazy_import(".inventory_service.IInventoryService")
register_lazy_import(".material_service.IMaterialService")
register_lazy_import(".material_service.MaterialType")
register_lazy_import(".order_service.IOrderService")
register_lazy_import(".order_service.OrderStatus")
register_lazy_import(".order_service.PaymentStatus")
register_lazy_import(".pattern_service.IPatternService")
register_lazy_import(".pattern_service.PatternStatus")
register_lazy_import(".project_service.IProjectService")
register_lazy_import(".project_service.ProjectType")
register_lazy_import(".project_service.SkillLevel")
register_lazy_import(".shopping_list_service.IShoppingListService")
register_lazy_import(".shopping_list_service.ShoppingListStatus")
register_lazy_import(".storage_service.IStorageService")
register_lazy_import(".storage_service.StorageCapacityStatus")
register_lazy_import(".storage_service.StorageLocationType")
register_lazy_import(".supplier_service.ISupplierService")
register_lazy_import(".supplier_service.SupplierStatus")

# Add a function to resolve lazy imports
def resolve_lazy_import(import_path):
    """Resolve a lazily imported module or class."""
    try:
        return resolve_lazy_import(import_path)
    except ImportError as e:
        logging.warning(f"Failed to resolve lazy import {import_path}: {e}")
        return None

# Export all interfaces and types
INTERFACES = {
    "IBaseService": ".base_service.IBaseService",
    "IHardwareService": ".hardware_service.IHardwareService",
    "IInventoryService": ".inventory_service.IInventoryService",
    "IMaterialService": ".material_service.IMaterialService",
    "MaterialType": ".material_service.MaterialType",
    "IOrderService": ".order_service.IOrderService",
    "OrderStatus": ".order_service.OrderStatus",
    "PaymentStatus": ".order_service.PaymentStatus",
    "IPatternService": ".pattern_service.IPatternService",
    "PatternStatus": ".pattern_service.PatternStatus",
    "IProjectService": ".project_service.IProjectService",
    "ProjectType": ".project_service.ProjectType",
    "SkillLevel": ".project_service.SkillLevel",
    "IShoppingListService": ".shopping_list_service.IShoppingListService",
    "ShoppingListStatus": ".shopping_list_service.ShoppingListStatus",
    "IStorageService": ".storage_service.IStorageService",
    "StorageCapacityStatus": ".storage_service.StorageCapacityStatus",
    "StorageLocationType": ".storage_service.StorageLocationType",
    "ISupplierService": ".supplier_service.ISupplierService",
    "SupplierStatus": ".supplier_service.SupplierStatus"
}

# Import from compatibility module if needed
try:
    from ..compatibility import *
except ImportError as e:
    logging.warning(f"Failed to import compatibility module: {e}")