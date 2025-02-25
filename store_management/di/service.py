# Relative path: store_management/service.py

"""
Base service class module.

Provides the foundational service class that leverages dependency injection.
"""

import abc
from typing import Generic, Type, TypeVar

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from container import DependencyContainer

# Type variable for generic dependency type
T = TypeVar('T')


class Service(abc.ABC, Generic[T]):
    """Base class for services that use dependency injection."""

    def __init__(self, container: DependencyContainer):
        """
        Initialize the service with a dependency container.

        Args:
            container: Dependency injection container
        """
        self._container = container

    def get_dependency(self, dependency_type: Type[T]) -> T:
        """
        Get a dependency from the container.

        Args:
            dependency_type: Type of dependency to retrieve

        Returns:
            Instance of the requested dependency
        """
        return self._container.resolve(dependency_type)