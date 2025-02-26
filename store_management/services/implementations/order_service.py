# services/implementations/order_service.py
"""
Order service implementation for managing order-related business logic.

This module provides service layer operations for orders,
interfacing between the repository and the application logic.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.models.order import Order, OrderItem
from database.repositories.order_repository import OrderRepository
from services.interfaces.order_service import (
    IOrderService,
    OrderStatus,
    PaymentStatus
)

import logging


class OrderService(IOrderService):
    """
    Concrete implementation of the IOrderService interface.

    Provides comprehensive order management functionality
    with business logic and validation.
    """

    def __init__(self, order_repository: OrderRepository):
        """
        Initialize the OrderService with a repository.

        Args:
            order_repository (OrderRepository): Repository for order data access
        """
        self._repository = order_repository
        self._logger = logging.getLogger(__name__)

    # Existing methods from previous implementation...
    def create_order(self, order_data: Dict[str, Any]) -> Optional[Order]:
        """Create a new order."""
        try:
            # Validate order data
            self._validate_order_data(order_data)

            # Set default status if not provided
            order_data.setdefault('status', OrderStatus.PENDING)
            order_data.setdefault('payment_status', PaymentStatus.UNPAID)

            # Create order
            order = self._repository.create(order_data)

            self._logger.info(f"Order created successfully. Order ID: {order.id}")
            return order
        except Exception as e:
            self._logger.error(f"Error creating order: {e}")
            return None

    def get_order(self, order_id: int) -> Optional[Order]:
        """Retrieve an order by its ID."""
        try:
            order = self._repository.get_by_id(order_id)
            if not order:
                self._logger.warning(f"Order not found. ID: {order_id}")
            return order
        except Exception as e:
            self._logger.error(f"Error retrieving order {order_id}: {e}")
            return None

    def get_orders(
            self,
            status: Optional[OrderStatus] = None,
            date_range: Optional[Tuple[datetime, datetime]] = None,
            payment_status: Optional[PaymentStatus] = None
    ) -> List[Order]:
        """Retrieve orders with optional filtering."""
        try:
            # Start with all orders
            orders = self._repository.get_all_orders()

            # Apply filters
            filtered_orders = orders
            if status:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.status == status
                ]

            if date_range:
                start_date, end_date = date_range
                filtered_orders = [
                    order for order in filtered_orders
                    if start_date <= order.created_at <= end_date
                ]

            if payment_status:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.payment_status == payment_status
                ]

            return filtered_orders
        except Exception as e:
            self._logger.error(f"Error retrieving orders: {e}")
            return []

    def update_order(
            self,
            order_id: int,
            update_data: Dict[str, Any]
    ) -> Optional[Order]:
        """Update an existing order."""
        try:
            # Validate update data
            self._validate_update_data(update_data)

            # Perform update
            updated_order = self._repository.update_order(order_id, update_data)

            if updated_order:
                self._logger.info(f"Order {order_id} updated successfully")
            else:
                self._logger.warning(f"Order {order_id} not found or update failed")

            return updated_order
        except Exception as e:
            self._logger.error(f"Error updating order {order_id}: {e}")
            return None

    def delete_order(self, order_id: int) -> bool:
        """Delete an order."""
        try:
            success = self._repository.delete_order(order_id)

            if success:
                self._logger.info(f"Order {order_id} deleted successfully")
            else:
                self._logger.warning(f"Order {order_id} not found or deletion failed")

            return success
        except Exception as e:
            self._logger.error(f"Error deleting order {order_id}: {e}")
            return False

    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Optional[OrderItem]:
        """Add an item to an existing order."""
        try:
            # Validate item data
            self._validate_order_item_data(item_data)

            # Retrieve the order
            order = self.get_order(order_id)
            if not order:
                self._logger.warning(f"Cannot add item. Order {order_id} not found")
                return None

            # Create the order item (implementation depends on your ORM)
            new_item = OrderItem(**item_data)
            order.order_items.append(new_item)

            # Save changes
            self._repository._session.commit()

            self._logger.info(f"Item added to order {order_id}")
            return new_item
        except Exception as e:
            self._repository._session.rollback()
            self._logger.error(f"Error adding item to order {order_id}: {e}")
            return None

    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """Remove an item from an existing order."""
        try:
            # Retrieve the order
            order = self.get_order(order_id)
            if not order:
                self._logger.warning(f"Cannot remove item. Order {order_id} not found")
                return False

            # Find and remove the item
            item_to_remove = next(
                (item for item in order.order_items if item.id == item_id),
                None
            )

            if not item_to_remove:
                self._logger.warning(f"Item {item_id} not found in order {order_id}")
                return False

            # Remove the item
            order.order_items.remove(item_to_remove)
            self._repository._session.delete(item_to_remove)
            self._repository._session.commit()

            self._logger.info(f"Item {item_id} removed from order {order_id}")
            return True
        except Exception as e:
            self._repository._session.rollback()
            self._logger.error(f"Error removing item {item_id} from order {order_id}: {e}")
            return False

    def update_order_status(
            self,
            order_id: int,
            new_status: OrderStatus
    ) -> Optional[Order]:
        """Update the status of an existing order."""
        try:
            # Update the order status
            updated_order = self.update_order(order_id, {'status': new_status})

            if updated_order:
                self._logger.info(f"Order {order_id} status updated to {new_status}")

            return updated_order
        except Exception as e:
            self._logger.error(f"Error updating status for order {order_id}: {e}")
            return None

    def process_payment(
            self,
            order_id: int,
            payment_amount: float
    ) -> Optional[Order]:
        """Process payment for an order."""
        try:
            # Retrieve the order
            order = self.get_order(order_id)
            if not order:
                self._logger.warning(f"Cannot process payment. Order {order_id} not found")
                return None

            # Calculate total order amount
            total_amount = self.calculate_order_total(order_id)
            if total_amount is None:
                self._logger.error(f"Could not calculate total for order {order_id}")
                return None

            # Validate payment amount
            if payment_amount < 0:
                raise ValueError("Payment amount cannot be negative")

            # Determine payment status
            if payment_amount >= total_amount:
                payment_status = PaymentStatus.PAID
            elif payment_amount > 0:
                payment_status = PaymentStatus.PARTIALLY_PAID
            else:
                payment_status = PaymentStatus.UNPAID

            # Update order with payment details
            updated_order = self.update_order(order_id, {
                'payment_status': payment_status,
                'amount_paid': payment_amount
            })

            if updated_order:
                self._logger.info(f"Payment processed for order {order_id}. Amount: {payment_amount}")

            return updated_order
        except Exception as e:
            self._logger.error(f"Error processing payment for order {order_id}: {e}")
            return None

    def calculate_order_total(self, order_id: int) -> Optional[float]:
        """Calculate the total cost of an order."""
        try:
            # Retrieve the order
            order = self.get_order(order_id)
            if not order:
                self._logger.warning(f"Cannot calculate total. Order {order_id} not found")
                return None

            # Calculate total from order items
            total = sum(item.quantity * item.unit_price for item in order.order_items)

            return total
        except Exception as e:
            self._logger.error(f"Error calculating total for order {order_id}: {e}")
            return None

    def generate_order_report(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Generate a report of orders within a specified date range."""
        try:
            # Retrieve orders within date range
            orders = self.get_orders(date_range=(start_date, end_date))

            # Generate report
            report = []
            for order in orders:
                report.append({
                    'order_id': order.id,
                    'customer_name': order.customer_name,
                    'total_amount': self.calculate_order_total(order.id),
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'created_at': order.created_at
                })

            return report
        except Exception as e:
            self._logger.error(f"Error generating order report: {e}")
            return []

    def search_orders(
            self,
            search_term: str,
            search_fields: Optional[List[str]] = None
    ) -> List[Order]:
        """Search for orders based on a search term."""
        try:
            # Default search fields if not provided
            if not search_fields:
                search_fields = ['customer_name', 'id']

            # Retrieve all orders
            all_orders = self._repository.get_all_orders()

            # Filter orders
            matching_orders = []
            for order in all_orders:
                for field in search_fields:
                    # Get the field value, handling potential nested attributes
                    try:
                        field_value = getattr(order, field)
                        if (isinstance(field_value, str) and
                                search_term.lower() in field_value.lower()):
                            matching_orders.append(order)
                            break
                        elif (not isinstance(field_value, str) and
                              str(search_term) == str(field_value)):
                            matching_orders.append(order)
                            break
                    except AttributeError:
                        continue

            return matching_orders
        except Exception as e:
            self._logger.error(f"Error searching orders: {e}")
            return []

    def list_orders(
            self,
            page: int = 1,
            per_page: int = 10,
            sort_by: Optional[str] = None
    ) -> List[Order]:
        """List orders with pagination and optional sorting."""
        try:
            # Retrieve all orders
            all_orders = self._repository.get_all_orders()

            # Sort if specified
            if sort_by:
                try:
                    all_orders = sorted(all_orders, key=lambda x: getattr(x, sort_by))
                except AttributeError:
                    self._logger.warning(f"Cannot sort by {sort_by}. Using default order.")

            # Pagination
            start_index = (page - 1) * per_page
            end_index = start_index + per_page

            return all_orders[start_index:end_index]
        except Exception as e:
            self._logger.error(f"Error listing orders: {e}")
            return []

    def _validate_order_data(self, order_data: Dict[str, Any]) -> None:
        """
        Validate order creation data.

        Args:
            order_data (Dict[str, Any]): Order data to validate

        Raises:
            ValueError: If validation fails
        """
        # Add specific validation logic
        if not order_data.get('customer_name'):
            raise ValueError("Customer name is required")

        # Add more validation as needed

    def _validate_update_data(self, update_data: Dict[str, Any]) -> None:
        """
        Validate order update data.

        Args:
            update_data (Dict[str, Any]): Update data to validate

        Raises:
            ValueError: If validation fails
        """
        # Prevent updating certain critical fields
        if 'id' in update_data:
            raise ValueError("Cannot update order ID")

        # Add more validation as needed

    def _validate_order_item_data(self, item_data: Dict[str, Any]) -> None:
        """
        Validate order item data.

        Args:
            item_data (Dict[str, Any]): Order item data to validate

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields for order items
        if 'product_id' not in item_data:
            raise ValueError("Product ID is required for order items")

        if 'quantity' not in item_data or item_data['quantity'] <= 0:
            raise ValueError("Quantity must be a positive number")

        if 'unit_price' not in item_data or item_data['unit_price'] < 0:
            raise ValueError("Unit price must be non-negative")