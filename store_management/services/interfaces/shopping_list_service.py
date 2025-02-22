# Path: store_management/services/interfaces/shopping_list_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from services.interfaces.base_service import IBaseService


class IShoppingListService(IBaseService):
    """
    Interface for shopping list management operations.

    Defines the contract for services handling shopping list-related functionality.
    """

    @abstractmethod
    def get_all_shopping_lists(self) -> List[Dict[str, Any]]:
        """
        Retrieve all shopping lists.

        Returns:
            List of shopping list dictionaries
        """
        pass

    @abstractmethod
    def get_shopping_list_by_id(self, list_id: int) -> Optional[Dict[str, Any]]:
        """
        Get shopping list details by ID.

        Args:
            list_id: Shopping list ID

        Returns:
            Shopping list details or None if not found
        """
        pass

    @abstractmethod
    def create_shopping_list(self, list_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Optional[
        Dict[str, Any]]:
        """
        Create a new shopping list with optional items.

        Args:
            list_data: Shopping list data
            items: Optional list of item data

        Returns:
            Created shopping list or None
        """
        pass

    @abstractmethod
    def update_shopping_list(self, list_id: int, list_data: Dict[str, Any],
                             items: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing shopping list.

        Args:
            list_id: ID of the shopping list to update
            list_data: Updated shopping list data
            items: Optional list of updated items

        Returns:
            Updated shopping list or None
        """
        pass

    @abstractmethod
    def delete_shopping_list(self, list_id: int) -> bool:
        """
        Delete a shopping list.

        Args:
            list_id: ID of the shopping list to delete

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add an item to a shopping list.

        Args:
            list_id: Shopping list ID
            item_data: Item data to add

        Returns:
            Added item or None
        """
        pass

    @abstractmethod
    def remove_item_from_list(self, list_id: int, item_id: int) -> bool:
        """
        Remove an item from a shopping list.

        Args:
            list_id: Shopping list ID
            item_id: Item ID to remove

        Returns:
            True if removal successful, False otherwise
        """
        pass

    @abstractmethod
    def mark_item_purchased(self, item_id: int, purchase_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Mark a shopping list item as purchased.

        Args:
            item_id: Shopping list item ID
            purchase_data: Purchase details

        Returns:
            Updated item or None
        """
        pass

    @abstractmethod
    def search_shopping_lists(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search shopping lists by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching shopping lists
        """
        pass