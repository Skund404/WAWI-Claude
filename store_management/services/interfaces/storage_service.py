# services/interfaces/storage_service.py
"""
Interface definition for Storage Service in the Store Management System.

This module defines the contract for storage-related operations
that must be implemented by concrete storage service classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class IStorageService(ABC):
    """
    Abstract base class defining the contract for storage services.

    This interface outlines the core operations that can be performed
    on storage locations in the application, ensuring a consistent
    approach to storage management across different implementations.
    """

    @abstractmethod
    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations from the system.

        Returns:
            List[Dict[str, Any]]: A list of storage locations with their details.

        Raises:
            Exception: If retrieval fails due to database or system errors.
        """
        pass

    @abstractmethod
    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by its unique identifier.

        Args:
            storage_id (int): The unique identifier of the storage location.

        Returns:
            Optional[Dict[str, Any]]: Details of the storage location if found,
                                      None otherwise.

        Raises:
            ValueError: If the storage_id is invalid.
            Exception: If retrieval fails due to database or system errors.
        """
        pass

    @abstractmethod
    def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new storage location in the system.

        Args:
            storage_data (Dict[str, Any]): Data for the new storage location.

        Returns:
            Dict[str, Any]: Details of the created storage location.

        Raises:
            ValueError: If the provided storage data is invalid.
            Exception: If creation fails due to database or system errors.
        """
        pass

    @abstractmethod
    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            storage_id (int): Unique identifier of the storage location to update.
            storage_data (Dict[str, Any]): Updated data for the storage location.

        Returns:
            Dict[str, Any]: Updated details of the storage location.

        Raises:
            ValueError: If the storage_id is invalid or storage data is incomplete.
            Exception: If update fails due to database or system errors.
        """
        pass

    @abstractmethod
    def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location from the system.

        Args:
            storage_id (int): Unique identifier of the storage location to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            ValueError: If the storage_id is invalid.
            Exception: If deletion fails due to existing dependencies or system errors.
        """
        pass

    @abstractmethod
    def search_storage_locations(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for storage locations based on a search term.

        Args:
            search_term (str): Term to search for in storage locations.

        Returns:
            List[Dict[str, Any]]: List of storage locations matching the search term.

        Raises:
            ValueError: If the search term is empty or invalid.
            Exception: If search fails due to database or system errors.
        """
        pass

    @abstractmethod
    def get_storage_status(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a specific storage location.

        Args:
            storage_id (int): Unique identifier of the storage location.

        Returns:
            Optional[Dict[str, Any]]: Dictionary with storage status information
                                      or None if not found.

        Raises:
            ValueError: If the storage_id is invalid.
            Exception: If status retrieval fails due to database or system errors.
        """
        pass