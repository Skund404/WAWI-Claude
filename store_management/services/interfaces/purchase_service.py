purchase_service# services/interfaces/purchase_service.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

class IPurchaseService(Protocol):
    """Protocol defining the purchase service interface."""

    def get_all_purchases(self) -> List[Dict[str, Any]]:
        """Get all purchases.

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries
        """
        ...

    def get_purchase_by_id(self, purchase_id: int) -> Dict[str, Any]:
        """Get purchase by ID.

        Args:
            purchase_id: ID of the purchase

        Returns:
            Dict[str, Any]: Purchase dictionary

        Raises:
            NotFoundError: If purchase not found
        """
        ...

    def create_purchase(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase order.

        Args:
            purchase_data: Purchase data dictionary

        Returns:
            Dict[str, Any]: Created purchase dictionary

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update_purchase(self, purchase_id: int, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing purchase.

        Args:
            purchase_id: ID of the purchase to update
            purchase_data: Updated purchase data

        Returns:
            Dict[str, Any]: Updated purchase dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        ...

    def delete_purchase(self, purchase_id: int) -> bool:
        """Delete a purchase.

        Args:
            purchase_id: ID of the purchase to delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If purchase not found
        """
        ...

    def add_purchase_item(self, purchase_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a purchase.

        Args:
            purchase_id: ID of the purchase
            item_data: Purchase item data

        Returns:
            Dict[str, Any]: Created purchase item dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        ...

    def update_purchase_status(self, purchase_id: int, status: str) -> Dict[str, Any]:
        """Update the status of a purchase.

        Args:
            purchase_id: ID of the purchase
            status: New status value

        Returns:
            Dict[str, Any]: Updated purchase dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        ...

    def receive_purchase(self, purchase_id: int, received_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mark a purchase as received and update inventory.

        Args:
            purchase_id: ID of the purchase
            received_items: List of received items with quantities

        Returns:
            Dict[str, Any]: Updated purchase dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        ...

    def get_purchases_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get purchases by supplier ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries

        Raises:
            NotFoundError: If supplier not found
        """
        ...

    def get_purchases_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get purchases within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries
        """
        ...