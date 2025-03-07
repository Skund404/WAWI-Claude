# services/interfaces/picking_list_service.py
"""
Interface for Picking List Service that manages picking lists for sales orders.
"""

from abc import ABC, abstractmethod
from database.models.enums import PickingListStatus
from database.models.picking_list import PickingList, PickingListItem
from datetime import datetime
from typing import Any, Dict, List, Optional


class IPickingListService(ABC):
    """Interface for the Picking List Service that handles operations related to picking lists."""

    @abstractmethod
    def get_picking_list(self, picking_list_id: int) -> PickingList:
        """
        Retrieve a picking list by its ID.

        Args:
            picking_list_id: ID of the picking list to retrieve

        Returns:
            PickingList: The retrieved picking list

        Raises:
            NotFoundError: If the picking list does not exist
        """
        pass

    @abstractmethod
    def get_picking_lists(self, **filters) -> List[PickingList]:
        """
        Retrieve picking lists based on optional filters.

        Args:
            **filters: Optional keyword arguments for filtering picking lists

        Returns:
            List[PickingList]: List of picking lists matching the filters
        """
        pass

    @abstractmethod
    def create_picking_list(self, sales_id: int, picking_list_data: Dict[str, Any] = None) -> PickingList:
        """
        Create a new picking list for a sales order with the provided data.

        Args:
            sales_id: ID of the sales order to create a picking list for
            picking_list_data: Additional data for creating the picking list

        Returns:
            PickingList: The created picking list

        Raises:
            ValidationError: If the picking list data is invalid
            NotFoundError: If the sales order does not exist
        """
        pass

    @abstractmethod
    def update_picking_list(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> PickingList:
        """
        Update a picking list with the provided data.

        Args:
            picking_list_id: ID of the picking list to update
            picking_list_data: Data for updating the picking list

        Returns:
            PickingList: The updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the picking list data is invalid
        """
        pass

    @abstractmethod
    def delete_picking_list(self, picking_list_id: int) -> bool:
        """
        Delete a picking list by its ID.

        Args:
            picking_list_id: ID of the picking list to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the picking list does not exist
        """
        pass

    @abstractmethod
    def update_picking_list_status(self, picking_list_id: int, status: PickingListStatus) -> PickingList:
        """
        Update the status of a picking list.

        Args:
            picking_list_id: ID of the picking list to update
            status: New status for the picking list

        Returns:
            PickingList: The updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the status transition is invalid
        """
        pass

    @abstractmethod
    def mark_picking_list_completed(self, picking_list_id: int) -> PickingList:
        """
        Mark a picking list as completed.

        Args:
            picking_list_id: ID of the picking list to mark as completed

        Returns:
            PickingList: The updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the picking list cannot be marked as completed
        """
        pass

    @abstractmethod
    def get_picking_list_items(self, picking_list_id: int) -> List[PickingListItem]:
        """
        Retrieve items in a picking list.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            List[PickingListItem]: List of items in the picking list

        Raises:
            NotFoundError: If the picking list does not exist
        """
        pass

    @abstractmethod
    def add_item_to_picking_list(
        self, picking_list_id: int, item_data: Dict[str, Any]
    ) -> PickingListItem:
        """
        Add an item to a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_data: Data for the item to add (component_id, material_id, leather_id, hardware_id, etc.)

        Returns:
            PickingListItem: The created picking list item

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the item data is invalid
        """
        pass

    @abstractmethod
    def update_picking_list_item(
        self, picking_list_id: int, item_id: int, item_data: Dict[str, Any]
    ) -> PickingListItem:
        """
        Update a picking list item.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the item to update
            item_data: Data for updating the item

        Returns:
            PickingListItem: The updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the item data is invalid
        """
        pass

    @abstractmethod
    def remove_item_from_picking_list(self, picking_list_id: int, item_id: int) -> bool:
        """
        Remove an item from a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the item to remove

        Returns:
            bool: True if the item was removed successfully

        Raises:
            NotFoundError: If the picking list or item does not exist
        """
        pass

    @abstractmethod
    def update_item_quantities(
        self, picking_list_id: int, item_id: int, quantity_picked: int
    ) -> PickingListItem:
        """
        Update the quantities of a picking list item.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the item to update
            quantity_picked: The quantity that has been picked

        Returns:
            PickingListItem: The updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the quantity is invalid
        """
        pass

    @abstractmethod
    def get_picking_lists_by_sales_order(self, sales_id: int) -> List[PickingList]:
        """
        Retrieve picking lists for a specific sales order.

        Args:
            sales_id: ID of the sales order

        Returns:
            List[PickingList]: List of picking lists for the sales order
        """
        pass