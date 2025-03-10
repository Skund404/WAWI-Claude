# services/interfaces/sales_service.py
# Protocol definition for sales service

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class ISalesService(Protocol):
    """Interface for sales-related operations."""

    def get_by_id(self, sales_id: int) -> Dict[str, Any]:
        """Get sale by ID.

        Args:
            sales_id: ID of the sale to retrieve

        Returns:
            Dict representing the sale

        Raises:
            NotFoundError: If sale not found
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all sales, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing sales
        """
        ...

    def create(self, sales_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sale.

        Args:
            sales_data: Dict containing sale properties

        Returns:
            Dict representing the created sale

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update(self, sales_id: int, sales_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing sale.

        Args:
            sales_id: ID of the sale to update
            sales_data: Dict containing updated sale properties

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If validation fails
        """
        ...

    def delete(self, sales_id: int) -> bool:
        """Delete a sale by ID.

        Args:
            sales_id: ID of the sale to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale not found
        """
        ...

    def add_item(self, sales_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to sale.

        Args:
            sales_id: ID of the sale
            item_data: Dict containing item properties

        Returns:
            Dict representing the created sales item

        Raises:
            NotFoundError: If sale or product not found
            ValidationError: If validation fails
        """
        ...

    def remove_item(self, sales_id: int, item_id: int) -> bool:
        """Remove item from sale.

        Args:
            sales_id: ID of the sale
            item_id: ID of the item

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale or item not found
        """
        ...

    def update_item(self, sales_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update item in sale.

        Args:
            sales_id: ID of the sale
            item_id: ID of the item
            item_data: Dict containing updated item properties

        Returns:
            Dict representing the updated item

        Raises:
            NotFoundError: If sale or item not found
            ValidationError: If validation fails
        """
        ...

    def update_status(self, sales_id: int, status: str) -> Dict[str, Any]:
        """Update sale status.

        Args:
            sales_id: ID of the sale
            status: New status

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If validation fails
        """
        ...

    def update_payment_status(self, sales_id: int, payment_status: str) -> Dict[str, Any]:
        """Update sale payment status.

        Args:
            sales_id: ID of the sale
            payment_status: New payment status

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If validation fails
        """
        ...

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales by customer ID.

        Args:
            customer_id: ID of the customer

        Returns:
            List of sales for the specified customer
        """
        ...

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get sales within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of sales within the specified date range
        """
        ...

    def calculate_total(self, sales_id: int) -> float:
        """Calculate total amount for a sale.

        Args:
            sales_id: ID of the sale

        Returns:
            Total amount

        Raises:
            NotFoundError: If sale not found
        """
        ...