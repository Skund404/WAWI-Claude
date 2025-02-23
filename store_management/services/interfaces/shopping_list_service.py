# services/interfaces/shopping_list_service.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from database.models.shopping_list import ShoppingList


class IShoppingListService(ABC):
    """
    Interface defining the contract for shopping list management services.

    Specifies all operations that must be supported by shopping list service implementations.
    """

    @abstractmethod
    def get_all_shopping_lists(self) -> List[ShoppingList]:
        """
        Get all shopping lists in the system.

        Returns:
            List of ShoppingList objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_shopping_list_by_id(self, list_id: int) -> Optional[ShoppingList]:
        """
        Get a shopping list by its ID.

        Args:
            list_id: ID of the shopping list to retrieve

        Returns:
            ShoppingList object if found, None otherwise

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def create_shopping_list(self, list_data: Dict[str, Any]) -> ShoppingList:
        """
        Create a new shopping list.

        Args:
            list_data: Dictionary containing list data and items

        Returns:
            Created ShoppingList object

        Raises:
            Exception: If creation fails
        """
        pass

    @abstractmethod
    def update_shopping_list(self, list_id: int, list_data: Dict[str, Any]) -> ShoppingList:
        """
        Update an existing shopping list.

        Args:
            list_id: ID of the list to update
            list_data: Dictionary containing updated list data

        Returns:
            Updated ShoppingList object

        Raises:
            Exception: If update fails
        """
        pass

    @abstractmethod
    def delete_shopping_list(self, list_id: int) -> None:
        """
        Delete a shopping list.

        Args:
            list_id: ID of the list to delete

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) -> ShoppingList:
        """
        Add an item to a shopping list.

        Args:
            list_id: ID of the list to add to
            item_data: Dictionary containing item data

        Returns:
            Updated ShoppingList object

        Raises:
            Exception: If addition fails
        """
        pass

    @abstractmethod
    def remove_item_from_list(self, list_id: int, item_id: int) -> ShoppingList:
        """
        Remove an item from a shopping list.

        Args:
            list_id: ID of the list
            item_id: ID of the item to remove

        Returns:
            Updated ShoppingList object

        Raises:
            Exception: If removal fails
        """
        pass

    @abstractmethod
    def mark_item_purchased(self, list_id: int, item_id: int, quantity: float) -> ShoppingList:
        """
        Mark an item as purchased.

        Args:
            list_id: ID of the list
            item_id: ID of the item
            quantity: Quantity purchased

        Returns:
            Updated ShoppingList object

        Raises:
            Exception: If update fails
        """
        pass

    @abstractmethod
    def get_active_lists(self) -> List[ShoppingList]:
        """
        Get all active shopping lists.

        Returns:
            List of active ShoppingList objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_lists_by_status(self, status: str) -> List[ShoppingList]:
        """
        Get all shopping lists with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of matching ShoppingList objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def search_shopping_lists(self, search_term: str) -> List[ShoppingList]:
        """
        Search shopping lists by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching ShoppingList objects

        Raises:
            Exception: If search fails
        """
        pass

    @abstractmethod
    def get_pending_items(self) -> List[Dict[str, Any]]:
        """
        Get all unpurchased items across all active lists.

        Returns:
            List of dictionaries containing pending item details

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        pass