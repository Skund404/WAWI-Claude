# database/repositories/hardware_repository.py
"""
Repository for hardware data access.
Provides database operations for hardware items.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import and_, or_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database.models.enums import HardwareType, HardwareFinish, MaterialType
from database.models.enums import InventoryStatus, TransactionType
from database.models.material import Hardware
from database.models.inventory import Inventory
from database.repositories.base_repository import BaseRepository
from database.models.base import ModelValidationError
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError
from services.interfaces.material_service import IMaterialService
from utils.logger import get_logger

logger = get_logger(__name__)


class HardwareRepository(BaseRepository[Hardware]):
    """
    Repository for hardware data access operations.
    Extends BaseRepository with hardware-specific functionality.
    """

    def __init__(self, session: Session, material_service: Optional[IMaterialService] = None):
        """
        Initialize the HardwareRepository with a database session.

        Args:
            session: SQLAlchemy database session
            material_service (Optional[IMaterialService], optional): Material service for additional operations
        """
        super().__init__(session, Hardware)
        self.material_service = material_service
        logger.debug("Initialized HardwareRepository")

    def get_all_hardware(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         hardware_type: Optional[HardwareType] = None,
                         finish: Optional[str] = None,
                         hardware_material: Optional[str] = None,
                         supplier_id: Optional[int] = None) -> List[Hardware]:
        """
        Get all hardware items with optional filtering.

        Args:
            include_deleted (bool): Whether to include soft-deleted hardware
            status (Optional[InventoryStatus]): Filter by inventory status
            hardware_type (Optional[HardwareType]): Filter by hardware type
            finish (Optional[str]): Filter by finish
            hardware_material (Optional[str]): Filter by hardware material
            supplier_id (Optional[int]): Filter by supplier ID

        Returns:
            List[Hardware]: List of hardware objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Join with inventory to filter by status if needed
            if status:
                query = select(Hardware).join(
                    Inventory,
                    and_(
                        Inventory.item_id == Hardware.id,
                        Inventory.item_type == 'material'
                    )
                )
            else:
                query = select(Hardware)

            # Ensure only hardware materials are returned
            query = query.where(Hardware.material_type == MaterialType.HARDWARE)

            # Build filter conditions
            conditions = []

            if not include_deleted:
                conditions.append(Hardware.is_deleted == False)

            if status:
                conditions.append(Inventory.status == status)

            if hardware_type:
                conditions.append(Hardware.hardware_type == hardware_type)

            if finish:
                conditions.append(Hardware.finish.ilike(f"%{finish}%"))

            if hardware_material:
                conditions.append(Hardware.hardware_material.ilike(f"%{hardware_material}%"))

            if supplier_id:
                conditions.append(Hardware.supplier_id == supplier_id)

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Optionally load inventory relationship
            if status:
                query = query.options(joinedload(Hardware.inventory))

            # Execute query
            result = self.session.execute(query.order_by(Hardware.name)).scalars().all()
            logger.debug(f"Retrieved {len(result)} hardware items with filters: {locals()}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware: {str(e)}")

    def search_hardware(self, search_term: str, include_deleted: bool = False) -> List[Hardware]:
        """
        Search for hardware by name, description, or other text fields.

        Args:
            search_term (str): Search term to look for
            include_deleted (bool): Whether to include soft-deleted hardware

        Returns:
            List[Hardware]: List of matching hardware objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Create base query for hardware type only
            query = select(Hardware).where(Hardware.material_type == MaterialType.HARDWARE)

            # Add search conditions
            search_conditions = [
                Hardware.name.ilike(f"%{search_term}%"),
                Hardware.description.ilike(f"%{search_term}%"),
                Hardware.finish.ilike(f"%{search_term}%"),
                Hardware.hardware_material.ilike(f"%{search_term}%"),
                Hardware.size.ilike(f"%{search_term}%")
            ]

            query = query.where(or_(*search_conditions))

            # Filter deleted if needed
            if not include_deleted:
                query = query.where(Hardware.is_deleted == False)

            # Execute query
            result = self.session.execute(query.order_by(Hardware.name)).scalars().all()
            logger.debug(f"Search for '{search_term}' returned {len(result)} hardware items")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error searching hardware: {str(e)}")
            raise RepositoryError(f"Failed to search hardware: {str(e)}")

    def get_hardware_with_inventory(self, hardware_id: int) -> Optional[Hardware]:
        """
        Get a hardware item by ID with related inventory information.

        Args:
            hardware_id (int): ID of the hardware

        Returns:
            Optional[Hardware]: Hardware object with loaded inventory or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.id == hardware_id,
                    Hardware.material_type == MaterialType.HARDWARE
                )
            ).options(
                joinedload(Hardware.inventory)
            )

            # Changed from .first() to .scalar_one_or_none() for SQLAlchemy 2.0
            result = self.session.execute(query).scalar_one_or_none()
            if result:
                logger.debug(f"Retrieved hardware ID {hardware_id} with inventory info")
            else:
                logger.debug(f"No hardware found with ID {hardware_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware with inventory: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware with inventory: {str(e)}")

    def get_hardware_with_supplier(self, hardware_id: int) -> Optional[Hardware]:
        """
        Get a hardware item by ID with supplier information.

        Args:
            hardware_id (int): ID of the hardware

        Returns:
            Optional[Hardware]: Hardware object with loaded supplier or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.id == hardware_id,
                    Hardware.material_type == MaterialType.HARDWARE
                )
            ).options(
                joinedload(Hardware.supplier)
            )

            # Changed from .first() to .scalar_one_or_none() for SQLAlchemy 2.0
            result = self.session.execute(query).scalar_one_or_none()
            if result:
                logger.debug(f"Retrieved hardware ID {hardware_id} with supplier info")
            else:
                logger.debug(f"No hardware found with ID {hardware_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware with supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware with supplier: {str(e)}")

    def get_hardware_by_status(self, status: InventoryStatus) -> List[Hardware]:
        """
        Get hardware filtered by inventory status.

        Args:
            status (InventoryStatus): Status to filter by

        Returns:
            List[Hardware]: List of hardware objects with the specified status

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).join(
                Inventory,
                and_(
                    Inventory.item_id == Hardware.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Hardware.material_type == MaterialType.HARDWARE,
                    Inventory.status == status,
                    Hardware.is_deleted == False
                )
            ).options(
                joinedload(Hardware.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} hardware items with status {status.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware by status: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware by status: {str(e)}")

    def get_hardware_inventory_value(self) -> Dict[str, Any]:
        """
        Calculate the total inventory value of all hardware items.

        Returns:
            Dict[str, Any]: Dictionary with total value and breakdowns by type

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).join(
                Inventory,
                and_(
                    Inventory.item_id == Hardware.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Hardware.material_type == MaterialType.HARDWARE,
                    Hardware.is_deleted == False
                )
            ).options(
                joinedload(Hardware.inventory)
            )

            hardware_items = self.session.execute(query).scalars().all()

            # Calculate totals
            total_value = 0.0
            by_type = {}
            by_material = {}

            for hardware in hardware_items:
                if hardware.inventory and hardware.inventory.unit_cost is not None:
                    # Calculate value based on inventory
                    value = hardware.inventory.calculate_value()
                    total_value += value

                    # Group by type
                    type_name = hardware.hardware_type.name if hardware.hardware_type else "Unknown"
                    by_type[type_name] = by_type.get(type_name, 0.0) + value

                    # Group by material
                    material_name = hardware.hardware_material or "Unknown"
                    by_material[material_name] = by_material.get(material_name, 0.0) + value

            result = {
                "total_value": total_value,
                "by_hardware_type": by_type,
                "by_material": by_material
            }

            logger.debug(f"Calculated hardware inventory value: {total_value:.2f}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error calculating hardware inventory value: {str(e)}")
            raise RepositoryError(f"Failed to calculate hardware inventory value: {str(e)}")

    def update_inventory_quantity(self, hardware_id: int, quantity_change: float,
                                  transaction_type: TransactionType,
                                  reference_type: Optional[str] = None,
                                  reference_id: Optional[int] = None,
                                  notes: Optional[str] = None) -> Inventory:
        """
        Update the inventory quantity for a hardware item.

        Args:
            hardware_id (int): ID of the hardware
            quantity_change (float): Quantity to add (positive) or remove (negative)
            transaction_type (TransactionType): Type of transaction
            reference_type (Optional[str]): Type of reference document
            reference_id (Optional[int]): ID of the reference document
            notes (Optional[str]): Optional notes about the transaction

        Returns:
            Inventory: The updated inventory record

        Raises:
            ModelNotFoundError: If the hardware or inventory does not exist
            ModelValidationError: If quantity would go negative
            RepositoryError: If a database error occurs
        """
        try:
            # Get the hardware with inventory
            hardware = self.get_hardware_with_inventory(hardware_id)
            if not hardware:
                logger.error(f"Cannot update inventory: Hardware ID {hardware_id} not found")
                raise ModelNotFoundError(f"Hardware with ID {hardware_id} not found")

            # Check if inventory exists
            if not hardware.inventory:
                logger.error(f"No inventory record exists for Hardware ID {hardware_id}")
                raise ModelNotFoundError(f"No inventory record exists for Hardware ID {hardware_id}")

            # Update the inventory quantity
            try:
                hardware.inventory.update_quantity(
                    change=quantity_change,
                    transaction_type=transaction_type,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    notes=notes
                )
            except ModelValidationError as e:
                raise ModelValidationError(str(e))

            self.session.commit()

            logger.info(f"Updated inventory for Hardware ID {hardware_id}. "
                        f"Quantity change: {quantity_change}, New quantity: {hardware.inventory.quantity}")

            return hardware.inventory

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except ModelValidationError:
            # Re-raise to be handled at the service level
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating hardware inventory: {str(e)}")
            raise RepositoryError(f"Failed to update hardware inventory: {str(e)}")

    def get_hardware_inventory_history(self, hardware_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for a specific hardware's inventory.

        Args:
            hardware_id (int): ID of the hardware
            limit (Optional[int]): Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of transaction records

        Raises:
            ModelNotFoundError: If the hardware or inventory does not exist
            RepositoryError: If a database error occurs
        """
        try:
            # Get the hardware with inventory
            hardware = self.get_hardware_with_inventory(hardware_id)
            if not hardware:
                logger.error(f"Cannot get history: Hardware ID {hardware_id} not found")
                raise ModelNotFoundError(f"Hardware with ID {hardware_id} not found")

            # Check if inventory exists
            if not hardware.inventory:
                logger.error(f"No inventory record exists for Hardware ID {hardware_id}")
                raise ModelNotFoundError(f"No inventory record exists for Hardware ID {hardware_id}")

            # Get transaction history from the inventory record
            history = hardware.inventory.transaction_history or []

            # Sort by date (most recent first)
            history = sorted(history,
                             key=lambda x: x.get('date', ''),
                             reverse=True)

            # Apply limit if specified
            if limit is not None and limit > 0:
                history = history[:limit]

            logger.debug(f"Retrieved {len(history)} transaction records for Hardware ID {hardware_id}")
            return history

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware inventory history: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware inventory history: {str(e)}")

    def get_low_stock_hardware(self, threshold: Optional[float] = None) -> List[Hardware]:
        """
        Get all hardware with low stock.

        Args:
            threshold (Optional[float]): Override the defined min_stock_level

        Returns:
            List[Hardware]: List of hardware objects with low stock

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).join(
                Inventory,
                and_(
                    Inventory.item_id == Hardware.id,
                    Inventory.item_type == 'material'
                )
            )

            conditions = [
                Hardware.material_type == MaterialType.HARDWARE,
                Hardware.is_deleted == False
            ]

            if threshold is not None:
                # Use provided threshold
                conditions.append(
                    and_(
                        Inventory.quantity <= threshold,
                        Inventory.quantity > 0
                    )
                )
            else:
                # Use each item's defined min_stock_level or fallback to LOW_STOCK status
                conditions.append(
                    or_(
                        and_(
                            Inventory.min_stock_level.is_not(None),
                            Inventory.quantity <= Inventory.min_stock_level,
                            Inventory.quantity > 0
                        ),
                        Inventory.status == InventoryStatus.LOW_STOCK
                    )
                )

            query = query.where(and_(*conditions)).options(
                joinedload(Hardware.inventory)
            ).order_by(Inventory.quantity)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} hardware items with low stock")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving low stock hardware: {str(e)}")
            raise RepositoryError(f"Failed to retrieve low stock hardware: {str(e)}")

    def get_out_of_stock_hardware(self) -> List[Hardware]:
        """
        Get all hardware that is out of stock.

        Returns:
            List[Hardware]: List of hardware objects with zero quantity

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).join(
                Inventory,
                and_(
                    Inventory.item_id == Hardware.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Hardware.material_type == MaterialType.HARDWARE,
                    or_(
                        Inventory.status == InventoryStatus.OUT_OF_STOCK,
                        Inventory.quantity == 0
                    ),
                    Hardware.is_deleted == False
                )
            ).options(
                joinedload(Hardware.inventory)
            ).order_by(Hardware.name)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} out of stock hardware items")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving out of stock hardware: {str(e)}")
            raise RepositoryError(f"Failed to retrieve out of stock hardware: {str(e)}")

    def get_hardware_by_type(self, hardware_type: HardwareType) -> List[Hardware]:
        """
        Get hardware items of a specific type.

        Args:
            hardware_type (HardwareType): Type of hardware to filter by

        Returns:
            List[Hardware]: List of hardware objects matching the type

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.material_type == MaterialType.HARDWARE,
                    Hardware.hardware_type == hardware_type,
                    Hardware.is_deleted == False
                )
            ).options(joinedload(Hardware.inventory))

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} hardware items of type {hardware_type.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware by type: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware by type: {str(e)}")

    def get_hardware_by_supplier(self, supplier_id: int) -> List[Hardware]:
        """
        Get hardware items from a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Hardware]: List of hardware objects from the supplier

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.material_type == MaterialType.HARDWARE,
                    Hardware.supplier_id == supplier_id,
                    Hardware.is_deleted == False
                )
            ).options(
                joinedload(Hardware.inventory),
                joinedload(Hardware.supplier)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} hardware items from supplier ID {supplier_id}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware by supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware by supplier: {str(e)}")

    def batch_update(self, updates: List[Dict[str, Any]]) -> List[Hardware]:
        """
        Update multiple hardware records in a batch.

        Args:
            updates (List[Dict[str, Any]]): List of dictionaries with 'id' and fields to update

        Returns:
            List[Hardware]: List of updated hardware objects

        Raises:
            ModelNotFoundError: If any hardware ID is not found
            ModelValidationError: If any of the updates fail validation
            RepositoryError: If a database error occurs
        """
        try:
            updated_hardware = []

            for update_data in updates:
                hardware_id = update_data.pop('id', None)
                inventory_data = update_data.pop('inventory', None)

                if not hardware_id:
                    logger.error("Missing hardware ID in batch update")
                    raise ModelValidationError("Hardware ID is required for batch update")

                hardware = self.get_by_id(hardware_id)
                if not hardware:
                    logger.error(f"Hardware ID {hardware_id} not found in batch update")
                    raise ModelNotFoundError(f"Hardware with ID {hardware_id} not found")

                # Ensure this is a hardware type
                if hardware.material_type != MaterialType.HARDWARE:
                    logger.error(f"Material ID {hardware_id} is not a hardware type")
                    raise ModelValidationError(f"Material ID {hardware_id} is not a hardware type")

                # Update hardware fields
                for key, value in update_data.items():
                    setattr(hardware, key, value)

                # Update inventory if provided
                if inventory_data and hardware.inventory:
                    for key, value in inventory_data.items():
                        setattr(hardware.inventory, key, value)

                    # Update status based on new quantities
                    hardware.inventory._update_status()

                hardware.validate()
                updated_hardware.append(hardware)

            # Commit all updates
            self.session.commit()
            logger.info(f"Batch updated {len(updated_hardware)} hardware items")
            return updated_hardware

        except ModelValidationError:
            # Rollback and re-raise
            self.session.rollback()
            raise
        except ModelNotFoundError:
            # Rollback and re-raise
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error in batch update: {str(e)}")
            raise RepositoryError(f"Failed to batch update hardware: {str(e)}")

    def get_hardware_by_ids(self, hardware_ids: List[int]) -> List[Hardware]:
        """
        Get multiple hardware items by their IDs.

        Args:
            hardware_ids (List[int]): List of hardware IDs

        Returns:
            List[Hardware]: List of found hardware objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            if not hardware_ids:
                return []

            query = select(Hardware).where(
                and_(
                    Hardware.id.in_(hardware_ids),
                    Hardware.material_type == MaterialType.HARDWARE,
                    Hardware.is_deleted == False
                )
            ).options(
                joinedload(Hardware.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} hardware items by IDs")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hardware by IDs: {str(e)}")
            raise RepositoryError(f"Failed to retrieve hardware by IDs: {str(e)}")

    def get_hardware_stats(self) -> Dict[str, Any]:
        """
        Get statistics about hardware inventory.

        Returns:
            Dict[str, Any]: Dictionary with hardware inventory statistics

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Get all hardware with inventory
            query = select(Hardware).join(
                Inventory,
                and_(
                    Inventory.item_id == Hardware.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Hardware.material_type == MaterialType.HARDWARE,
                    Hardware.is_deleted == False
                )
            ).options(
                joinedload(Hardware.inventory)
            )

            hardware_items = self.session.execute(query).scalars().all()

            # Calculate statistics
            stats = {
                'total_count': len(hardware_items),
                'total_value': 0.0,
                'low_stock_count': 0,
                'out_of_stock_count': 0,
                'by_type': {},
                'by_material': {}
            }

            # Process each hardware item
            for hardware in hardware_items:
                # Count by type
                type_name = hardware.hardware_type.name if hardware.hardware_type else "Unknown"
                if type_name not in stats['by_type']:
                    stats['by_type'][type_name] = {'count': 0, 'value': 0.0}
                stats['by_type'][type_name]['count'] += 1

                # Count by material
                material_name = hardware.hardware_material or "Unknown"
                if material_name not in stats['by_material']:
                    stats['by_material'][material_name] = {'count': 0, 'value': 0.0}
                stats['by_material'][material_name]['count'] += 1

                # Process inventory data
                if hardware.inventory:
                    inventory = hardware.inventory
                    value = inventory.calculate_value()
                    stats['total_value'] += value

                    # Update type and material value
                    stats['by_type'][type_name]['value'] += value
                    stats['by_material'][material_name]['value'] += value

                    # Check stock status
                    if inventory.status == InventoryStatus.OUT_OF_STOCK or inventory.quantity == 0:
                        stats['out_of_stock_count'] += 1
                    elif (inventory.status == InventoryStatus.LOW_STOCK or
                          (inventory.min_stock_level is not None and inventory.quantity <= inventory.min_stock_level)):
                        stats['low_stock_count'] += 1

            logger.debug(
                f"Calculated hardware stats: {len(hardware_items)} items, total value: ${stats['total_value']:.2f}")
            return stats

        except SQLAlchemyError as e:
            logger.error(f"Database error getting hardware stats: {str(e)}")
            raise RepositoryError(f"Failed to get hardware stats: {str(e)}")