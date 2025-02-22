# services/interfaces/storage_service.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class IStorageService(ABC):
    """
    Abstract base class defining the contract for storage services.

    This interface outlines the operations that can be performed
    on storage locations in the application.
    """

    @abstractmethod
    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations.

        Returns:
            List of storage locations as dictionaries.
        """
        pass

    @abstractmethod
    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by its ID.

        Args:
            storage_id (int): Unique identifier for the storage location.

        Returns:
            Dictionary representation of the storage location or None if not found.
        """
        pass

    @abstractmethod
    def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new storage location.

        Args:
            storage_data (dict): Data for the new storage location.

        Returns:
            Dictionary of the newly created storage location.
        """
        pass

    @abstractmethod
    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            storage_id (int): Unique identifier of the storage location to update.
            storage_data (dict): Updated data for the storage location.

        Returns:
            Dictionary of the updated storage location.
        """
        pass

    @abstractmethod
    def delete_storage_location(self, storage_id: int) -> None:
        """
        Delete a storage location.

        Args:
            storage_id (int): Unique identifier of the storage location to delete.
        """
        pass

    @abstractmethod
    def search_storage_locations(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search storage locations based on a search term.

        Args:
            search_term (str): Term to search for in storage locations.

        Returns:
            List of matching storage locations as dictionaries.
        """
        pass

    @abstractmethod
    def get_storage_status(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific storage location.

        Args:
            storage_id (int): Unique identifier of the storage location.

        Returns:
            Dictionary with storage status information or None if not found.
        """
        pass