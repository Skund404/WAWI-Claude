# services/implementations/order_service.py
"""
Implementation of the Order Service for managing orders in the leatherworking store.
Handles CRUD operations for orders and order items.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.models.order import Order, OrderItem
from database.repositories.order_repository import OrderRepository
from services.interfaces.order_service import IOrderService, OrderStatus, PaymentStatus

# Configure logger
logger = logging.getLogger(__name__)


class OrderService(IOrderService):
    """Implementation of the Order Service interface."""

    def __init__(self, order_repository: OrderRepository):
        """Initialize the OrderService with a repository.

        Args:
            order_repository (OrderRepository): Repository for order data access
        """
        self.order_repository = order_repository
        logger.info("OrderService initialized")

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders.

        Returns:
            List[Dict[str, Any]]: List of orders as dictionaries
        """
        try:
            orders = self.order_repository.get_all()
            return self._convert_orders_to_dicts(orders)
        except Exception as e:
            logger.error(f"Error retrieving orders: {str(e)}", exc_info=True)
            # Return empty list instead of raising exception to avoid UI crashes
            return []

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get an order by its ID.

        Args:
            order_id (int): ID of the order to retrieve

        Returns:
            Optional[Dict[str, Any]]: Order data as dictionary or None if not found
        """
        try:
            order = self.order_repository.get_by_id(order_id)
            if order:
                return self._convert_order_to_dict(order)
            return None
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {str(e)}", exc_info=True)
            return None

    def create_order(self, order_data: Dict[str, Any]) -> Optional[int]:
        """Create a new order.

        Args:
            order_data (Dict[str, Any]): Order data containing customer info and items

        Returns:
            Optional[int]: ID of the created order or None if creation failed
        """
        try:
            # Extract basic order information
            customer_name = order_data.get('customer_name', '')
            customer_email = order_data.get('customer_email', '')
            customer_phone = order_data.get('customer_phone', '')
            notes = order_data.get('notes', '')

            # Create order object
            order = Order(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                status=OrderStatus.PENDING.name,
                payment_status=PaymentStatus.UNPAID.name,
                order_date=datetime.now(),
                notes=notes
            )

            # Save order to get ID
            order = self.order_repository.create(order)

            # Add order items if present
            items = order_data.get('items', [])
            for item_data in items:
                item = OrderItem(
                    order_id=order.id,
                    product_id=item_data.get('product_id'),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', 0.0)
                )
                self.order_repository.add_item(item)

            logger.info(f"Created order {order.id} with {len(items)} items")
            return order.id
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}", exc_info=True)
            return None

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> bool:
        """Update an existing order.

        Args:
            order_id (int): ID of the order to update
            order_data (Dict[str, Any]): Updated order data

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Get existing order
            order = self.order_repository.get_by_id(order_id)
            if not order:
                logger.warning(f"Order {order_id} not found for update")
                return False

            # Update basic order information
            if 'customer_name' in order_data:
                order.customer_name = order_data['customer_name']
            if 'customer_email' in order_data:
                order.customer_email = order_data['customer_email']
            if 'customer_phone' in order_data:
                order.customer_phone = order_data['customer_phone']
            if 'status' in order_data:
                order.status = order_data['status']
            if 'payment_status' in order_data:
                order.payment_status = order_data['payment_status']
            if 'notes' in order_data:
                order.notes = order_data['notes']

            # Save order changes
            self.order_repository.update(order)

            # Update items if provided
            if 'items' in order_data:
                # Clear existing items and add new ones
                self.order_repository.clear_items(order_id)

                for item_data in order_data['items']:
                    item = OrderItem(
                        order_id=order_id,
                        product_id=item_data.get('product_id'),
                        quantity=item_data.get('quantity', 1),
                        unit_price=item_data.get('unit_price', 0.0)
                    )
                    self.order_repository.add_item(item)

            logger.info(f"Updated order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}", exc_info=True)
            return False

    def delete_order(self, order_id: int) -> bool:
        """Delete an order.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Delete associated items first
            self.order_repository.clear_items(order_id)

            # Delete the order
            success = self.order_repository.delete(order_id)
            if success:
                logger.info(f"Deleted order {order_id}")
            else:
                logger.warning(f"Order {order_id} not found for deletion")

            return success
        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {str(e)}", exc_info=True)
            return False

    def search_orders(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for orders based on criteria.

        Args:
            criteria (Dict[str, Any]): Search criteria

        Returns:
            List[Dict[str, Any]]: List of matching orders
        """
        try:
            orders = self.order_repository.search(criteria)
            return self._convert_orders_to_dicts(orders)
        except Exception as e:
            logger.error(f"Error searching orders: {str(e)}", exc_info=True)
            return []

    def get_orders_by_status(self, status: OrderStatus) -> List[Dict[str, Any]]:
        """Get orders by status.

        Args:
            status (OrderStatus): Status to filter by

        Returns:
            List[Dict[str, Any]]: List of orders with the specified status
        """
        try:
            orders = self.order_repository.get_by_status(status.name)
            return self._convert_orders_to_dicts(orders)
        except Exception as e:
            logger.error(f"Error retrieving orders by status {status.name}: {str(e)}", exc_info=True)
            return []

    def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get orders within a date range.

        Args:
            start_date (datetime): Start date (inclusive)
            end_date (datetime): End date (inclusive)

        Returns:
            List[Dict[str, Any]]: List of orders within the date range
        """
        try:
            orders = self.order_repository.get_by_date_range(start_date, end_date)
            return self._convert_orders_to_dicts(orders)
        except Exception as e:
            logger.error(f"Error retrieving orders by date range: {str(e)}", exc_info=True)
            return []

    def update_order_status(self, order_id: int, status: OrderStatus) -> bool:
        """Update the status of an order.

        Args:
            order_id (int): ID of the order to update
            status (OrderStatus): New status

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            order = self.order_repository.get_by_id(order_id)
            if not order:
                logger.warning(f"Order {order_id} not found for status update")
                return False

            # Update status
            order.status = status.name

            # Save changes
            self.order_repository.update(order)

            logger.info(f"Updated order {order_id} status to {status.name}")
            return True
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}", exc_info=True)
            return False

    def update_payment_status(self, order_id: int, status: PaymentStatus) -> bool:
        """Update the payment status of an order.

        Args:
            order_id (int): ID of the order to update
            status (PaymentStatus): New payment status

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            order = self.order_repository.get_by_id(order_id)
            if not order:
                logger.warning(f"Order {order_id} not found for payment status update")
                return False

            # Update payment status
            order.payment_status = status.name

            # Save changes
            self.order_repository.update(order)

            logger.info(f"Updated order {order_id} payment status to {status.name}")
            return True
        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}", exc_info=True)
            return False

    def _convert_order_to_dict(self, order: Order) -> Dict[str, Any]:
        """Convert an Order model instance to a dictionary.

        Args:
            order (Order): Order model instance

        Returns:
            Dict[str, Any]: Order data as dictionary
        """
        # Get order items
        items = []
        for item in order.items:
            items.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': getattr(item, 'product_name', f"Product {item.product_id}"),
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total_price': item.quantity * item.unit_price
            })

        # Calculate total amount
        total_amount = sum(item.get('total_price', 0) for item in items)

        # Build order dictionary
        return {
            'id': order.id,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
            'order_date': order.order_date,
            'status': order.status,
            'payment_status': order.payment_status,
            'notes': order.notes,
            'items': items,
            'total_amount': total_amount,
            'created_at': order.created_at,
            'updated_at': order.updated_at
        }

    def _convert_orders_to_dicts(self, orders: List[Order]) -> List[Dict[str, Any]]:
        """Convert a list of Order model instances to dictionaries.

        Args:
            orders (List[Order]): List of Order model instances

        Returns:
            List[Dict[str, Any]]: List of order dictionaries
        """
        return [self._convert_order_to_dict(order) for order in orders]