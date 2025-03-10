"""
Dependency Injection Configuration.

Provides centralized configuration for service registrations.
"""

from typing import Dict, Any, Optional, Type, List

# Service mappings - using simple interface names
SERVICE_MAPPINGS = {
    # Real implementations (uncomment when implemented)
    # 'IPatternService': 'services.implementations.pattern_service.PatternService',
    # 'IToolListService': 'services.implementations.tool_list_service.ToolListService',
    # 'IMaterialService': 'services.implementations.material_service.MaterialService',
    # 'ICustomerService': 'services.implementations.customer_service.CustomerService',
    # 'IProjectService': 'services.implementations.project_service.ProjectService',
    # 'IInventoryService': 'services.implementations.inventory_service.InventoryService',
    # 'ISalesService': 'services.implementations.sales_service.SalesService',
    # 'ISupplierService': 'services.implementations.supplier_service.SupplierService',

    # Using mocks (remove these lines when real implementations are ready)
    'IPatternService': None,  # Using mock implementation
    'IToolListService': None,  # Using mock implementation
    'IMaterialService': None,  # Using mock implementation
    'ICustomerService': None,  # Using mock implementation
    'IProjectService': None,  # Using mock implementation
    'IInventoryService': None,  # Using mock implementation
    'ISalesService': None,  # Using mock implementation
    'ISupplierService': None,  # Using mock implementation
}

# Repository mappings - keep what we know exists
REPOSITORY_MAPPINGS = [
    # Base repositories
    'database.repositories.base_repository.BaseRepository',

    # Main entity repositories
    'database.repositories.customer_repository.CustomerRepository',
    'database.repositories.material_repository.MaterialRepository',
    'database.repositories.product_repository.ProductRepository',
    'database.repositories.pattern_repository.PatternRepository',
    'database.repositories.project_repository.ProjectRepository',
    'database.repositories.supplier_repository.SupplierRepository',
    'database.repositories.tool_repository.ToolRepository',
    'database.repositories.inventory_repository.InventoryRepository',
    'database.repositories.sales_repository.SalesRepository',
    'database.repositories.purchase_repository.PurchaseRepository',

    # Material type repositories
    'database.repositories.leather_repository.LeatherRepository',
    'database.repositories.hardware_repository.HardwareRepository',
    'database.repositories.supplies_repository.SuppliesRepository',

    # Component repositories
    'database.repositories.component_repository.ComponentRepository',

    # Transaction item repositories
    'database.repositories.sales_item_repository.SalesItemRepository',
    'database.repositories.purchase_item_repository.PurchaseItemRepository',

    # Production related repositories
    'database.repositories.picking_list_repository.PickingListRepository',
    'database.repositories.tool_list_repository.ToolListRepository',
]

# Database session configuration
DATABASE_SESSION_CONFIG = {
    'module': 'database.sqlalchemy.session',
    'factory_function': None  # We'll handle this in the setup code
}