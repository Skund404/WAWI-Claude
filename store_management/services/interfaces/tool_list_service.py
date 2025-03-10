from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IToolListService(Protocol):
    """Interface for tool list operations."""

    def get_by_id(self, tool_list_id: int) -> Dict[str, Any]:
        """Get tool list by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all tool lists, optionally filtered."""
        ...

    def create(self, tool_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool list."""
        ...

    def update(self, tool_list_id: int, tool_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool list."""
        ...

    def delete(self, tool_list_id: int) -> bool:
        """Delete a tool list by ID."""
        ...

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tool lists by project ID."""
        ...

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get tool lists by status."""
        ...

    def add_item(self, tool_list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a tool list."""
        ...

    def update_item(self, tool_list_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item in a tool list."""
        ...

    def remove_item(self, tool_list_id: int, item_id: int) -> bool:
        """Remove an item from a tool list."""
        ...

    def get_items(self, tool_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a tool list."""
        ...

    def checkout_tool(self, tool_list_id: int, item_id: int) -> Dict[str, Any]:
        """Checkout a tool from a tool list."""
        ...

    def return_tool(self, tool_list_id: int, item_id: int) -> Dict[str, Any]:
        """Return a tool to a tool list."""
        ...

    def complete_tool_list(self, tool_list_id: int) -> Dict[str, Any]:
        """Mark a tool list as completed."""
        ...

    def generate_for_project(self, project_id: int, project_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate a tool list for a project based on project type."""
        ...

    def get_project_recommended_tools(self, project_type: str) -> List[Dict[str, Any]]:
        """Get recommended tools for a project type."""
        ...