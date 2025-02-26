# services/interfaces/storage_service.py
"""
Interface definition for the storage service.
Provides functionality for managing storage locations for leatherworking materials.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from database.models.storage import Storage


class IStorageService(ABC):
    """Interface for storage service operations."""

    @abstractmethod
    def get_storage_location(self, storage_id: int) -> Dict[str, Any]:
        """
        Get details of a specific storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Dictionary with storage location details

        Raises:
            NotFoundError: If storage location not found
        """
        pass

    @abstractmethod
    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Get all storage locations.

        Returns:
            List of dictionaries with storage location details
        """
        pass

    @abstractmethod
    def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new storage location.

        Args:
            storage_data: Dictionary with storage location data

        Returns:
            Dictionary with created storage location details

        Raises:
            ValidationError: If storage data is invalid
        """
        pass

    @abstractmethod
    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            storage_id: ID of the storage location to update
            storage_data: Dictionary with updated storage location data

        Returns:
            Dictionary with updated storage location details

        Raises:
            NotFoundError: If storage location not found
            ValidationError: If storage data is invalid
        """
        pass

    @abstractmethod
    def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location.

        Args:
            storage_id: ID of the storage location to delete

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If storage location not found
        """
        pass

    @abstractmethod
    def assign_item_to_storage(self, storage_id: int, item_id: int, item_type: str) -> Dict[str, Any]:
        """
        Assign an item to a storage location.

        Args:
            storage_id: ID of the storage location
            item_id: ID of the item to assign
            item_type: Type of item ('material', 'tool', etc.)

        Returns:
            Dictionary with storage assignment details

        Raises:
            NotFoundError: If storage location or item not found
            ValidationError: If assignment is not valid
        """
        pass

    @abstractmethod
    def remove_item_from_storage(self, storage_id: int, item_id: int, item_type: str) -> bool:
        """
        Remove an item from a storage location.

        Args:
            storage_id: ID of the storage location
            item_id: ID of the item to remove
            item_type: Type of item ('material', 'tool', etc.)

        Returns:
            True if removal was successful

        Raises:
            NotFoundError: If storage location or item not found
        """
        pass

    @abstractmethod
    def get_items_in_storage(self, storage_id: int) -> List[Dict[str, Any]]:
        """
        Get all items in a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            List of dictionaries with item details

        Raises:
            NotFoundError: If storage location not found
        """
        pass

    @abstractmethod
    def get_storage_utilization(self, storage_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get utilization statistics for storage locations.

        Args:
            storage_id: Optional ID to get stats for a specific location

        Returns:
            Dictionary with utilization statistics
        """
        pass