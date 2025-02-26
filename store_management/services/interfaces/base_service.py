# services/interfaces/base_service.py
"""
Base interface for all service interfaces in the leatherworking store management system.
Defines common operations that all services should implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Type variable for generic service operations
T = TypeVar('T')


class IBaseService(ABC, Generic[T]):
    """Base interface for all services. Generic type T represents the primary entity type."""

    @abstractmethod
    def get_by_id(self, id_value: Any) -> Dict[str, Any]:
        """
        Retrieve an entity by its ID.

        Args:
            id_value: ID of the entity to retrieve

        Returns:
            Dictionary representation of the entity

        Raises:
            NotFoundError: If entity not found
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Retrieve all entities.

        Returns:
            List of dictionaries representing entities
        """
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity.

        Args:
            data: Dictionary with entity properties

        Returns:
            Dictionary representation of the created entity

        Raises:
            ValidationError: If entity data is invalid
        """
        pass

    @abstractmethod
    def update(self, id_value: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing entity.

        Args:
            id_value: ID of the entity to update
            data: Dictionary with updated entity properties

        Returns:
            Dictionary representation of the updated entity

        Raises:
            NotFoundError: If entity not found
            ValidationError: If entity data is invalid
        """
        pass

    @abstractmethod
    def delete(self, id_value: Any) -> bool:
        """
        Delete an entity.

        Args:
            id_value: ID of the entity to delete

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If entity not found
        """
        pass