# database/sqlalchemy/managers/incoming_goods_manager.py
"""
Manager for handling incoming goods and sale operations.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from di.core import inject
from services.interfaces import MaterialService
from core.exceptions import DatabaseError
from models.order import Order, OrderDetail, OrderStatus, PaymentStatus
from core.managers.base_manager import BaseManager
from models.storage import Storage
from models.product import Product
from models.supplier import Supplier

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IncomingGoodsManager(BaseManager[Order]):
    """
    Specialized manager for handling incoming goods and sale operations.
    """

    @inject(MaterialService)
    def __init__(self, session_factory):
        """
        Initialize the IncomingGoodsManager with a session factory.

        Args:
            session_factory: Factory to create database sessions
        """
        super().__init__(Order, session_factory)
        self.session = session_factory()

    @inject(MaterialService)
    def create_order(self, data: Dict[str, Any]) -> Order:
        """
        Create a new sale with validation and tracking.

        Args:
            data (Dict[str, Any]): Order data including sale number, supplier, etc.

        Returns:
            Order: Created sale instance

        Raises:
            DatabaseError: If sale creation fails
        """
        try:
            order = Order(
                order_number=data['sale_number'],
                supplier=data['supplier'],
                date_of_order=datetime.strptime(data['date_of_order'], '%Y-%m-%d'),
                status=OrderStatus(data['status']),
                payed=PaymentStatus(data['payed']),
                total_amount=data['total_amount']
            )
            self.session.add(order)
            self.session.commit()
            return order
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to create sale: {str(e)}')
            raise DatabaseError(f'Failed to create sale: {str(e)}') from e

    @inject(MaterialService)
    def get_all_orders(self) -> List[Order]:
        """
        Retrieve all orders from the database.

        Returns:
            List[Order]: List of all orders
        """
        try:
            return self.session.query(Order).all()
        except Exception as e:
            logger.error(f'Failed to retrieve orders: {str(e)}')
            raise DatabaseError(f'Failed to retrieve orders: {str(e)}') from e

    @inject(MaterialService)
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an sale by its ID.

        Args:
            order_id (int): ID of the sale to retrieve

        Returns:
            Optional[Order]: Order instance or None if not found
        """
        try:
            return self.session.query(Order).get(order_id)
        except Exception as e:
            logger.error(f'Failed to retrieve sale by ID {order_id}: {str(e)}')
            raise DatabaseError(f'Failed to retrieve sale by ID {order_id}: {str(e)}') from e

    @inject(MaterialService)
    def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """
        Retrieve an sale by its sale number.

        Args:
            order_number (str): Order number to search for

        Returns:
            Optional[Order]: Order instance or None if not found
        """
        try:
            return self.session.query(Order).filter_by(order_number=order_number).first()
        except Exception as e:
            logger.error(f'Failed to retrieve sale by number {order_number}: {str(e)}')
            raise DatabaseError(f'Failed to retrieve sale by number {order_number}: {str(e)}') from e

    @inject(MaterialService)
    def update_order(self, order_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing sale.

        Args:
            order_id (int): ID of the sale to update
            data (Dict[str, Any]): Updated sale data

        Returns:
            bool: True if update successful, False if sale not found
        """
        try:
            order = self.get_order_by_id(order_id)
            if order:
                for key, value in data.items():
                    setattr(order, key, value)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to update sale {order_id}: {str(e)}')
            raise DatabaseError(f'Failed to update sale {order_id}: {str(e)}') from e

    @inject(MaterialService)
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an sale by its ID.

        Args:
            order_id (int): ID of the sale to delete

        Returns:
            bool: True if deletion successful, False if sale not found
        """
        try:
            order = self.get_order_by_id(order_id)
            if order:
                self.session.delete(order)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to delete sale {order_id}: {str(e)}')
            raise DatabaseError(f'Failed to delete sale {order_id}: {str(e)}') from e

    @inject(MaterialService)
    def add_order_detail(self, order_id: int, data: Dict[str, Any]) -> OrderDetail:
        """
        Add a detail to an existing sale.

        Args:
            order_id (int): ID of the sale to add detail to
            data (Dict[str, Any]): Order detail data

        Returns:
            OrderDetail: Created sale detail instance
        """
        try:
            detail = OrderDetail(
                order_id=order_id,
                article=data['article'],
                unique_id=data['unique_id'],
                price=data['price'],
                amount=data['amount'],
                total=data['price'] * data['amount'],
                notes=data['notes']
            )
            self.session.add(detail)
            self.session.commit()
            return detail
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to add sale detail for sale {order_id}: {str(e)}')
            raise DatabaseError(f'Failed to add sale detail for sale {order_id}: {str(e)}') from e

    @inject(MaterialService)
    def get_order_details(self, order_id: int) -> List[OrderDetail]:
        """
        Retrieve all details for a specific sale.

        Args:
            order_id (int): ID of the sale to retrieve details for

        Returns:
            List[OrderDetail]: List of sale details
        """
        try:
            return self.session.query(OrderDetail).filter_by(order_id=order_id).all()
        except Exception as e:
            logger.error(f'Failed to retrieve sale details for sale {order_id}: {str(e)}')
            raise DatabaseError(f'Failed to retrieve sale details for sale {order_id}: {str(e)}') from e

    @inject(MaterialService)
    def update_order_detail(self, detail_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing sale detail.

        Args:
            detail_id (int): ID of the sale detail to update
            data (Dict[str, Any]): Updated sale detail data

        Returns:
            bool: True if update successful, False if detail not found
        """
        try:
            detail = self.session.query(OrderDetail).get(detail_id)
            if detail:
                for key, value in data.items():
                    setattr(detail, key, value)
                detail.total = detail.price * detail.amount
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to update sale detail {detail_id}: {str(e)}')
            raise DatabaseError(f'Failed to update sale detail {detail_id}: {str(e)}') from e

    @inject(MaterialService)
    def delete_order_detail(self, detail_id: int) -> bool:
        """
        Delete an sale detail by its ID.

        Args:
            detail_id (int): ID of the sale detail to delete

        Returns:
            bool: True if deletion successful, False if detail not found
        """
        try:
            detail = self.session.query(OrderDetail).get(detail_id)
            if detail:
                self.session.delete(detail)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to delete sale detail {detail_id}: {str(e)}')
            raise DatabaseError(f'Failed to delete sale detail {detail_id}: {str(e)}') from e

    @inject(MaterialService)
    def get_suppliers(self) -> List[str]:
        """
        Retrieve a list of supplier names.

        Returns:
            List[str]: List of supplier names
        """
        try:
            suppliers = self.session.query(Supplier.name).all()
            return [s[0] for s in suppliers]
        except Exception as e:
            logger.error(f'Failed to retrieve suppliers: {str(e)}')
            raise DatabaseError(f'Failed to retrieve suppliers: {str(e)}') from e

    @inject(MaterialService)
    def update_inventory(self, unique_id: str, amount: int, is_shelf: bool) -> None:
        """
        Update inventory for a product.

        Args:
            unique_id (str): Unique identifier of the product
            amount (int): Amount to update
            is_shelf (bool): Whether the item is on shelf or not
        """
        try:
            if is_shelf:
                item = self.session.query(Storage).filter_by(unique_id=unique_id).first()
            else:
                item = self.session.query(Product).filter_by(unique_id=unique_id).first()

            if item:
                item.amount += amount
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f'Failed to update inventory for {unique_id}: {str(e)}')
            raise DatabaseError(f'Failed to update inventory for {unique_id}: {str(e)}') from e