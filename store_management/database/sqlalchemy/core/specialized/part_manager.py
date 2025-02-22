# database/sqlalchemy/core/specialized/part_manager.py
"""
Specialized manager for Part-related database operations.
"""

from typing import List, Optional, Union

from database.sqlalchemy.base_manager import BaseManager
from database.models import (
    Part,
    InventoryTransaction,
    InventoryStatus,
    TransactionType
)


class PartManager(BaseManager):
    """
    Specialized manager for handling Part-related database operations.

    Provides methods for managing part inventory, transactions,
    and stock-related queries.
    """

    def get_part_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Retrieve a part with its associated transactions.

        Args:
            part_id (int): The unique identifier of the part.

        Returns:
            Optional[Part]: The part with its transactions, or None if not found.
        """
        try:
            with self.session_scope() as session:
                part = session.query(Part).filter(Part.id == part_id).first()
                if part:
                    # Eager load transactions if needed
                    part.transactions  # This will fetch related transactions
                return part
        except Exception as e:
            self._logger.error(f"Error retrieving part with transactions: {e}")
            return None

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
            notes (Optional[str], optional): Additional notes about the transaction. Defaults to None.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            with self.session_scope() as session:
                part = session.query(Part).filter(Part.id == part_id).first()
                if not part:
                    self._logger.warning(f"Part with ID {part_id} not found.")
                    return False

                # Update part stock
                part.stock += quantity_change

                # Create transaction record
                transaction = InventoryTransaction(
                    part_id=part_id,
                    quantity_change=quantity_change,
                    transaction_type=transaction_type,
                    notes=notes
                )
                session.add(transaction)

                return True
        except Exception as e:
            self._logger.error(f"Error updating part stock: {e}")
            return False

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
        """
        try:
            with self.session_scope() as session:
                query = session.query(Part)

                if include_out_of_stock:
                    query = query.filter(Part.stock <= Part.min_stock)
                else:
                    query = query.filter(
                        (Part.stock <= Part.min_stock) &
                        (Part.stock > 0)
                    )

                return query.all()
        except Exception as e:
            self._logger.error(f"Error retrieving low stock parts: {e}")
            return []

    def get_by_supplier(self, supplier_id: int) -> List[Part]:
        """
        Retrieve parts associated with a specific supplier.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            List[Part]: List of parts from the specified supplier.
        """
        try:
            with self.session_scope() as session:
                return session.query(Part).filter(Part.supplier_id == supplier_id).all()
        except Exception as e:
            self._logger.error(f"Error retrieving parts by supplier: {e}")
            return []