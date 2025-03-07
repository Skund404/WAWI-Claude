# database/repositories/leather_inventory_repository.py
"""Repository for managing leather inventory records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.enums import InventoryStatus
from database.models.leather_inventory import LeatherInventory
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class LeatherInventoryRepository(BaseRepository[LeatherInventory]):
    """Repository for leather inventory management operations."""

    def __init__(self, session: Session):
        """Initialize the LeatherInventory Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, LeatherInventory)
        self.logger = logging.getLogger(__name__)

    def get_by_leather_id(self, leather_id: int) -> List[LeatherInventory]:
        """Retrieve inventory entries for a specific leather.

        Args:
            leather_id: ID of the leather to search for

        Returns:
            List of leather inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(LeatherInventory).filter(
                LeatherInventory.leather_id == leather_id
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting leather inventory by leather_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving leather inventory: {str(e)}")

    def get_active_inventory(self) -> List[LeatherInventory]:
        """Retrieve all active leather inventory entries.

        Returns:
            List of active leather inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(LeatherInventory).filter(
                LeatherInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(LeatherInventory.leather))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting active leather inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving active leather inventory: {str(e)}")

    def get_by_status(self, status: InventoryStatus) -> List[LeatherInventory]:
        """Retrieve leather inventory entries by status.

        Args:
            status: Inventory status to filter by

        Returns:
            List of leather inventory entries with the specified status

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(LeatherInventory).filter(
                LeatherInventory.status == status
            ).options(joinedload(LeatherInventory.leather))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting leather inventory by status: {str(e)}")
            raise DatabaseError(f"Database error retrieving leather inventory by status: {str(e)}")

    def get_by_storage_location(self, location: str) -> List[LeatherInventory]:
        """Retrieve leather inventory entries by storage location.

        Args:
            location: Storage location to filter by

        Returns:
            List of leather inventory entries at the specified location

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(LeatherInventory).filter(
                LeatherInventory.storage_location.ilike(f"%{location}%")
            ).options(joinedload(LeatherInventory.leather))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting leather inventory by location: {str(e)}")
            raise DatabaseError(f"Database error retrieving leather inventory by location: {str(e)}")

    def get_low_stock(self, threshold: float = 10.0) -> List[LeatherInventory]:
        """Retrieve leather inventory entries with quantity below threshold.

        Args:
            threshold: Quantity threshold to consider low stock

        Returns:
            List of leather inventory entries with low stock

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(LeatherInventory).filter(
                LeatherInventory.quantity <= threshold,
                LeatherInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(LeatherInventory.leather))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting low stock leather inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving low stock leather inventory: {str(e)}")

    def update_quantity(self, inventory_id: int, new_quantity: float) -> LeatherInventory:
        """Update the quantity of a leather inventory entry.

        Args:
            inventory_id: ID of the inventory entry to update
            new_quantity: New quantity value

        Returns:
            Updated leather inventory entry

        Raises:
            ModelNotFoundError: If the inventory entry is not found
            DatabaseError: If a database error occurs
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Leather inventory with ID {inventory_id} not found")

            inventory.quantity = new_quantity

            # Update status based on quantity
            if new_quantity <= 0:
                inventory.status = InventoryStatus.OUT_OF_STOCK
            elif new_quantity <= 10:
                inventory.status = InventoryStatus.LOW_STOCK
            else:
                inventory.status = InventoryStatus.IN_STOCK

            self.session.commit()
            return inventory
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating leather inventory quantity: {str(e)}")
            raise DatabaseError(f"Database error updating leather inventory quantity: {str(e)}")

    def get_total_quantity_by_leather_id(self, leather_id: int) -> float:
        """Get the total quantity of a leather across all inventory entries.

        Args:
            leather_id: ID of the leather

        Returns:
            Total quantity available

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(func.sum(LeatherInventory.quantity)).filter(
                LeatherInventory.leather_id == leather_id,
                LeatherInventory.status != InventoryStatus.DISCONTINUED
            ).scalar()
            return float(result) if result is not None else 0.0
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total leather quantity: {str(e)}")
            raise DatabaseError(f"Database error calculating total leather quantity: {str(e)}")