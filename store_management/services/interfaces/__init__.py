# store_management/services/interfaces/__init__.py
"""
Services Interfaces Package Initialization.

Provides centralized imports and lazy loading of service interfaces.
"""

from utils.circular_import_resolver import CircularImportResolver

# Base Service Interface
from .base_service import IBaseService

# Lazy import registration for service interfaces
def _lazy_import(module_path: str, class_name: str):
    """
    Lazy import helper function.

    Args:
        module_path (str): Full module path to import
        class_name (str): Specific class to import

    Returns:
        Any: Imported class
    """
    return CircularImportResolver.lazy_import(module_path, class_name)

# Import and export service interfaces
IMaterialService = lambda: _lazy_import('services.interfaces.material_service', 'IMaterialService')
MaterialType = lambda: _lazy_import('services.interfaces.material_service', 'MaterialType')

IOrderService = lambda: _lazy_import('services.interfaces.order_service', 'IOrderService')
OrderStatus = lambda: _lazy_import('services.interfaces.order_service', 'OrderStatus')
PaymentStatus = lambda: _lazy_import('services.interfaces.order_service', 'PaymentStatus')

IProjectService = lambda: _lazy_import('services.interfaces.project_service', 'IProjectService')
ProjectType = lambda: _lazy_import('services.interfaces.project_service', 'ProjectType')
SkillLevel = lambda: _lazy_import('services.interfaces.project_service', 'SkillLevel')

IInventoryService = lambda: _lazy_import('services.interfaces.inventory_service', 'IInventoryService')
IStorageService = lambda: _lazy_import('services.interfaces.storage_service', 'IStorageService')
IPatternService = lambda: _lazy_import('services.interfaces.pattern_service', 'IPatternService')
IHardwareService = lambda: _lazy_import('services.interfaces.hardware_service', 'IHardwareService')
ISupplierService = lambda: _lazy_import('services.interfaces.supplier_service', 'ISupplierService')
IShoppingListService = lambda: _lazy_import('services.interfaces.shopping_list_service', 'IShoppingListService')

# Collect all service interfaces
__all__ = [
    'IBaseService',
    'IMaterialService', 'MaterialType',
    'IOrderService', 'OrderStatus', 'PaymentStatus',
    'IProjectService', 'ProjectType', 'SkillLevel',
    'IInventoryService',
    'IStorageService',
    'IPatternService',
    'IHardwareService',
    'ISupplierService',
    'IShoppingListService'
]