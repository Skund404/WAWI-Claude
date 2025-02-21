# database/sqlalchemy/core/specialized/leather_manager.py
"""
database/sqlalchemy/core/specialized/leather_manager.py
Specialized manager for Leather models with additional capabilities.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from store_management.database.sqlalchemy.core.base_manager import BaseManager
from store_management.database.sqlalchemy.models import Leather, LeatherTransaction, InventoryStatus, TransactionType
from store_management.utils.error_handling import DatabaseError


class LeatherManager(BaseManager[Leather]):
    """
    Specialized manager for Leather model operations.

    Extends BaseManager with leather-specific operations.
    """

    def get_leather_with_transactions(self, leather_id: int) -> Optional[Leather]:
        """
        Get leather with its transaction history.

        Args:
            leather_id: Leather ID

        Returns:
            Leather with transactions loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Leather).options(
                    joinedload(Leather.transactions)
                ).where(Leather.id == leather_id)

                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve leather with transactions", str(e))

    def update_leather_area(
            self,
            leather_id: int,
            area_change: float,
            transaction_type: TransactionType,
            notes: Optional[str] = None,
            wastage: Optional[float] = None
    ) -> Tuple[Optional[Leather], Optional[LeatherTransaction]]:
        """
        Update leather area with transaction tracking.

        Args:
            leather_id: Leather ID
            area_change: Change in area (positive or negative)
            transaction_type: Type of transaction
            notes: Optional transaction notes
            wastage: Optional wastage area

        Returns:
            Tuple of (updated Leather, created Transaction)

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                # Get the leather
                leather = session.get(Leather, leather_id)
                if not leather:
                    return None, None

                # Check if we're removing area and have enough
                if area_change < 0 and leather.area + area_change < 0:
                    raise ValueError(f"Not enough area. Current: {leather.area}, Change: {area_change}")

                # Update area
                old_area = leather.area
                leather.area += area_change

                # Update status if needed
                if leather.area <= 0:
                    leather.status = InventoryStatus.OUT_OF_STOCK
                elif leather.area <= leather.min_area:
                    leather.status = InventoryStatus.LOW_STOCK
                else:
                    leather.status = InventoryStatus.IN_STOCK

                # Create transaction record
                transaction = LeatherTransaction(
                    leather_id=leather_id,
                    area_change=area_change,
                    previous_area=old_area,
                    new_area=leather.area,
                    transaction_type=transaction_type,
                    transaction_date=datetime.now(),
                    notes=notes,
                    wastage=wastage
                )

                session.add(transaction)
                session.flush()

                return leather, transaction
        except Exception as e:
            raise DatabaseError(f"Failed to update leather area", str(e))

    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Leather]:
        """
        Get leather items with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of Leather instances with low stock

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # Build the query
                query = select(Leather).where(
                    Leather.area <= Leather.min_area
                )

                if not include_out_of_stock:
                    query = query.where(Leather.area > 0)

                # Order by area ratio (area / min_area)
                query = query.order_by(
                    (Leather.area / Leather.min_area).asc()
                )

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get low stock leather", str(e))

    def get_by_supplier(self, supplier_id: int) -> List[Leather]:
        """
        Get leather by supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of leather from the specified supplier

        Raises:
            DatabaseError: If retrieval fails
        """
        return self.filter_by(supplier_id=supplier_id)