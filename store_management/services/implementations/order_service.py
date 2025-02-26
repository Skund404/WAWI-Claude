# services/implementations/order_service.py
"""
Implementation of the OrderService interface. Provides functionality
for managing orders in the leatherworking store.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from services.interfaces.order_service import IOrderService, OrderStatus, PaymentStatus

# Configure logger
logger = logging.getLogger(__name__)


class OrderService(IOrderService):
    """Implementation of the order service interface."""

    def __init__(self):
        """Initialize the Order Service."""
        logger.info("OrderService initialized")

    def get_order(self, order_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get an order by ID.

        Args:
            order_id: ID of the order to retrieve

        Returns:
            Dictionary representing the order

        Raises:
            NotFoundError: If order is not found
        """
        logger.debug(f"Get order with ID: {order_id}")

        # Return dummy data for now
        return {
            "id": order_id,
            "customer_name": f"Customer {order_id}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": OrderStatus.PENDING.name,
            "total_items": 3,
            "total_amount": 150.00,
            "payment_status": PaymentStatus.UNPAID.name
        }

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Get all orders.

        Returns:
            List of dictionaries representing orders
        """
        logger.debug("Get all orders")

        # Return dummy data for now
        orders = []
        statuses = [status.name for status in OrderStatus]
        payment_statuses = [status.name for status in PaymentStatus]

        base_date = datetime.now()

        for i in range(1, 11):
            order_date = (base_date - timedelta(days=i * 3)).strftime("%Y-%m-%d")
            status_idx = (i - 1) % len(statuses)
            payment_idx = (i - 1) % len(payment_statuses)

            order = {
                "id": i,
                "customer_name": f"Customer {i}",
                "date": order_date,
                "status": statuses[status_idx],
                "total_items": i + 2,
                "total_amount": float(i * 50),
                "payment_status": payment_statuses[payment_idx]
            }
            orders.append(order)

        logger.info(f"Retrieved {len(orders)} orders")
        return orders

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data: Dictionary with order properties

        Returns:
            Dictionary representing the created order

        Raises:
            ValidationError: If order data is invalid
        """
        logger.debug(f"Create order with data: {order_data}")

        # Return dummy data for now
        return {
            "id": 999,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": OrderStatus.NEW.name,
            **order_data
        }

    def update_order(self, order_id: Union[int, str], order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.

        Args:
            order_id: ID of the order to update
            order_data: Dictionary with updated order properties

        Returns:
            Dictionary representing the updated order

        Raises:
            NotFoundError: If order is not found
            ValidationError: If order data is invalid
        """
        logger.debug(f"Update order {order_id} with data: {order_data}")

        # Get existing order and update it
        order = self.get_order(order_id)
        order.update(order_data)

        logger.info(f"Updated order: {order_id}")
        return order

    def delete_order(self, order_id: Union[int, str]) -> bool:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If order is not found
        """
        logger.debug(f"Delete order with ID: {order_id}")

        # Pretend we deleted it
        logger.info(f"Deleted order: {order_id}")
        return True

    def add_order_item(self, order_id: Union[int, str], item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to an order.

        Args:
            order_id: ID of the order
            item_data: Dictionary with item properties

        Returns:
            Dictionary representing the added item

        Raises:
            NotFoundError: If order is not found
            ValidationError: If item data is invalid
        """
        logger.debug(f"Add item to order {order_id}: {item_data}")

        # Return dummy data for now
        return {
            "id": 1,
            "order_id": order_id,
            **item_data
        }

    def remove_order_item(self, order_id: Union[int, str], item_id: Union[int, str]) -> bool:
        """
        Remove an item from an order.

        Args:
            order_id: ID of the order
            item_id: ID of the item to remove

        Returns:
            True if removal was successful

        Raises:
            NotFoundError: If order or item is not found
        """
        logger.debug(f"Remove item {item_id} from order {order_id}")

        # Pretend we removed it
        logger.info(f"Removed item {item_id} from order {order_id}")
        return True

    def get_order_items(self, order_id: Union[int, str]) -> List[Dict[str, Any]]:
        """
        Get all items in an order.

        Args:
            order_id: ID of the order

        Returns:
            List of dictionaries representing order items

        Raises:
            NotFoundError: If order is not found
        """
        logger.debug(f"Get items for order {order_id}")

        # Return dummy data for now
        items = []
        for i in range(1, 4):
            item = {
                "id": i,
                "order_id": order_id,
                "product_id": i * 10,
                "product_name": f"Product {i * 10}",
                "quantity": i,
                "unit_price": 50.0,
                "total_price": 50.0 * i
            }
            items.append(item)

        logger.info(f"Retrieved {len(items)} items for order {order_id}")
        return items

    def update_order_status(self, order_id: Union[int, str], status: OrderStatus) -> Dict[str, Any]:
        """
        Update the status of an order.

        Args:
            order_id: ID of the order
            status: New order status

        Returns:
            Dictionary representing the updated order

        Raises:
            NotFoundError: If order is not found
        """
        logger.debug(f"Update order {order_id} status to {status}")

        # Get existing order and update status
        order = self.get_order(order_id)
        order["status"] = status.name

        logger.info(f"Updated order {order_id} status to {status}")
        return order

    def update_payment_status(self, order_id: Union[int, str], status: PaymentStatus) -> Dict[str, Any]:
        """
        Update the payment status of an order.

        Args:
            order_id: ID of the order
            status: New payment status

        Returns:
            Dictionary representing the updated order

        Raises:
            NotFoundError: If order is not found
        """
        logger.debug(f"Update order {order_id} payment status to {status}")

        # Get existing order and update payment status
        order = self.get_order(order_id)
        order["payment_status"] = status.name

        logger.info(f"Updated order {order_id} payment status to {status}")
        return order