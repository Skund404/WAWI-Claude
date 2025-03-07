# database/repositories/tool_inventory_repository.py
"""Repository for managing tool inventory records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.enums import InventoryStatus, ToolCategory
from database.models.tool_inventory import ToolInventory
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class ToolInventoryRepository(BaseRepository[ToolInventory]):
    """Repository for tool inventory management operations."""

    def __init__(self, session: Session):
        """Initialize the ToolInventory Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ToolInventory)
        self.logger = logging.getLogger(__name__)

    def get_by_tool_id(self, tool_id: int) -> List[ToolInventory]:
        """Retrieve inventory entries for a specific tool.

        Args:
            tool_id: ID of the tool to search for

        Returns:
            List of tool inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(ToolInventory).filter(
                ToolInventory.tool_id == tool_id
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting tool inventory by tool_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving tool inventory: {str(e)}")

    def get_active_inventory(self) -> List[ToolInventory]:
        """Retrieve all active tool inventory entries.

        Returns:
            List of active tool inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(ToolInventory).filter(
                ToolInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(ToolInventory.tool))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting active tool inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving active tool inventory: {str(e)}")

    def get_by_status(self, status: InventoryStatus) -> List[ToolInventory]:
        """Retrieve tool inventory entries by status.

        Args:
            status: Inventory status to filter by

        Returns:
            List of tool inventory entries with the specified status

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(ToolInventory).filter(
                ToolInventory.status == status
            ).options(joinedload(ToolInventory.tool))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting tool inventory by status: {str(e)}")
            raise DatabaseError(f"Database error retrieving tool inventory by status: {str(e)}")

    def get_by_tool_category(self, category: ToolCategory) -> List[ToolInventory]:
        """Retrieve tool inventory entries by tool category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tool inventory entries with the specified tool category

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(ToolInventory).join(
                ToolInventory.tool
            ).filter(
                ToolInventory.tool.has(category=category)
            ).options(joinedload(ToolInventory.tool))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting tool inventory by tool category: {str(e)}")
            raise DatabaseError(f"Database error retrieving tool inventory by tool category: {str(e)}")

    def get_by_storage_location(self, location: str) -> List[ToolInventory]:
        """Retrieve tool inventory entries by storage location.

        Args:
            location: Storage location to filter by

        Returns:
            List of tool inventory entries at the specified location

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(ToolInventory).filter(
                ToolInventory.storage_location.ilike(f"%{location}%")
            ).options(joinedload(ToolInventory.tool))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting tool inventory by location: {str(e)}")
            raise DatabaseError(f"Database error retrieving tool inventory by location: {str(e)}")

    def get_low_stock(self, threshold: int = 2) -> List[ToolInventory]:
        """Retrieve tool inventory entries with quantity below threshold.

        Args:
            threshold: Quantity threshold to consider low stock

        Returns:
            List of tool inventory entries with low stock

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(ToolInventory).filter(
                ToolInventory.quantity <= threshold,
                ToolInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(ToolInventory.tool))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting low stock tool inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving low stock tool inventory: {str(e)}")

    def update_quantity(self, inventory_id: int, new_quantity: int) -> ToolInventory:
        """Update the quantity of a tool inventory entry.

        Args:
            inventory_id: ID of the inventory entry to update
            new_quantity: New quantity value

        Returns:
            Updated tool inventory entry

        Raises:
            ModelNotFoundError: If the inventory entry is not found
            DatabaseError: If a database error occurs
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Tool inventory with ID {inventory_id} not found")

            inventory.quantity = new_quantity

            # Update status based on quantity
            if new_quantity <= 0:
                inventory.status = InventoryStatus.OUT_OF_STOCK
            elif new_quantity <= 2:
                inventory.status = InventoryStatus.LOW_STOCK
            else:
                inventory.status = InventoryStatus.IN_STOCK

            self.session.commit()
            return inventory
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating tool inventory quantity: {str(e)}")
            raise DatabaseError(f"Database error updating tool inventory quantity: {str(e)}")

    def get_total_quantity_by_tool_id(self, tool_id: int) -> int:
        """Get the total quantity of a tool across all inventory entries.

        Args:
            tool_id: ID of the tool

        Returns:
            Total quantity available

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(func.sum(ToolInventory.quantity)).filter(
                ToolInventory.tool_id == tool_id,
                ToolInventory.status != InventoryStatus.DISCONTINUED
            ).scalar()
            return int(result) if result is not None else 0
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total tool quantity: {str(e)}")
            raise DatabaseError(f"Database error calculating total tool quantity: {str(e)}")