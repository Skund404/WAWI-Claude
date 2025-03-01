# services/interfaces/picking_list_service.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from models.picking_list import PickingListStatus


class IPickingListService(ABC):
    """Interface for picking list operations."""

    @abstractmethod
    def create_picking_list(self, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new picking list."""
        pass

    @abstractmethod
    def get_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """Get a picking list by ID."""
        pass

    @abstractmethod
    def get_all_picking_lists(self) -> List[Dict[str, Any]]:
        """Get all picking lists."""
        pass

    @abstractmethod
    def get_picking_lists_by_status(self, status: PickingListStatus) -> List[Dict[str, Any]]:
        """Get picking lists by status."""
        pass

    @abstractmethod
    def update_picking_list(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a picking list."""
        pass

    @abstractmethod
    def delete_picking_list(self, picking_list_id: int) -> bool:
        """Delete a picking list."""
        pass

    @abstractmethod
    def add_item_to_picking_list(self, picking_list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a picking list."""
        pass

    @abstractmethod
    def update_picking_list_item(self, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a picking list item."""
        pass

    @abstractmethod
    def remove_item_from_picking_list(self, item_id: int) -> bool:
        """Remove an item from a picking list."""
        pass

    @abstractmethod
    def mark_item_as_picked(self, item_id: int, quantity: float = None) -> Dict[str, Any]:
        """Mark an item as picked, optionally with a specific quantity."""
        pass

    @abstractmethod
    def generate_picking_list_from_project(self, project_id: int) -> Dict[str, Any]:
        """Generate a picking list from a project's required materials."""
        pass

    @abstractmethod
    def generate_picking_list_from_order(self, order_id: int) -> Dict[str, Any]:
        """Generate a picking list from an order's items."""
        pass

    @abstractmethod
    def complete_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """Mark a picking list as completed."""
        pass