# services/interfaces/order_service.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from database.models.order import Order
from database.models.enums import OrderStatus


class IOrderService(ABC):
    """
    Interface defining the contract for order management services.

    This interface specifies all operations that must be supported by
    any order service implementation.
    """

    @abstractmethod
    def get_all_orders(self) -> List[Order]:
        """
        Get all orders in the system.

        Returns:
            List of Order objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Get an order by its ID.

        Args:
            order_id: ID of the order to retrieve

        Returns:
            Order object if found, None otherwise

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """
        Get an order by its order number.

        Args:
            order_number: Order number to search for

        Returns:
            Order object if found, None otherwise

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """
        Create a new order.

        Args:
            order_data: Dictionary containing order data

        Returns:
            Created Order object

        Raises:
            Exception: If creation fails
        """
        pass

    @abstractmethod
    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Order:
        """
        Update an existing order.

        Args:
            order_id: ID of the order to update
            order_data: Dictionary containing updated order data

        Returns:
            Updated Order object

        Raises:
            Exception: If update fails
        """
        pass

    @abstractmethod
    def delete_order(self, order_id: int) -> None:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    def process_order_payment(self, order_id: int, payment_amount: float) -> Order:
        """
        Process a payment for an order.

        Args:
            order_id: ID of the order
            payment_amount: Amount being paid

        Returns:
            Updated Order object

        Raises:
            Exception: If payment processing fails
        """
        pass

    @abstractmethod
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Get all orders with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of matching Order objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_orders_by_customer(self, customer_name: str) -> List[Order]:
        """
        Get all orders for a specific customer.

        Args:
            customer_name: Name of the customer

        Returns:
            List of matching Order objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about orders.

        Returns:
            Dictionary containing order statistics

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        pass