# services/interfaces/order_service.py
"""
Interface definition for Order Service in the leatherworking store management application.

Defines the contract for order-related operations and provides
default implementations where possible.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable


class OrderStatus(Enum):
    """Enumeration of possible order statuses."""
    PENDING = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


class PaymentStatus(Enum):
    """Enumeration of possible payment statuses."""
    UNPAID = auto()
    PAID = auto()
    PARTIALLY_PAID = auto()
    REFUNDED = auto()


class IOrderService(ABC):
    """
    Abstract base class defining the contract for order-related services.

    Provides methods for managing orders with default implementations
    where possible.
    """

    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Optional[Any]:
        """
        Create a new order.

        Args:
            order_data (Dict[str, Any]): Data for creating the order

        Returns:
            Optional[Any]: Created order or None if creation fails
        """
        raise NotImplementedError("Subclass must implement create_order method")

    @abstractmethod
    def get_order(self, order_id: int) -> Optional[Any]:
        """
        Retrieve an order by its ID.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            Optional[Any]: Retrieved order or None
        """
        raise NotImplementedError("Subclass must implement get_order method")

    @abstractmethod
    def get_orders(
            self,
            status: Optional[OrderStatus] = None,
            date_range: Optional[Tuple[datetime, datetime]] = None,
            payment_status: Optional[PaymentStatus] = None
    ) -> List[Any]:
        """
        Retrieve orders with optional filtering.

        Args:
            status (Optional[OrderStatus]): Filter by order status
            date_range (Optional[Tuple[datetime, datetime]]): Filter by date range
            payment_status (Optional[PaymentStatus]): Filter by payment status

        Returns:
            List[Any]: List of matching orders
        """
        raise NotImplementedError("Subclass must implement get_orders method")

    @abstractmethod
    def update_order(
            self,
            order_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Update an existing order.

        Args:
            order_id (int): ID of the order to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Any]: Updated order or None if update fails
        """
        raise NotImplementedError("Subclass must implement update_order method")

    @abstractmethod
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        raise NotImplementedError("Subclass must implement delete_order method")

    @abstractmethod
    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Optional[Any]:
        """
        Add an item to an existing order.

        Args:
            order_id (int): ID of the order to modify
            item_data (Dict[str, Any]): Data for the new order item

        Returns:
            Optional[Any]: Added order item or None if addition fails
        """
        raise NotImplementedError("Subclass must implement add_order_item method")

    @abstractmethod
    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """
        Remove an item from an existing order.

        Args:
            order_id (int): ID of the order to modify
            item_id (int): ID of the item to remove

        Returns:
            bool: True if item removal was successful, False otherwise
        """
        raise NotImplementedError("Subclass must implement remove_order_item method")

    @abstractmethod
    def update_order_status(
            self,
            order_id: int,
            new_status: OrderStatus
    ) -> Optional[Any]:
        """
        Update the status of an existing order.

        Args:
            order_id (int): ID of the order to update
            new_status (OrderStatus): New status for the order

        Returns:
            Optional[Any]: Updated order or None if update fails
        """
        raise NotImplementedError("Subclass must implement update_order_status method")

    @abstractmethod
    def process_payment(
            self,
            order_id: int,
            payment_amount: float
    ) -> Optional[Any]:
        """
        Process payment for an order.

        Args:
            order_id (int): ID of the order to process payment for
            payment_amount (float): Amount of payment

        Returns:
            Optional[Any]: Updated order or None if payment processing fails
        """
        raise NotImplementedError("Subclass must implement process_payment method")

    @abstractmethod
    def calculate_order_total(self, order_id: int) -> Optional[float]:
        """
        Calculate the total cost of an order.

        Args:
            order_id (int): ID of the order to calculate total for

        Returns:
            Optional[float]: Total cost of the order or None if calculation fails
        """
        raise NotImplementedError("Subclass must implement calculate_order_total method")

    @abstractmethod
    def generate_order_report(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a report of orders within a specified date range.

        Args:
            start_date (Optional[datetime]): Start of date range
            end_date (Optional[datetime]): End of date range

        Returns:
            List[Dict[str, Any]]: List of order reports
        """
        raise NotImplementedError("Subclass must implement generate_order_report method")

    @abstractmethod
    def search_orders(
            self,
            search_term: str,
            search_fields: Optional[List[str]] = None
    ) -> List[Any]:
        """
        Search for orders based on a search term.

        Args:
            search_term (str): Term to search for
            search_fields (Optional[List[str]]): Fields to search in

        Returns:
            List[Any]: List of matching orders
        """
        raise NotImplementedError("Subclass must implement search_orders method")

    @abstractmethod
    def list_orders(
            self,
            page: int = 1,
            per_page: int = 10,
            sort_by: Optional[str] = None
    ) -> List[Any]:
        """
        List orders with pagination and optional sorting.

        Args:
            page (int): Page number
            per_page (int): Number of orders per page
            sort_by (Optional[str]): Field to sort by

        Returns:
            List[Any]: List of orders for the specified page
        """
        raise NotImplementedError("Subclass must implement list_orders method")