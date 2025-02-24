# Relative path: store_management/services/interfaces/storage_service.py

"""
Storage Service Interface Module

Defines the abstract base interface for storage-related operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any

from database.models import Part


class IStorageService(ABC):
    """
    Abstract base class defining the interface for storage-related operations.

    This service provides methods for managing inventory storage, 
    tracking, and manipulation of stored items.
    """

    @abstractmethod
    def add_to_storage(
            self,
            part: Part,
            quantity: float,
            storage_location: Optional[str] = None
    ) -> bool:
        """
        Add a specified quantity of a part to storage.

        Args:
            part (Part): The part to be added to storage.
            quantity (float): The quantity of the part to add.
            storage_location (Optional[str], optional): Specific storage location. 
                Defaults to None.

        Returns:
            bool: True if the addition was successful, False otherwise.
        """
        pass

    @abstractmethod
    def remove_from_storage(
            self,
            part: Part,
            quantity: float,
            storage_location: Optional[str] = None
    ) -> bool:
        """
        Remove a specified quantity of a part from storage.

        Args:
            part (Part): The part to be removed from storage.
            quantity (float): The quantity of the part to remove.
            storage_location (Optional[str], optional): Specific storage location. 
                Defaults to None.

        Returns:
            bool: True if the removal was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_storage_quantity(
            self,
            part: Part,
            storage_location: Optional[str] = None
    ) -> float:
        """
        Get the current quantity of a part in storage.

        Args:
            part (Part): The part to check.
            storage_location (Optional[str], optional): Specific storage location. 
                Defaults to None.

        Returns:
            float: The current quantity of the part in storage.
        """
        pass

    @abstractmethod
    def list_storage_items(
            self,
            filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List items currently in storage with optional filtering.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional): 
                Dictionary of filter parameters. Defaults to None.

        Returns:
            List[Dict[str, Any]]: A list of storage items matching the criteria.
        """
        pass

    @abstractmethod
    def move_storage_item(
            self,
            part: Part,
            quantity: float,
            from_location: str,
            to_location: str
    ) -> bool:
        """
        Move a specified quantity of a part between storage locations.

        Args:
            part (Part): The part to be moved.
            quantity (float): The quantity of the part to move.
            from_location (str): The source storage location.
            to_location (str): The destination storage location.

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        pass

    @abstractmethod
    def validate_storage_operation(
            self,
            part: Part,
            quantity: float,
            operation_type: str
    ) -> bool:
        """
        Validate a storage operation before execution.

        Args:
            part (Part): The part involved in the operation.
            quantity (float): The quantity involved in the operation.
            operation_type (str): Type of operation (e.g., 'add', 'remove', 'move').

        Returns:
            bool: True if the operation would be valid, False otherwise.
        """
        pass