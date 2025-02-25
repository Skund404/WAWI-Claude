# database/sqlalchemy/core/specialized/supplier_manager.py
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from di.core import inject
from services.interfaces import MaterialService
from models.supplier import Supplier
from models.order import Order
from models.part import Part
from models.leather import Leather
from core.exceptions import DatabaseError
from core.base_manager import BaseManager


class SupplierManager(BaseManager[Supplier]):
    """
    Specialized manager for Supplier models with additional capabilities.

    Extends BaseManager with supplier-specific operations.
    """

    def __init__(self, session_factory):
        """
        Initialize the SupplierManager.

        Args:
            session_factory (Callable[[], Session]): A factory function 
            that returns a SQLAlchemy Session.
        """
        super().__init__(Supplier, session_factory)
        self._logger = logging.getLogger(self.__class__.__name__)

    @inject(MaterialService)
    def get_supplier_with_orders(self, supplier_id: int) -> Optional[Supplier]:
        """
        Get supplier with their order history.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            Optional[Supplier]: Supplier with orders loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Supplier).options(
                    joinedload(Supplier.orders)
                ).where(Supplier.id == supplier_id)
                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            self._logger.error(f'Failed to retrieve supplier with orders: {e}')
            raise DatabaseError(f'Failed to retrieve supplier with orders', str(e))

    @inject(MaterialService)
    def get_supplier_products(self, supplier_id: int) -> Dict[str, List]:
        """
        Get all products supplied by a supplier.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            Dict[str, List]: Dictionary containing parts and leather supplied

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # Retrieve parts from the supplier
                parts_query = select(Part).where(Part.supplier_id == supplier_id)
                parts_result = session.execute(parts_query)
                parts = list(parts_result.scalars().all())

                # Retrieve leather from the supplier
                leather_query = select(Leather).where(Leather.supplier_id == supplier_id)
                leather_result = session.execute(leather_query)
                leather = list(leather_result.scalars().all())

                return {'parts': parts, 'leather': leather}
        except Exception as e:
            self._logger.error(f'Failed to get supplier products: {e}')
            raise DatabaseError(f'Failed to get supplier products', str(e))

    @inject(MaterialService)
    def get_supplier_order_history(
            self,
            supplier_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Order]:
        """
        Get supplier's order history with optional date range.

        Args:
            supplier_id (int): Supplier ID
            start_date (Optional[datetime]): Optional start date
            end_date (Optional[datetime]): Optional end date

        Returns:
            List[Order]: List of Order instances

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Order).where(Order.supplier_id == supplier_id)

                # Add date filtering if dates are provided
                if start_date:
                    query = query.where(Order.order_date >= start_date)
                if end_date:
                    query = query.where(Order.order_date <= end_date)

                # Order by most recent first
                query = query.order_by(Order.order_date.desc())

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            self._logger.error(f'Failed to get supplier order history: {e}')
            raise DatabaseError(f'Failed to get supplier order history', str(e))

    @inject(MaterialService)
    def update_supplier_rating(
            self,
            supplier_id: int,
            rating: float,
            notes: Optional[str] = None
    ) -> Optional[Supplier]:
        """
        Update supplier quality rating.

        Args:
            supplier_id (int): Supplier ID
            rating (float): New rating (0-5)
            notes (Optional[str]): Optional notes about the rating

        Returns:
            Optional[Supplier]: Updated Supplier instance

        Raises:
            DatabaseError: If update fails
            ValueError: If rating is out of valid range
        """
        # Validate rating
        if rating < 0 or rating > 5:
            raise ValueError('Rating must be between 0 and 5')

        try:
            with self.session_scope() as session:
                supplier = session.get(Supplier, supplier_id)

                if not supplier:
                    self._logger.warning(f'Supplier with ID {supplier_id} not found.')
                    return None

                # Update rating and notes
                supplier.rating = rating
                if notes:
                    supplier.rating_notes = notes

                session.commit()
                session.refresh(supplier)
                return supplier
        except Exception as e:
            self._logger.error(f'Failed to update supplier rating: {e}')
            raise DatabaseError(f'Failed to update supplier rating', str(e))

    @inject(MaterialService)
    def search_suppliers(self, term: str) -> List[Supplier]:
        """
        Search suppliers across multiple fields.

        Args:
            term (str): Term to search for

        Returns:
            List[Supplier]: List of matching Supplier instances

        Raises:
            DatabaseError: If search fails
        """
        try:
            with self.session_scope() as session:
                return session.query(Supplier).filter(
                    (Supplier.name.ilike(f'%{term}%')) |
                    (Supplier.contact_name.ilike(f'%{term}%')) |
                    (Supplier.contact_email.ilike(f'%{term}%')) |
                    (Supplier.contact_phone.ilike(f'%{term}%'))
                ).all()
        except Exception as e:
            self._logger.error(f'Failed to search suppliers: {e}')
            raise DatabaseError(f'Failed to search suppliers', str(e))

    @inject(MaterialService)
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Supplier:
        """
        Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): Dictionary containing supplier information

        Returns:
            Supplier: The created Supplier instance

        Raises:
            DatabaseError: If supplier creation fails
        """
        try:
            with self.session_scope() as session:
                # Validate required supplier data
                if not supplier_data:
                    raise ValueError("Supplier data cannot be empty")

                supplier = Supplier(**supplier_data)
                session.add(supplier)
                session.commit()
                session.refresh(supplier)
                return supplier
        except Exception as e:
            self._logger.error(f'Failed to create supplier: {e}')
            raise DatabaseError(f'Failed to create supplier', str(e))

    @inject(MaterialService)
    def get_supplier_performance_metrics(self, supplier_id: int) -> Dict[str, Any]:
        """
        Calculate performance metrics for a supplier.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            Dict[str, Any]: Dictionary of performance metrics

        Raises:
            DatabaseError: If metrics calculation fails
        """
        try:
            with self.session_scope() as session:
                # Total number of orders
                total_orders_query = select(func.count(Order.id)).where(Order.supplier_id == supplier_id)
                total_orders = session.execute(total_orders_query).scalar_one()

                # Total order value
                total_value_query = select(func.sum(Order.total_amount)).where(Order.supplier_id == supplier_id)
                total_value = session.execute(total_value_query).scalar_one() or 0

                # Average order value
                avg_order_value = total_value / total_orders if total_orders > 0 else 0

                # Get last order date
                last_order_query = select(func.max(Order.order_date)).where(Order.supplier_id == supplier_id)
                last_order_date = session.execute(last_order_query).scalar_one()

                return {
                    'total_orders': total_orders,
                    'total_order_value': total_value,
                    'average_order_value': avg_order_value,
                    'last_order_date': last_order_date
                }
        except Exception as e:
            self._logger.error(f'Failed to calculate supplier performance metrics: {e}')
            raise DatabaseError(f'Failed to calculate supplier performance metrics', str(e))