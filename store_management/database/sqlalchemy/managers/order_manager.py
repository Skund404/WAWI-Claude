# database/sqlalchemy/managers/order_manager.py
"""
Enhanced order manager implementing specialized order operations
while leveraging base manager functionality.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from core.exceptions import DatabaseError
from core.managers.base_manager import BaseManager
from models.order import Order, OrderItem
from models.part import Part
from models.leather import Leather
from models.supplier import Supplier

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OrderManager(BaseManager[Order]):
    """
    Enhanced order manager implementing specialized order operations
    while leveraging base manager functionality.
    """

    @inject(MaterialService)
    def __init__(self, session_factory):
        """
        Initialize OrderManager with session factory.

        Args:
            session_factory: Factory to create database sessions
        """
        super().__init__(session_factory, Order)

    @inject(MaterialService)
    def create_order(
            self,
            order_data: Dict[str, Any],
            items: List[Dict[str, Any]]
    ) -> Order:
        """
        Create a new order with items.

        Args:
            order_data (Dict[str, Any]): Dictionary containing order data
            items (List[Dict[str, Any]]): List of dictionaries containing order item data

        Returns:
            Order: Created Order instance

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            # Validate required order fields
            required_fields = ['supplier_id', 'order_date', 'status']
            missing_fields = [field for field in required_fields if field not in order_data]

            if missing_fields:
                raise DatabaseError(
                    f"Missing required order fields: {', '.join(missing_fields)}"
                )

            with self.session_scope() as session:
                # Create order
                order = Order(**order_data)
                session.add(order)
                session.flush()

                # Add order items
                for item_data in items:
                    # Validate item data
                    if not all(k in item_data for k in ['item_type', 'item_id', 'quantity']):
                        raise DatabaseError('Invalid order item data')

                    # Create order item
                    order_item = OrderItem(
                        order_id=order.id,
                        **item_data
                    )
                    session.add(order_item)

                return order

        except Exception as e:
            logger.error(f'Failed to create order: {str(e)}')
            raise DatabaseError(f'Failed to create order: {str(e)}') from e

    @inject(MaterialService)
    def get_order_with_items(self, order_id: int) -> Optional[Order]:
        """
        Get order with all its items.

        Args:
            order_id (int): Order ID

        Returns:
            Optional[Order]: Order instance with items loaded or None if not found
        """
        with self.session_scope() as session:
            query = select(Order).options(joinedload(Order.items)).filter(Order.id == order_id)
            return session.execute(query).scalar()

    @inject(MaterialService)
    def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """
        Update order status with proper validation.

        Args:
            order_id (int): Order ID
            status (str): New status

        Returns:
            Optional[Order]: Updated Order instance or None if not found

        Raises:
            DatabaseError: If status is invalid
        """
        # Define valid statuses
        valid_statuses = ['pending', 'approved', 'processing', 'shipped', 'delivered', 'cancelled']

        # Validate status
        if status not in valid_statuses:
            raise DatabaseError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Update order with new status
        return self.update(order_id, {'status': status, 'modified_at': datetime.utcnow()})

    @inject(MaterialService)
    def add_order_items(
            self,
            order_id: int,
            items: List[Dict[str, Any]]
    ) -> Order:
        """
        Add items to an existing order.

        Args:
            order_id (int): Order ID
            items (List[Dict[str, Any]]): List of dictionaries containing item data

        Returns:
            Order: Updated Order instance

        Raises:
            DatabaseError: If order not found or validation fails
        """
        with self.session_scope() as session:
            # Retrieve order
            order = session.get(Order, order_id)

            if not order:
                raise DatabaseError(f'Order {order_id} not found')

            # Add new items
            for item_data in items:
                # Validate item data
                if not all(k in item_data for k in ['item_type', 'item_id', 'quantity']):
                    raise DatabaseError('Invalid order item data')

                # Create order item
                order_item = OrderItem(
                    order_id=order_id,
                    **item_data
                )
                session.add(order_item)

            # Update modification time
            order.modified_at = datetime.utcnow()

            return order

    @inject(MaterialService)
    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """
        Remove an item from an order.

        Args:
            order_id (int): Order ID
            item_id (int): Order Item ID

        Returns:
            bool: True if item was removed, False otherwise
        """
        with self.session_scope() as session:
            # Find the specific order item
            item = (session.query(OrderItem)
                    .filter(and_(OrderItem.order_id == order_id, OrderItem.id == item_id))
                    .first()
                    )

            if item:
                session.delete(item)
                return True

            return False

    @inject(MaterialService)
    def search_orders(self, search_term: str) -> List[Order]:
        """
        Search orders by various fields.

        Args:
            search_term (str): Term to search for

        Returns:
            List[Order]: List of matching Order instances
        """
        query = select(Order).filter(
            or_(
                Order.order_number.ilike(f'%{search_term}%'),
                Order.notes.ilike(f'%{search_term}%'),
                Order.status.ilike(f'%{search_term}%')
            )
        )

        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    @inject(MaterialService)
    def get_orders_by_date_range(
            self,
            start_date: datetime,
            end_date: datetime
    ) -> List[Order]:
        """
        Get orders within a date range.

        Args:
            start_date (datetime): Start date
            end_date (datetime): End date

        Returns:
            List[Order]: List of Order instances within the date range
        """
        query = (
            select(Order)
            .filter(and_(
                Order.order_date >= start_date,
                Order.order_date <= end_date
            ))
            .order_by(Order.order_date.desc())
        )

        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    @inject(MaterialService)
    def get_supplier_orders(self, supplier_id: int) -> List[Order]:
        """
        Get all orders for a specific supplier.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            List[Order]: List of Order instances for the supplier
        """
        query = select(Order).filter(Order.supplier_id == supplier_id)

        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    @inject(MaterialService)
    def calculate_order_total(self, order_id: int) -> float:
        """
        Calculate total value of an order.

        Args:
            order_id (int): Order ID

        Returns:
            float: Total order value

        Raises:
            DatabaseError: If order not found
        """
        with self.session_scope() as session:
            # Retrieve order
            order = session.get(Order, order_id)

            if not order:
                raise DatabaseError(f'Order {order_id} not found')

            # Calculate total
            total = 0.0
            for item in order.items:
                if item.item_type == 'part':
                    part = session.get(Part, item.item_id)
                    if part:
                        total += part.price * item.quantity
                elif item.item_type == 'leather':
                    leather = session.get(Leather, item.item_id)
                    if leather:
                        total += leather.price_per_sqft * item.quantity

            return total