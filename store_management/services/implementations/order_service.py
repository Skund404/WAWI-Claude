# services/implementations/order_service.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from services.interfaces.order_service import IOrderService
from database.models.order import Order, OrderItem
from database.models.enums import OrderStatus, PaymentStatus
from database.session import get_db_session


class OrderService(IOrderService):
    """
    Service implementation for managing orders.

    Handles:
    - Order CRUD operations
    - Order status management
    - Payment processing
    - Order reporting
    """

    def __init__(self, container: Any) -> None:
        """
        Initialize the order service.

        Args:
            container: Dependency injection container
        """
        self.logger = logging.getLogger(__name__)
        self.session: Session = get_db_session()

    def get_all_orders(self) -> List[Order]:
        """
        Get all orders in the system.

        Returns:
            List of Order objects

        Raises:
            Exception: If database query fails
        """
        try:
            return self.session.query(Order).order_by(Order.created_at.desc()).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving orders: {str(e)}")
            raise Exception("Failed to retrieve orders") from e

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Get an order by its ID.

        Args:
            order_id: ID of the order to retrieve

        Returns:
            Order object if found, None otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            return self.session.query(Order).filter(Order.id == order_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving order {order_id}: {str(e)}")
            raise Exception(f"Failed to retrieve order {order_id}") from e

    def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """
        Get an order by its order number.

        Args:
            order_number: Order number to search for

        Returns:
            Order object if found, None otherwise

        Raises:
            Exception: If database query fails
        """
        try:
            return self.session.query(Order).filter(Order.order_number == order_number).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving order {order_number}: {str(e)}")
            raise Exception(f"Failed to retrieve order {order_number}") from e

    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """
        Create a new order.

        Args:
            order_data: Dictionary containing order data

        Returns:
            Created Order object

        Raises:
            Exception: If order creation fails
        """
        try:
            # Generate order number if not provided
            if 'order_number' not in order_data:
                order_data['order_number'] = self._generate_order_number()

            # Create order
            order = Order(
                order_number=order_data['order_number'],
                customer_name=order_data['customer_name'],
                status=OrderStatus[order_data.get('status', 'NEW')],
                payment_status=PaymentStatus[order_data.get('payment_status', 'PENDING')],
                notes=order_data.get('notes')
            )

            # Add items if provided
            if 'items' in order_data:
                for item_data in order_data['items']:
                    item = OrderItem(
                        product_name=item_data['product_name'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=item_data['quantity'] * item_data['unit_price']
                    )
                    order.items.append(item)

            # Calculate total
            order.total_amount = sum(item.total_price for item in order.items)

            # Save to database
            self.session.add(order)
            self.session.commit()

            self.logger.info(f"Created order {order.order_number}")
            return order

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating order: {str(e)}")
            raise Exception("Failed to create order") from e

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Order:
        """
        Update an existing order.

        Args:
            order_id: ID of the order to update
            order_data: Dictionary containing updated order data

        Returns:
            Updated Order object

        Raises:
            Exception: If order update fails
        """
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                raise Exception(f"Order {order_id} not found")

            # Update basic fields
            order.customer_name = order_data.get('customer_name', order.customer_name)
            order.status = OrderStatus[order_data.get('status', order.status.name)]
            order.payment_status = PaymentStatus[order_data.get('payment_status', order.payment_status.name)]
            order.notes = order_data.get('notes', order.notes)

            # Update items if provided
            if 'items' in order_data:
                # Remove existing items
                order.items.clear()

                # Add new items
                for item_data in order_data['items']:
                    item = OrderItem(
                        product_name=item_data['product_name'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=item_data['quantity'] * item_data['unit_price']
                    )
                    order.items.append(item)

                # Recalculate total
                order.total_amount = sum(item.total_price for item in order.items)

            self.session.commit()
            self.logger.info(f"Updated order {order.order_number}")
            return order

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating order {order_id}: {str(e)}")
            raise Exception(f"Failed to update order {order_id}") from e

    def delete_order(self, order_id: int) -> None:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete

        Raises:
            Exception: If order deletion fails
        """
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                raise Exception(f"Order {order_id} not found")

            self.session.delete(order)
            self.session.commit()
            self.logger.info(f"Deleted order {order.order_number}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting order {order_id}: {str(e)}")
            raise Exception(f"Failed to delete order {order_id}") from e

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
        try:
            order = self.get_order_by_id(order_id)
            if not order:
                raise Exception(f"Order {order_id} not found")

            # Validate payment amount
            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than zero")

            if payment_amount >= order.total_amount:
                order.payment_status = PaymentStatus.PAID
            else:
                order.payment_status = PaymentStatus.PARTIAL

            self.session.commit()
            self.logger.info(f"Processed payment of ${payment_amount:.2f} for order {order.order_number}")
            return order

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error processing payment for order {order_id}: {str(e)}")
            raise Exception(f"Failed to process payment for order {order_id}") from e

    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Get all orders with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of matching Order objects

        Raises:
            Exception: If query fails
        """
        try:
            return self.session.query(Order).filter(Order.status == status).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving orders with status {status}: {str(e)}")
            raise Exception(f"Failed to retrieve orders with status {status}") from e

    def get_orders_by_customer(self, customer_name: str) -> List[Order]:
        """
        Get all orders for a specific customer.

        Args:
            customer_name: Name of the customer

        Returns:
            List of matching Order objects

        Raises:
            Exception: If query fails
        """
        try:
            return (self.session.query(Order)
                    .filter(Order.customer_name.ilike(f"%{customer_name}%"))
                    .order_by(Order.created_at.desc())
                    .all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving orders for customer {customer_name}: {str(e)}")
            raise Exception(f"Failed to retrieve orders for customer {customer_name}") from e

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about orders.

        Returns:
            Dictionary containing order statistics

        Raises:
            Exception: If query fails
        """
        try:
            total_orders = self.session.query(Order).count()
            pending_orders = self.session.query(Order).filter(Order.status == OrderStatus.NEW).count()
            completed_orders = self.session.query(Order).filter(Order.status == OrderStatus.COMPLETED).count()
            total_revenue = self.session.query(func.sum(Order.total_amount)).scalar() or 0.0

            return {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders,
                'total_revenue': total_revenue
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving order statistics: {str(e)}")
            raise Exception("Failed to retrieve order statistics") from e

    def _generate_order_number(self) -> str:
        """
        Generate a unique order number.

        Returns:
            Unique order number string
        """
        prefix = "ORD"
        date_part = datetime.now().strftime("%Y%m")

        # Get the last order number for this month
        last_order = (self.session.query(Order)
                      .filter(Order.order_number.like(f"{prefix}-{date_part}%"))
                      .order_by(Order.order_number.desc())
                      .first())

        if last_order:
            # Extract and increment the sequence number
            seq_num = int(last_order.order_number.split('-')[-1]) + 1
        else:
            seq_num = 1

        return f"{prefix}-{date_part}-{seq_num:04d}"

    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        if self.session:
            self.session.close()