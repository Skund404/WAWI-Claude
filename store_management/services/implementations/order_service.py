#!/usr/bin/env python3
"""
Order Service Implementation

Provides functionality for managing orders, order items, and order processing.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService
from services.interfaces.order_service import IOrderService
from services.base_service import Service
from utils.circular_import_resolver import CircularImportResolver

# Dynamically import modules
Order = CircularImportResolver.get_module('models.order').Order
OrderItem = CircularImportResolver.get_module('models.order').OrderItem
OrderStatus = CircularImportResolver.get_module('database.models.enums').OrderStatus
Supplier = CircularImportResolver.get_module('models.supplier').Supplier
from database.session import get_db
from exceptions import ResourceNotFoundError, ValidationError


class OrderService(Service, IOrderService):
    """
    Implementation of the Order Service.

    Provides methods for managing order-related operations.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the Order Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
        """
        super().__init__(None)
        self._session = session or get_db()
        self._logger = logging.getLogger(__name__)

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all orders.

        Returns:
            List[Dict[str, Any]]: List of order dictionaries

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            orders = self._session.query(Order).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving orders: {e}')
            raise

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            Optional[Dict[str, Any]]: Order details or None if not found

        Raises:
            ResourceNotFoundError: If order is not found
        """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))
            return order.to_dict(include_items=True)
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving order {order_id}: {e}')
            raise

    def get_order_by_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by order number.

        Args:
            order_number (str): Order number to retrieve

        Returns:
            Optional[Dict[str, Any]]: Order details or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            order = self._session.query(Order).filter(Order.order_number == order_number).first()
            if not order:
                return None
            return order.to_dict(include_items=True)
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving order with number {order_number}: {e}')
            raise

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data (Dict[str, Any]): Data for creating a new order

        Returns:
            Dict[str, Any]: Created order details

        Raises:
            ValidationError: If order data is invalid
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate required fields
            required_fields = ['supplier_id', 'order_number']
            for field in required_fields:
                if field not in order_data:
                    raise ValidationError(f'Missing required field: {field}')

            # Verify supplier exists
            supplier = self._session.query(Supplier).get(order_data['supplier_id'])
            if not supplier:
                raise ResourceNotFoundError('Supplier', str(order_data['supplier_id']))

            # Create order
            order = Order(
                order_number=order_data['order_number'],
                supplier_id=order_data['supplier_id'],
                customer_name=order_data.get('customer_name', ''),
                status=order_data.get('status', OrderStatus.NEW)
            )

            # Add order items if provided
            if 'order_items' in order_data:
                for item_data in order_data['order_items']:
                    order_item = OrderItem(
                        product_id=item_data.get('product_id'),
                        quantity=item_data.get('quantity', 1),
                        unit_price=item_data.get('unit_price', 0.0),
                        description=item_data.get('description')
                    )
                    order.items.append(order_item)

            # Calculate total amount
            order.total_amount = order.calculate_total()

            self._session.add(order)
            self._session.commit()
            self._session.refresh(order)

            return order.to_dict(include_items=True)

        except (SQLAlchemyError, ValidationError) as e:
            self._session.rollback()
            self._logger.error(f'Error creating order: {e}')
            raise

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing order.

        Args:
            order_id (int): Unique identifier for the order
            order_data (Dict[str, Any]): Updated order information

        Returns:
            Optional[Dict[str, Any]]: Updated order details

        Raises:
            ResourceNotFoundError: If order is not found
            SQLAlchemyError: If database operation fails
        """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))

            # Update basic order attributes
            if 'customer_name' in order_data:
                order.customer_name = order_data['customer_name']

            if 'status' in order_data:
                order.status = order_data['status']

            # Update order items if provided
            if 'order_items' in order_data:
                # Clear existing items
                order.items.clear()

                # Add new items
                for item_data in order_data['order_items']:
                    order_item = OrderItem(
                        product_id=item_data.get('product_id'),
                        quantity=item_data.get('quantity', 1),
                        unit_price=item_data.get('unit_price', 0.0),
                        description=item_data.get('description')
                    )
                    order.items.append(order_item)

            # Recalculate total amount
            order.total_amount = order.calculate_total()

            self._session.commit()
            self._session.refresh(order)

            return order.to_dict(include_items=True)

        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error updating order {order_id}: {e}')
            raise

    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            bool: True if deletion was successful

        Raises:
            ResourceNotFoundError: If order is not found
            SQLAlchemyError: If database operation fails
        """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))

            self._session.delete(order)
            self._session.commit()
            return True

        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error deleting order {order_id}: {e}')
            raise

    def process_order_payment(self, order_id: int, payment_amount: float) -> bool:
        """
        Process a payment for an order.

        Args:
            order_id (int): ID of the order
            payment_amount (float): Amount of the payment

        Returns:
            bool: True if payment was processed successfully

        Raises:
            ResourceNotFoundError: If order is not found
            ValidationError: If payment amount is invalid
        """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))

            if payment_amount < 0:
                raise ValidationError('Payment amount cannot be negative')

            # TODO: Implement specific payment processing logic
            # This might involve updating payment status, creating payment records, etc.

            # For now, just a simple placeholder
            self._logger.info(f'Processed payment of {payment_amount} for order {order_id}')

            self._session.commit()
            return True

        except (SQLAlchemyError, ValidationError) as e:
            self._session.rollback()
            self._logger.error(f'Error processing payment for order {order_id}: {e}')
            raise

    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get orders with a specific status.

        Args:
            status (str): Status to filter by

        Returns:
            List[Dict[str, Any]]: List of orders with the specified status

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Convert string to enum if necessary
            status_enum = OrderStatus[status.upper()] if isinstance(status, str) else status

            orders = self._session.query(Order).filter(Order.status == status_enum).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving orders with status {status}: {e}')
            raise

    def get_orders_by_customer(self, customer_name: str) -> List[Dict[str, Any]]:
        """
        Get orders for a specific customer.

        Args:
            customer_name (str): Name of the customer

        Returns:
            List[Dict[str, Any]]: List of orders for the customer

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            orders = self._session.query(Order).filter(Order.customer_name.ilike(f'%{customer_name}%')).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving orders for customer {customer_name}: {e}')
            raise

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        Get order statistics.

        Returns:
            Dict[str, Any]: Dictionary containing order statistics

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Total number of orders
            total_orders = self._session.query(Order).count()

            # Orders by status
            status_counts = {}
            for status in OrderStatus:
                status_counts[status.name] = self._session.query(Order).filter(Order.status == status).count()

            # Total revenue
            total_revenue = self._session.query(Order).with_entities(
                self._session.query(Order).func.sum(Order.total_amount).label('total')
            ).scalar() or 0.0

            return {
                'total_orders': total_orders,
                'orders_by_status': status_counts,
                'total_revenue': total_revenue
            }
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving order statistics: {e}')
            raise

    def generate_order_report(self,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive order report for a given period.

        Args:
            start_date (Optional[datetime]): Start of the reporting period
            end_date (Optional[datetime]): End of the reporting period

        Returns:
            Dict[str, Any]: Detailed order report

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Base query
            query = self._session.query(Order)

            # Apply date filters if provided
            if start_date:
                query = query.filter(Order.order_date >= start_date)
            if end_date:
                query = query.filter(Order.order_date <= end_date)

            # Execute query
            orders = query.all()

            # Generate report
            report = {
                'total_orders': len(orders),
                'total_revenue': sum(order.total_amount for order in orders),
                'orders_by_status': {},
                'top_customers': {}
            }

            # Count orders by status
            for status in OrderStatus:
                report['orders_by_status'][status.name] = sum(1 for order in orders if order.status == status)

            # Calculate totals by customer
            customer_totals = {}
            for order in orders:
                customer_totals[order.customer_name] = customer_totals.get(order.customer_name, 0) + order.total_amount

            # Get top 5 customers by order value
            report['top_customers'] = dict(sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:5])

            return report

        except SQLAlchemyError as e:
            self._logger.error(f'Error generating order report: {e}')
            raise

    def cleanup(self) -> None:
        """
        Perform cleanup operations for the order service.

        This method can be used to perform any necessary cleanup tasks,
        such as removing old or obsolete orders.
        """
        try:
            # Example: Remove orders older than 2 years
            two_years_ago = datetime.utcnow() - timedelta(days=365 * 2)
            obsolete_orders = self._session.query(Order).filter(Order.order_date < two_years_ago).all()

            for order in obsolete_orders:
                self._session.delete(order)

            self._session.commit()
            self._logger.info(f'Cleaned up {len(obsolete_orders)} old orders')
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error during order service cleanup: {e}')
            raise