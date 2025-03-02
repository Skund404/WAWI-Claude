"""
services/interfaces/picking_list_service.py - Interface for Picking List Service
"""
from abc import ABC, abstractmethod
from database.models.picking_list import PickingListStatus
from typing import Any, Dict, List, Optional


class IPickingListService(ABC):
    """Interface for the picking list service which manages picking lists and items."""

    @abstractmethod
    def get_all_lists(self) -> List[Dict[str, Any]]:
        """
        Get all picking lists.

        Returns:
            List[Dict[str, Any]]: List of picking lists data
        """
        pass

    @abstractmethod
    def get_list_by_id(self, list_id: int) -> Dict[str, Any]:
        """
        Get a picking list by ID.

        Args:
            list_id: ID of the picking list to retrieve

        Returns:
            Dict[str, Any]: Picking list data

        Raises:
            NotFoundError: If picking list not found
        """
        pass

    @abstractmethod
    def create_list(self, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new picking list.

        Args:
            list_data: Picking list data

        Returns:
            Dict[str, Any]: Created picking list

        Raises:
            ValidationError: If data is invalid
        """
        pass

    @abstractmethod
    def update_list(self, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing picking list.

        Args:
            list_data: Picking list data including ID

        Returns:
            Dict[str, Any]: Updated picking list

        Raises:
            NotFoundError: If picking list not found
            ValidationError: If data is invalid
        """
        pass

    @abstractmethod
    def delete_list(self, list_id: int) -> bool:
        """
        Delete a picking list.

        Args:
            list_id: ID of the picking list to delete

        Returns:
            bool: True if successfully deleted

        Raises:
            NotFoundError: If picking list not found
        """
        pass

    @abstractmethod
    def get_list_items(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get all items for a picking list.

        Args:
            list_id: ID of the picking list

        Returns:
            List[Dict[str, Any]]: List of picking list items

        Raises:
            NotFoundError: If picking list not found
        """
        pass

    @abstractmethod
    def add_item(self, list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to a picking list.

        Args:
            list_id: ID of the picking list
            item_data: Item data to add

        Returns:
            Dict[str, Any]: Added item

        Raises:
            NotFoundError: If picking list not found
            ValidationError: If data is invalid
        """
        pass

    @abstractmethod
    def update_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a picking list item.

        Args:
            item_data: Item data including ID

        Returns:
            Dict[str, Any]: Updated item

        Raises:
            NotFoundError: If item not found
            ValidationError: If data is invalid
        """
        pass

    @abstractmethod
    def remove_item(self, item_id: int) -> bool:
        """
        Remove an item from a picking list.

        Args:
            item_id: ID of the item to remove

        Returns:
            bool: True if successfully removed

        Raises:
            NotFoundError: If item not found
        """
        pass

    @abstractmethod
    def mark_item_picked(self, item_id: int, quantity: float) -> Dict[str, Any]:
        """
        Mark a picking list item as picked with the specified quantity.

        Args:
            item_id: ID of the item to mark
            quantity: Quantity picked

        Returns:
            Dict[str, Any]: Updated item

        Raises:
            NotFoundError: If item not found
            ValidationError: If quantity is invalid
        """
        pass

    @abstractmethod
    def filter_lists_by_status(self, status: PickingListStatus) -> List[Dict[str, Any]]:
        """
        Filter picking lists by status.

        Args:
            status: Status to filter by

        Returns:
            List[Dict[str, Any]]: Filtered picking lists
        """
        pass

    @abstractmethod
    def search_lists(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search picking lists by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List[Dict[str, Any]]: Matching picking lists
        """
        pass