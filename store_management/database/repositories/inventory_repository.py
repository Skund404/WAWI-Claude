# Path: database/repositories/inventory_repository.py
"""
Enhanced Inventory Repository for managing inventory-related database operations.

Provides comprehensive inventory management capabilities including tracking,
movement recording, and advanced inventory analytics.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from database.repositories.base_repository import BaseRepository
from database.models.inventory import Inventory
from database.models.enums import (
    InventoryStatus, TransactionType, InventoryAdjustmentType
)
from database.exceptions import DatabaseError, ModelNotFoundError


class InventoryRepository(BaseRepository[Inventory]):
    """
    Enhanced Repository for managing inventory items in the database.

    Provides comprehensive methods for inventory management including:
    - Advanced CRUD operations
    - Movement and transaction tracking
    - Location management
    - Inventory analytics and reporting
    - Threshold-based monitoring
    """

    def __init__(self, session: Session):
        """
        Initialize the Inventory Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Inventory)
        self._logger = logging.getLogger(__name__)

    def search(
            self,
            filter_criteria: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Inventory]:
        """
        Search for inventory items with flexible filtering and pagination.

        Args:
            filter_criteria: Filtering parameters (field__operator: value)
            sort_by: Field to sort by (prefix with '-' for descending)
            limit: Maximum number of results
            offset: Number of items to skip

        Returns:
            List of matching inventory items
        """
        try:
            # Build the select statement
            stmt = select(Inventory)

            # Apply filters
            if filter_criteria:
                conditions = []
                for key, value in filter_criteria.items():
                    # Handle special filtering cases
                    if '__' in key:
                        field, operator = key.split('__')
                        column = getattr(Inventory, field)

                        if operator == 'lt':
                            conditions.append(column < value)
                        elif operator == 'gt':
                            conditions.append(column > value)
                        elif operator == 'lte':
                            conditions.append(column <= value)
                        elif operator == 'gte':
                            conditions.append(column >= value)
                        elif operator == 'in':
                            conditions.append(column.in_(value))
                        elif operator == 'contains':
                            conditions.append(column.contains(value))
                        elif operator == 'icontains':
                            conditions.append(column.ilike(f'%{value}%'))
                    else:
                        # Exact match
                        conditions.append(getattr(Inventory, key) == value)

                if conditions:
                    stmt = stmt.where(and_(*conditions))

            # Apply sorting
            if sort_by:
                # Check if sort is descending
                if sort_by.startswith('-'):
                    sort_field = sort_by[1:]
                    stmt = stmt.order_by(desc(getattr(Inventory, sort_field)))
                else:
                    stmt = stmt.order_by(getattr(Inventory, sort_by))

            # Apply pagination
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            # Execute query and return results
            results = self.session.execute(stmt).scalars().all()

            self._logger.info(f"Search returned {len(results)} inventory items")
            return list(results)

        except SQLAlchemyError as e:
            self._logger.error(f"Database error searching inventory items: {e}")
            raise DatabaseError(f"Error searching inventory: {e}")
        except Exception as e:
            self._logger.error(f"Error searching inventory items: {e}")
            raise

    def get_by_item_type(
            self,
            item_type: str,
            status: Optional[InventoryStatus] = None
    ) -> List[Inventory]:
        """
        Get inventory items of a specific type with optional status filtering.

        Args:
            item_type: Type of item ('material', 'product', 'tool')
            status: Optional inventory status filter

        Returns:
            List of inventory items matching the criteria
        """
        try:
            stmt = select(Inventory).where(Inventory.item_type == item_type)

            if status:
                stmt = stmt.where(Inventory.status == status)

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving {item_type} inventory: {e}")
            raise DatabaseError(f"Error retrieving {item_type} inventory: {e}")

    def get_items_below_threshold(
            self,
            threshold_type: str = 'reorder_point'
    ) -> List[Inventory]:
        """
        Get inventory items below specified threshold.

        Args:
            threshold_type: Type of threshold to check ('min_stock_level' or 'reorder_point')

        Returns:
            List of inventory items below threshold
        """
        try:
            if threshold_type == 'min_stock_level':
                # Items below minimum stock level
                stmt = select(Inventory).where(
                    and_(
                        Inventory.min_stock_level.is_not(None),
                        Inventory.quantity <= Inventory.min_stock_level
                    )
                )
            else:
                # Items below reorder point
                stmt = select(Inventory).where(
                    and_(
                        Inventory.reorder_point.is_not(None),
                        Inventory.quantity <= Inventory.reorder_point
                    )
                )

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving items below threshold: {e}")
            raise DatabaseError(f"Error retrieving items below threshold: {e}")

    def get_items_by_location(self, location: str) -> List[Inventory]:
        """
        Get inventory items by storage location.

        Args:
            location: Storage location to filter by

        Returns:
            List of inventory items at the specified location
        """
        try:
            stmt = select(Inventory).where(Inventory.storage_location == location)
            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving items by location: {e}")
            raise DatabaseError(f"Error retrieving items by location: {e}")

    def get_inactive_items(self, days: int = 90) -> List[Inventory]:
        """
        Get items with no movement in the specified number of days.

        Args:
            days: Number of days to consider as inactive threshold

        Returns:
            List of inactive inventory items
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = select(Inventory).where(
                or_(
                    Inventory.last_movement_date < cutoff_date,
                    and_(
                        Inventory.last_movement_date.is_(None),
                        Inventory.created_at < cutoff_date
                    )
                )
            )

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error retrieving inactive items: {e}")
            raise DatabaseError(f"Error retrieving inactive items: {e}")

    def record_movement(
            self,
            inventory_id: int,
            quantity_change: float,
            transaction_type: TransactionType,
            reference_type: Optional[str] = None,
            reference_id: Optional[int] = None,
            notes: Optional[str] = None
    ) -> Inventory:
        """
        Record a movement (quantity change) for an inventory item.

        Args:
            inventory_id: ID of the inventory item
            quantity_change: Amount to add (positive) or remove (negative)
            transaction_type: Type of transaction causing the movement
            reference_type: Optional reference document type
            reference_id: Optional reference document ID
            notes: Optional notes about the movement

        Returns:
            Updated inventory item
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Inventory item with ID {inventory_id} not found")

            # Update quantity with transaction tracking
            inventory.update_quantity(
                change=quantity_change,
                transaction_type=transaction_type,
                reference_type=reference_type,
                reference_id=reference_id,
                notes=notes
            )

            # Commit changes
            self.session.commit()

            self._logger.info(f"Recorded movement of {quantity_change} for item {inventory_id}")
            return inventory

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error recording movement: {e}")
            raise DatabaseError(f"Error recording movement: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error recording movement: {e}")
            raise

    def record_adjustment(
            self,
            inventory_id: int,
            quantity_change: float,
            adjustment_type: InventoryAdjustmentType,
            reason: str,
            authorized_by: Optional[str] = None
    ) -> Inventory:
        """
        Record a manual inventory adjustment.

        Args:
            inventory_id: ID of the inventory item
            quantity_change: Amount to adjust
            adjustment_type: Type of adjustment
            reason: Reason for the adjustment
            authorized_by: Person who authorized the adjustment

        Returns:
            Updated inventory item
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Inventory item with ID {inventory_id} not found")

            # Record adjustment
            inventory.record_adjustment(
                quantity_change=quantity_change,
                adjustment_type=adjustment_type,
                reason=reason,
                authorized_by=authorized_by
            )

            # Commit changes
            self.session.commit()

            self._logger.info(f"Recorded adjustment of {quantity_change} for item {inventory_id}")
            return inventory

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error recording adjustment: {e}")
            raise DatabaseError(f"Error recording adjustment: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error recording adjustment: {e}")
            raise

    def transfer_location(
            self,
            inventory_id: int,
            new_location: str,
            new_details: Optional[Dict[str, Any]] = None,
            notes: Optional[str] = None
    ) -> Inventory:
        """
        Transfer inventory to a new storage location.

        Args:
            inventory_id: ID of the inventory item
            new_location: New storage location
            new_details: Optional new location details
            notes: Optional notes about the transfer

        Returns:
            Updated inventory item
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Inventory item with ID {inventory_id} not found")

            # Transfer location
            inventory.transfer_location(
                new_location=new_location,
                new_details=new_details,
                notes=notes
            )

            # Commit changes
            self.session.commit()

            self._logger.info(f"Transferred item {inventory_id} to {new_location}")
            return inventory

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error transferring location: {e}")
            raise DatabaseError(f"Error transferring location: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error transferring location: {e}")
            raise

    def record_physical_count(
            self,
            inventory_id: int,
            counted_quantity: float,
            adjustment_notes: Optional[str] = None,
            counted_by: Optional[str] = None
    ) -> Inventory:
        """
        Record a physical inventory count and adjust as needed.

        Args:
            inventory_id: ID of the inventory item
            counted_quantity: Actual quantity counted
            adjustment_notes: Notes about any discrepancy
            counted_by: Person who performed the count

        Returns:
            Updated inventory item
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Inventory item with ID {inventory_id} not found")

            # Record physical count
            inventory.record_physical_count(
                counted_quantity=counted_quantity,
                adjustment_notes=adjustment_notes,
                counted_by=counted_by
            )

            # Commit changes
            self.session.commit()

            self._logger.info(f"Recorded physical count of {counted_quantity} for item {inventory_id}")
            return inventory

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error recording physical count: {e}")
            raise DatabaseError(f"Error recording physical count: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error recording physical count: {e}")
            raise

    def calculate_total_inventory_value(self) -> float:
        """
        Calculate the total value of all inventory.

        Returns:
            Total inventory value
        """
        try:
            items = self.get_all()
            total_value = sum(item.calculate_value() for item in items)

            self._logger.info(f"Calculated total inventory value: {total_value}")
            return total_value

        except SQLAlchemyError as e:
            self._logger.error(f"Database error calculating inventory value: {e}")
            raise DatabaseError(f"Error calculating inventory value: {e}")
        except Exception as e:
            self._logger.error(f"Error calculating inventory value: {e}")
            raise

    def get_transaction_history(
            self,
            inventory_id: int,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for an inventory item.

        Args:
            inventory_id: ID of the inventory item
            limit: Maximum number of transactions to return

        Returns:
            List of transaction records
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Inventory item with ID {inventory_id} not found")

            # Get transaction history from the inventory item
            if not inventory.transaction_history:
                return []

            # Return the most recent transactions up to the limit
            history = inventory.transaction_history
            if len(history) > limit:
                history = history[-limit:]

            return history

        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting transaction history: {e}")
            raise DatabaseError(f"Error getting transaction history: {e}")
        except Exception as e:
            self._logger.error(f"Error getting transaction history: {e}")
            raise

    def get_items_needing_reorder(self) -> List[Inventory]:
        """
        Get items that need to be reordered based on reorder point.

        Returns:
            List of inventory items needing reorder
        """
        try:
            items = self.get_all()
            return [item for item in items if item.needs_reorder()]

        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting items needing reorder: {e}")
            raise DatabaseError(f"Error getting items needing reorder: {e}")
        except Exception as e:
            self._logger.error(f"Error getting items needing reorder: {e}")
            raise

    def get_items_by_age(self, days: int) -> List[Inventory]:
        """
        Get inventory items older than specified number of days.

        Args:
            days: Age threshold in days

        Returns:
            List of inventory items older than threshold
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = select(Inventory).where(Inventory.created_at < cutoff_date)
            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting items by age: {e}")
            raise DatabaseError(f"Error getting items by age: {e}")
        except Exception as e:
            self._logger.error(f"Error getting items by age: {e}")
            raise

    def get_items_needing_count(self, days: int = 90) -> List[Inventory]:
        """
        Get items that haven't been counted in the specified number of days.

        Args:
            days: Number of days since last count

        Returns:
            List of inventory items needing count
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = select(Inventory).where(
                or_(
                    Inventory.last_count_date < cutoff_date,
                    Inventory.last_count_date.is_(None)
                )
            )

            return list(self.session.execute(stmt).scalars().all())

        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting items needing count: {e}")
            raise DatabaseError(f"Error getting items needing count: {e}")
        except Exception as e:
            self._logger.error(f"Error getting items needing count: {e}")
            raise

    def create_with_defaults(self, **data) -> Inventory:
        """
        Create inventory item with default values for optional fields.

        Args:
            **data: Data for the inventory item

        Returns:
            Created inventory item
        """
        try:
            # Set default values if not provided
            if 'status' not in data:
                qty = data.get('quantity', 0)
                min_level = data.get('min_stock_level')
                reorder_point = data.get('reorder_point')

                if qty <= 0:
                    data['status'] = InventoryStatus.OUT_OF_STOCK
                elif min_level is not None and qty <= min_level:
                    data['status'] = InventoryStatus.LOW_STOCK
                elif reorder_point is not None and qty <= reorder_point:
                    data['status'] = InventoryStatus.PENDING_REORDER
                else:
                    data['status'] = InventoryStatus.IN_STOCK

            if 'transaction_history' not in data:
                data['transaction_history'] = []

            if 'created_at' not in data:
                data['created_at'] = datetime.now()

            # Create the item
            return self.create(**data)

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error creating inventory item: {e}")
            raise DatabaseError(f"Error creating inventory item: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error creating inventory item: {e}")
            raise

    def get_storage_locations(self) -> List[str]:
        """
        Get all unique storage locations in use.

        Returns:
            List of storage locations
        """
        try:
            stmt = select(Inventory.storage_location).distinct()
            result = self.session.execute(stmt).scalars().all()

            # Remove None values
            return [loc for loc in result if loc]

        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting storage locations: {e}")
            raise DatabaseError(f"Error getting storage locations: {e}")
        except Exception as e:
            self._logger.error(f"Error getting storage locations: {e}")
            raise