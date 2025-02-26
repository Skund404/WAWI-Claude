# di/setup.py
"""
Setup module for dependency injection.
"""

import logging
from typing import Optional, Any

# Import service interfaces
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService

# Import concrete service implementations
from services.implementations.inventory_service import InventoryService
from services.implementations.material_service import MaterialService
from services.implementations.order_service import OrderService
from services.implementations.project_service import ProjectService
from services.implementations.storage_service import StorageService

# Import container
from di.container import DependencyContainer

# Configure logger
logger = logging.getLogger(__name__)


def setup_dependency_injection(container: Optional[DependencyContainer] = None) -> DependencyContainer:
    """
    Set up dependency injection for the application.

    Args:
        container: Optional existing container. If None, a new one is created.

    Returns:
        Configured dependency injection container
    """
    # Create a new container if one was not provided
    if container is None:
        container = DependencyContainer()

    # Register services
    container.register(IInventoryService, InventoryService)
    container.register(IMaterialService, MaterialService)
    container.register(IOrderService, OrderService)
    container.register(IProjectService, ProjectService)
    container.register(IStorageService, StorageService)

    logger.info("Dependency injection setup completed")

    return container