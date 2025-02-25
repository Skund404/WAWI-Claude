# database/sqlalchemy/core/specialized/part_manager.py
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from di.core import inject
from services.interfaces import MaterialService
from models.part import Part, InventoryTransaction
from models.transaction import TransactionType
from core.exceptions import DatabaseError
from core.base_manager import BaseManager


class PartManager(BaseManager[Part]):
    """
    Specialized manager for Part-related database operations.

    Provides methods for managing part inventory, transactions,
    and stock-related queries.
    """

    def __init__(self, session_factory):
        """
        Initialize the PartManager.

        Args:
            session_factory (Callable[[], Session]): A factory function 
            that returns a SQLAlchemy Session.
        """
        super().__init__(Part, session_factory)
        self._logger = logging.getLogger(self.__class__.__name__)

    @inject(MaterialService)
    def get_part_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Retrieve a part with its associated transactions.

        Args:
            part_id (int): The unique identifier of the part.

        Returns:
            Optional[Part]: The part with its transactions, or None if not found.

        Raises:
            DatabaseError: If there's an error retrieving the part.
        """
        try:
            with self.session_scope() as session:
                query = select(Part).options(
                    joinedload(Part.transactions)
                ).where(Part.id == part_id)
                result = session.execute(query)
                part = result.scalars().first()
                return part
        except Exception as e:
            self._logger.error(f'Error retrieving part with transactions: {e}')
            raise DatabaseError(f'Failed to retrieve part with transactions', str(e))

    @inject(MaterialService)
    def update_part_stock(
            self,
            part_id: int,
            quantity_change: float,
            transaction_type: TransactionType,
            notes: Optional[str] = None
    ) -> bool:
        """
        Update part stock and create a corresponding transaction.

        Args:
            part_id (int): The unique identifier of the part.
            quantity_change (float): The amount to change in stock (can be positive or negative).
            transaction_type (TransactionType): The type of stock transaction.
            notes (Optional[str], optional): Additional notes about the transaction.

        Returns:
            bool: True if the update was successful, False otherwise.

        Raises:
            DatabaseError: If there's an error updating part stock.
        """
        try:
            with self.session_scope() as session:
                part = session.get(Part, part_id)

                if not part:
                    self._logger.warning(f'Part with ID {part_id} not found.')
                    return False

                # Validate stock change doesn't result in negative stock
                if part.stock + quantity_change < 0:
                    self._logger.warning(f'Insufficient stock for change: {quantity_change}')
                    return False

                part.stock += quantity_change

                # Create transaction record
                transaction = InventoryTransaction(
                    part_id=part_id,
                    quantity_change=quantity_change,
                    transaction_type=transaction_type,
                    notes=notes
                )
                session.add(transaction)
                session.commit()
                return True
        except Exception as e:
            self._logger.error(f'Error updating part stock: {e}')
            raise DatabaseError(f'Failed to update part stock', str(e))

    @inject(MaterialService)
    def get_low_stock_parts(
            self,
            include_out_of_stock: bool = False
    ) -> List[Part]:
        """
        Retrieve parts with low stock.

        Args:
            include_out_of_stock (bool, optional): Whether to include parts with zero stock. 
                Defaults to False.

        Returns:
            List[Part]: List of parts with low stock.

        Raises:
            DatabaseError: If there's an error retrieving low stock parts.
        """
        try:
            with self.session_scope() as session:
                query = session.query(Part)

                # Filter by stock level
                if include_out_of_stock:
                    query = query.filter(Part.stock <= Part.min_stock)
                else:
                    query = query.filter(
                        (Part.stock <= Part.min_stock) &
                        (Part.stock > 0)
                    )

                return query.all()
        except Exception as e:
            self._logger.error(f'Error retrieving low stock parts: {e}')
            raise DatabaseError(f'Failed to retrieve low stock parts', str(e))

    @inject(MaterialService)
    def get_by_supplier(self, supplier_id: int) -> List[Part]:
        """
        Retrieve parts associated with a specific supplier.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            List[Part]: List of parts from the specified supplier.

        Raises:
            DatabaseError: If there's an error retrieving parts by supplier.
        """
        try:
            with self.session_scope() as session:
                return session.query(Part).filter(Part.supplier_id == supplier_id).all()
        except Exception as e:
            self._logger.error(f'Error retrieving parts by supplier: {e}')
            raise DatabaseError(f'Failed to retrieve parts by supplier', str(e))