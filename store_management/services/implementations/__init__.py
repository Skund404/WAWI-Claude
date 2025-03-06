# store_management/services/implementations/__init__.py
"""
Services Implementations Package Initialization.

Provides centralized imports and lazy loading of service implementations.
"""

from utils.circular_import_resolver import register_lazy_import, lazy_import

# Lazy import registration for service implementations
register_lazy_import(
    'services.implementations.material_service',
    'MaterialService',
    'MaterialService'
)

register_lazy_import(
    'services.implementations.order_service',
    'SaleService',
    'SaleService'
)

register_lazy_import(
    'services.implementations.project_service',
    'ProjectService',
    'ProjectService'
)

register_lazy_import(
    'services.implementations.inventory_service',
    'InventoryService',
    'InventoryService'
)

register_lazy_import(
    'services.implementations.storage_service',
    'StorageService',
    'StorageService'
)

# Convenient exports - using lazy_import instead of get_lazy_import
MaterialService = lambda: lazy_import('services.implementations.material_service', 'MaterialService')
OrderService = lambda: lazy_import('services.implementations.order_service', 'SaleService')
ProjectService = lambda: lazy_import('services.implementations.project_service', 'ProjectService')
InventoryService = lambda: lazy_import('services.implementations.inventory_service', 'InventoryService')
StorageService = lambda: lazy_import('services.implementations.storage_service', 'StorageService')

# These will be used in other parts of the project
__all__ = [
    'MaterialService',
    'OrderService',
    'ProjectService',
    'InventoryService',
    'StorageService'
]