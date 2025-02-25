# database/sqlalchemy/core/specialized/leather_manager.py
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from di.core import inject
from services.interfaces import MaterialService
from models.leather import Leather, LeatherTransaction
from models.transaction import TransactionType
from core.exceptions import DatabaseError
from core.base_manager import BaseManager


class LeatherManager(BaseManager[Leather]):
    """
    Specialized manager for Leather-related database operations.

    Provides methods for managing leather inventory, transactions,
    and stock-related queries.
    """

    def __init__(self, session_factory):
        """
        Initialize the LeatherManager.

        Args:
            session_factory (Callable[[], Session]): A factory function 
            that returns a SQLAlchemy Session.
        """
        super().__init__(Leather, session_factory)
        self._logger = logging.getLogger(self.__class__.__name__)

    @inject(MaterialService)
    def get_leather_with_transactions(self, leather_id: int) -> Optional[Leather]:
        """
        Retrieve a leather item with its associated transactions.

        Args:
            leather_id (int): The unique identifier of the leather item.

        Returns:
            Optional[Leather]: The leather item with its transactions, or None if not found.

        Raises:
            DatabaseError: If there's an error retrieving the leather item.
        """
        try:
            with self.session_scope() as session:
                query = select(Leather).options(
                    joinedload(Leather.transactions)
                ).where(Leather.id == leather_id)
                result = session.execute(query)
                leather = result.scalars().first()
                return leather
        except Exception as e:
            self._logger.error(f'Error retrieving leather with transactions: {e}')
            raise DatabaseError(f'Failed to retrieve leather with transactions', str(e))

    @inject(MaterialService)
    def update_leather_area(
            self,
            leather_id: int,
            area_change: float,
            transaction_type: TransactionType,
            notes: Optional[str] = None,
            wastage: Optional[float] = None
    ) -> bool:
        """
        Update leather area and create a corresponding transaction.

        Args:
            leather_id (int): The unique identifier of the leather.
            area_change (float): The amount to change in area (can be positive or negative).
            transaction_type (TransactionType): The type of stock transaction.
            notes (Optional[str], optional): Additional notes about the transaction.
            wastage (Optional[float], optional): Wastage amount during the transaction.

        Returns:
            bool: True if the update was successful, False otherwise.

        Raises:
            DatabaseError: If there's an error updating the leather area.
        """
        try:
            with self.session_scope() as session:
                leather = session.get(Leather, leather_id)

                if not leather:
                    self._logger.warning(f'Leather with ID {leather_id} not found.')
                    return False

                # Validate area change doesn't result in negative area
                if leather.current_area + area_change < 0:
                    self._logger.warning(f'Insufficient leather area for change: {area_change}')
                    return False

                leather.current_area += area_change

                # Create transaction record
                transaction = LeatherTransaction(
                    leather_id=leather_id,
                    area_change=area_change,
                    transaction_type=transaction_type,
                    notes=notes,
                    wastage=wastage
                )
                session.add(transaction)
                session.commit()
                return True
        except Exception as e:
            self._logger.error(f'Error updating leather area: {e}')
            raise DatabaseError(f'Failed to update leather area', str(e))

    @inject(MaterialService)
    def get_low_stock_leather(
            self,
            include_out_of_stock: bool = False,
            supplier_id: Optional[int] = None
    ) -> List[Leather]:
        """
        Retrieve leather items with low stock.

        Args:
            include_out_of_stock (bool, optional): Whether to include leather with zero area. 
                Defaults to False.
            supplier_id (Optional[int], optional): Filter by specific supplier. 
                Defaults to None.

        Returns:
            List[Leather]: List of leather items with low stock.

        Raises:
            DatabaseError: If there's an error retrieving low stock leather.
        """
        try:
            with self.session_scope() as session:
                query = session.query(Leather)

                # Filter by stock level
                if include_out_of_stock:
                    query = query.filter(Leather.current_area <= Leather.min_area)
                else:
                    query = query.filter(
                        (Leather.current_area <= Leather.min_area) &
                        (Leather.current_area > 0)
                    )

                # Optional supplier filtering
                if supplier_id is not None:
                    query = query.filter(Leather.supplier_id == supplier_id)

                return query.all()
        except Exception as e:
            self._logger.error(f'Error retrieving low stock leather: {e}')
            raise DatabaseError(f'Failed to retrieve low stock leather', str(e))

    @inject(MaterialService)
    def get_by_supplier(self, supplier_id: int) -> List[Leather]:
        """
        Retrieve leather items associated with a specific supplier.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            List[Leather]: List of leather items from the specified supplier.

        Raises:
            DatabaseError: If there's an error retrieving leather by supplier.
        """
        try:
            with self.session_scope() as session:
                return session.query(Leather).filter(Leather.supplier_id == supplier_id).all()
        except Exception as e:
            self._logger.error(f'Error retrieving leather by supplier: {e}')
            raise DatabaseError(f'Failed to retrieve leather by supplier', str(e))