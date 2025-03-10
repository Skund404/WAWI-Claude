# services/interfaces/tool_service.py
from typing import Dict, List, Any, Optional, Protocol
from datetime import datetime


class IToolService(Protocol):
    """Interface for the Tool Service.

    The Tool Service handles operations related to leatherworking tools,
    including inventory management, maintenance tracking, and usage in projects.
    """

    def get_by_id(self, tool_id: int) -> Dict[str, Any]:
        """Retrieve a tool by its ID.

        Args:
            tool_id: The ID of the tool to retrieve

        Returns:
            A dictionary representation of the tool

        Raises:
            NotFoundError: If the tool with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all tools with optional filtering.

        Args:
            filters: Optional filters to apply to the tool query

        Returns:
            List of dictionaries representing tools
        """
        ...

    def create(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool.

        Args:
            tool_data: Dictionary containing tool data

        Returns:
            Dictionary representation of the created tool

        Raises:
            ValidationError: If the tool data is invalid
        """
        ...

    def update(self, tool_id: int, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool.

        Args:
            tool_id: ID of the tool to update
            tool_data: Dictionary containing updated tool data

        Returns:
            Dictionary representation of the updated tool

        Raises:
            NotFoundError: If the tool with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, tool_id: int) -> bool:
        """Delete a tool by its ID.

        Args:
            tool_id: ID of the tool to delete

        Returns:
            True if the tool was successfully deleted

        Raises:
            NotFoundError: If the tool with the given ID does not exist
            ServiceError: If the tool cannot be deleted (e.g., in use)
        """
        ...

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find tools by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching tools
        """
        ...

    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Find tools by category.

        Args:
            category: Tool category to filter by

        Returns:
            List of dictionaries representing tools in the specified category
        """
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Find tools provided by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of dictionaries representing tools from the supplier

        Raises:
            NotFoundError: If the supplier does not exist
        """
        ...

    def record_maintenance(self, tool_id: int,
                           maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record maintenance performed on a tool.

        Args:
            tool_id: ID of the tool
            maintenance_data: Dictionary containing maintenance information

        Returns:
            Dictionary representing the maintenance record

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the maintenance data is invalid
        """
        ...

    def get_maintenance_history(self, tool_id: int) -> List[Dict[str, Any]]:
        """Get the maintenance history for a tool.

        Args:
            tool_id: ID of the tool

        Returns:
            List of dictionaries containing maintenance records

        Raises:
            NotFoundError: If the tool does not exist
        """
        ...

    def schedule_maintenance(self, tool_id: int,
                             scheduled_date: datetime,
                             maintenance_type: str,
                             notes: Optional[str] = None) -> Dict[str, Any]:
        """Schedule maintenance for a tool.

        Args:
            tool_id: ID of the tool
            scheduled_date: Date when maintenance is scheduled
            maintenance_type: Type of maintenance to perform
            notes: Optional notes about the scheduled maintenance

        Returns:
            Dictionary representing the scheduled maintenance

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the maintenance data is invalid
        """
        ...

    def check_out_tool(self, tool_id: int,
                       project_id: Optional[int] = None,
                       user_id: Optional[int] = None,
                       quantity: int = 1,
                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Check out a tool for use.

        Args:
            tool_id: ID of the tool
            project_id: Optional ID of the project the tool is used for
            user_id: Optional ID of the user checking out the tool
            quantity: Quantity of tools to check out
            notes: Optional notes about the checkout

        Returns:
            Dictionary representing the checkout record

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the checkout data is invalid or insufficient tools available
        """
        ...

    def check_in_tool(self, tool_id: int,
                      checkout_id: int,
                      condition_notes: Optional[str] = None,
                      quantity: Optional[int] = None) -> Dict[str, Any]:
        """Check in a previously checked out tool.

        Args:
            tool_id: ID of the tool
            checkout_id: ID of the checkout record
            condition_notes: Optional notes about the condition of the tool
            quantity: Optional quantity to check in (defaults to all checked out)

        Returns:
            Dictionary representing the checkin record

        Raises:
            NotFoundError: If the tool or checkout record does not exist
            ValidationError: If the checkin data is invalid
        """
        ...

    def get_checked_out_tools(self,
                              project_id: Optional[int] = None,
                              user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get a list of currently checked out tools.

        Args:
            project_id: Optional ID of the project to filter by
            user_id: Optional ID of the user to filter by

        Returns:
            List of dictionaries representing checked out tools
        """
        ...

    def update_tool_condition(self, tool_id: int,
                              condition: str,
                              notes: Optional[str] = None) -> Dict[str, Any]:
        """Update the condition of a tool.

        Args:
            tool_id: ID of the tool
            condition: New condition of the tool
            notes: Optional notes about the condition

        Returns:
            Dictionary representing the updated tool

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the condition is invalid
        """
        ...