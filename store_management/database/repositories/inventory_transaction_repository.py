# database/repositories/inventory_transaction_repository.py
"""
Inventory Transaction Repository for managing inventory transaction records.

Provides methods for creating, retrieving, and analyzing inventory movements.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, or_, desc, between
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from database.repositories.base_repository import BaseRepository
from database.models.inventory_transaction import InventoryTransaction
from database.models.enums import TransactionType, InventoryAdjustmentType
from database.exceptions import DatabaseError, ModelNotFoundError


class InventoryTransactionRepository(BaseRepository[InventoryTransaction]):
    """
    Repository for managing inventory transactions in the database.

    Provides methods for creating, retrieving, and analyzing inventory
    movements with comprehensive reporting capabilities.
    """

    def __init__(self, session: Session):
        """
        Initialize the Inventory Transaction Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, InventoryTransaction)
        self._logger = logging.getLogger(__name__)

    def get_by_inventory_id(
            self,
            inventory_id: int,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[InventoryTransaction]:
        """
        Get transactions for a specific inventory item.

        Args:
            inventory_id: ID of the inventory item
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            List of inventory transactions for the specified item
        """
        try:
            stmt = (
                select(InventoryTransaction)
                .where(InventoryTransaction.inventory_id == inventory_id)
                .order_by(desc(InventoryTransaction.created_at))
            )

            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving transactions for inventory {inventory_id}: {e}")
            raise DatabaseError(f"Error retrieving transactions: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving transactions for inventory {inventory_id}: {e}")
            raise

    def get_by_transaction_type(
            self,
            transaction_type: TransactionType,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: Optional[int] = None
    ) -> List[InventoryTransaction]:
        """
        Get transactions by type with optional date range filtering.

        Args:
            transaction_type: Type of transaction to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of transactions to return

        Returns:
            List of transactions of the specified type
        """
        try:
            conditions = [InventoryTransaction.transaction_type == transaction_type]

            if start_date and end_date:
                conditions.append(
                    between(InventoryTransaction.created_at, start_date, end_date)
                )
            elif start_date:
                conditions.append(InventoryTransaction.created_at >= start_date)
            elif end_date:
                conditions.append(InventoryTransaction.created_at <= end_date)

            stmt = (
                select(InventoryTransaction)
                .where(and_(*conditions))
                .order_by(desc(InventoryTransaction.created_at))
            )

            if limit is not None:
                stmt = stmt.limit(limit)

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving transactions by type: {e}")
            raise DatabaseError(f"Error retrieving transactions by type: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving transactions by type: {e}")
            raise

    def get_by_date_range(
            self,
            start_date: datetime,
            end_date: datetime,
            item_type: Optional[str] = None
    ) -> List[InventoryTransaction]:
        """
        Get transactions within a date range with optional item type filtering.

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            item_type: Optional item type for filtering ('material', 'product', 'tool')

        Returns:
            List of transactions within the date range
        """
        try:
            conditions = [
                between(InventoryTransaction.created_at, start_date, end_date)
            ]

            if item_type:
                stmt = (
                    select(InventoryTransaction)
                    .join(InventoryTransaction.inventory)
                    .where(and_(*conditions))
                    .where(InventoryTransaction.inventory.item_type == item_type)
                    .order_by(desc(InventoryTransaction.created_at))
                )
            else:
                stmt = (
                    select(InventoryTransaction)
                    .where(and_(*conditions))
                    .order_by(desc(InventoryTransaction.created_at))
                )

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving transactions by date range: {e}")
            raise DatabaseError(f"Error retrieving transactions by date range: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving transactions by date range: {e}")
            raise

    def create_transaction(
            self,
            inventory_id: int,
            quantity_before: float,
            quantity_after: float,
            transaction_type: TransactionType,
            reference_type: Optional[str] = None,
            reference_id: Optional[int] = None,
            notes: Optional[str] = None
    ) -> InventoryTransaction:
        """
        Create a new inventory transaction.

        Args:
            inventory_id: ID of the inventory item
            quantity_before: Quantity before the transaction
            quantity_after: Quantity after the transaction
            transaction_type: Type of transaction
            reference_type: Optional reference document type
            reference_id: Optional reference document ID
            notes: Optional notes about the transaction

        Returns:
            Created inventory transaction
        """
        try:
            # Calculate quantity changed
            quantity_changed = quantity_after - quantity_before

            # Create transaction
            transaction_data = {
                'inventory_id': inventory_id,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after,
                'quantity_changed': quantity_changed,
                'transaction_type': transaction_type,
                'reference_type': reference_type,
                'reference_id': reference_id,
                'notes': notes,
                'created_at': datetime.now()
            }

            transaction = InventoryTransaction(**transaction_data)
            self.session.add(transaction)
            self.session.commit()

            self._logger.info(f"Created transaction for inventory {inventory_id}, change: {quantity_changed}")
            return transaction

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error creating transaction: {e}")
            raise DatabaseError(f"Error creating transaction: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error creating transaction: {e}")
            raise

    def get_material_usage(
            self,
            start_date: datetime,
            end_date: datetime,
            item_type: str = 'material'
    ) -> Dict[int, float]:
        """
        Get material usage statistics for a date range.

        Args:
            start_date: Start date for the analysis
            end_date: End date for the analysis
            item_type: Type of items to analyze (default: 'material')

        Returns:
            Dictionary mapping inventory_id to total usage (negative quantity_changed)
        """
        try:
            conditions = [
                between(InventoryTransaction.created_at, start_date, end_date),
                InventoryTransaction.quantity_changed < 0,  # Only consumption/usage
                InventoryTransaction.transaction_type == TransactionType.USAGE
            ]

            stmt = (
                select(
                    InventoryTransaction.inventory_id,
                    func.sum(InventoryTransaction.quantity_changed * -1).label('total_usage')
                )
                .join(InventoryTransaction.inventory)
                .where(and_(*conditions))
                .where(InventoryTransaction.inventory.item_type == item_type)
                .group_by(InventoryTransaction.inventory_id)
            )

            result = self.session.execute(stmt).all()

            # Convert to dictionary
            usage_dict = {row[0]: row[1] for row in result}

            self._logger.info(f"Retrieved usage statistics for {len(usage_dict)} items")
            return usage_dict

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving material usage: {e}")
            raise DatabaseError(f"Error retrieving material usage: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving material usage: {e}")
            raise

    def get_daily_transaction_counts(
            self,
            days: int = 30,
            transaction_type: Optional[TransactionType] = None
    ) -> Dict[str, int]:
        """
        Get daily transaction counts for historical analysis.

        Args:
            days: Number of days to analyze
            transaction_type: Optional transaction type filter

        Returns:
            Dictionary mapping dates (as strings) to transaction counts
        """
        try:
            start_date = datetime.now() - timedelta(days=days)

            # Build conditions
            conditions = [InventoryTransaction.created_at >= start_date]
            if transaction_type:
                conditions.append(InventoryTransaction.transaction_type == transaction_type)

            # Use SQLAlchemy func to extract date
            stmt = (
                select(
                    func.date(InventoryTransaction.created_at).label('date'),
                    func.count().label('count')
                )
                .where(and_(*conditions))
                .group_by(func.date(InventoryTransaction.created_at))
                .order_by(func.date(InventoryTransaction.created_at))
            )

            result = self.session.execute(stmt).all()

            # Convert to dictionary
            date_counts = {str(row[0]): row[1] for row in result}

            self._logger.info(f"Retrieved daily transaction counts for {len(date_counts)} days")
            return date_counts

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving daily transaction counts: {e}")
            raise DatabaseError(f"Error retrieving daily transaction counts: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving daily transaction counts: {e}")
            raise

    def get_transactions_with_inventory(
            self,
            limit: int = 50,
            offset: int = 0
    ) -> List[InventoryTransaction]:
        """
        Get transactions with inventory data eagerly loaded.

        Args:
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            List of transactions with inventory data
        """
        try:
            stmt = (
                select(InventoryTransaction)
                .options(selectinload(InventoryTransaction.inventory))
                .order_by(desc(InventoryTransaction.created_at))
                .limit(limit)
                .offset(offset)
            )

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving transactions with inventory: {e}")
            raise DatabaseError(f"Error retrieving transactions with inventory: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving transactions with inventory: {e}")
            raise

    def get_adjustment_transactions(
            self,
            adjustment_type: Optional[InventoryAdjustmentType] = None,
            days: int = 30
    ) -> List[InventoryTransaction]:
        """
        Get adjustment transactions with optional filtering.

        Args:
            adjustment_type: Optional specific adjustment type to filter by
            days: Number of days to look back

        Returns:
            List of adjustment transactions
        """
        try:
            start_date = datetime.now() - timedelta(days=days)

            # Build conditions
            conditions = [
                InventoryTransaction.created_at >= start_date,
                InventoryTransaction.transaction_type == TransactionType.ADJUSTMENT
            ]

            # If adjustment type is specified, filter notes
            if adjustment_type:
                conditions.append(
                    InventoryTransaction.notes.ilike(f"%Type: {adjustment_type.name}%")
                )

            stmt = (
                select(InventoryTransaction)
                .where(and_(*conditions))
                .order_by(desc(InventoryTransaction.created_at))
            )

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving adjustment transactions: {e}")
            raise DatabaseError(f"Error retrieving adjustment transactions: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving adjustment transactions: {e}")
            raise

    def get_transaction_statistics(
            self,
            days: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistical summary of transactions.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with transaction statistics
        """
        try:
            start_date = datetime.now() - timedelta(days=days)

            # Get total count
            count_stmt = (
                select(func.count())
                .select_from(InventoryTransaction)
                .where(InventoryTransaction.created_at >= start_date)
            )
            total_count = self.session.execute(count_stmt).scalar() or 0

            # Get count by transaction type
            type_counts_stmt = (
                select(
                    InventoryTransaction.transaction_type,
                    func.count().label('count')
                )
                .where(InventoryTransaction.created_at >= start_date)
                .group_by(InventoryTransaction.transaction_type)
            )
            type_results = self.session.execute(type_counts_stmt).all()
            type_counts = {str(row[0].name): row[1] for row in type_results}

            # Get positive and negative quantity changes
            sum_stmt = (
                select(
                    func.sum(
                        func.case(
                            (InventoryTransaction.quantity_changed > 0, InventoryTransaction.quantity_changed),
                            else_=0
                        )
                    ).label('positive_change'),
                    func.sum(
                        func.case(
                            (InventoryTransaction.quantity_changed < 0, InventoryTransaction.quantity_changed),
                            else_=0
                        )
                    ).label('negative_change')
                )
                .where(InventoryTransaction.created_at >= start_date)
            )
            sums = self.session.execute(sum_stmt).first()

            # Compile statistics
            stats = {
                'total_count': total_count,
                'by_type': type_counts,
                'positive_change': float(sums[0] or 0),
                'negative_change': float(sums[1] or 0),
                'days_analyzed': days
            }

            self._logger.info(f"Retrieved transaction statistics for the past {days} days")
            return stats

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving transaction statistics: {e}")
            raise DatabaseError(f"Error retrieving transaction statistics: {e}")
        except Exception as e:
            self._logger.error(f"Error retrieving transaction statistics: {e}")
            raise