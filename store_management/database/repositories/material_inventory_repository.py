# database/repositories/material_inventory_repository.py
"""Repository for managing material inventory records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.enums import InventoryStatus, MaterialType
from database.models.material_inventory import MaterialInventory
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class MaterialInventoryRepository(BaseRepository[MaterialInventory]):
    """Repository for material inventory management operations."""

    def __init__(self, session: Session):
        """Initialize the MaterialInventory Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, MaterialInventory)
        self.logger = logging.getLogger(__name__)

    def get_by_material_id(self, material_id: int) -> List[MaterialInventory]:
        """Retrieve inventory entries for a specific material.

        Args:
            material_id: ID of the material to search for

        Returns:
            List of material inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(MaterialInventory).filter(
                MaterialInventory.material_id == material_id
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting material inventory by material_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving material inventory: {str(e)}")

    def get_active_inventory(self) -> List[MaterialInventory]:
        """Retrieve all active material inventory entries.

        Returns:
            List of active material inventory entries

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(MaterialInventory).filter(
                MaterialInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(MaterialInventory.material))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting active material inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving active material inventory: {str(e)}")

    def get_by_status(self, status: InventoryStatus) -> List[MaterialInventory]:
        """Retrieve material inventory entries by status.

        Args:
            status: Inventory status to filter by

        Returns:
            List of material inventory entries with the specified status

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(MaterialInventory).filter(
                MaterialInventory.status == status
            ).options(joinedload(MaterialInventory.material))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting material inventory by status: {str(e)}")
            raise DatabaseError(f"Database error retrieving material inventory by status: {str(e)}")

    def get_by_material_type(self, material_type: MaterialType) -> List[MaterialInventory]:
        """Retrieve material inventory entries by material type.

        Args:
            material_type: Material type to filter by

        Returns:
            List of material inventory entries with the specified material type

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(MaterialInventory).join(
                MaterialInventory.material
            ).filter(
                MaterialInventory.material.has(type=material_type)
            ).options(joinedload(MaterialInventory.material))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting material inventory by material type: {str(e)}")
            raise DatabaseError(f"Database error retrieving material inventory by material type: {str(e)}")

    def get_by_storage_location(self, location: str) -> List[MaterialInventory]:
        """Retrieve material inventory entries by storage location.

        Args:
            location: Storage location to filter by

        Returns:
            List of material inventory entries at the specified location

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(MaterialInventory).filter(
                MaterialInventory.storage_location.ilike(f"%{location}%")
            ).options(joinedload(MaterialInventory.material))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting material inventory by location: {str(e)}")
            raise DatabaseError(f"Database error retrieving material inventory by location: {str(e)}")

    def get_low_stock(self, threshold: float = 10.0) -> List[MaterialInventory]:
        """Retrieve material inventory entries with quantity below threshold.

        Args:
            threshold: Quantity threshold to consider low stock

        Returns:
            List of material inventory entries with low stock

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(MaterialInventory).filter(
                MaterialInventory.quantity <= threshold,
                MaterialInventory.status != InventoryStatus.DISCONTINUED
            ).options(joinedload(MaterialInventory.material))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting low stock material inventory: {str(e)}")
            raise DatabaseError(f"Database error retrieving low stock material inventory: {str(e)}")

    def update_quantity(self, inventory_id: int, new_quantity: float) -> MaterialInventory:
        """Update the quantity of a material inventory entry.

        Args:
            inventory_id: ID of the inventory entry to update
            new_quantity: New quantity value

        Returns:
            Updated material inventory entry

        Raises:
            ModelNotFoundError: If the inventory entry is not found
            DatabaseError: If a database error occurs
        """
        try:
            inventory = self.get_by_id(inventory_id)
            if not inventory:
                raise ModelNotFoundError(f"Material inventory with ID {inventory_id} not found")

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
            self.logger.error(f"Error updating material inventory quantity: {str(e)}")
            raise DatabaseError(f"Database error updating material inventory quantity: {str(e)}")

    def get_total_quantity_by_material_id(self, material_id: int) -> float:
        """Get the total quantity of a material across all inventory entries.

        Args:
            material_id: ID of the material

        Returns:
            Total quantity available

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(func.sum(MaterialInventory.quantity)).filter(
                MaterialInventory.material_id == material_id,
                MaterialInventory.status != InventoryStatus.DISCONTINUED
            ).scalar()
            return float(result) if result is not None else 0.0
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total material quantity: {str(e)}")
            raise DatabaseError(f"Database error calculating total material quantity: {str(e)}")