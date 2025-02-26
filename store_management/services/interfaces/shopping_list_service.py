# store_management/services/interfaces/shopping_list_service.py
"""
Interface for Shopping List Service in Leatherworking Store Management.

Defines the contract for shopping list-related operations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from di.core import inject
from utils.circular_import_resolver import CircularImportResolver

class ShoppingListStatus(Enum):
    """
    Enumeration of possible shopping list statuses.
    """
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

class IShoppingListService(ABC):
    """
    Abstract base class defining the interface for shopping list-related operations.
    """

    @abstractmethod
    @inject('IMaterialService')
    def create_shopping_list(
        self,
        name: str,
        description: Optional[str] = None,
        status: ShoppingListStatus = ShoppingListStatus.DRAFT,
        material_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new shopping list.

        Args:
            name (str): Name of the shopping list
            description (Optional[str], optional): Description of the shopping list
            status (ShoppingListStatus, optional): Initial status of the shopping list
            material_service (Optional[Any], optional): Material service for additional operations

        Returns:
            Dict[str, Any]: Details of the created shopping list
        """
        pass

    @abstractmethod
    def add_item_to_shopping_list(
        self,
        shopping_list_id: str,
        material_id: str,
        quantity: float,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an item to an existing shopping list.

        Args:
            shopping_list_id (str): Unique identifier of the shopping list
            material_id (str): Unique identifier of the material to add
            quantity (float): Quantity of the material
            notes (Optional[str], optional): Additional notes about the item

        Returns:
            Dict[str, Any]: Details of the added shopping list item
        """
        pass

    @abstractmethod
    def remove_item_from_shopping_list(
        self,
        shopping_list_id: str,
        item_id: str
    ) -> bool:
        """
        Remove an item from a shopping list.

        Args:
            shopping_list_id (str): Unique identifier of the shopping list
            item_id (str): Unique identifier of the item to remove

        Returns:
            bool: True if removal was successful, False otherwise
        """
        pass

    @abstractmethod
    def update_shopping_list(
        self,
        shopping_list_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing shopping list.

        Args:
            shopping_list_id (str): Unique identifier of the shopping list
            updates (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Dict[str, Any]: Updated shopping list details
        """
        pass

    @abstractmethod
    def get_shopping_list(
        self,
        shopping_list_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific shopping list by its ID.

        Args:
            shopping_list_id (str): Unique identifier of the shopping list

        Returns:
            Optional[Dict[str, Any]]: Shopping list details, or None if not found
        """
        pass

    @abstractmethod
    def list_shopping_lists(
        self,
        status: Optional[ShoppingListStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        List shopping lists with optional filtering.

        Args:
            status (Optional[ShoppingListStatus], optional): Filter by shopping list status

        Returns:
            List[Dict[str, Any]]: List of shopping lists matching the criteria
        """
        pass

    @abstractmethod
    def delete_shopping_list(
        self,
        shopping_list_id: str
    ) -> bool:
        """
        Delete a shopping list.

        Args:
            shopping_list_id (str): Unique identifier of the shopping list to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    @inject('IMaterialService')
    def generate_purchase_order(
        self,
        shopping_list_id: str,
        material_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a purchase order from a shopping list.

        Args:
            shopping_list_id (str): Unique identifier of the shopping list
            material_service (Optional[Any], optional): Material service for order generation

        Returns:
            Dict[str, Any]: Details of the generated purchase order
        """
        pass

    @abstractmethod
    def search_shopping_lists(
        self,
        query: Optional[str] = None,
        material_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for shopping lists with optional filtering.

        Args:
            query (Optional[str], optional): Search term
            material_types (Optional[List[str]], optional): List of material types

        Returns:
            List[Dict[str, Any]]: List of shopping lists matching the search criteria
        """
        pass