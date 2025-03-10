from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IPickingListService(Protocol):
    """Interface for picking list operations."""

    def get_by_id(self, picking_list_id: int) -> Dict[str, Any]:
        """Get picking list by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all picking lists, optionally filtered."""
        ...

    def create(self, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new picking list."""
        ...

    def update(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing picking list."""
        ...

    def delete(self, picking_list_id: int) -> bool:
        """Delete a picking list by ID."""
        ...

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get picking lists by project ID."""
        ...

    def get_by_sales(self, sales_id: int) -> List[Dict[str, Any]]:
        """Get picking lists by sales ID."""
        ...

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get picking lists by status."""
        ...

    def add_item(self, picking_list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a picking list."""
        ...

    def update_item(self, picking_list_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item in a picking list."""
        ...

    def remove_item(self, picking_list_id: int, item_id: int) -> bool:
        """Remove an item from a picking list."""
        ...

    def get_items(self, picking_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a picking list."""
        ...

    def process_picking_list(self, picking_list_id: int, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a picking list (mark items as picked, update inventory)."""
        ...

    def complete_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """Mark a picking list as completed."""
        ...

    def generate_from_project(self, project_id: int) -> Dict[str, Any]:
        """Generate a picking list from a project."""
        ...