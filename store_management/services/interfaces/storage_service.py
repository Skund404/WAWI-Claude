# Path: store_management/services/interfaces/storage_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from store_management.services.interfaces.base_service import IBaseService


class IStorageService(IBaseService):
    """
    Interface for storage-related operations.

    Defines the contract for services managing storage locations
    This interface establishes a standard set of methods for interacting
    with storage locations in the application.
    """

    @abstractmethod
    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations.

        Returns:
            A list of dictionaries, each representing a storage location.
        """
        pass

    @abstractmethod
    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by its ID.

        Args:
            storage_id: The unique identifier of the storage location.

        Returns:
            A dictionary representing the storage location if found, None otherwise.
        """
        pass

    @abstractmethod
    def create_storage_location(self, storage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new storage location.

        Args:
            storage_data: Dictionary containing storage location information

        Returns:
            Created storage location dictionary or None if creation fails
        """
        pass

    @abstractmethod
    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing storage location.

        Args:
            storage_id: ID of the storage location to update
            storage_data: Dictionary with updated storage location information

        Returns:
            Updated storage location dictionary or None if update fails
        """
        pass

    @abstractmethod
    def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location.

        Args:
            storage_id: ID of the storage location to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def search_storage_locations(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search storage locations by location or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching storage locations
        """
        pass

    @abstractmethod
    def get_storage_status(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Dictionary containing storage status details or None
        """
        pass