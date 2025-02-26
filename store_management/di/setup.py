# di/setup.py
"""
Setup module for dependency injection in the leatherworking store management application.
Registers service implementations with their interfaces.
"""

import logging
from typing import Any, Optional

from database.repositories.order_repository import OrderRepository
from database.sqlalchemy.session import get_db_session
from di.container import DependencyContainer
from services.implementations.inventory_service import InventoryService
from services.implementations.material_service import MaterialService
from services.implementations.order_service import OrderService
from services.implementations.project_service import ProjectService
from services.implementations.storage_service import StorageService
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService

# Import material management service
from services.material_management_service import MaterialManagementService

# Configure logger
logger = logging.getLogger(__name__)


def setup_dependency_injection(container: Optional[DependencyContainer] = None) -> DependencyContainer:
    """
    Set up dependency injection by registering service implementations.

    Args:
        container (Optional[DependencyContainer]): Dependency injection container to use.
                                                   If None, a new container is created.

    Returns:
        DependencyContainer: Configured dependency injection container
    """
    logger.info("Setting up dependency injection...")

    # Use provided container or create a new one
    if container is None:
        container = DependencyContainer()

    # Reset container to clear any existing registrations
    container.reset()

    try:
        # Material Management Service (standalone)
        material_management_service = MaterialManagementService()

        # Register services using factories to ensure proper instantiation with dependencies

        # MaterialService
        container.register(
            IMaterialService,
            lambda: MaterialService(material_management_service)
        )

        # OrderService with OrderRepository dependency
        container.register(
            IOrderService,
            lambda: OrderService(
                OrderRepository(get_db_session())
            )
        )

        # ProjectService with MaterialManagementService
        container.register(
            IProjectService,
            lambda: ProjectService(material_management_service)
        )

        # InventoryService
        container.register(
            IInventoryService,
            lambda: InventoryService()
        )

        # StorageService
        container.register(
            IStorageService,
            lambda: StorageService()
        )

        logger.info("Dependency injection setup completed successfully")
        return container

    except Exception as e:
        logger.error(f"Error setting up dependency injection: {e}", exc_info=True)
        raise


def main():
    """
    Demonstration of dependency injection setup.
    Useful for testing and verifying the configuration.
    """
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Setup dependency injection
        container = setup_dependency_injection()

        # Retrieve and test services
        material_service = container.get_service(IMaterialService)
        order_service = container.get_service(IOrderService)
        project_service = container.get_service(IProjectService)

        print("Dependency Injection Test:")
        print(f"Material Service: {material_service}")
        print(f"Order Service: {order_service}")
        print(f"Project Service: {project_service}")

    except Exception as e:
        logger.error(f"Dependency injection test failed: {e}", exc_info=True)


if __name__ == '__main__':
    main()