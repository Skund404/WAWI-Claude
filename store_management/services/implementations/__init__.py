# store_management/services/implementations/__init__.py
"""
Services Implementations Package Initialization.

Provides centralized imports and lazy loading of service implementations.
"""

from utils.circular_import_resolver import CircularImportResolver

# Lazy import registration for service implementations
CircularImportResolver.register_lazy_import(
    'MaterialService',
    lambda: CircularImportResolver.lazy_import(
        'services.implementations.material_service',
        'MaterialService'
    )
)

CircularImportResolver.register_lazy_import(
    'OrderService',
    lambda: CircularImportResolver.lazy_import(
        'services.implementations.order_service',
        'OrderService'
    )
)

CircularImportResolver.register_lazy_import(
    'ProjectService',
    lambda: CircularImportResolver.lazy_import(
        'services.implementations.project_service',
        'ProjectService'
    )
)

CircularImportResolver.register_lazy_import(
    'InventoryService',
    lambda: CircularImportResolver.lazy_import(
        'services.implementations.inventory_service',
        'InventoryService'
    )
)

CircularImportResolver.register_lazy_import(
    'StorageService',
    lambda: CircularImportResolver.lazy_import(
        'services.implementations.storage_service',
        'StorageService'
    )
)

# Convenient exports
MaterialService = lambda: CircularImportResolver.get_lazy_import('MaterialService')
OrderService = lambda: CircularImportResolver.get_lazy_import('OrderService')
ProjectService = lambda: CircularImportResolver.get_lazy_import('ProjectService')
InventoryService = lambda: CircularImportResolver.get_lazy_import('InventoryService')
StorageService = lambda: CircularImportResolver.get_lazy_import('StorageService')

# These will be used in other parts of the project
__all__ = [
    'MaterialService',
    'OrderService',
    'ProjectService',
    'InventoryService',
    'StorageService'
]