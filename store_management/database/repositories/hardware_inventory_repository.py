# database/repositories/hardware_inventory_repository.py
"""Repository for managing hardware inventory records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.enums import InventoryStatus, HardwareType
from database.models.hardware_inventory import HardwareInventory
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class HardwareInventoryRepository(BaseRepository[HardwareInventory]):
    """Repository for hardware inventory management operations."""

    def __init__(self, session: Session):
        """Initialize the HardwareInventory Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, HardwareInventory)
        self.logger = logging.getLogger(__name__)

    def get_by_hardware_id(self, hardware_id: int) -> List[HardwareInventory]:
        """Retrieve inventory entries for a specific hardware.

        Args:
            hardware_id: ID of the hardware to search for

        Returns:
            List of hardware inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(HardwareInventory).filter(
                HardwareInventory.hardware_id == hardware_id
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware inventory by hardware_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving hardware inventory: {str(e)}")

    def get_active_inventory(self) -> List[HardwareInventory]:
        """Retrieve all active hardware inventory entries.

        Returns:
            List of active hardware inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(HardwareInventory).filter(
                HardwareInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(HardwareInventory.hardware))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting active hardware inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving active hardware inventory: {str(e)}")

    def get_by_status(self, status: InventoryStatus) -> List[HardwareInventory]:
        """Retrieve hardware inventory entries by status.

        Args:
            status: Inventory status to filter by

        Returns:
            List of hardware inventory entries with the specified status

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(HardwareInventory).filter(
                HardwareInventory.status == status
            ).options(joinedload(HardwareInventory.hardware))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware inventory by status: {str(e)}")
            raise DatabaseError(f"Database error retrieving hardware inventory by status: {str(e)}")

    def get_by_hardware_type(self, hardware_type: HardwareType) -> List[HardwareInventory]:
        """Retrieve hardware inventory entries by hardware type.

        Args:
            hardware_type: Hardware type to filter by

        Returns:
            List of hardware inventory entries with the specified hardware type

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(HardwareInventory).join(
                HardwareInventory.hardware
            ).filter(
                HardwareInventory.hardware.has(type=hardware_type)
            ).options(joinedload(HardwareInventory.hardware))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware inventory by hardware type: {str(e)}")
            raise DatabaseError(f"Database error retrieving hardware inventory by hardware type: {str(e)}")

    def get_by_storage_location(self, location: str) -> List[HardwareInventory]:
        """Retrieve hardware inventory entries by storage location.

        Args:
            location: Storage location to filter by

        Returns:
            List of hardware inventory entries at the specified location

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(HardwareInventory).filter(
                HardwareInventory.storage_location.ilike(f"%{location}%")
            ).options(joinedload(HardwareInventory.hardware))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware inventory by location: {str(e)}")
            raise DatabaseError(f"Database error retrieving hardware inventory by location: {str(e)}")

    def get_low_stock(self, threshold: int = 5) -> List[HardwareInventory]:
        """Retrieve hardware inventory entries with quantity below threshold.

        Args:
            threshold: Quantity threshold to consider low stock

        Returns:
            List of hardware inventory entries with low stock

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(HardwareInventory).filter(
                HardwareInventory.quantity <= threshold,
                HardwareInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(HardwareInventory.hardware))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting low stock hardware inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving low stock hardware inventory: {str(e)}")

    def update_quantity(self, inventory_id: int, new_quantity: int) -> HardwareInventory:
        """Update the quantity of a hardware inventory entry.

        Args:
            inventory_id: ID of the inventory entry to update
            new_quantity: New quantity value

        Returns:
            Updated hardware inventory entry

        Raises:
            ModelNotFoundError: If the inventory entry is not found
            DatabaseError: If a database error occurs
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Hardware inventory with ID {inventory_id} not found")

            inventory.quantity = new_quantity

            # Update status based on quantity
            if new_quantity <= 0:
                inventory.status = InventoryStatus.OUT_OF_STOCK
            elif new_quantity <= 5:
                inventory.status = InventoryStatus.LOW_STOCK
            else:
                inventory.status = InventoryStatus.IN_STOCK

            self.session.commit()
            return inventory
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating hardware inventory quantity: {str(e)}")
            raise DatabaseError(f"Database error updating hardware inventory quantity: {str(e)}")

    def get_total_quantity_by_hardware_id(self, hardware_id: int) -> int:
        """Get the total quantity of hardware across all inventory entries.

        Args:
            hardware_id: ID of the hardware

        Returns:
            Total quantity available

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(func.sum(HardwareInventory.quantity)).filter(
                HardwareInventory.hardware_id == hardware_id,
                HardwareInventory.status != InventoryStatus.DISCONTINUED
            ).scalar()
            return int(result) if result is not None else 0
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total hardware quantity: {str(e)}")
            raise DatabaseError(f"Database error calculating total hardware quantity: {str(e)}")