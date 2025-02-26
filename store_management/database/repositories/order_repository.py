# database/repositories/order_repository.py
"""
Repository for Order-related database operations.

This module provides data access and manipulation methods for orders
using SQLAlchemy ORM.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

from utils.circular_import_resolver import get_module


class OrderRepository:
    """
    Repository for handling Order-related database operations.

    Provides methods for creating, retrieving, updating, and deleting
    order records in the database.
    """

    def __init__(self, session: Session):
        """
        Initialize the OrderRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self._session = session

        # Lazy import to avoid circular dependencies
        try:
            self.Order = get_module('database.models.order').Order
            self.OrderItem = get_module('database.models.order').OrderItem
        except ImportError as e:
            logging.error(f"Failed to import Order models: {e}")
            raise

    def create(self, order_data: Dict[str, Any]) -> Any:
        """
        Create a new order in the database.

        Args:
            order_data (Dict[str, Any]): Dictionary of order details

        Returns:
            Order: The newly created order object

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            new_order = self.Order(**order_data)
            self._session.add(new_order)
            self._session.commit()
            return new_order
        except SQLAlchemyError as e:
            self._session.rollback()
            logging.error(f"Error creating order: {e}")
            raise

    def get_by_id(self, order_id: int) -> Optional[Any]:
        """
        Retrieve an order by its ID.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            Optional[Order]: The order if found, None otherwise
        """
        try:
            return self._session.query(self.Order).options(
                joinedload(self.Order.order_items)
            ).filter(self.Order.id == order_id).first()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving order {order_id}: {e}")
            return None

    def get_all_orders(self,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Any]:
        """
        Retrieve all orders, optionally filtered by date range.

        Args:
            start_date (Optional[datetime]): Start of date range
            end_date (Optional[datetime]): End of date range

        Returns:
            List[Order]: List of orders matching the criteria
        """
        try:
            query = self._session.query(self.Order)

            if start_date:
                query = query.filter(self.Order.created_at >= start_date)
            if end_date:
                query = query.filter(self.Order.created_at <= end_date)

            return query.options(joinedload(self.Order.order_items)).all()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving orders: {e}")
            return []

    def update_order(self, order_id: int, update_data: Dict[str, Any]) -> Optional[Any]:
        """
        Update an existing order.

        Args:
            order_id (int): ID of the order to update
            update_data (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Optional[Order]: The updated order, or None if update fails
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                logging.warning(f"No order found with ID {order_id}")
                return None

            for key, value in update_data.items():
                setattr(order, key, value)

            self._session.commit()
            return order
        except SQLAlchemyError as e:
            self._session.rollback()
            logging.error(f"Error updating order {order_id}: {e}")
            return None

    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order from the database.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            order = self.get_by_id(order_id)
            if not order:
                logging.warning(f"No order found with ID {order_id}")
                return False

            self._session.delete(order)
            self._session.commit()
            return True
        except SQLAlchemyError as e:
            self._session.rollback()
            logging.error(f"Error deleting order {order_id}: {e}")
            return False

    def get_recent_orders(self, days: int = 30) -> List[Any]:
        """
        Retrieve orders from the past specified number of days.

        Args:
            days (int, optional): Number of days to look back. Defaults to 30.

        Returns:
            List[Order]: List of recent orders
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return self._session.query(self.Order).filter(
                self.Order.created_at >= cutoff_date
            ).options(joinedload(self.Order.order_items)).all()
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving recent orders: {e}")
            return []