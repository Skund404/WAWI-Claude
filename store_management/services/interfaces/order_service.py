# services/interfaces/order_service.py

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


class OrderStatus(Enum):
    """
    Enum for order processing status.
    """
    PENDING = auto()  # Order received but not yet processed
    PROCESSING = auto()  # Order is being processed
    SHIPPED = auto()  # Order has been shipped
    DELIVERED = auto()  # Order has been delivered
    CANCELLED = auto()  # Order has been cancelled


class PaymentStatus(Enum):
    """
    Enum for order payment status.
    """
    UNPAID = auto()  # Payment not yet received
    PAID = auto()  # Payment received in full
    PARTIALLY_PAID = auto()  # Partial payment received
    REFUNDED = auto()  # Payment refunded


class IOrderService(ABC):
    """
    Interface for the Order Service.

    Defines methods for order management, including CRUD operations
    and order status management.
    """

    @abstractmethod
    def get_all_orders(
            self,
            status: Optional[OrderStatus] = None,
            payment_status: Optional[PaymentStatus] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            include_deleted: bool = False,
            page: int = 1,
            page_size: int = 50,
            sort_by: str = "order_date",
            sort_desc: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all orders with optional filtering, pagination, and sorting.

        Args:
            status: Filter by order status
            payment_status: Filter by payment status
            start_date: Filter by orders on or after this date
            end_date: Filter by orders on or before this date
            include_deleted: Whether to include soft-deleted orders
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order

        Returns:
            Tuple containing:
                - List of orders as dictionaries
                - Total count of orders matching the filters
        """
        pass

    @abstractmethod
    def get_order_by_id(self, order_id: int, include_items: bool = True) -> Dict[str, Any]:
        """
        Get order by ID.

        Args:
            order_id: ID of the order to retrieve
            include_items: Whether to include order items

        Returns:
            Order data as a dictionary

        Raises:
            NotFoundError: If order doesn't exist
        """
        pass

    @abstractmethod
    def get_order_by_number(self, order_number: str) -> Dict[str, Any]:
        """
        Get order by order number.

        Args:
            order_number: Order number to retrieve

        Returns:
            Order data as a dictionary

        Raises:
            NotFoundError: If order doesn't exist
        """
        pass

    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data: Order data

        Returns:
            Created order data

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.

        Args:
            order_id: ID of the order to update
            order_data: Updated order data

        Returns:
            Updated order data

        Raises:
            NotFoundError: If order doesn't exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def delete_order(self, order_id: int, permanent: bool = False) -> bool:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete
            permanent: Whether to permanently delete the order

        Returns:
            True if successful

        Raises:
            NotFoundError: If order doesn't exist
        """
        pass

    @abstractmethod
    def restore_order(self, order_id: int) -> Dict[str, Any]:
        """
        Restore a soft-deleted order.

        Args:
            order_id: ID of the order to restore

        Returns:
            Restored order data

        Raises:
            NotFoundError: If order doesn't exist
        """
        pass

    @abstractmethod
    def update_order_status(self, order_id: int, status: OrderStatus) -> Dict[str, Any]:
        """
        Update the status of an order.

        Args:
            order_id: ID of the order to update
            status: New status

        Returns:
            Updated order data

        Raises:
            NotFoundError: If order doesn't exist
        """
        pass

    @abstractmethod
    def update_payment_status(self, order_id: int, payment_status: PaymentStatus) -> Dict[str, Any]:
        """
        Update the payment status of an order.

        Args:
            order_id: ID of the order to update
            payment_status: New payment status

        Returns:
            Updated order data

        Raises:
            NotFoundError: If order doesn't exist
        """
        pass

    @abstractmethod
    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to an order.

        Args:
            order_id: ID of the order
            item_data: Item data including product_id, quantity, and unit_price

        Returns:
            Added order item data

        Raises:
            NotFoundError: If order doesn't exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def update_order_item(self, order_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an order item.

        Args:
            order_id: ID of the order
            item_id: ID of the item to update
            item_data: Updated item data

        Returns:
            Updated order item data

        Raises:
            NotFoundError: If order or item doesn't exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """
        Remove an item from an order.

        Args:
            order_id: ID of the order
            item_id: ID of the item to remove

        Returns:
            True if successful

        Raises:
            NotFoundError: If order or item doesn't exist
        """
        pass

    @abstractmethod
    def get_order_statistics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[
        str, Any]:
        """
        Get order statistics for a given period.

        Args:
            start_date: Start date for the period
            end_date: End date for the period

        Returns:
            Dictionary with order statistics
        """
        pass

    @abstractmethod
    def search_orders(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for orders by various criteria.

        Args:
            query: Search query string

        Returns:
            List of matching orders
        """
        pass