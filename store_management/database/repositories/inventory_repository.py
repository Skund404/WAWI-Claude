# Path: database/repositories/inventory_repository.py
"""
Inventory Repository for managing inventory-related database operations.

Provides CRUD and search functionality for inventory items.
"""

import logging
from typing import Any, Dict, List, Optional

from database.repositories.base_repository import BaseRepository
from database.models.inventory import Inventory
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc


class InventoryRepository(BaseRepository):
    """
    Repository for managing inventory items in the database.

    Provides methods for creating, reading, updating, and deleting
    inventory items with flexible search capabilities.
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
            filter_criteria (Optional[Dict[str, Any]], optional): Filtering parameters
            sort_by (Optional[str], optional): Field to sort by
            limit (Optional[int], optional): Maximum number of results
            offset (Optional[int], optional): Number of items to skip

        Returns:
            List[Inventory]: List of matching inventory items
        """
        try:
            # Start with base query
            query = self._session.query(Inventory)

            # Apply filters
            if filter_criteria:
                for key, value in filter_criteria.items():
                    # Handle special filtering cases
                    if '__' in key:
                        field, operator = key.split('__')
                        column = getattr(Inventory, field)

                        if operator == 'lt':
                            query = query.filter(column < value)
                        elif operator == 'gt':
                            query = query.filter(column > value)
                        elif operator == 'lte':
                            query = query.filter(column <= value)
                        elif operator == 'gte':
                            query = query.filter(column >= value)
                        elif operator == 'in':
                            query = query.filter(column.in_(value))
                    else:
                        # Exact match
                        query = query.filter(getattr(Inventory, key) == value)

            # Apply sorting
            if sort_by:
                # Check if sort is descending
                if sort_by.startswith('-'):
                    sort_field = sort_by[1:]
                    query = query.order_by(desc(getattr(Inventory, sort_field)))
                else:
                    query = query.order_by(getattr(Inventory, sort_by))

            # Apply pagination
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            # Execute query and return results
            results = query.all()

            self._logger.info(f"Search returned {len(results)} inventory items")
            return results

        except Exception as e:
            self._logger.error(f"Error searching inventory items: {e}")
            raise

    def get_low_stock_items(
            self,
            threshold: float = 10.0,
            material_type: Optional[str] = None
    ) -> List[Inventory]:
        """
        Retrieve inventory items with stock below a specified threshold.

        Args:
            threshold (float, optional): Minimum stock level. Defaults to 10.0.
            material_type (Optional[str], optional): Specific material type to filter

        Returns:
            List[Inventory]: List of low stock inventory items
        """
        try:
            # Start with base query for low stock items
            query = self._session.query(Inventory).filter(Inventory.quantity < threshold)

            # Optional material type filter
            if material_type:
                query = query.filter(Inventory.material_type == material_type)

            # Execute query
            low_stock_items = query.all()

            self._logger.info(f"Found {len(low_stock_items)} low stock items")
            return low_stock_items

        except Exception as e:
            self._logger.error(f"Error retrieving low stock items: {e}")
            raise

    def adjust_stock(
            self,
            item_id: str,
            quantity_change: float,
            reason: Optional[str] = None
    ) -> Inventory:
        """
        Adjust the stock of an inventory item.

        Args:
            item_id (str): Unique identifier of the inventory item
            quantity_change (float): Amount to add or subtract from current stock
            reason (Optional[str], optional): Reason for stock adjustment

        Returns:
            Inventory: Updated inventory item
        """
        try:
            # Retrieve the current item
            item = self.get_by_id(item_id)

            if not item:
                raise ValueError(f"Inventory item {item_id} not found")

            # Calculate new quantity
            current_quantity = item.quantity
            new_quantity = current_quantity + quantity_change

            # Update the item
            item.quantity = new_quantity
            item.last_adjusted_at = func.now()

            # Add optional tracking for adjustment reason
            if reason:
                item.last_adjustment_reason = reason

            # Commit changes
            self._session.commit()

            self._logger.info(f"Adjusted stock for item {item_id}: {quantity_change}")
            return item

        except Exception as e:
            # Rollback in case of error
            self._session.rollback()
            self._logger.error(f"Error adjusting stock for item {item_id}: {e}")
            raise

    def get_total_inventory_value(self) -> float:
        """
        Calculate the total value of all inventory items.

        Returns:
            float: Total inventory value
        """
        try:
            # Calculate total value using SQLAlchemy func
            total_value = self._session.query(
                func.sum(Inventory.quantity * Inventory.unit_price)
            ).scalar() or 0.0

            self._logger.info(f"Total inventory value calculated: {total_value}")
            return total_value

        except Exception as e:
            self._logger.error(f"Error calculating total inventory value: {e}")
            raise

    def get_by_material_type(self, material_type: str) -> List[Inventory]:
        """
        Retrieve inventory items of a specific material type.

        Args:
            material_type (str): Type of material to filter by

        Returns:
            List[Inventory]: List of inventory items of the specified type
        """
        try:
            # Query items by material type
            items = self._session.query(Inventory).filter(
                Inventory.material_type == material_type
            ).all()

            self._logger.info(f"Found {len(items)} items of type {material_type}")
            return items

        except Exception as e:
            self._logger.error(f"Error retrieving items of type {material_type}: {e}")
            raise

    def create(self, **kwargs) -> Inventory:
        """
        Create a new inventory item with additional validation.

        Args:
            **kwargs: Keyword arguments for creating the inventory item

        Returns:
            Inventory: Created inventory item
        """
        try:
            # Validate required fields
            required_fields = ['material_type', 'quantity', 'unit_of_measurement']
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure quantity is non-negative
            if kwargs.get('quantity', 0) < 0:
                raise ValueError("Quantity cannot be negative")

            # Create the item
            new_item = Inventory(**kwargs)

            # Add to session and commit
            self._session.add(new_item)
            self._session.commit()

            self._logger.info(f"Created new inventory item for {kwargs.get('material_type')}")
            return new_item

        except Exception as e:
            # Rollback in case of error
            self._session.rollback()
            self._logger.error(f"Error creating inventory item: {e}")
            raise