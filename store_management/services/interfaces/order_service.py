# Path: services/interfaces/order_service.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.models.order import OrderStatus


class IOrderService(ABC):
    """
    Abstract base class defining the interface for Order Service operations.
    """

    @abstractmethod
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all orders.

        Returns:
            List[Dict[str, Any]]: List of order dictionaries
        """
        pass

    @abstractmethod
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            Optional[Dict[str, Any]]: Order details
        """
        pass

    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data (Dict[str, Any]): Data for creating a new order

        Returns:
            Dict[str, Any]: Created order details
        """
        pass

    @abstractmethod
    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.

        Args:
            order_id (int): Unique identifier for the order
            order_data (Dict[str, Any]): Updated order information

        Returns:
            Dict[str, Any]: Updated order details
        """
        pass

    @abstractmethod
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            bool: True if deletion was successful
        """
        pass

    @abstractmethod
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