# store_management/services/__init__.py
"""
Services package initialization.

Provides centralized imports and lazy loading of service interfaces.
"""

from utils.circular_import_resolver import CircularImportResolver

# Lazy import registration for service interfaces
CircularImportResolver.register_lazy_import(
    'IMaterialService',  # target_name
    'services.interfaces.material_service',  # module_path
    'IMaterialService'  # class_name
)

CircularImportResolver.register_lazy_import(
    'IOrderService',
    'services.interfaces.order_service',
    'IOrderService'
)

CircularImportResolver.register_lazy_import(
    'IProjectService',
    'services.interfaces.project_service',
    'IProjectService'
)

CircularImportResolver.register_lazy_import(
    'IInventoryService',
    'services.interfaces.inventory_service',
    'IInventoryService'
)

CircularImportResolver.register_lazy_import(
    'IStorageService',
    'services.interfaces.storage_service',
    'IStorageService'
)

# Define lazily loaded service implementations
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

StorageService = lambda: CircularImportResolver.lazy_import(
    'services.implementations.storage_service',
    'StorageService'
)

HardwareService = lambda: CircularImportResolver.lazy_import(
    'services.implementations.hardware_service',
    'HardwareService'
)

# Add any additional service imports or configurations as needed