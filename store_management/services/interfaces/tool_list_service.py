# services/interfaces/tool_list_service.py
from typing import Dict, List, Any, Optional, Protocol


class IToolListService(Protocol):
    """Interface for the ToolList Service.

    The ToolList Service manages tool lists for projects, tracks tool allocation,
    and handles tool returns for leatherworking projects.
    """

    def get_by_id(self, tool_list_id: int) -> Dict[str, Any]:
        """Retrieve a tool list by its ID.

        Args:
            tool_list_id: The ID of the tool list to retrieve

        Returns:
            A dictionary representation of the tool list

        Raises:
            NotFoundError: If the tool list with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all tool lists with optional filtering.

        Args:
            filters: Optional filters to apply to the tool list query

        Returns:
            List of dictionaries representing tool lists
        """
        ...

    def create_for_project(self, project_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new tool list for a project.

        Args:
            project_id: ID of the project
            notes: Optional notes about the tool list

        Returns:
            Dictionary representation of the created tool list

        Raises:
            NotFoundError: If the project does not exist
            ServiceError: If a tool list already exists for the project
        """
        ...

    def update(self, tool_list_id: int, tool_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool list.

        Args:
            tool_list_id: ID of the tool list to update
            tool_list_data: Dictionary containing updated tool list data

        Returns:
            Dictionary representation of the updated tool list

        Raises:
            NotFoundError: If the tool list with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, tool_list_id: int) -> bool:
        """Delete a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to delete

        Returns:
            True if the tool list was successfully deleted

        Raises:
            NotFoundError: If the tool list with the given ID does not exist
            ServiceError: If the tool list cannot be deleted (e.g., in progress)
        """
        ...

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tool lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of dictionaries representing tool lists for the project

        Raises:
            NotFoundError: If the project does not exist
        """
        ...

    def get_tool_list_items(self, tool_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a tool list.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            List of dictionaries representing tool list items

        Raises:
            NotFoundError: If the tool list does not exist
        """
        ...

    def add_tool(self, tool_list_id: int, tool_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Add a tool to a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_id: ID of the tool
            quantity: Quantity of the tool needed

        Returns:
            Dictionary representing the added tool list item

        Raises:
            NotFoundError: If the tool list or tool does not exist
            ValidationError: If the quantity is invalid
        """
        ...

    def remove_tool(self, tool_list_id: int, tool_item_id: int) -> bool:
        """Remove a tool from a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_item_id: ID of the tool list item

        Returns:
            True if the tool was successfully removed

        Raises:
            NotFoundError: If the tool list or item does not exist
            ServiceError: If the tool cannot be removed (e.g., already allocated)
        """
        ...

    def update_tool_quantity(self, tool_list_id: int,
                             tool_item_id: int,
                             quantity: int) -> Dict[str, Any]:
        """Update the quantity of a tool in a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_item_id: ID of the tool list item
            quantity: New quantity of the tool needed

        Returns:
            Dictionary representing the updated tool list item

        Raises:
            NotFoundError: If the tool list or item does not exist
            ValidationError: If the quantity is invalid
        """
        ...

    def allocate_tools(self, tool_list_id: int,
                       allocate_all: bool = False,
                       tool_item_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Allocate tools from inventory to a tool list.

        Args:
            tool_list_id: ID of the tool list
            allocate_all: Whether to allocate all tools in the list
            tool_item_ids: Optional list of specific tool items to allocate

        Returns:
            Dictionary with allocation results

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If both allocate_all and tool_item_ids are specified
            ServiceError: If insufficient tools are available
        """
        ...

    def return_tools(self, tool_list_id: int,
                     return_all: bool = False,
                     tool_item_ids: Optional[List[int]] = None,
                     condition_notes: Optional[Dict[int, str]] = None) -> Dict[str, Any]:
        """Return allocated tools to inventory.

        Args:
            tool_list_id: ID of the tool list
            return_all: Whether to return all tools in the list
            tool_item_ids: Optional list of specific tool items to return
            condition_notes: Optional dictionary mapping tool_item_ids to condition notes

        Returns:
            Dictionary with return results

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If both return_all and tool_item_ids are specified
        """
        ...

    def complete_tool_list(self, tool_list_id: int,
                           notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a tool list as complete.

        Args:
            tool_list_id: ID of the tool list
            notes: Optional notes about the completion

        Returns:
            Dictionary representing the updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If not all tools have been returned
        """
        ...

    def cancel_tool_list(self, tool_list_id: int, reason: str) -> Dict[str, Any]:
        """Cancel a tool list.

        Args:
            tool_list_id: ID of the tool list
            reason: Reason for cancellation

        Returns:
            Dictionary representing the updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ServiceError: If the tool list cannot be cancelled
        """
        ...

    def validate_tool_availability(self, tool_list_id: int) -> Dict[str, Any]:
        """Validate that sufficient tools are available for a tool list.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            Dictionary with validation results

        Raises:
            NotFoundError: If the tool list does not exist
        """
        ...