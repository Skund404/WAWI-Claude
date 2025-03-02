# services/interfaces/shopping_list_service.py
from abc import ABC, abstractmethod
from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.enums import ShoppingListStatus, Priority
from typing import List, Dict, Any, Optional
from datetime import datetime


class IShoppingListService(ABC):
    """
    Abstract base class defining the interface for Shopping List services.

    Defines the contract for creating, retrieving, updating,
    and deleting Shopping List entities.
    """

    @abstractmethod
    def create_shopping_list(self, shopping_list_data: Dict[str, Any]) -> ShoppingList:
        """
        Create a new shopping list.

        Args:
            shopping_list_data (Dict[str, Any]): Shopping list creation data

        Returns:
            ShoppingList: Newly created shopping list instance

        Raises:
            ValidationError: If shopping list data is invalid
        """
        pass

    @abstractmethod
    def get_shopping_list_by_id(self, shopping_list_id: int) -> ShoppingList:
        """
        Retrieve a shopping list by its ID.

        Args:
            shopping_list_id (int): Unique identifier of the shopping list

        Returns:
            ShoppingList: Retrieved shopping list instance

        Raises:
            NotFoundError: If no shopping list is found with the given ID
        """
        pass

    @abstractmethod
    def update_shopping_list(self, shopping_list_id: int, update_data: Dict[str, Any]) -> ShoppingList:
        """
        Update an existing shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            ShoppingList: Updated shopping list instance

        Raises:
            NotFoundError: If shopping list doesn't exist
            ValidationError: If update data is invalid
        """
        pass

    @abstractmethod
    def delete_shopping_list(self, shopping_list_id: int) -> None:
        """
        Delete a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to delete

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        pass

    @abstractmethod
    def list_shopping_lists(self,
                            status: Optional[ShoppingListStatus] = None,
                            priority: Optional[Priority] = None,
                            is_completed: Optional[bool] = None) -> List[ShoppingList]:
        """
        List shopping lists with optional filtering.

        Args:
            status (Optional[ShoppingListStatus]): Filter by shopping list status
            priority (Optional[Priority]): Filter by priority
            is_completed (Optional[bool]): Filter by completion status

        Returns:
            List[ShoppingList]: List of shopping lists matching the criteria
        """
        pass

    @abstractmethod
    def add_item_to_shopping_list(self,
                                  shopping_list_id: int,
                                  item_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Add an item to an existing shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list
            item_data (Dict[str, Any]): Data for the new shopping list item

        Returns:
            ShoppingListItem: The newly created item

        Raises:
            NotFoundError: If shopping list doesn't exist
            ValidationError: If item data is invalid
        """
        pass

    @abstractmethod
    def update_shopping_list_item(self,
                                  item_id: int,
                                  update_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Update an existing shopping list item.

        Args:
            item_id (int): ID of the shopping list item to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            ShoppingListItem: Updated shopping list item

        Raises:
            NotFoundError: If shopping list item doesn't exist
            ValidationError: If update data is invalid
        """
        pass

    @abstractmethod
    def remove_item_from_shopping_list(self, item_id: int) -> None:
        """
        Remove an item from a shopping list.

        Args:
            item_id (int): ID of the shopping list item to remove

        Raises:
            NotFoundError: If shopping list item doesn't exist
        """
        pass

    @abstractmethod
    def mark_shopping_list_completed(self, shopping_list_id: int) -> ShoppingList:
        """
        Mark a shopping list as completed.

        Args:
            shopping_list_id (int): ID of the shopping list to mark as completed

        Returns:
            ShoppingList: Updated shopping list instance

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        pass

    @abstractmethod
    def reset_shopping_list(self, shopping_list_id: int) -> ShoppingList:
        """
        Reset a shopping list to draft status and unmark all items.

        Args:
            shopping_list_id (int): ID of the shopping list to reset

        Returns:
            ShoppingList: Reset shopping list instance

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        pass

    @abstractmethod
    def calculate_shopping_list_total(self, shopping_list_id: int) -> Dict[str, Any]:
        """
        Calculate the total estimated cost of a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list

        Returns:
            Dict[str, Any]: Dictionary containing total cost and item details

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        pass