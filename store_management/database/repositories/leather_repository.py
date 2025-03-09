# database/repositories/leather_repository.py
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select, desc

from database.models.enums import InventoryStatus, LeatherType, QualityGrade, TransactionType, MaterialType
from database.models.material import Leather
from database.models.inventory import Inventory
from database.repositories.base_repository import BaseRepository
from database.models.base import ModelValidationError
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError
from utils.logger import get_logger

logger = get_logger(__name__)


class LeatherRepository(BaseRepository[Leather]):
    """
    Repository for leather model operations.
    Provides data access methods for the leather table.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the LeatherRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Leather)
        logger.debug("Initialized LeatherRepository")

    def get_all_leathers(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         leather_type: Optional[LeatherType] = None,
                         quality: Optional[QualityGrade] = None,
                         color: Optional[str] = None,
                         thickness_min: Optional[float] = None,
                         thickness_max: Optional[float] = None,
                         area_min: Optional[float] = None) -> List[Leather]:
        """
        Get all leathers with optional filtering.

        Args:
            include_deleted (bool): Whether to include soft-deleted leathers
            status (Optional[InventoryStatus]): Filter by inventory status
            leather_type (Optional[LeatherType]): Filter by leather type
            quality (Optional[QualityGrade]): Filter by quality grade
            color (Optional[str]): Filter by color
            thickness_min (Optional[float]): Filter by minimum thickness
            thickness_max (Optional[float]): Filter by maximum thickness
            area_min (Optional[float]): Filter by minimum area in square feet

        Returns:
            List[Leather]: List of leather objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Join with inventory to filter by status if needed
            if status:
                query = select(Leather).join(
                    Inventory,
                    and_(
                        Inventory.item_id == Leather.id,
                        Inventory.item_type == 'material'
                    )
                )
            else:
                query = select(Leather)

            # Ensure only leather materials are returned
            query = query.where(Leather.material_type == MaterialType.LEATHER)

            # Build filter conditions
            conditions = []

            if not include_deleted:
                conditions.append(Leather.is_deleted == False)

            if status:
                conditions.append(Inventory.status == status)

            if leather_type:
                conditions.append(Leather.leather_type == leather_type)

            if quality:
                conditions.append(Leather.quality == quality)

            if color:
                conditions.append(Leather.color.ilike(f"%{color}%"))

            if thickness_min is not None:
                conditions.append(Leather.thickness >= thickness_min)

            if thickness_max is not None:
                conditions.append(Leather.thickness <= thickness_max)

            if area_min is not None:
                conditions.append(Leather.area >= area_min)

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Optionally load inventory relationship
            if status:
                query = query.options(joinedload(Leather.inventory))

            # Execute query
            result = self.session.execute(query.order_by(Leather.name)).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers with filters: {locals()}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leathers: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leathers: {str(e)}")

    def search_leathers(self, search_term: str, include_deleted: bool = False) -> List[Leather]:
        """
        Search for leathers by name, description, or other text fields.

        Args:
            search_term (str): Search term to look for
            include_deleted (bool): Whether to include soft-deleted leathers

        Returns:
            List[Leather]: List of matching leather objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Create base query for leather type only
            query = select(Leather).where(Leather.material_type == MaterialType.LEATHER)

            # Add search conditions
            search_conditions = [
                Leather.name.ilike(f"%{search_term}%"),
                Leather.description.ilike(f"%{search_term}%")
            ]

            query = query.where(or_(*search_conditions))

            # Filter deleted if needed
            if not include_deleted:
                query = query.where(Leather.is_deleted == False)

            # Execute query
            result = self.session.execute(query.order_by(Leather.name)).scalars().all()
            logger.debug(f"Search for '{search_term}' returned {len(result)} leathers")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error searching leathers: {str(e)}")
            raise RepositoryError(f"Failed to search leathers: {str(e)}")

    def get_leather_with_inventory(self, leather_id: int) -> Optional[Leather]:
        """
        Get a leather by ID with related inventory information.

        Args:
            leather_id (int): ID of the leather

        Returns:
            Optional[Leather]: Leather object with loaded inventory or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).where(
                and_(
                    Leather.id == leather_id,
                    Leather.material_type == MaterialType.LEATHER
                )
            ).options(
                joinedload(Leather.inventory)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved leather ID {leather_id} with inventory info")
            else:
                logger.debug(f"No leather found with ID {leather_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leather with inventory: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leather with inventory: {str(e)}")

    def get_leather_with_supplier(self, leather_id: int) -> Optional[Leather]:
        """
        Get a leather by ID with supplier information.

        Args:
            leather_id (int): ID of the leather

        Returns:
            Optional[Leather]: Leather object with loaded supplier or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).where(
                and_(
                    Leather.id == leather_id,
                    Leather.material_type == MaterialType.LEATHER
                )
            ).options(
                joinedload(Leather.supplier)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved leather ID {leather_id} with supplier info")
            else:
                logger.debug(f"No leather found with ID {leather_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leather with supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leather with supplier: {str(e)}")

    def get_leathers_by_status(self, status: InventoryStatus) -> List[Leather]:
        """
        Get leathers filtered by inventory status.

        Args:
            status (InventoryStatus): Status to filter by

        Returns:
            List[Leather]: List of leather objects with the specified status

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).join(
                Inventory,
                and_(
                    Inventory.item_id == Leather.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Leather.material_type == MaterialType.LEATHER,
                    Inventory.status == status,
                    Leather.is_deleted == False
                )
            ).options(
                joinedload(Leather.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers with status {status.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leathers by status: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leathers by status: {str(e)}")

    def get_leather_inventory_value(self) -> Dict[str, Any]:
        """
        Calculate the total inventory value of all leather items.

        Returns:
            Dict[str, Any]: Dictionary with total value and breakdowns by type and quality

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).join(
                Inventory,
                and_(
                    Inventory.item_id == Leather.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Leather.material_type == MaterialType.LEATHER,
                    Leather.is_deleted == False
                )
            ).options(
                joinedload(Leather.inventory)
            )

            leathers = self.session.execute(query).scalars().all()

            # Calculate totals
            total_value = 0.0
            by_type = {}
            by_quality = {}

            for leather in leathers:
                if leather.inventory and leather.inventory.unit_cost is not None:
                    # Calculate value based on inventory
                    value = leather.inventory.calculate_value()
                    total_value += value

                    # Group by type
                    type_name = leather.leather_type.name if leather.leather_type else "Unknown"
                    by_type[type_name] = by_type.get(type_name, 0.0) + value

                    # Group by quality
                    quality_name = leather.quality.name if leather.quality else "Unknown"
                    by_quality[quality_name] = by_quality.get(quality_name, 0.0) + value

            result = {
                "total_value": total_value,
                "by_leather_type": by_type,
                "by_quality": by_quality
            }

            logger.debug(f"Calculated leather inventory value: {total_value:.2f}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error calculating leather inventory value: {str(e)}")
            raise RepositoryError(f"Failed to calculate leather inventory value: {str(e)}")

    def update_inventory_quantity(self, leather_id: int, quantity_change: float,
                                  transaction_type: TransactionType,
                                  reference_type: Optional[str] = None,
                                  reference_id: Optional[int] = None,
                                  notes: Optional[str] = None) -> Inventory:
        """
        Update the inventory quantity for a leather item.

        Args:
            leather_id (int): ID of the leather
            quantity_change (float): Quantity to add (positive) or remove (negative)
            transaction_type (TransactionType): Type of transaction
            reference_type (Optional[str]): Type of reference document
            reference_id (Optional[int]): ID of the reference document
            notes (Optional[str]): Optional notes about the transaction

        Returns:
            Inventory: The updated inventory record

        Raises:
            ModelNotFoundError: If the leather or inventory does not exist
            ModelValidationError: If quantity would go negative
            RepositoryError: If a database error occurs
        """
        try:
            # Get the leather with inventory
            leather = self.get_leather_with_inventory(leather_id)
            if not leather:
                logger.error(f"Cannot update inventory: Leather ID {leather_id} not found")
                raise ModelNotFoundError(f"Leather with ID {leather_id} not found")

            # Check if inventory exists
            if not leather.inventory:
                logger.error(f"No inventory record exists for Leather ID {leather_id}")
                raise ModelNotFoundError(f"No inventory record exists for Leather ID {leather_id}")

            # Update the inventory quantity
            try:
                leather.inventory.update_quantity(
                    change=quantity_change,
                    transaction_type=transaction_type,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    notes=notes
                )
            except ModelValidationError as e:
                raise ModelValidationError(str(e))

            self.session.commit()

            logger.info(f"Updated inventory for Leather ID {leather_id}. "
                        f"Quantity change: {quantity_change}, New quantity: {leather.inventory.quantity}")

            return leather.inventory

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except ModelValidationError:
            # Re-raise to be handled at the service level
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating leather inventory: {str(e)}")
            raise RepositoryError(f"Failed to update leather inventory: {str(e)}")

    def get_leather_inventory_history(self, leather_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for a specific leather's inventory.

        Args:
            leather_id (int): ID of the leather
            limit (Optional[int]): Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of transaction records

        Raises:
            ModelNotFoundError: If the leather or inventory does not exist
            RepositoryError: If a database error occurs
        """
        try:
            # Get the leather with inventory
            leather = self.get_leather_with_inventory(leather_id)
            if not leather:
                logger.error(f"Cannot get history: Leather ID {leather_id} not found")
                raise ModelNotFoundError(f"Leather with ID {leather_id} not found")

            # Check if inventory exists
            if not leather.inventory:
                logger.error(f"No inventory record exists for Leather ID {leather_id}")
                raise ModelNotFoundError(f"No inventory record exists for Leather ID {leather_id}")

            # Get transaction history from the inventory record
            history = leather.inventory.transaction_history or []

            # Sort by date (most recent first)
            history = sorted(history,
                             key=lambda x: x.get('date', ''),
                             reverse=True)

            # Apply limit if specified
            if limit is not None and limit > 0:
                history = history[:limit]

            logger.debug(f"Retrieved {len(history)} transaction records for Leather ID {leather_id}")
            return history

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leather inventory history: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leather inventory history: {str(e)}")

    def get_low_stock_leathers(self, threshold: Optional[float] = None) -> List[Leather]:
        """
        Get all leathers with low stock.

        Args:
            threshold (Optional[float]): Override the defined min_stock_level

        Returns:
            List[Leather]: List of leather objects with low stock

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).join(
                Inventory,
                and_(
                    Inventory.item_id == Leather.id,
                    Inventory.item_type == 'material'
                )
            )

            conditions = [
                Leather.material_type == MaterialType.LEATHER,
                Leather.is_deleted == False
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
                joinedload(Leather.inventory)
            ).order_by(Inventory.quantity)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers with low stock")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving low stock leathers: {str(e)}")
            raise RepositoryError(f"Failed to retrieve low stock leathers: {str(e)}")

    def get_out_of_stock_leathers(self) -> List[Leather]:
        """
        Get all leathers that are out of stock.

        Returns:
            List[Leather]: List of leather objects with zero quantity

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).join(
                Inventory,
                and_(
                    Inventory.item_id == Leather.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Leather.material_type == MaterialType.LEATHER,
                    or_(
                        Inventory.status == InventoryStatus.OUT_OF_STOCK,
                        Inventory.quantity == 0
                    ),
                    Leather.is_deleted == False
                )
            ).options(
                joinedload(Leather.inventory)
            ).order_by(Leather.name)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} out of stock leathers")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving out of stock leathers: {str(e)}")
            raise RepositoryError(f"Failed to retrieve out of stock leathers: {str(e)}")

    def batch_update(self, updates: List[Dict[str, Any]]) -> List[Leather]:
        """
        Update multiple leather records in a batch.

        Args:
            updates (List[Dict[str, Any]]): List of dictionaries with 'id' and fields to update

        Returns:
            List[Leather]: List of updated leather objects

        Raises:
            ModelNotFoundError: If any leather ID is not found
            ModelValidationError: If any of the updates fail validation
            RepositoryError: If a database error occurs
        """
        try:
            updated_leathers = []

            for update_data in updates:
                leather_id = update_data.pop('id', None)
                inventory_data = update_data.pop('inventory', None)

                if not leather_id:
                    logger.error("Missing leather ID in batch update")
                    raise ModelValidationError("Leather ID is required for batch update")

                leather = self.get_by_id(leather_id)
                if not leather:
                    logger.error(f"Leather ID {leather_id} not found in batch update")
                    raise ModelNotFoundError(f"Leather with ID {leather_id} not found")

                # Ensure this is a leather type
                if leather.material_type != MaterialType.LEATHER:
                    logger.error(f"Material ID {leather_id} is not a leather type")
                    raise ModelValidationError(f"Material ID {leather_id} is not a leather type")

                # Update leather fields
                for key, value in update_data.items():
                    setattr(leather, key, value)

                # Update inventory if provided
                if inventory_data and leather.inventory:
                    for key, value in inventory_data.items():
                        setattr(leather.inventory, key, value)

                    # Update status based on new quantities
                    leather.inventory._update_status()

                leather.validate()
                updated_leathers.append(leather)

            # Commit all updates
            self.session.commit()
            logger.info(f"Batch updated {len(updated_leathers)} leathers")
            return updated_leathers

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
            raise RepositoryError(f"Failed to batch update leathers: {str(e)}")

    def get_leathers_by_ids(self, leather_ids: List[int]) -> List[Leather]:
        """
        Get multiple leathers by their IDs.

        Args:
            leather_ids (List[int]): List of leather IDs

        Returns:
            List[Leather]: List of found leather objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            if not leather_ids:
                return []

            query = select(Leather).where(
                and_(
                    Leather.id.in_(leather_ids),
                    Leather.material_type == MaterialType.LEATHER,
                    Leather.is_deleted == False
                )
            ).options(
                joinedload(Leather.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers by IDs")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leathers by IDs: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leathers by IDs: {str(e)}")