# services/interfaces/picking_list_service.py
"""
Interface for Picking List Service in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from database.models.enums import PickingListStatus
from database.models.picking_list import PickingList, PickingListItem


class IPickingListService(ABC):
    """
    Abstract base class defining the interface for Picking List Service.
    Handles operations related to picking lists for material and resource collection.
    """

    @abstractmethod
    def create_picking_list(
        self,
        sales_id: int,
        status: PickingListStatus = PickingListStatus.PENDING,
        **kwargs
    ) -> PickingList:
        """
        Create a new picking list for a sales order.

        Args:
            sales_id (int): ID of the associated sales order
            status (PickingListStatus): Initial status of the picking list
            **kwargs: Additional attributes for the picking list

        Returns:
            PickingList: The created picking list
        """
        pass

    @abstractmethod
    def get_picking_list_by_id(self, picking_list_id: int) -> PickingList:
        """
        Retrieve a picking list by its ID.

        Args:
            picking_list_id (int): ID of the picking list

        Returns:
            PickingList: The retrieved picking list
        """
        pass

    @abstractmethod
    def get_picking_lists_by_status(
        self,
        status: PickingListStatus
    ) -> List[PickingList]:
        """
        Retrieve picking lists by their status.

        Args:
            status (PickingListStatus): Status to filter picking lists

        Returns:
            List[PickingList]: List of picking lists matching the status
        """
        pass

    @abstractmethod
    def update_picking_list_status(
        self,
        picking_list_id: int,
        status: PickingListStatus
    ) -> PickingList:
        """
        Update the status of a picking list.

        Args:
            picking_list_id (int): ID of the picking list
            status (PickingListStatus): New status for the picking list

        Returns:
            PickingList: The updated picking list
        """
        pass

    @abstractmethod
    def add_picking_list_item(
        self,
        picking_list_id: int,
        component_id: Optional[int] = None,
        material_id: Optional[int] = None,
        leather_id: Optional[int] = None,
        hardware_id: Optional[int] = None,
        quantity_ordered: int = 1
    ) -> PickingListItem:
        """
        Add an item to a picking list.

        Args:
            picking_list_id (int): ID of the picking list
            component_id (Optional[int]): ID of the component (if applicable)
            material_id (Optional[int]): ID of the material (if applicable)
            leather_id (Optional[int]): ID of the leather (if applicable)
            hardware_id (Optional[int]): ID of the hardware (if applicable)
            quantity_ordered (int): Quantity of the item ordered

        Returns:
            PickingListItem: The created picking list item
        """
        pass

    @abstractmethod
    def update_picking_list_item(
        self,
        picking_list_item_id: int,
        quantity_picked: Optional[int] = None,
        **kwargs
    ) -> PickingListItem:
        """
        Update a picking list item.

        Args:
            picking_list_item_id (int): ID of the picking list item
            quantity_picked (Optional[int]): Quantity actually picked
            **kwargs: Additional attributes to update

        Returns:
            PickingListItem: The updated picking list item
        """
        pass

    @abstractmethod
    def complete_picking_list(self, picking_list_id: int) -> PickingList:
        """
        Mark a picking list as completed.

        Args:
            picking_list_id (int): ID of the picking list to complete

        Returns:
            PickingList: The completed picking list
        """
        pass