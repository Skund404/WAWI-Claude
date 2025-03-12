"""
Dependency Injection Configuration.

Provides centralized configuration for service registrations.
"""

from typing import Dict, Optional, List

# Service mappings – map each interface to its real concrete implementation.
SERVICE_MAPPINGS: Dict[str, Optional[str]] = {
    "IPatternService": "services.implementations.pattern_service.PatternService",
    "IMaterialService": "services.implementations.material_service.MaterialService",
    "ICustomerService": "services.implementations.customer_service.CustomerService",
    "IProjectService": "services.implementations.project_service.ProjectService",
    "IInventoryService": "services.implementations.inventory_service.InventoryService",
    "ISalesService": "services.implementations.sales_service.SalesService",
    "ISupplierService": "services.implementations.supplier_service.SupplierService",
    "IToolListService": "services.implementations.tool_list_service.ToolListService",
    "ILeatherService": "services.implementations.leather_service.LeatherService",
    "IHardwareService": "services.implementations.hardware_service.HardwareService",
    "ISuppliesService": "services.implementations.supplies_service.SuppliesService",
    "IComponentService": "services.implementations.component_service.ComponentService",
    "IProductService": "services.implementations.product_service.ProductService",
    "IPurchaseService": "services.implementations.purchase_service.PurchaseService",
    "IPickingListService": "services.implementations.picking_list_service.PickingListService",
    "IToolService": "services.implementations.tool_service.ToolService",
    "IToolCheckoutService": "services.implementations.tool_checkout_service.ToolCheckoutService",
    "IToolMaintenanceService": "services.implementations.tool_maintenance_service.ToolMaintenanceService",
}

# Repository mappings remain the same.
REPOSITORY_MAPPINGS: List[str] = [
    "database.repositories.base_repository.BaseRepository",
    "database.repositories.customer_repository.CustomerRepository",
    "database.repositories.material_repository.MaterialRepository",
    "database.repositories.product_repository.ProductRepository",
    "database.repositories.pattern_repository.PatternRepository",
    "database.repositories.project_repository.ProjectRepository",
    "database.repositories.supplier_repository.SupplierRepository",
    "database.repositories.tool_repository.ToolRepository",
    "database.repositories.inventory_repository.InventoryRepository",
    "database.repositories.sales_repository.SalesRepository",
    "database.repositories.purchase_repository.PurchaseRepository",
    "database.repositories.leather_repository.LeatherRepository",
    "database.repositories.hardware_repository.HardwareRepository",
    "database.repositories.supplies_repository.SuppliesRepository",
    "database.repositories.component_repository.ComponentRepository",
    "database.repositories.project_component_repository.ProjectComponentRepository",
    "database.repositories.sales_item_repository.SalesItemRepository",
    "database.repositories.purchase_item_repository.PurchaseItemRepository",
    "database.repositories.picking_list_repository.PickingListRepository",
    "database.repositories.tool_list_repository.ToolListRepository",
]

# Database session configuration.
DATABASE_SESSION_CONFIG: Dict[str, Optional[str]] = {
    "module": "database.sqlalchemy.session",
    "factory_function": None,  # The session factory is initialized in the DI setup code.
}
