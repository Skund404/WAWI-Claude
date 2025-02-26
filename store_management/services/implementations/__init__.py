# services/implementations/__init__.py
"""
Service implementations module.
Contains concrete implementations of service interfaces.
"""

import logging
from abc import ABC, abstractmethod

# Import concrete service implementations
from services.implementations.inventory_service import InventoryService
from services.implementations.material_service import MaterialService
from services.implementations.order_service import OrderService
from services.implementations.project_service import ProjectService
from services.implementations.storage_service import StorageService

# Import service interfaces for type hints
from services.interfaces import (
    IMaterialService,
    IProjectService,
    IOrderService,
    IInventoryService,
    IStorageService
)

# Configure logger
logger = logging.getLogger(__name__)

# Re-export services for easy imports
__all__ = [
    'InventoryService',
    'MaterialService',
    'OrderService',
    'ProjectService',
    'StorageService'
]


# Stub implementations for fallback during development

class StubServiceImpl:
    """Stub implementation for services that could not be imported."""

    def __init__(self):
        logger.warning(f"Using stub implementation of {self.__class__.__name__}")


class MaterialServiceStub(StubServiceImpl, IMaterialService):
    """Stub implementation of MaterialService."""

    def get_all_materials(self):
        """Return empty list of materials."""
        return []


class ProjectServiceStub(StubServiceImpl, IProjectService):
    """Stub implementation of ProjectService."""

    def get_all_projects(self):
        """Return empty list of projects."""
        return []


class OrderServiceStub(StubServiceImpl, IOrderService):
    """Stub implementation of OrderService."""

    def get_all_orders(self):
        """Return empty list of orders."""
        return []


class InventoryServiceStub(StubServiceImpl, IInventoryService):
    """Stub implementation of InventoryService."""

    def get_inventory_status(self):
        """Return empty inventory status."""
        return {}


class StorageServiceStub(StubServiceImpl, IStorageService):
    """Stub implementation of StorageService."""

    def get_all_storage_locations(self):
        """Return empty list of storage locations."""
        return []