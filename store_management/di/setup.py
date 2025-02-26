# di/setup.py
"""
Dependency Injection Setup for the Leatherworking Store Management Application.

This module configures the dependency injection container
by registering service implementations and their dependencies.
"""

import logging
from typing import Any, Optional

from di.container import DependencyContainer

# Import services and interfaces
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService

# Import service implementations
from services.implementations.inventory_service import InventoryService
from services.implementations.material_service import MaterialService
from services.implementations.order_service import OrderService
from services.implementations.project_service import ProjectService
from services.implementations.storage_service import StorageService

# Import repositories
from database.repositories.order_repository import OrderRepository
from database.sqlalchemy.session import get_db_session


def setup_dependency_injection(db_session: Any = None) -> DependencyContainer:
    """
    Set up the dependency injection container.

    Args:
        db_session (Any, optional): Database session to use for repositories.
                                    If None, a new session will be created.

    Returns:
        DependencyContainer: Configured dependency injection container
    """
    try:
        # Get the singleton container instance
        container = DependencyContainer()

        # Reset any existing registrations
        container.reset()

        # Create logger
        logger = logging.getLogger(__name__)
        logger.info("Setting up dependency injection...")

        # Ensure we have a database session
        if db_session is None:
            db_session = get_db_session()

        # Create repositories with the database session
        order_repository = OrderRepository(db_session)

        # Register service implementations with their dependencies
        container.register(
            IInventoryService,
            lambda: InventoryService()
        )

        container.register(
            IMaterialService,
            lambda: MaterialService()
        )

        container.register(
            IOrderService,
            lambda: OrderService(order_repository)
        )

        container.register(
            IProjectService,
            lambda: ProjectService()
        )

        container.register(
            IStorageService,
            lambda: StorageService()
        )

        logger.info("Dependency injection setup completed")
        return container

    except Exception as e:
        logger.error(f"Error setting up dependency injection: {e}")
        raise