# di/service_configuration.py
"""
Dependency Configuration for Services
Uses the CircularImportResolver for lazy loading and dependency management
"""

from di.container import DependencyContainer
from utils.circular_import_resolver import (
    register_lazy_import,
    lazy_import
)
from typing import Callable, Any

# Define service mappings for lazy loading
SERVICE_MAPPINGS = {
    # Product Pattern Service
    'IProductPatternService': {
        'interface': 'services.interfaces.product_pattern_service.IProductPatternService',
        'implementation': 'services.implementations.product_pattern_service.ProductPatternService'
    },
    # Component Service
    'IComponentService': {
        'interface': 'services.interfaces.component_service.IComponentService',
        'implementation': 'services.implementations.component_service.ComponentService'
    },
    # Transaction Services
    'IMaterialTransactionService': {
        'interface': 'services.interfaces.transaction_service.IMaterialTransactionService',
        'implementation': 'services.implementations.transaction_service.MaterialTransactionService'
    },
    'ILeatherTransactionService': {
        'interface': 'services.interfaces.transaction_service.ILeatherTransactionService',
        'implementation': 'services.implementations.transaction_service.LeatherTransactionService'
    },
    'IHardwareTransactionService': {
        'interface': 'services.interfaces.transaction_service.IHardwareTransactionService',
        'implementation': 'services.implementations.transaction_service.HardwareTransactionService'
    },
    # Picking List Service
    'IPickingListService': {
        'interface': 'services.interfaces.picking_list_service.IPickingListService',
        'implementation': 'services.implementations.picking_list_service.PickingListService'
    },
    # Tool List Service
    'IToolListService': {
        'interface': 'services.interfaces.tool_list_service.IToolListService',
        'implementation': 'services.implementations.tool_list_service.ToolListService'
    },
    # Project Component Service
    'IProjectComponentService': {
        'interface': 'services.interfaces.project_component_service.IProjectComponentService',
        'implementation': 'services.implementations.project_component_service.ProjectComponentService'
    },
    # Supplier Service
    'ISupplierService': {
        'interface': 'services.interfaces.supplier_service.ISupplierService',
        'implementation': 'services.implementations.supplier_service.SupplierService'
    },
    # Project Service
    'IProjectService': {
        'interface': 'services.interfaces.project_service.IProjectService',
        'implementation': 'services.implementations.project_service.ProjectService'
    },
    # Sales Service
    'ISalesService': {
        'interface': 'services.interfaces.sales_service.ISalesService',
        'implementation': 'services.implementations.sales_service.SalesService'
    },
    # Purchase Service
    'IPurchaseService': {
        'interface': 'services.interfaces.purchase_service.IPurchaseService',
        'implementation': 'services.implementations.purchase_service.PurchaseService'
    }
}


def create_lazy_registration(
        container: DependencyContainer,
        service_key: str
) -> Callable:
    """
    Create a lazy registration function for service instantiation.

    Args:
        container (DependencyContainer): Dependency injection container
        service_key (str): Key for the service in SERVICE_MAPPINGS

    Returns:
        Callable: Lazy registration function
    """

    def lazy_loader() -> Any:
        # Retrieve service configuration
        service_config = SERVICE_MAPPINGS.get(service_key, {})

        # Register lazy imports
        register_lazy_import(
            service_config['interface'],
            '.'.join(service_config['interface'].split('.')[:-1]),
            service_config['interface'].split('.')[-1]
        )
        register_lazy_import(
            service_config['implementation'],
            '.'.join(service_config['implementation'].split('.')[:-1]),
            service_config['implementation'].split('.')[-1]
        )

        # Resolve and return the implementation
        return lazy_import(
            service_config['implementation']
        )

    return lazy_loader


def register_project_services(container: DependencyContainer) -> None:
    """
    Register all project services with lazy loading.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    for service_key in SERVICE_MAPPINGS:
        container.register_lazy(
            service_key,
            create_lazy_registration(container, service_key)
        )


def setup_di() -> DependencyContainer:
    """
    Set up dependency injection container with service configurations.

    Returns:
        DependencyContainer: Configured dependency injection container
    """
    container = DependencyContainer()
    register_project_services(container)
    return container