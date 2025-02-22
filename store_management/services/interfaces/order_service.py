# Path: store_management/services/interfaces/order_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from services.interfaces.base_service import IBaseService


class IOrderService(IBaseService):
    """
    Interface for order management operations.

    Defines the contract for services handling order-related functionality.
    """

    @abstractmethod
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all orders.

        Returns:
            List of order dictionaries
        """
        pass

    @abstractmethod
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Get order details by ID.

        Args:
            order_id: Order ID

        Returns:
            Order details or None if not found
        """
        pass

    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new order.

        Args:
            order_data: Dictionary with order data

        Returns:
            Created order or None
        """
        pass

    @abstractmethod
    def update_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing order.

        Args:
            order_data: Dictionary with updated order information

        Returns:
            Updated order or None
        """
        pass

    @abstractmethod
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete

        Returns:
            True if deletion successful, False otherwise
        """
        pass