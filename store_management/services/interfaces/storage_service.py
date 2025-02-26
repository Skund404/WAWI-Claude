# store_management/services/interfaces/storage_service.py
"""
Comprehensive Interface for Storage Service in Leatherworking Store Management.

Defines the contract for storage-related operations, including location management,
product assignment, and inventory tracking.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

class StorageLocationType(Enum):
    """
    Enumeration of possible storage location types.
    """
    SHELF = "Shelf"
    BIN = "Bin"
    DRAWER = "Drawer"
    CABINET = "Cabinet"
    RACK = "Rack"
    BOX = "Box"
    WAREHOUSE = "Warehouse"
    OTHER = "Other"

class StorageCapacityStatus(Enum):
    """
    Enumeration of storage capacity statuses.
    """
    EMPTY = "Empty"
    PARTIALLY_FILLED = "Partially Filled"
    NEARLY_FULL = "Nearly Full"
    FULL = "Full"

class IStorageService(ABC):
    """
    Abstract base class defining the comprehensive interface for storage-related operations.
    """

    @abstractmethod
    def create_storage_location(
        self,
        name: str,
        location_type: StorageLocationType,
        capacity: Optional[float] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new storage location.

        Args:
            name (str): Name or identifier of the storage location
            location_type (StorageLocationType): Type of storage location
            capacity (Optional[float], optional): Maximum capacity of the storage location
            description (Optional[str], optional): Additional details about the location

        Returns:
            Dict[str, Any]: Details of the created storage location
        """
        pass

    @abstractmethod
    def update_storage_location(
        self,
        location_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            location_id (str): Unique identifier of the storage location
            updates (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Dict[str, Any]: Updated storage location details
        """
        pass

    @abstractmethod
    def delete_storage_location(self, location_id: str) -> bool:
        """
        Delete a storage location.

        Args:
            location_id (str): Unique identifier of the storage location to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_storage_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve details of a specific storage location.

        Args:
            location_id (str): Unique identifier of the storage location

        Returns:
            Optional[Dict[str, Any]]: Storage location details, or None if not found
        """
        pass

    @abstractmethod
    def list_storage_locations(
        self,
        location_type: Optional[StorageLocationType] = None,
        min_capacity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        List storage locations with optional filtering.

        Args:
            location_type (Optional[StorageLocationType], optional): Filter by location type
            min_capacity (Optional[float], optional): Minimum available capacity

        Returns:
            List[Dict[str, Any]]: List of storage locations matching the criteria
        """
        pass

    @abstractmethod
    def assign_item_to_storage(
        self,
        item_id: str,
        location_id: str,
        quantity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Assign an item (product, material, etc.) to a specific storage location.

        Args:
            item_id (str): Unique identifier of the item
            location_id (str): Unique identifier of the storage location
            quantity (float, optional): Quantity of the item to store. Defaults to 1.0

        Returns:
            Dict[str, Any]: Assignment details
        """
        pass

    @abstractmethod
    def remove_item_from_storage(
        self,
        item_id: str,
        location_id: str,
        quantity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Remove an item from a specific storage location.

        Args:
            item_id (str): Unique identifier of the item
            location_id (str): Unique identifier of the storage location
            quantity (Optional[float], optional): Quantity to remove. If None, remove all.

        Returns:
            Dict[str, Any]: Removal details
        """
        pass

    @abstractmethod
    def get_storage_contents(
        self,
        location_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all items stored in a specific location.

        Args:
            location_id (str): Unique identifier of the storage location

        Returns:
            List[Dict[str, Any]]: List of items stored in the location
        """
        pass

    @abstractmethod
    def get_storage_capacity_status(
        self,
        location_id: str
    ) -> StorageCapacityStatus:
        """
        Get the current capacity status of a storage location.

        Args:
            location_id (str): Unique identifier of the storage location

        Returns:
            StorageCapacityStatus: Current capacity status of the storage location
        """
        pass

    @abstractmethod
    def move_item_between_storage(
        self,
        item_id: str,
        source_location_id: str,
        destination_location_id: str,
        quantity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Move an item from one storage location to another.

        Args:
            item_id (str): Unique identifier of the item
            source_location_id (str): Current storage location
            destination_location_id (str): Target storage location
            quantity (Optional[float], optional): Quantity to move. If None, move all.

        Returns:
            Dict[str, Any]: Movement transaction details
        """
        pass

    @abstractmethod
    def search_items_in_storage(
        self,
        query: Optional[str] = None,
        item_type: Optional[str] = None,
        min_quantity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for items across all storage locations.

        Args:
            query (Optional[str], optional): Search term
            item_type (Optional[str], optional): Type of item to search for
            min_quantity (Optional[float], optional): Minimum quantity filter

        Returns:
            List[Dict[str, Any]]: List of matching storage entries
        """
        pass