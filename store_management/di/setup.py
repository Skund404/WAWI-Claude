# di/setup.py
"""
Dependency Injection setup for the leatherworking store management application.
"""

import logging

# Database Session
from database.session import get_db_session

# Services Interfaces
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.inventory_service import IInventoryService

# Services Implementations
from services.implementations.material_service import MaterialServiceImpl
from services.implementations.order_service import OrderServiceImpl
from services.implementations.project_service import ProjectServiceImpl
from services.implementations.inventory_service import InventoryServiceImpl

def setup_dependency_injection() -> None:
    """
    Set up dependency injection for the application services.

    This function registers the concrete service implementations
    with their respective interfaces in the dependency injection container.
    """
    try:
        from di.container import DependencyContainer

        # Get database session
        session = get_db_session()

        # Register service implementations
        DependencyContainer.register(IMaterialService, MaterialServiceImpl(session))
        DependencyContainer.register(IOrderService, OrderServiceImpl(session))
        DependencyContainer.register(IProjectService, ProjectServiceImpl(session))
        DependencyContainer.register(IInventoryService, InventoryServiceImpl(session))

        logging.info("Dependency injection setup completed successfully")
    except Exception as e:
        logging.error(f"Error setting up dependency injection: {e}")
        raise

# Optional: Can be called directly to ensure services are registered
if __name__ == "__main__":
    setup_dependency_injection()