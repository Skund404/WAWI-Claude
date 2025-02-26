# services/implementations/order_service.py

import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta

from services.interfaces.order_service import IOrderService, OrderStatus, PaymentStatus
from database.repositories.order_repository import OrderRepository
from database.models.order import Order, OrderItem


class OrderService(IOrderService):
    def __init__(self, order_repository: OrderRepository):
        """
        Initialize the Order Service.

        Args:
            order_repository (OrderRepository): Repository for order data access
        """
        self.order_repository = order_repository
        logging.info("OrderService initialized")

    def calculate_order_total(self, order_id: int) -> float:
        """
        Calculate the total amount for an order.

        Args:
            order_id (int): ID of the order

        Returns:
            float: Total order amount
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        total = sum(item.quantity * item.unit_price for item in order.items)
        return round(total, 2)

    def generate_order_report(self, order_id: int) -> Dict[str, Any]:
        """
        Generate a detailed report for an order.

        Args:
            order_id (int): ID of the order

        Returns:
            Dict[str, Any]: Order report data
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        report_data = {
            "order_id": order.id,
            "customer_name": order.customer_name,
            "order_date": order.order_date.strftime("%Y-%m-%d"),
            "status": order.status.value,
            "items": [],
            "total_amount": self.calculate_order_total(order_id),
        }

        for item in order.items:
            item_data = {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.quantity * item.unit_price,
            }
            report_data["items"].append(item_data)

        return report_data

    def list_orders(self, status: OrderStatus = None,
                    date_range: Tuple[datetime, datetime] = None,
                    payment_status: PaymentStatus = None) -> List[Dict[str, Any]]:
        """
        List orders based on optional filters.

        Args:
            status (OrderStatus, optional): Filter by order status. Defaults to None.
            date_range (Tuple[datetime, datetime], optional): Filter by date range. Defaults to None.
            payment_status (PaymentStatus, optional): Filter by payment status. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of order data dictionaries
        """
        orders = self.order_repository.list(
            status=status,
            date_range=date_range,
            payment_status=payment_status
        )

        order_data_list = []
        for order in orders:
            order_data = {
                "id": order.id,
                "customer_name": order.customer_name,
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "status": order.status.value,
                "total_amount": self.calculate_order_total(order.id),
            }
            order_data_list.append(order_data)

        return order_data_list

    def process_payment(self, order_id: int) -> bool:
        """
        Process payment for an order.

        Args:
            order_id (int): ID of the order

        Returns:
            bool: True if payment processed successfully, False otherwise
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order not found: {order_id}")

        if order.payment_status == PaymentStatus.PAID:
            logging.warning(f"Payment already processed for order: {order_id}")
            return True

        # TODO: Integrate with payment gateway API to process payment
        # Simulating payment processing success
        order.payment_status = PaymentStatus.PAID
        self.order_repository.update(order)

        logging.info(f"Payment processed successfully for order: {order_id}")
        return True

    def search_orders(self, query: str) -> List[Dict[str, Any]]:
        """
        Search orders based on a query string.

        Args:
            query (str): Search query

        Returns:
            List[Dict[str, Any]]: List of matching order data dictionaries
        """
        orders = self.order_repository.search(query)

        order_data_list = []
        for order in orders:
            order_data = {
                "id": order.id,
                "customer_name": order.customer_name,
                "order_date": order.order_date.strftime("%Y-%m-%d"),
                "status": order.status.value,
                "total_amount": self.calculate_order_total(order.id),
            }
            order_data_list.append(order_data)

        return order_data_list