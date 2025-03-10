from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IToolService(Protocol):
    """Interface for tool-related operations."""

    def get_by_id(self, tool_id: int) -> Dict[str, Any]:
        """Get tool by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all tools, optionally filtered."""
        ...

    def create(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool."""
        ...

    def update(self, tool_id: int, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool."""
        ...

    def delete(self, tool_id: int) -> bool:
        """Delete a tool by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for tools by name or other properties."""
        ...

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get tools by category."""
        ...

    def get_inventory_status(self, tool_id: int) -> Dict[str, Any]:
        """Get inventory status for a tool."""
        ...

    def adjust_inventory(self, tool_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a tool."""
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get tools by supplier ID."""
        ...

    def record_maintenance(self, tool_id: int, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record maintenance for a tool."""
        ...

    def get_maintenance_history(self, tool_id: int) -> List[Dict[str, Any]]:
        """Get maintenance history for a tool."""
        ...

    def get_tools_due_maintenance(self) -> List[Dict[str, Any]]:
        """Get tools that are due for maintenance."""
        ...

    def get_usage_history(self, tool_id: int) -> List[Dict[str, Any]]:
        """Get usage history for a tool."""
        ...