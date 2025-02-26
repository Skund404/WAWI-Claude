# database/repositories/order_repository.py
"""
Repository for Order and OrderItem models providing data access methods.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy
from sqlalchemy import and_, exc, func, or_
from sqlalchemy.orm import Session, joinedload

from database.models.order import Order, OrderItem
from database.repositories.base_repository import BaseRepository
from utils.circular_import_resolver import get_module

# Configure logger
logger = logging.getLogger(__name__)


class OrderRepository(BaseRepository):
    """Repository for managing Order and OrderItem database operations."""

    def __init__(self, session: Session):
        """Initialize the OrderRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Order)
        logger.debug("OrderRepository initialized")

    def get_all(self) -> List[Order]:
        """Get all orders with their items.

        Returns:
            List[Order]: List of Order objects with loaded items
        """
        try:
            return self.session.query(Order).options(
                joinedload(Order.items)
            ).order_by(Order.order_date.desc()).all()
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error getting all orders: {str(e)}", exc_info=True)
            return []

    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get an order by its ID.

        Args:
            order_id (int): Order ID

        Returns:
            Optional[Order]: Order object if found, None otherwise
        """
        try:
            return self.session.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error getting order {order_id}: {str(e)}", exc_info=True)
            return None

    def get_by_status(self, status: str) -> List[Order]:
        """Get orders by status.

        Args:
            status (str): Status to filter by

        Returns:
            List[Order]: List of orders with the specified status
        """
        try:
            return self.session.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.status == status).order_by(Order.order_date.desc()).all()
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error getting orders by status {status}: {str(e)}", exc_info=True)
            return []

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Get orders within a date range.

        Args:
            start_date (datetime): Start date (inclusive)
            end_date (datetime): End date (inclusive)

        Returns:
            List[Order]: List of orders within the date range
        """
        try:
            return self.session.query(Order).options(
                joinedload(Order.items)
            ).filter(
                and_(
                    Order.order_date >= start_date,
                    Order.order_date <= end_date
                )
            ).order_by(Order.order_date.desc()).all()
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error getting orders by date range: {str(e)}", exc_info=True)
            return []

    def create(self, order: Order) -> Order:
        """Create a new order.

        Args:
            order (Order): Order object to create

        Returns:
            Order: Created order with ID
        """
        try:
            self.session.add(order)
            self.session.flush()  # Flush to get ID but don't commit yet
            return order
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating order: {str(e)}", exc_info=True)
            raise

    def update(self, order: Order) -> bool:
        """Update an order.

        Args:
            order (Order): Order object to update

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            self.session.add(order)
            self.session.flush()
            return True
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating order {order.id}: {str(e)}", exc_info=True)
            return False

    def delete(self, order_id: int) -> bool:
        """Delete an order.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            order = self.session.query(Order).get(order_id)
            if not order:
                return False

            self.session.delete(order)
            self.session.flush()
            return True
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error deleting order {order_id}: {str(e)}", exc_info=True)
            return False

    def add_item(self, item: OrderItem) -> bool:
        """Add an item to an order.

        Args:
            item (OrderItem): Order item to add

        Returns:
            bool: True if add was successful, False otherwise
        """
        try:
            self.session.add(item)
            self.session.flush()
            return True
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error adding item to order {item.order_id}: {str(e)}", exc_info=True)
            return False

    def update_item(self, item: OrderItem) -> bool:
        """Update an order item.

        Args:
            item (OrderItem): Order item to update

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            self.session.add(item)
            self.session.flush()
            return True
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating item {item.id}: {str(e)}", exc_info=True)
            return False

    def delete_item(self, item_id: int) -> bool:
        """Delete an order item.

        Args:
            item_id (int): ID of the item to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            item = self.session.query(OrderItem).get(item_id)
            if not item:
                return False

            self.session.delete(item)
            self.session.flush()
            return True
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error deleting item {item_id}: {str(e)}", exc_info=True)
            return False

    def clear_items(self, order_id: int) -> bool:
        """Delete all items for an order.

        Args:
            order_id (int): ID of the order to clear items for

        Returns:
            bool: True if clearing was successful, False otherwise
        """
        try:
            self.session.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
            self.session.flush()
            return True
        except exc.SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error clearing items for order {order_id}: {str(e)}", exc_info=True)
            return False

    def search(self, criteria: Dict[str, Any]) -> List[Order]:
        """Search for orders based on criteria.

        Args:
            criteria (Dict[str, Any]): Search criteria

        Returns:
            List[Order]: List of matching orders
        """
        try:
            query = self.session.query(Order).options(
                joinedload(Order.items)
            )

            # Apply search criteria
            if 'customer_name' in criteria:
                query = query.filter(Order.customer_name.ilike(f"%{criteria['customer_name']}%"))

            if 'customer_email' in criteria:
                query = query.filter(Order.customer_email.ilike(f"%{criteria['customer_email']}%"))

            if 'status' in criteria:
                query = query.filter(Order.status == criteria['status'])

            if 'payment_status' in criteria:
                query = query.filter(Order.payment_status == criteria['payment_status'])

            if 'start_date' in criteria and 'end_date' in criteria:
                query = query.filter(
                    and_(
                        Order.order_date >= criteria['start_date'],
                        Order.order_date <= criteria['end_date']
                    )
                )
            elif 'start_date' in criteria:
                query = query.filter(Order.order_date >= criteria['start_date'])
            elif 'end_date' in criteria:
                query = query.filter(Order.order_date <= criteria['end_date'])

            # Order by date descending (newest first)
            query = query.order_by(Order.order_date.desc())

            return query.all()
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error searching orders: {str(e)}", exc_info=True)
            return []

    def get_recent_orders(self, days: int = 30) -> List[Order]:
        """Get orders from the last N days.

        Args:
            days (int, optional): Number of days to look back. Defaults to 30.

        Returns:
            List[Order]: List of recent orders
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return self.session.query(Order).options(
                joinedload(Order.items)
            ).filter(
                Order.order_date >= cutoff_date
            ).order_by(Order.order_date.desc()).all()
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error getting recent orders: {str(e)}", exc_info=True)
            return []

    def get_order_count_by_status(self) -> Dict[str, int]:
        """Get count of orders grouped by status.

        Returns:
            Dict[str, int]: Dictionary mapping status to count
        """
        try:
            results = self.session.query(
                Order.status, func.count(Order.id)
            ).group_by(Order.status).all()

            return dict(results)
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error getting order counts by status: {str(e)}", exc_info=True)
            return {}