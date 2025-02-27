# services/implementations/order_service_debug.py
"""
Simplified debug version of the order service implementation to help identify issues.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from services.interfaces.order_service import IOrderService, OrderStatus, PaymentStatus

# Configure logger
logger = logging.getLogger(__name__)


class OrderService(IOrderService):
    """Simplified implementation of the order service interface for debugging."""

    def __init__(self):
        """Initialize the Order Service."""
        logger.info("Debug OrderService initialized")

    def get_order(self, order_id: Union[int, str]) -> Dict[str, Any]:
        """Get an order by ID."""
        logger.debug(f"Debug get_order called with ID: {order_id}")
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
        """Get all orders."""
        logger.debug("Debug get_all_orders called")

        # Return some dummy data
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

        return orders

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order."""
        logger.debug(f"Debug create_order called with: {order_data}")
        return {"id": 1, "date": datetime.now().strftime("%Y-%m-%d"), **order_data}

    def update_order(self, order_id: Union[int, str], order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an order."""
        logger.debug(f"Debug update_order called with ID: {order_id}, data: {order_data}")
        order = self.get_order(order_id)
        order.update(order_data)
        return order

    def delete_order(self, order_id: Union[int, str]) -> bool:
        """Delete an order."""
        logger.debug(f"Debug delete_order called with ID: {order_id}")
        return True

    def add_order_item(self, order_id: Union[int, str], item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to an order."""
        logger.debug(f"Debug add_order_item called with order ID: {order_id}, item: {item_data}")
        return {
            "id": 1,
            "order_id": order_id,
            **item_data
        }

    def remove_order_item(self, order_id: Union[int, str], item_id: Union[int, str]) -> bool:
        """Remove an item from an order."""
        logger.debug(f"Debug remove_order_item called with order ID: {order_id}, item ID: {item_id}")
        return True

    def get_order_items(self, order_id: Union[int, str]) -> List[Dict[str, Any]]:
        """Get all items in an order."""
        logger.debug(f"Debug get_order_items called with order ID: {order_id}")

        # Return some dummy items
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

        return items

    def update_order_status(self, order_id: Union[int, str], status: OrderStatus) -> Dict[str, Any]:
        """Update the status of an order."""
        logger.debug(f"Debug update_order_status called with order ID: {order_id}, status: {status}")
        order = self.get_order(order_id)
        order["status"] = status.name
        return order

    def update_payment_status(self, order_id: Union[int, str], status: PaymentStatus) -> Dict[str, Any]:
        """Update the payment status of an order."""
        logger.debug(f"Debug update_payment_status called with order ID: {order_id}, status: {status}")
        order = self.get_order(order_id)
        order["payment_status"] = status.name
        return order