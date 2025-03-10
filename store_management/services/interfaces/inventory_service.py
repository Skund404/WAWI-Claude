# services/interfaces/inventory_service.py
# Protocol definition for inventory service

from typing import Protocol, List, Optional, Dict, Any, Union
from datetime import datetime


class IInventoryService(Protocol):
    """Interface for inventory-related operations."""

    def get_by_id(self, inventory_id: int) -> Dict[str, Any]:
        """Get inventory entry by ID.

        Args:
            inventory_id: ID of the inventory entry to retrieve

        Returns:
            Dict representing the inventory entry

        Raises:
            NotFoundError: If inventory entry not found
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all inventory entries, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing inventory entries
        """
        ...

    def create(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new inventory entry.

        Args:
            inventory_data: Dict containing inventory properties

        Returns:
            Dict representing the created inventory entry

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing inventory entry.

        Args:
            inventory_id: ID of the inventory entry to update
            inventory_data: Dict containing updated inventory properties

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        ...

    def delete(self, inventory_id: int) -> bool:
        """Delete an inventory entry by ID.

        Args:
            inventory_id: ID of the inventory entry to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If inventory entry not found
        """
        ...

    def get_by_item(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get inventory entry by item type and ID.

        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item

        Returns:
            Dict representing the inventory entry

        Raises:
            NotFoundError: If inventory entry not found
        """
        ...

    def adjust_quantity(self, inventory_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust quantity for an inventory entry.

        Args:
            inventory_id: ID of the inventory entry
            quantity: Quantity to adjust (positive for increase, negative for decrease)
            reason: Reason for adjustment

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        ...

    def get_low_stock_items(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get inventory items with low stock levels.

        Args:
            threshold: Optional threshold for what's considered "low stock"

        Returns:
            List of inventory items with low stock
        """
        ...

    def log_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an inventory transaction.

        Args:
            transaction_data: Dict containing transaction properties

        Returns:
            Dict representing the created transaction

        Raises:
            ValidationError: If validation fails
        """
        ...

    def get_transaction_history(self,
                                item_type: Optional[str] = None,
                                item_id: Optional[int] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get transaction history for an item or date range.

        Args:
            item_type: Optional type of the item (material, product, tool)
            item_id: Optional ID of the item
            start_date: Optional start date for the range
            end_date: Optional end date for the range

        Returns:
            List of transactions matching the criteria
        """
        ...

    def update_storage_location(self, inventory_id: int, location: str) -> Dict[str, Any]:
        """Update storage location for an inventory entry.

        Args:
            inventory_id: ID of the inventory entry
            location: New storage location

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        ...

    def update_status(self, inventory_id: int, status: str) -> Dict[str, Any]:
        """Update status for an inventory entry.

        Args:
            inventory_id: ID of the inventory entry
            status: New status

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        ...

    def get_item_availability(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get availability information for an item.

        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item

        Returns:
            Dict with availability information

        Raises:
            NotFoundError: If item not found
        """
        ...