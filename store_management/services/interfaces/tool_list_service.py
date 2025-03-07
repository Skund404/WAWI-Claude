# services/interfaces/tool_list_service.py
"""
Interface for Tool List Service that manages tool lists for projects.
"""

from abc import ABC, abstractmethod
from database.models.enums import ToolListStatus
from database.models.tool_list import ToolList, ToolListItem
from datetime import datetime
from typing import Any, Dict, List, Optional


class IToolListService(ABC):
    """Interface for the Tool List Service that handles operations related to tool lists."""

    @abstractmethod
    def get_tool_list(self, tool_list_id: int) -> ToolList:
        """
        Retrieve a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to retrieve

        Returns:
            ToolList: The retrieved tool list

        Raises:
            NotFoundError: If the tool list does not exist
        """
        pass

    @abstractmethod
    def get_tool_lists(self, **filters) -> List[ToolList]:
        """
        Retrieve tool lists based on optional filters.

        Args:
            **filters: Optional keyword arguments for filtering tool lists

        Returns:
            List[ToolList]: List of tool lists matching the filters
        """
        pass

    @abstractmethod
    def create_tool_list(self, project_id: int, tool_list_data: Dict[str, Any] = None) -> ToolList:
        """
        Create a new tool list for a project with the provided data.

        Args:
            project_id: ID of the project to create a tool list for
            tool_list_data: Additional data for creating the tool list

        Returns:
            ToolList: The created tool list

        Raises:
            ValidationError: If the tool list data is invalid
            NotFoundError: If the project does not exist
        """
        pass

    @abstractmethod
    def update_tool_list(self, tool_list_id: int, tool_list_data: Dict[str, Any]) -> ToolList:
        """
        Update a tool list with the provided data.

        Args:
            tool_list_id: ID of the tool list to update
            tool_list_data: Data for updating the tool list

        Returns:
            ToolList: The updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If the tool list data is invalid
        """
        pass

    @abstractmethod
    def delete_tool_list(self, tool_list_id: int) -> bool:
        """
        Delete a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the tool list does not exist
        """
        pass

    @abstractmethod
    def update_tool_list_status(self, tool_list_id: int, status: ToolListStatus) -> ToolList:
        """
        Update the status of a tool list.

        Args:
            tool_list_id: ID of the tool list to update
            status: New status for the tool list

        Returns:
            ToolList: The updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If the status transition is invalid
        """
        pass

    @abstractmethod
    def get_tool_list_items(self, tool_list_id: int) -> List[ToolListItem]:
        """
        Retrieve items in a tool list.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            List[ToolListItem]: List of items in the tool list

        Raises:
            NotFoundError: If the tool list does not exist
        """
        pass

    @abstractmethod
    def add_tool_to_list(self, tool_list_id: int, tool_id: int, quantity: int = 1) -> ToolListItem:
        """
        Add a tool to a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_id: ID of the tool to add
            quantity: Quantity of the tool to add (default 1)

        Returns:
            ToolListItem: The created tool list item

        Raises:
            NotFoundError: If the tool list or tool does not exist
            ValidationError: If the quantity is invalid
        """
        pass

    @abstractmethod
    def update_tool_list_item(
        self, tool_list_id: int, item_id: int, item_data: Dict[str, Any]
    ) -> ToolListItem:
        """
        Update a tool list item.

        Args:
            tool_list_id: ID of the tool list
            item_id: ID of the item to update
            item_data: Data for updating the item

        Returns:
            ToolListItem: The updated tool list item

        Raises:
            NotFoundError: If the tool list or item does not exist
            ValidationError: If the item data is invalid
        """
        pass

    @abstractmethod
    def remove_tool_from_list(self, tool_list_id: int, item_id: int) -> bool:
        """
        Remove a tool from a tool list.

        Args:
            tool_list_id: ID of the tool list
            item_id: ID of the item to remove

        Returns:
            bool: True if the item was removed successfully

        Raises:
            NotFoundError: If the tool list or item does not exist
        """
        pass

    @abstractmethod
    def get_tool_lists_by_project(self, project_id: int) -> List[ToolList]:
        """
        Retrieve tool lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List[ToolList]: List of tool lists for the project
        """
        pass