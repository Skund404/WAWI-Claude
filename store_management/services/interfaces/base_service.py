# services/interfaces/base_service.py
"""
Base interfaces for service implementations.

This module provides foundational interfaces for services, ensuring
consistent service patterns across the application.
"""

import abc
from typing import Any, Dict, Generic, List, Optional, TypeVar
from typing import Callable

T = TypeVar('T')


class IBaseService(abc.ABC):
    """
    Interface for base service operations with generic type support.

    Provides a standardized interface for core service methods.
    """

    @abc.abstractmethod
    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data (Dict[str, Any]): Data for creating the entity

        Returns:
            T: Created entity

        Raises:
            ValidationError: If data is invalid
        """
        pass

    @abc.abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Retrieve an entity by its identifier.

        Args:
            entity_id (Any): Unique identifier for the entity

        Returns:
            Optional[T]: Retrieved entity or None if not found
        """
        pass

    @abc.abstractmethod
    def update(self, entity_id: Any, data: Dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            entity_id (Any): Unique identifier for the entity
            data (Dict[str, Any]): Updated data for the entity

        Returns:
            T: Updated entity

        Raises:
            NotFoundError: If entity doesn't exist
            ValidationError: If update data is invalid
        """
        pass

    @abc.abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity by its identifier.

        Args:
            entity_id (Any): Unique identifier for the entity

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If entity doesn't exist
        """
        pass


# For backward compatibility and to match existing code
Service = IBaseService