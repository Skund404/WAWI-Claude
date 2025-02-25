# Relative path: store_management/services/interfaces/order_service.py

"""
Order Service Interface Module

Defines the abstract base interface for order-related operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from di.core import inject
from services.interfaces import MaterialService


class OrderStatus(Enum):
    """Enumeration of possible order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class IOrderService(ABC):
    """
    Abstract base class defining the interface for Order Service operations.
    """

    @abstractmethod
    @inject(MaterialService)
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all orders.

        Returns:
            List[Dict[str, Any]]: List of order dictionaries
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            Optional[Dict[str, Any]]: Order details

        Raises:
            KeyError: If order with the given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data (Dict[str, Any]): Data for creating a new order

        Returns:
            Dict[str, Any]: Created order details

        Raises:
            ValueError: If order data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.

        Args:
            order_id (int): Unique identifier for the order
            order_data (Dict[str, Any]): Updated order information

        Returns:
            Dict[str, Any]: Updated order details

        Raises:
            KeyError: If order with the given ID does not exist
            ValueError: If order data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            bool: True if deletion was successful

        Raises:
            KeyError: If order with the given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_orders_by_status(self, status: OrderStatus) -> List[Dict[str, Any]]:
        """
        Retrieve orders by their status.

        Args:
            status (OrderStatus): Status to filter orders by

        Returns:
            List[Dict[str, Any]]: List of orders with the specified status
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Retrieve orders within a specific date range.

        Args:
            start_date (datetime): Start of the date range
            end_date (datetime): End of the date range

        Returns:
            List[Dict[str, Any]]: List of orders within the date range
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_supplier_orders(self, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all orders for a specific supplier.

        Args:
            supplier_id (int): Unique identifier for the supplier

        Returns:
            List[Dict[str, Any]]: List of orders for the specified supplier
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def generate_order_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate a comprehensive order report for a given period.

        Args:
            start_date (datetime): Start of the reporting period
            end_date (datetime): End of the reporting period

        Returns:
            Dict[str, Any]: Detailed order report
        """
        pass