# store_management/services/__init__.py
"""
Services package initialization.

Provides centralized imports and lazy loading of service interfaces.
"""

from utils.circular_import_resolver import CircularImportResolver

# Lazy import registration for service interfaces
CircularImportResolver.register_lazy_import(
    'IMaterialService',
    lambda: CircularImportResolver.lazy_import(
        'services.interfaces.material_service',
        'IMaterialService'
    )
)

CircularImportResolver.register_lazy_import(
    'IOrderService',
    lambda: CircularImportResolver.lazy_import(
        'services.interfaces.order_service',
        'IOrderService'
    )
)

CircularImportResolver.register_lazy_import(
    'IProjectService',
    lambda: CircularImportResolver.lazy_import(
        'services.interfaces.project_service',
        'IProjectService'
    )
)

CircularImportResolver.register_lazy_import(
    'IInventoryService',
    lambda: CircularImportResolver.lazy_import(
        'services.interfaces.inventory_service',
        'IInventoryService'
    )
)

CircularImportResolver.register_lazy_import(
    'IStorageService',
    lambda: CircularImportResolver.lazy_import(
        'services.interfaces.storage_service',
        'IStorageService'
    )
)

# Define lazily loaded exports
MaterialService = lambda: CircularImportResolver.lazy_import(
    'services.implementations.material_service',
    'MaterialService'
)

ProjectService = lambda: CircularImportResolver.lazy_import(
    'services.implementations.project_service',
    'ProjectService'
)

InventoryService = lambda: CircularImportResolver.lazy_import(
    'services.implementations.inventory_service',
    'InventoryService'
)

OrderService = lambda: CircularImportResolver.lazy_import(
    'services.implementations.order_service',
    'OrderService'
)