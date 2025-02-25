# database/sqlalchemy/core/specialized/order_manager.py
import logging
from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select
from di.core import inject
from services.interfaces import MaterialService, OrderService
from models.order import Order
from core.exceptions import DatabaseError
from core.base_manager import BaseManager


class OrderManager(BaseManager[Order]):
    """
    Specialized manager for Order model operations.

    This class extends BaseManager with order-specific operations.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize the OrderManager.

        Args:
            session_factory (Callable[[], Session]): A factory function 
            that returns a SQLAlchemy Session.
        """
        super().__init__(Order, session_factory)
        self._logger = logging.getLogger(self.__class__.__name__)

    @inject(MaterialService)
    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """
        Create a new order.

        Args:
            order_data (Dict[str, Any]): Dictionary containing order information.

        Returns:
            Order: The created Order instance.

        Raises:
            DatabaseError: If there's an error creating the order.
        """
        try:
            with self.session_scope() as session:
                # Validate required order data
                if not order_data:
                    raise ValueError("Order data cannot be empty")

                # Create order instance
                order = Order(**order_data)
                session.add(order)
                session.commit()
                session.refresh(order)
                return order
        except Exception as e:
            self._logger.error(f'Error creating order: {e}')
            raise DatabaseError(f'Failed to create order: {str(e)}', str(e))

    @inject(MaterialService)
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an order by its ID.

        Args:
            order_id (int): The ID of the order to retrieve.

        Returns:
            Optional[Order]: The Order instance if found, None otherwise.

        Raises:
            DatabaseError: If there's an error retrieving the order.
        """
        try:
            with self.session_scope() as session:
                return session.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            self._logger.error(f'Error retrieving order with ID {order_id}: {e}')
            raise DatabaseError(f'Failed to retrieve order', str(e))

    @inject(MaterialService)
    def get_all_orders(self) -> List[Order]:
        """
        Retrieve all orders.

        Returns:
            List[Order]: A list of all Order instances.

        Raises:
            DatabaseError: If there's an error retrieving orders.
        """
        try:
            with self.session_scope() as session:
                return session.query(Order).all()
        except Exception as e:
            self._logger.error(f'Error retrieving all orders: {e}')
            raise DatabaseError('Failed to retrieve orders', str(e))

    @inject(MaterialService)
    def update_order(self, order_id: int, update_data: Dict[str, Any]) -> Optional[Order]:
        """
        Update an existing order.

        Args:
            order_id (int): The ID of the order to update.
            update_data (Dict[str, Any]): Dictionary containing fields to update.

        Returns:
            Optional[Order]: The updated Order instance, or None if not found.

        Raises:
            DatabaseError: If there's an error updating the order.
        """
        try:
            with self.session_scope() as session:
                order = session.get(Order, order_id)

                if not order:
                    self._logger.warning(f'Order with ID {order_id} not found.')
                    return None

                # Update order attributes
                for key, value in update_data.items():
                    setattr(order, key, value)

                session.commit()
                session.refresh(order)
                return order
        except Exception as e:
            self._logger.error(f'Error updating order {order_id}: {e}')
            raise DatabaseError(f'Failed to update order', str(e))

    @inject(MaterialService)
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order by its ID.

        Args:
            order_id (int): The ID of the order to delete.

        Returns:
            bool: True if the order was deleted, False otherwise.

        Raises:
            DatabaseError: If there's an error deleting the order.
        """
        try:
            with self.session_scope() as session:
                order = session.get(Order, order_id)

                if not order:
                    self._logger.warning(f'Order with ID {order_id} not found.')
                    return False

                session.delete(order)
                session.commit()
                return True
        except Exception as e:
            self._logger.error(f'Error deleting order {order_id}: {e}')
            raise DatabaseError(f'Failed to delete order', str(e))