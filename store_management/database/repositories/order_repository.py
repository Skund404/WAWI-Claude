# store_management/database/repositories/order_repository.py

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.order import Order, OrderItem
from ..models.enums import OrderStatus


class OrderRepository(BaseRepository[Order]):
    """Repository for Order model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Order)

    def get_with_items(self, order_id: int) -> Optional[Order]:
        """
        Get order with all items.

        Args:
            order_id: Order ID

        Returns:
            Order with loaded items or None
        """
        return self.session.query(Order) \
            .options(joinedload(Order.items)) \
            .filter(Order.id == order_id) \
            .first()

    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Get orders by status.

        Args:
            status: Order status

        Returns:
            List of orders with the specified status
        """
        return self.session.query(Order).filter(Order.status == status).all()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """
        Get orders within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of orders within the date range
        """
        return self.session.query(Order) \
            .filter(Order.order_date >= start_date, Order.order_date <= end_date) \
            .all()

    def get_by_supplier(self, supplier_id: int) -> List[Order]:
        """
        Get orders for a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of orders for the supplier
        """
        return self.session.query(Order).filter(Order.supplier_id == supplier_id).all()