# fix_order_service.py
"""
This module provides a direct implementation of OrderService that doesn't rely on imports
from the services package, to ensure all required methods are implemented.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.sqlalchemy.session import get_db_session
from database.repositories.order_repository import OrderRepository
from services.interfaces.order_service import IOrderService, OrderStatus, PaymentStatus
from di.container import DependencyContainer


class FixedOrderService(IOrderService):
    """Direct implementation of OrderService with all required methods."""

    def __init__(self, order_repository=None):
        """Initialize the OrderService with a repository.

        Args:
            order_repository: Repository for order data access
        """
        self._logger = logging.getLogger(__name__)

        # Create repository with session if not provided
        if order_repository is None:
            session = get_db_session()
            self._repository = OrderRepository(session)
        else:
            self._repository = order_repository

        self._logger.info("FixedOrderService initialized")

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders from the system.

        Returns:
            List[Dict[str, Any]]: List of all orders as dictionaries
        """
        try:
            orders = self._repository.get_all()
            return [self._to_dict(order) for order in orders]
        except Exception as e:
            self._logger.error(f"Error getting all orders: {str(e)}")
            return []

    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Dict[str, Any]]:
        """Get orders filtered by status.

        Args:
            status (OrderStatus, optional): Filter orders by this status. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of orders matching the criteria
        """
        try:
            orders = self._repository.get_by_status(status) if status else self._repository.get_all()
            return [self._to_dict(order) for order in orders]
        except Exception as e:
            self._logger.error(f"Error getting orders with status {status}: {str(e)}")
            return []

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific order by ID.

        Args:
            order_id (int): The ID of the order to retrieve

        Returns:
            Optional[Dict[str, Any]]: The order as a dictionary, or None if not found
        """
        try:
            order = self._repository.get_by_id(order_id)
            return self._to_dict(order) if order else None
        except Exception as e:
            self._logger.error(f"Error getting order {order_id}: {str(e)}")
            return None

    def search_orders(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for orders based on specified criteria.

        Args:
            search_criteria (Dict[str, Any]): Criteria to search by (e.g., customer name, date range)

        Returns:
            List[Dict[str, Any]]: List of matching orders
        """
        try:
            # Get all orders and filter based on search criteria
            all_orders = self.get_all_orders()
            filtered_orders = []

            for order in all_orders:
                match = True

                # Check each search criteria
                for key, value in search_criteria.items():
                    if key in order:
                        # String search (case-insensitive partial match)
                        if isinstance(order[key], str) and isinstance(value, str):
                            if value.lower() not in order[key].lower():
                                match = False
                                break
                        # Date range search
                        elif key == 'order_date_from' and 'order_date' in order:
                            try:
                                order_date = datetime.fromisoformat(order['order_date'])
                                if order_date < value:
                                    match = False
                                    break
                            except (ValueError, TypeError):
                                match = False
                                break
                        elif key == 'order_date_to' and 'order_date' in order:
                            try:
                                order_date = datetime.fromisoformat(order['order_date'])
                                if order_date > value:
                                    match = False
                                    break
                            except (ValueError, TypeError):
                                match = False
                                break
                        # Exact value match
                        elif order[key] != value:
                            match = False
                            break

                if match:
                    filtered_orders.append(order)

            return filtered_orders
        except Exception as e:
            self._logger.error(f"Error searching orders with criteria {search_criteria}: {str(e)}")
            return []

    def list_orders(self, filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List orders with filtering options.

        Args:
            filter_params (Dict[str, Any], optional): Parameters to filter orders by. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of filtered orders
        """
        try:
            # Extract filter parameters if provided
            if filter_params is None:
                filter_params = {}

            status = filter_params.get('status')
            date_from = filter_params.get('date_from')
            date_to = filter_params.get('date_to')
            customer = filter_params.get('customer')

            # Apply filters
            if status:
                orders = self._repository.get_by_status(status)
            else:
                orders = self._repository.get_all()

            # Further filtering
            result = []
            for order in orders:
                order_dict = self._to_dict(order)

                # Filter by date range
                if date_from and order.order_date < date_from:
                    continue
                if date_to and order.order_date > date_to:
                    continue

                # Filter by customer
                if customer and customer.lower() not in order.customer_name.lower():
                    continue

                result.append(order_dict)

            return result
        except Exception as e:
            self._logger.error(f"Error listing orders with filters {filter_params}: {str(e)}")
            return []

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order.

        Args:
            order_data (Dict[str, Any]): The data for the new order

        Returns:
            Optional[Dict[str, Any]]: The created order or None if creation failed
        """
        try:
            # Set default values if not provided
            if 'order_date' not in order_data:
                order_data['order_date'] = datetime.now()
            if 'status' not in order_data:
                order_data['status'] = OrderStatus.PENDING
            if 'payment_status' not in order_data:
                order_data['payment_status'] = PaymentStatus.UNPAID

            # Create order
            order = self._repository.create(order_data)
            self._repository.save()

            self._logger.info(f"Created new order with ID {order.id}")
            return self._to_dict(order)
        except Exception as e:
            self._logger.error(f"Error creating order: {str(e)}")
            return None

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing order.

        Args:
            order_id (int): The ID of the order to update
            order_data (Dict[str, Any]): The new order data

        Returns:
            Optional[Dict[str, Any]]: The updated order or None if update failed
        """
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for update")
                return None

            # Update order fields
            for key, value in order_data.items():
                if hasattr(order, key):
                    setattr(order, key, value)

            self._repository.save()
            self._logger.info(f"Updated order with ID {order_id}")
            return self._to_dict(order)
        except Exception as e:
            self._logger.error(f"Error updating order {order_id}: {str(e)}")
            return None

    def update_order_status(self, order_id: int, new_status: OrderStatus) -> bool:
        """Update the status of an order.

        Args:
            order_id (int): The ID of the order to update
            new_status (OrderStatus): The new status to set

        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # Get the order
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for status update")
                return False

            # Update the status
            order.status = new_status
            self._repository.save()

            self._logger.info(f"Updated status of order {order_id} to {new_status.name}")
            return True
        except Exception as e:
            self._logger.error(f"Error updating status of order {order_id}: {str(e)}")
            return False

    def delete_order(self, order_id: int) -> bool:
        """Delete an order.

        Args:
            order_id (int): The ID of the order to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            success = self._repository.delete(order_id)
            if success:
                self._repository.save()
                self._logger.info(f"Deleted order with ID {order_id}")
            else:
                self._logger.warning(f"Order with ID {order_id} not found for deletion")
            return success
        except Exception as e:
            self._logger.error(f"Error deleting order {order_id}: {str(e)}")
            return False

    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add an item to an order.

        Args:
            order_id (int): The ID of the order to add an item to
            item_data (Dict[str, Any]): The data for the new item

        Returns:
            Optional[Dict[str, Any]]: The added item or None if addition failed
        """
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for adding item")
                return None

            # Create new order item
            item_data['order_id'] = order_id
            new_item = self._repository.add_item(order, item_data)

            self._repository.save()

            self._logger.info(f"Added item to order {order_id}")
            return self._item_to_dict(new_item)
        except Exception as e:
            self._logger.error(f"Error adding item to order {order_id}: {str(e)}")
            return None

    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """Remove an item from an order.

        Args:
            order_id (int): The ID of the order
            item_id (int): The ID of the item to remove

        Returns:
            bool: True if removal was successful, False otherwise
        """
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for item removal")
                return False

            # Find and remove the item
            success = self._repository.remove_item(order, item_id)
            if success:
                self._repository.save()
                self._logger.info(f"Removed item {item_id} from order {order_id}")
            else:
                self._logger.warning(f"Item {item_id} not found in order {order_id}")

            return success
        except Exception as e:
            self._logger.error(f"Error removing item {item_id} from order {order_id}: {str(e)}")
            return False

    def calculate_order_total(self, order_id: int) -> float:
        """Calculate the total price of an order.

        Args:
            order_id (int): The ID of the order

        Returns:
            float: The total price of the order
        """
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for total calculation")
                return 0.0

            total = sum(item.quantity * item.unit_price for item in order.items)
            self._logger.debug(f"Calculated total {total} for order {order_id}")
            return total
        except Exception as e:
            self._logger.error(f"Error calculating total for order {order_id}: {str(e)}")
            return 0.0

    def process_payment(self, order_id: int, payment_data: Dict[str, Any]) -> bool:
        """Process a payment for an order.

        Args:
            order_id (int): The ID of the order
            payment_data (Dict[str, Any]): The payment data

        Returns:
            bool: True if payment processing was successful, False otherwise
        """
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for payment processing")
                return False

            # Update payment status based on amount
            amount = payment_data.get('amount', 0.0)
            total = self.calculate_order_total(order_id)

            if amount >= total:
                order.payment_status = PaymentStatus.PAID
            elif amount > 0:
                order.payment_status = PaymentStatus.PARTIALLY_PAID
            else:
                order.payment_status = PaymentStatus.UNPAID

            # Record payment details if provided
            if 'payment_method' in payment_data:
                order.payment_method = payment_data['payment_method']
            if 'payment_date' in payment_data:
                order.payment_date = payment_data['payment_date']
            else:
                order.payment_date = datetime.now()

            self._repository.save()
            self._logger.info(f"Processed payment for order {order_id}, status: {order.payment_status}")
            return True
        except Exception as e:
            self._logger.error(f"Error processing payment for order {order_id}: {str(e)}")
            return False

    def generate_order_report(self, order_id: int) -> Dict[str, Any]:
        """Generate a detailed report for an order.

        Args:
            order_id (int): The ID of the order

        Returns:
            Dict[str, Any]: A detailed report of the order
        """
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order with ID {order_id} not found for report generation")
                return {}

            # Basic order information
            report = self._to_dict(order)

            # Add calculated fields
            report['total'] = self.calculate_order_total(order_id)
            report['item_count'] = len(order.items)

            # Add timestamps
            report['generated_at'] = datetime.now().isoformat()

            self._logger.info(f"Generated report for order {order_id}")
            return report
        except Exception as e:
            self._logger.error(f"Error generating report for order {order_id}: {str(e)}")
            return {}

    def _to_dict(self, order) -> Dict[str, Any]:
        """Convert an Order object to a dictionary.

        Args:
            order: The order to convert

        Returns:
            Dict[str, Any]: The order as a dictionary
        """
        if not order:
            return {}

        try:
            return {
                'id': order.id,
                'customer_name': getattr(order, 'customer_name', ''),
                'customer_email': getattr(order, 'customer_email', ''),
                'order_date': order.order_date.isoformat() if hasattr(order,
                                                                      'order_date') and order.order_date else None,
                'status': order.status.name if hasattr(order, 'status') and hasattr(order.status, 'name') else str(
                    getattr(order, 'status', '')),
                'payment_status': order.payment_status.name if hasattr(order, 'payment_status') and hasattr(
                    order.payment_status, 'name') else str(getattr(order, 'payment_status', '')),
                'shipping_address': getattr(order, 'shipping_address', ''),
                'notes': getattr(order, 'notes', ''),
                'items': [self._item_to_dict(item) for item in getattr(order, 'items', [])] if hasattr(order,
                                                                                                       'items') else []
            }
        except Exception as e:
            self._logger.error(f"Error converting order to dict: {str(e)}")
            return {'id': getattr(order, 'id', 0), 'error': str(e)}

    def _item_to_dict(self, item) -> Dict[str, Any]:
        """Convert an OrderItem object to a dictionary.

        Args:
            item: The order item to convert

        Returns:
            Dict[str, Any]: The order item as a dictionary
        """
        if not item:
            return {}

        try:
            return {
                'id': getattr(item, 'id', 0),
                'product_id': getattr(item, 'product_id', 0),
                'product_name': item.product.name if hasattr(item, 'product') and getattr(item,
                                                                                          'product') else "Unknown Product",
                'quantity': getattr(item, 'quantity', 0),
                'unit_price': getattr(item, 'unit_price', 0.0),
                'subtotal': getattr(item, 'quantity', 0) * getattr(item, 'unit_price', 0.0)
            }
        except Exception as e:
            self._logger.error(f"Error converting order item to dict: {str(e)}")
            return {'id': getattr(item, 'id', 0), 'error': str(e)}


def fix_order_service_registration():
    """
    Ensure the OrderService is correctly registered with the DI container.

    This function should be called after the normal dependency injection setup
    if there are issues with the OrderService.
    """
    logger = logging.getLogger(__name__)
    logger.info("Applying OrderService registration fix")

    try:
        # Get the DI container
        container = DependencyContainer()

        # Create a database session
        session = get_db_session()

        # Create and register a proper OrderService
        order_repository = OrderRepository(session)
        order_service = FixedOrderService(order_repository)

        # Register the service instance directly
        container.register(IOrderService, order_service)

        logger.info("OrderService registration fix applied successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to apply OrderService registration fix: {str(e)}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    # Apply the fix
    fix_order_service_registration()