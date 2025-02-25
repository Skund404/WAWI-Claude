# services/interfaces/order_service.py
"""
Order service interface definitions.

This module defines the interface for order-related services,
which provide functionality for managing orders in the system.
"""

import enum
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Union


class OrderStatus(enum.Enum):
    """Enumeration of order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(enum.Enum):
    """Enumeration of payment statuses."""
    UNPAID = "unpaid"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"


class IOrderService(ABC):
    """
    Interface for order service.

    This interface defines the contract for services that manage orders
    in the leatherworking store management system.
    """

    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data: Dictionary containing order attributes

        Returns:
            Dictionary representing the created order

        Raises:
            ValidationError: If order data is invalid
        """
        pass

    @abstractmethod
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an order by ID.

        Args:
            order_id: ID of the order to retrieve

        Returns:
            Dictionary representing the order or None if not found

        Raises:
            NotFoundError: If order is not found
        """
        pass

    @abstractmethod
    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing order.

        Args:
            order_id: ID of the order to update
            order_data: Dictionary containing updated attributes

        Returns:
            Dictionary representing the updated order or None if not found

        Raises:
            ValidationError: If update data is invalid
            NotFoundError: If order is not found
        """
        pass

    @abstractmethod
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete

        Returns:
            True if the order was deleted, False otherwise

        Raises:
            NotFoundError: If order is not found
        """
        pass

    @abstractmethod
    def list_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[OrderStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List orders with optional filtering and pagination.

        Args:
            start_date: Filter orders from this date
            end_date: Filter orders up to this date
            status: Filter by order status
            payment_status: Filter by payment status
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            List of order dictionaries
        """
        pass

    @abstractmethod
    def search_orders(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for orders based on parameters.

        Args:
            search_params: Dictionary of search parameters

        Returns:
            List of dictionaries representing matching orders
        """
        pass

    @abstractmethod
    def update_order_status(self, order_id: int, new_status: OrderStatus) -> Optional[Dict[str, Any]]:
        """
        Update the status of an existing order.

        Args:
            order_id: ID of the order to update
            new_status: New status for the order

        Returns:
            Updated order dictionary or None if not found

        Raises:
            NotFoundError: If order is not found
            ValidationError: If status change is invalid
        """
        pass

    @abstractmethod
    def process_payment(self, order_id: int, payment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process payment for an order.

        Args:
            order_id: ID of the order to process payment for
            payment_data: Dictionary containing payment details

        Returns:
            Updated order dictionary with payment information

        Raises:
            NotFoundError: If order is not found
            ValidationError: If payment processing fails
        """
        pass

    @abstractmethod
    def generate_order_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report of orders.

        Args:
            start_date: Start date for the report
            end_date: End date for the report

        Returns:
            Dictionary containing order report metrics
        """
        pass

    @abstractmethod
    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add an item to an existing order.

        Args:
            order_id: ID of the order to add an item to
            item_data: Dictionary containing item details

        Returns:
            Updated order dictionary or None if not found

        Raises:
            NotFoundError: If order is not found
            ValidationError: If item data is invalid
        """
        pass

    @abstractmethod
    def remove_order_item(self, order_id: int, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Remove an item from an existing order.

        Args:
            order_id: ID of the order to remove an item from
            item_id: ID of the item to remove

        Returns:
            Updated order dictionary or None if not found

        Raises:
            NotFoundError: If order or item is not found
        """
        pass

    @abstractmethod
    def calculate_order_total(self, order_id: int) -> float:
        """
        Calculate the total cost of an order.

        Args:
            order_id: ID of the order to calculate total for

        Returns:
            Total cost of the order

        Raises:
            NotFoundError: If order is not found
        """
        pass


# Class type alias for backward compatibility
OrderService = IOrderService