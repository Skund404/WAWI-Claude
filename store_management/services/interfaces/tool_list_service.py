# services/interfaces/tool_list_service.py
"""
Interface for Tool List Service in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from database.models.enums import ToolListStatus
from database.models.tool_list import ToolList, ToolListItem


class IToolListService(ABC):
    """
    Abstract base class defining the interface for Tool List Service.
    Handles operations related to tool lists for projects.
    """

    @abstractmethod
    def create_tool_list(
        self,
        project_id: int,
        status: ToolListStatus = ToolListStatus.PENDING,
        **kwargs
    ) -> ToolList:
        """
        Create a new tool list for a project.

        Args:
            project_id (int): ID of the associated project
            status (ToolListStatus): Initial status of the tool list
            **kwargs: Additional attributes for the tool list

        Returns:
            ToolList: The created tool list
        """
        pass

    @abstractmethod
    def get_tool_list_by_id(self, tool_list_id: int) -> ToolList:
        """
        Retrieve a tool list by its ID.

        Args:
            tool_list_id (int): ID of the tool list

        Returns:
            ToolList: The retrieved tool list
        """
        pass

    @abstractmethod
    def get_tool_lists_by_project(self, project_id: int) -> List[ToolList]:
        """
        Retrieve tool lists for a specific project.

        Args:
            project_id (int): ID of the project

        Returns:
            List[ToolList]: List of tool lists for the project
        """
        pass

    @abstractmethod
    def update_tool_list_status(
        self,
        tool_list_id: int,
        status: ToolListStatus
    ) -> ToolList:
        """
        Update the status of a tool list.

        Args:
            tool_list_id (int): ID of the tool list
            status (ToolListStatus): New status for the tool list

        Returns:
            ToolList: The updated tool list
        """
        pass

    @abstractmethod
    def add_tool_to_list(
        self,
        tool_list_id: int,
        tool_id: int,
        quantity: int = 1
    ) -> ToolListItem:
        """
        Add a tool to a tool list.

        Args:
            tool_list_id (int): ID of the tool list
            tool_id (int): ID of the tool to add
            quantity (int): Quantity of the tool to add

        Returns:
            ToolListItem: The created tool list item
        """
        pass

    @abstractmethod
    def update_tool_list_item(
        self,
        tool_list_item_id: int,
        quantity: Optional[int] = None,
        **kwargs
    ) -> ToolListItem:
        """
        Update a tool list item.

        Args:
            tool_list_item_id (int): ID of the tool list item
            quantity (Optional[int]): New quantity of the tool
            **kwargs: Additional attributes to update

        Returns:
            ToolListItem: The updated tool list item
        """
        pass

    @abstractmethod
    def remove_tool_from_list(
        self,
        tool_list_item_id: int
    ) -> bool:
        """
        Remove a tool from a tool list.

        Args:
            tool_list_item_id (int): ID of the tool list item to remove

        Returns:
            bool: True if removal was successful, False otherwise
        """
        pass

    @abstractmethod
    def complete_tool_list(self, tool_list_id: int) -> ToolList:
        """
        Mark a tool list as completed.

        Args:
            tool_list_id (int): ID of the tool list to complete

        Returns:
            ToolList: The completed tool list
        """
        pass