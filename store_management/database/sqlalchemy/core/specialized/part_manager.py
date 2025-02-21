# database/sqlalchemy/core/specialized/part_manager.py
"""
database/sqlalchemy/core/specialized/part_manager.py
Specialized manager for Part models with additional capabilities.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from store_management.database.sqlalchemy.core.base_manager import BaseManager
from store_management.database.sqlalchemy.models import Part, InventoryTransaction, InventoryStatus, TransactionType
from store_management.utils.error_handling import DatabaseError


class PartManager(BaseManager[Part]):
    """
    Specialized manager for Part model operations.

    Extends BaseManager with part-specific operations.
    """

    def get_part_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Get part with its transaction history.

        Args:
            part_id: Part ID

        Returns:
            Part with transactions loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Part).options(
                    joinedload(Part.transactions)
                ).where(Part.id == part_id)

                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve part with transactions", str(e))

    def update_part_stock(
            self,
            part_id: int,
            quantity_change: int,
            transaction_type: TransactionType,
            notes: Optional[str] = None
    ) -> Tuple[Optional[Part], Optional[InventoryTransaction]]:
        """
        Update part stock levels with transaction tracking.

        Args:
            part_id: Part ID
            quantity_change: Change in quantity (positive or negative)
            transaction_type: Type of transaction
            notes: Optional transaction notes

        Returns:
            Tuple of (updated Part, created Transaction)

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                # Get the part
                part = session.get(Part, part_id)
                if not part:
                    return None, None

                # Check if we're removing stock and have enough
                if quantity_change < 0 and part.stock_level + quantity_change < 0:
                    raise ValueError(f"Not enough stock. Current: {part.stock_level}, Change: {quantity_change}")

                # Update stock level
                old_stock = part.stock_level
                part.stock_level += quantity_change

                # Update status if needed
                if part.stock_level <= 0:
                    part.status = InventoryStatus.OUT_OF_STOCK
                elif part.stock_level <= part.min_stock_level:
                    part.status = InventoryStatus.LOW_STOCK
                else:
                    part.status = InventoryStatus.IN_STOCK

                # Create transaction record
                transaction = InventoryTransaction(
                    part_id=part_id,
                    quantity=quantity_change,
                    previous_quantity=old_stock,
                    new_quantity=part.stock_level,
                    transaction_type=transaction_type,
                    transaction_date=datetime.now(),
                    notes=notes
                )

                session.add(transaction)
                session.flush()

                return part, transaction
        except Exception as e:
            raise DatabaseError(f"Failed to update part stock", str(e))

    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Part]:
        """
        Get all parts with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of Part instances with low stock

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # Build the query
                query = select(Part).where(
                    Part.stock_level <= Part.min_stock_level
                )

                if not include_out_of_stock:
                    query = query.where(Part.stock_level > 0)

                # Order by stock level ratio (stock_level / min_stock_level)
                query = query.order_by(
                    (Part.stock_level / Part.min_stock_level).asc()
                )

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get low stock parts", str(e))

    def get_by_supplier(self, supplier_id: int) -> List[Part]:
        """
        Get parts by supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of parts from the specified supplier

        Raises:
            DatabaseError: If retrieval fails
        """
        return self.filter_by(supplier_id=supplier_id)