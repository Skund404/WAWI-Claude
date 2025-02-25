# Relative path: store_management/services/interfaces/shopping_list_service.py

"""
Shopping List Service Interface Module

Defines the abstract base interface for shopping list operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from di.core import inject
from services.interfaces import MaterialService


class IShoppingListService(ABC):
    """
    Interface for shopping list management service.

    Provides methods for creating, retrieving, updating, and managing
    shopping lists for the leatherworking management system.
    """

    @abstractmethod
    @inject(MaterialService)
    def get_all_shopping_lists(self) -> List[Any]:
        """
        Get all shopping lists.

        Returns:
            List[Any]: List of all shopping lists in the system
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_shopping_list_by_id(self, list_id: int) -> Optional[Any]:
        """
        Get shopping list by ID.

        Args:
            list_id (int): ID of the shopping list to retrieve

        Returns:
            Optional[Any]: Shopping list if found, None otherwise

        Raises:
            KeyError: If list with given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def create_shopping_list(self, list_data: Dict[str, Any]) -> Any:
        """
        Create a new shopping list.

        Args:
            list_data (Dict[str, Any]): Data for the new shopping list

        Returns:
            Any: The created shopping list

        Raises:
            ValueError: If list data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def update_shopping_list(self, list_id: int, list_data: Dict[str, Any]) -> Optional[Any]:
        """
        Update existing shopping list.

        Args:
            list_id (int): ID of the shopping list to update
            list_data (Dict[str, Any]): Updated shopping list data

        Returns:
            Optional[Any]: Updated shopping list if successful, None otherwise

        Raises:
            KeyError: If list with given ID does not exist
            ValueError: If list data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def delete_shopping_list(self, list_id: int) -> bool:
        """
        Delete shopping list.

        Args:
            list_id (int): ID of the shopping list to delete

        Returns:
            bool: True if deleted successfully, False otherwise

        Raises:
            KeyError: If list with given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) -> Any:
        """
        Add item to shopping list.

        Args:
            list_id (int): ID of the shopping list
            item_data (Dict[str, Any]): Data for the item to add

        Returns:
            Any: The updated shopping list or added item

        Raises:
            KeyError: If list with given ID does not exist
            ValueError: If item data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def remove_item_from_list(self, list_id: int, item_id: int) -> bool:
        """
        Remove item from shopping list.

        Args:
            list_id (int): ID of the shopping list
            item_id (int): ID of the item to remove

        Returns:
            bool: True if removed successfully, False otherwise

        Raises:
            KeyError: If list or item with given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def mark_item_purchased(self, list_id: int, item_id: int, quantity: float) -> bool:
        """
        Mark item as purchased.

        Args:
            list_id (int): ID of the shopping list
            item_id (int): ID of the item to mark
            quantity (float): Quantity purchased

        Returns:
            bool: True if marked successfully, False otherwise

        Raises:
            KeyError: If list or item with given ID does not exist
            ValueError: If quantity is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_active_lists(self) -> List[Any]:
        """
        Get all active shopping lists.

        Returns:
            List[Any]: List of active shopping lists
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_pending_items(self) -> List[Any]:
        """
        Get all pending items across all lists.

        Returns:
            List[Any]: List of pending items
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_lists_by_status(self, status: str) -> List[Any]:
        """
        Get lists by status.

        Args:
            status (str): Status to filter by

        Returns:
            List[Any]: List of shopping lists matching the status
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def search_shopping_lists(self, search_term: str) -> List[Any]:
        """
        Search shopping lists.

        Args:
            search_term (str): Term to search for

        Returns:
            List[Any]: List of shopping lists matching the search term
        """
        pass