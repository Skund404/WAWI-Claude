# File: F:\WAWI Homebrew\WAWI Claude\store_management\database\sqlalchemy\core\specialized\order_manager.py

from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from database.sqlalchemy.core.base_manager import BaseManager
from database.models.order import Order

class OrderManager(BaseManager):
    """
    Specialized manager for Order model operations.

    This class extends BaseManager with order-specific operations.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize the OrderManager.

        Args:
            session_factory: A callable that returns a SQLAlchemy Session.
        """
        super().__init__(Order, session_factory)

    def create_order(self, order_data: Dict[str, Any]) -> Order:
        """
        Create a new order.

        Args:
            order_data: Dictionary containing order information.

        Returns:
            The created Order instance.
        """
        with self.session_scope() as session:
            order = Order(**order_data)
            session.add(order)
            session.commit()
            return order

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an order by its ID.

        Args:
            order_id: The ID of the order to retrieve.

        Returns:
            The Order instance if found, None otherwise.
        """
        with self.session_scope() as session:
            return session.query(Order).filter(Order.id == order_id).first()

    def get_all_orders(self) -> List[Order]:
        """
        Retrieve all orders.

        Returns:
            A list of all Order instances.
        """
        with self.session_scope() as session:
            return session.query(Order).all()

    # Add more order-specific methods as needed