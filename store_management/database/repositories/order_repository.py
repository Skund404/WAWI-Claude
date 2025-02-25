# store_management/database/repositories/order_repository.py
"""
Repository for managing order-related database operations.

Provides specialized methods for retrieving, creating, and managing
orders with advanced querying capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import MaterialService, OrderService
from models.order import Order, OrderStatus, OrderItem
from models.supplier import Supplier

# Configure logging
logger = logging.getLogger(__name__)


class OrderRepository:
    """
    Repository for managing order-related database operations.

    Provides methods to interact with orders, including 
    retrieval, creation, and advanced querying.
    """

    @inject(MaterialService)
    def __init__(self, session):
        """
        Initialize the OrderRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_with_items(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an order with its associated items and supplier in a single query.

        Args:
            order_id (int): Unique identifier of the order

        Returns:
            Optional[Order]: Order instance with populated order items and supplier, or None if not found

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            return (
                self.session.query(Order)
                .options(
                    joinedload(Order.order_items),
                    joinedload(Order.supplier)
                )
                .filter(Order.id == order_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving order with items: {e}')
            raise

    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Retrieve orders filtered by their current status.

        Args:
            status (OrderStatus): Status to filter orders by

        Returns:
            List[Order]: List of Order instances matching the specified status

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            return (
                self.session.query(Order)
                .options(
                    joinedload(Order.order_items),
                    joinedload(Order.supplier)
                )
                .filter(Order.status == status)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving orders by status: {e}')
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Order]:
        """
        Retrieve all orders for a specific supplier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            List[Order]: List of Order instances for the specified supplier

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            return (
                self.session.query(Order)
                .options(
                    joinedload(Order.order_items),
                    joinedload(Order.supplier)
                )
                .filter(Order.supplier_id == supplier_id)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving orders for supplier: {e}')
            raise

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """
        Retrieve orders within a specific date range.

        Args:
            start_date (datetime): Start of the date range
            end_date (datetime): End of the date range

        Returns:
            List[Order]: List of Order instances within the specified date range

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            return (
                self.session.query(Order)
                .options(
                    joinedload(Order.order_items),
                    joinedload(Order.supplier)
                )
                .filter(Order.order_date.between(start_date, end_date))
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving orders by date range: {e}')
            raise

    def search(
            self,
            search_term: str,
            fields: Optional[List[str]] = None,
            limit: int = 10
    ) -> List[Order]:
        """
        Search for orders using a flexible search across multiple fields.

        Args:
            search_term (str): Term to search for
            fields (Optional[List[str]], optional): Specific fields to search. Defaults to order_number and notes.
            limit (int, optional): Maximum number of results. Defaults to 10.

        Returns:
            List[Order]: List of Order instances matching the search criteria

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            # Default search fields if not provided
            if not fields:
                fields = ['order_number', 'notes']

            # Normalize search term
            normalized_term = f'%{search_term.lower().strip()}%'

            # Build search conditions
            search_conditions = []
            for field in fields:
                if field == 'order_number':
                    search_conditions.append(Order.order_number.ilike(normalized_term))
                elif field == 'notes':
                    search_conditions.append(Order.notes.ilike(normalized_term))

            # Include supplier search
            # Add supplier name search
            supplier_subquery = (
                self.session.query(Supplier)
                .filter(Supplier.name.ilike(normalized_term))
                .subquery()
            )

            # Construct final query
            query = (
                self.session.query(Order)
                .options(
                    joinedload(Order.order_items),
                    joinedload(Order.supplier)
                )
                .filter(or_(*search_conditions))
                .limit(limit)
            )

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error searching orders: {e}')
            raise

    def create(self, order_data: Dict[str, Any]) -> Order:
        """
        Create a new order with associated items.

        Args:
            order_data (Dict[str, Any]): Order creation data

        Returns:
            Order: Created Order instance

        Raises:
            ValueError: If order validation fails
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate order items
            if 'order_items' not in order_data or not order_data['order_items']:
                raise ValueError('Order must have at least one item')

            # Create order instance
            order = Order(**{k: v for k, v in order_data.items() if k != 'order_items'})
            order.order_date = datetime.utcnow()

            # Calculate total amount
            order.calculate_total_amount()

            # Add order to session
            self.session.add(order)

            # Add order items
            for item_data in order_data.get('order_items', []):
                order_item = OrderItem(**item_data)
                order_item.order = order
                self.session.add(order_item)

            # Commit transaction
            self.session.commit()

            return order
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating order: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error creating order: {e}')
            raise

    def update(self, order_id: int, order_data: Dict[str, Any]) -> Order:
        """
        Update an existing order with new information.

        Args:
            order_id (int): ID of the order to update
            order_data (Dict[str, Any]): Updated order data

        Returns:
            Order: Updated Order instance

        Raises:
            ValueError: If order validation fails
            SQLAlchemyError: If database operation fails
        """
        try:
            # Retrieve existing order
            existing_order = self.get_with_items(order_id)

            if not existing_order:
                raise ValueError(f'Order with ID {order_id} not found')

            # Validate order items
            if 'order_items' not in order_data or not order_data['order_items']:
                raise ValueError('Order must have at least one item')

            # Update order attributes
            for key, value in order_data.items():
                if key != 'order_items' and hasattr(existing_order, key):
                    setattr(existing_order, key, value)

            # Recalculate total amount
            existing_order.calculate_total_amount()

            # Clear existing order items
            existing_order.order_items.clear()

            # Add new order items
            for item_data in order_data.get('order_items', []):
                order_item = OrderItem(**item_data)
                order_item.order = existing_order
                self.session.add(order_item)

            # Commit transaction
            self.session.commit()

            return existing_order
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating order: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error updating order: {e}')
            raise

    def delete(self, order_id: int) -> bool:
        """
        Delete an order and its associated items.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            ValueError: If order cannot be found
            SQLAlchemyError: If database operation fails
        """
        try:
            # Retrieve order
            order = self.get_with_items(order_id)

            if not order:
                raise ValueError(f'Order with ID {order_id} not found')

            # Delete order items first
            for item in order.order_items:
                self.session.delete(item)

            # Delete order
            self.session.delete(order)

            # Commit transaction
            self.session.commit()

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error deleting order: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error deleting order: {e}')
            raise

    def get_orders_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[
        str, Any]:
        """
        Generate a summary of orders within an optional date range.

        Args:
            start_date (Optional[datetime], optional): Start of date range
            end_date (Optional[datetime], optional): End of date range

        Returns:
            Dict[str, Any]: Order summary statistics

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Base query
            query = self.session.query(Order)

            # Apply date range filter if provided
            if start_date:
                query = query.filter(Order.order_date >= start_date)
            if end_date:
                query = query.filter(Order.order_date <= end_date)

            # Calculate summary metrics
            total_orders = query.count()
            total_amount = query.with_entities(func.sum(Order.total_amount)).scalar() or 0

            # Order status breakdown
            status_breakdown = (
                query.with_entities(
                    Order.status,
                    func.count(Order.id).label('count')
                )
                .group_by(Order.status)
                .all()
            )

            return {
                'total_orders': total_orders,
                'total_amount': float(total_amount),
                'status_breakdown': {
                    status: count for status, count in status_breakdown
                }
            }
        except SQLAlchemyError as e:
            logger.error(f'Error generating order summary: {e}')
            raise