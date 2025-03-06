# services/interfaces/sale_service.py

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


class SaleStatus(Enum):
    """
    Enum for sale processing status.
    """
    PENDING = auto()  # Sale received but not yet processed
    PROCESSING = auto()  # Sale is being processed
    SHIPPED = auto()  # Sale has been shipped
    DELIVERED = auto()  # Sale has been delivered
    CANCELLED = auto()  # Sale has been cancelled


class PaymentStatus(Enum):
    """
    Enum for sale payment status.
    """
    UNPAID = auto()  # Payment not yet received
    PAID = auto()  # Payment received in full
    PARTIALLY_PAID = auto()  # Partial payment received
    REFUNDED = auto()  # Payment refunded


class ISaleService(ABC):
    """
    Interface for the Sale Service.

    Defines methods for sale management, including CRUD operations
    and sale status management.
    """

    @abstractmethod
    def get_all_sales(
            self,
            status: Optional[SaleStatus] = None,
            payment_status: Optional[PaymentStatus] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            include_deleted: bool = False,
            page: int = 1,
            page_size: int = 50,
            sort_by: str = "sale_date",
            sort_desc: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all sales with optional filtering, pagination, and sorting.

        Args:
            status: Filter by sale status
            payment_status: Filter by payment status
            start_date: Filter by sales on or after this date
            end_date: Filter by sales on or before this date
            include_deleted: Whether to include soft-deleted sales
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending sale

        Returns:
            Tuple containing:
                - List of sales as dictionaries
                - Total count of sales matching the filters
        """
        pass

    @abstractmethod
    def get_sale_by_id(self, sale_id: int, include_items: bool = True) -> Dict[str, Any]:
        """
        Get sale by ID.

        Args:
            sale_id: ID of the sale to retrieve
            include_items: Whether to include sale items

        Returns:
            Sale data as a dictionary

        Raises:
            NotFoundError: If sale doesn't exist
        """
        pass

    @abstractmethod
    def get_sale_by_number(self, sale_number: str) -> Dict[str, Any]:
        """
        Get sale by sale number.

        Args:
            sale_number: Sale number to retrieve

        Returns:
            Sale data as a dictionary

        Raises:
            NotFoundError: If sale doesn't exist
        """
        pass

    @abstractmethod
    def create_sale(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new sale.

        Args:
            sale_data: Sale data

        Returns:
            Created sale data

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def update_sale(self, sale_id: int, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing sale.

        Args:
            sale_id: ID of the sale to update
            sale_data: Updated sale data

        Returns:
            Updated sale data

        Raises:
            NotFoundError: If sale doesn't exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def delete_sale(self, sale_id: int, permanent: bool = False) -> bool:
        """
        Delete an sale.

        Args:
            sale_id: ID of the sale to delete
            permanent: Whether to permanently delete the sale

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale doesn't exist
        """
        pass

    @abstractmethod
    def restore_sale(self, sale_id: int) -> Dict[str, Any]:
        """
        Restore a soft-deleted sale.

        Args:
            sale_id: ID of the sale to restore

        Returns:
            Restored sale data

        Raises:
            NotFoundError: If sale doesn't exist
        """
        pass

    @abstractmethod
    def update_sale_status(self, sale_id: int, status: SaleStatus) -> Dict[str, Any]:
        """
        Update the status of an sale.

        Args:
            sale_id: ID of the sale to update
            status: New status

        Returns:
            Updated sale data

        Raises:
            NotFoundError: If sale doesn't exist
        """
        pass

    @abstractmethod
    def update_payment_status(self, sale_id: int, payment_status: PaymentStatus) -> Dict[str, Any]:
        """
        Update the payment status of an sale.

        Args:
            sale_id: ID of the sale to update
            payment_status: New payment status

        Returns:
            Updated sale data

        Raises:
            NotFoundError: If sale doesn't exist
        """
        pass

    @abstractmethod
    def add_sale_item(self, sale_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to an sale.

        Args:
            sale_id: ID of the sale
            item_data: Item data including product_id, quantity, and unit_price

        Returns:
            Added sale item data

        Raises:
            NotFoundError: If sale doesn't exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def update_sale_item(self, sale_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an sale item.

        Args:
            sale_id: ID of the sale
            item_id: ID of the item to update
            item_data: Updated item data

        Returns:
            Updated sale item data

        Raises:
            NotFoundError: If sale or item doesn't exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def remove_sale_item(self, sale_id: int, item_id: int) -> bool:
        """
        Remove an item from an sale.

        Args:
            sale_id: ID of the sale
            item_id: ID of the item to remove

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale or item doesn't exist
        """
        pass

    @abstractmethod
    def get_sale_statistics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[
        str, Any]:
        """
        Get sale statistics for a given period.

        Args:
            start_date: Start date for the period
            end_date: End date for the period

        Returns:
            Dictionary with sale statistics
        """
        pass

    @abstractmethod
    def search_sales(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for sales by various criteria.

        Args:
            query: Search query string

        Returns:
            List of matching sales
        """
        pass