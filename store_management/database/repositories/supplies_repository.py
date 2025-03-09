# database/repositories/supplies_repository.py
"""
Repository for supplies and consumables data access.
Provides database operations for thread, adhesives, dyes, edge paints,
and other consumable materials used in leatherworking.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from database.models.enums import MaterialType, InventoryStatus, TransactionType
from database.models.material import Material, Supplies  # Updated to use Supplies class
from database.models.inventory import Inventory
from database.repositories.base_repository import BaseRepository
from database.models.base import ModelValidationError
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError
from utils.logger import get_logger

logger = get_logger(__name__)

# List of material types handled by this repository
SUPPLY_MATERIAL_TYPES = [
    MaterialType.THREAD,
    MaterialType.ADHESIVE,
    MaterialType.DYE,
    MaterialType.EDGE_PAINT,
    MaterialType.EDGE_COAT,
    MaterialType.WAX,
    MaterialType.FINISH,
    MaterialType.LINING,
    MaterialType.INTERFACING,
    MaterialType.ELASTIC,
    MaterialType.PADDING
]


class SuppliesRepository(BaseRepository[Supplies]):
    """
    Repository for supplies and consumable materials data access operations.

    Handles all consumable materials used in leatherworking including:
    - Threads
    - Adhesives (glue)
    - Dyes
    - Edge paints/finishes
    - Waxes
    - Other consumable supplies

    Extends BaseRepository with supply-specific functionality.
    """

    def __init__(self, session: Session):
        """
        Initialize the SuppliesRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Supplies)
        logger.debug("Initialized SuppliesRepository")

    def _build_base_supplies_query(self,
                                   material_type: Optional[MaterialType] = None,
                                   include_deleted: bool = False):
        """
        Build a base query for supplies with common filtering conditions.

        Args:
            material_type (Optional[MaterialType]): Optional specific material type to filter
            include_deleted (bool): Whether to include soft-deleted supplies

        Returns:
            sqlalchemy.Select: Base query for supplies
        """
        # Determine material types to search
        if material_type:
            material_types = [material_type]
        else:
            material_types = SUPPLY_MATERIAL_TYPES

        # Build base query with options for loading related data
        query = select(Supplies).options(
            selectinload(Supplies.inventory),
            selectinload(Supplies.supplier)
        )

        # Build conditions
        conditions = [Supplies.material_type.in_([t.value for t in material_types])]

        if not include_deleted:
            conditions.append(Supplies.is_deleted == False)

        return query.where(and_(*conditions))

    def get_all_supplies(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         material_type: Optional[MaterialType] = None,
                         supplier_id: Optional[int] = None) -> List[Supplies]:
        """
        Get all supplies with optional filtering.

        Args:
            include_deleted (bool): Whether to include soft-deleted supplies
            status (Optional[InventoryStatus]): Filter by inventory status
            material_type (Optional[MaterialType]): Filter by specific material type
            supplier_id (Optional[int]): Filter by supplier ID

        Returns:
            List[Supplies]: List of supply materials

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Start with base query
            query = self._build_base_supplies_query(material_type, include_deleted)

            # Add status filtering if needed
            if status:
                query = query.join(
                    Inventory,
                    and_(
                        Inventory.item_id == Supplies.id,
                        Inventory.item_type == 'material',
                        Inventory.status == status
                    )
                )

            # Add supplier filter if needed
            if supplier_id:
                query = query.filter(Supplies.supplier_id == supplier_id)

            # Execute query and return results
            result = self.session.execute(query.order_by(Supplies.name)).scalars().all()
            logger.debug(f"Retrieved {len(result)} supplies with filters: {locals()}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supplies: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supplies: {str(e)}")


    def search_supplies(self,
                        search_term: str,
                        material_types: Optional[List[MaterialType]] = None,
                        include_deleted: bool = False) -> List[Supplies]:
        """
        Search for supplies by name, description, or other fields.

        Args:
            search_term (str): Search term to look for
            material_types (Optional[List[MaterialType]]): List of material types to search within
            include_deleted (bool): Whether to include soft-deleted supplies

        Returns:
            List[Supplies]: List of matching supply objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Determine material types to search
            if not material_types:
                material_types = SUPPLY_MATERIAL_TYPES

            # Build base query
            query = select(Supplies).options(
                selectinload(Supplies.inventory)
            )

            # Add material type filter
            material_type_condition = Supplies.material_type.in_([t.value for t in material_types])

            # Add search conditions
            search_conditions = [
                Supplies.name.ilike(f"%{search_term}%"),
                Supplies.description.ilike(f"%{search_term}%"),
                Supplies.supplies_type.ilike(f"%{search_term}%")  # Search in supplies_type field
            ]

            # Apply filters
            query = query.where(
                and_(
                    material_type_condition,
                    or_(*search_conditions),
                    Supplies.is_deleted == False if not include_deleted else True
                )
            )

            # Execute query
            result = self.session.execute(query.order_by(Supplies.name)).scalars().all()
            logger.debug(f"Search for '{search_term}' returned {len(result)} supplies")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error searching supplies: {str(e)}")
            raise RepositoryError(f"Failed to search supplies: {str(e)}")

    def get_supply_with_inventory(self, supply_id: int) -> Optional[Supplies]:
        """
        Get a supply by ID with related inventory information.

        Args:
            supply_id (int): ID of the supply

        Returns:
            Optional[Supplies]: Supply object with loaded inventory or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.id == supply_id,
                    Supplies.material_type.in_([t.value for t in SUPPLY_MATERIAL_TYPES])
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved supply ID {supply_id} with inventory info")
            else:
                logger.debug(f"No supply found with ID {supply_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supply with inventory: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supply with inventory: {str(e)}")

    def get_supply_with_supplier(self, supply_id: int) -> Optional[Supplies]:
        """
        Get a supply by ID with supplier information.

        Args:
            supply_id (int): ID of the supply

        Returns:
            Optional[Supplies]: Supply object with loaded supplier or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.id == supply_id,
                    Supplies.material_type.in_([t.value for t in SUPPLY_MATERIAL_TYPES])
                )
            ).options(
                joinedload(Supplies.supplier)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved supply ID {supply_id} with supplier info")
            else:
                logger.debug(f"No supply found with ID {supply_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supply with supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supply with supplier: {str(e)}")

    def get_supplies_by_status(self, status: InventoryStatus,
                               material_type: Optional[MaterialType] = None) -> List[Supplies]:
        """
        Get supplies filtered by inventory status.

        Args:
            status (InventoryStatus): Status to filter by
            material_type (Optional[MaterialType]): Optional specific material type to filter by

        Returns:
            List[Supplies]: List of supply objects with the specified status

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).join(
                Inventory,
                and_(
                    Inventory.item_id == Supplies.id,
                    Inventory.item_type == 'material'
                )
            )

            # Determine material types to search
            if material_type:
                material_types = [material_type]
            else:
                material_types = SUPPLY_MATERIAL_TYPES

            # Build conditions
            conditions = [
                Supplies.material_type.in_([t.value for t in material_types]),
                Inventory.status == status,
                Supplies.is_deleted == False
            ]

            query = query.where(and_(*conditions)).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} supplies with status {status.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supplies by status: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supplies by status: {str(e)}")

    def get_supplies_by_material_type(self, material_type: MaterialType) -> List[Supplies]:
        """
        Get supplies of a specific material type.

        Args:
            material_type (MaterialType): Type of material to filter by

        Returns:
            List[Supplies]: List of supply objects of the specified type

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.material_type == material_type.value,
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} supplies of type {material_type.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supplies by type: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supplies by type: {str(e)}")

    def get_threads(self) -> List[Supplies]:
        """
        Get all thread materials.

        Returns:
            List[Supplies]: List of thread materials

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.material_type == MaterialType.THREAD.value,
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} thread supplies")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving threads: {str(e)}")
            raise RepositoryError(f"Failed to retrieve threads: {str(e)}")

    def get_adhesives(self) -> List[Supplies]:
        """
        Get all adhesive materials.

        Returns:
            List[Supplies]: List of adhesive materials

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.material_type == MaterialType.ADHESIVE.value,
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} adhesive supplies")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving adhesives: {str(e)}")
            raise RepositoryError(f"Failed to retrieve adhesives: {str(e)}")

    def get_dyes(self) -> List[Supplies]:
        """
        Get all dye materials.

        Returns:
            List[Supplies]: List of dye materials

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.material_type == MaterialType.DYE.value,
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} dye supplies")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving dyes: {str(e)}")
            raise RepositoryError(f"Failed to retrieve dyes: {str(e)}")

    def get_edge_paints(self) -> List[Supplies]:
        """
        Get all edge paint materials.

        Returns:
            List[Supplies]: List of edge paint materials

        Raises:
            RepositoryError: If a database error occurs
        """
        # Get both edge paint and edge coat (for backward compatibility)
        try:
            query = select(Supplies).where(
                and_(
                    Supplies.material_type.in_([
                        MaterialType.EDGE_PAINT.value,
                        MaterialType.EDGE_COAT.value
                    ]),
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} edge paint materials")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving edge paints: {str(e)}")
            raise RepositoryError(f"Failed to retrieve edge paints: {str(e)}")

    def get_supplies_inventory_value(self,
                                     material_type: Optional[MaterialType] = None) -> Dict[str, Any]:
        """
        Calculate the total inventory value of supplies.

        Args:
            material_type (Optional[MaterialType]): Optional specific material type to calculate value for

        Returns:
            Dict[str, Any]: Dictionary with total value and breakdowns by type

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Determine material types to calculate
            if material_type:
                material_types = [material_type]
            else:
                material_types = SUPPLY_MATERIAL_TYPES

            query = select(Supplies).join(
                Inventory,
                and_(
                    Inventory.item_id == Supplies.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Supplies.material_type.in_([t.value for t in material_types]),
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            supplies = self.session.execute(query).scalars().all()

            # Calculate totals
            total_value = 0.0
            by_type = {}
            by_supplies_type = {}  # Group by supplies_type

            for supply in supplies:
                if supply.inventory and supply.inventory.unit_cost is not None:
                    # Calculate value based on inventory
                    value = supply.inventory.calculate_value()
                    total_value += value

                    # Group by material type
                    type_name = supply.material_type or "Unknown"
                    by_type[type_name] = by_type.get(type_name, 0.0) + value

                    # Group by supplies_type if available
                    if hasattr(supply, 'supplies_type') and supply.supplies_type:
                        supplies_type = supply.supplies_type
                        by_supplies_type[supplies_type] = by_supplies_type.get(supplies_type, 0.0) + value

            result = {
                "total_value": total_value,
                "by_material_type": by_type,
                "by_supplies_type": by_supplies_type
            }

            logger.debug(f"Calculated supplies inventory value: {total_value:.2f}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error calculating supplies inventory value: {str(e)}")
            raise RepositoryError(f"Failed to calculate supplies inventory value: {str(e)}")

    def update_inventory_quantity(self, supply_id: int, quantity_change: float,
                                  transaction_type: TransactionType,
                                  reference_type: Optional[str] = None,
                                  reference_id: Optional[int] = None,
                                  notes: Optional[str] = None) -> Inventory:
        """
        Update the inventory quantity for a supply item.

        Args:
            supply_id (int): ID of the supply
            quantity_change (float): Quantity to add (positive) or remove (negative)
            transaction_type (TransactionType): Type of transaction
            reference_type (Optional[str]): Type of reference document
            reference_id (Optional[int]): ID of the reference document
            notes (Optional[str]): Optional notes about the transaction

        Returns:
            Inventory: The updated inventory record

        Raises:
            ModelNotFoundError: If the supply or inventory does not exist
            ModelValidationError: If quantity would go negative
            RepositoryError: If a database error occurs
        """
        try:
            # Get the supply with inventory
            supply = self.get_supply_with_inventory(supply_id)
            if not supply:
                logger.error(f"Cannot update inventory: Supply ID {supply_id} not found")
                raise ModelNotFoundError(f"Supply with ID {supply_id} not found")

            # Check if inventory exists
            if not supply.inventory:
                logger.error(f"No inventory record exists for Supply ID {supply_id}")
                raise ModelNotFoundError(f"No inventory record exists for Supply ID {supply_id}")

            # Update the inventory quantity
            try:
                supply.inventory.update_quantity(
                    change=quantity_change,
                    transaction_type=transaction_type,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    notes=notes
                )
            except ModelValidationError as e:
                raise ModelValidationError(str(e))

            self.session.commit()

            logger.info(f"Updated inventory for Supply ID {supply_id}. "
                        f"Quantity change: {quantity_change}, New quantity: {supply.inventory.quantity}")

            return supply.inventory

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except ModelValidationError:
            # Re-raise to be handled at the service level
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating supply inventory: {str(e)}")
            raise RepositoryError(f"Failed to update supply inventory: {str(e)}")

    def get_supply_inventory_history(self, supply_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for a specific supply's inventory.

        Args:
            supply_id (int): ID of the supply
            limit (Optional[int]): Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of transaction records

        Raises:
            ModelNotFoundError: If the supply or inventory does not exist
            RepositoryError: If a database error occurs
        """
        try:
            # Get the supply with inventory
            supply = self.get_supply_with_inventory(supply_id)
            if not supply:
                logger.error(f"Cannot get history: Supply ID {supply_id} not found")
                raise ModelNotFoundError(f"Supply with ID {supply_id} not found")

            # Check if inventory exists
            if not supply.inventory:
                logger.error(f"No inventory record exists for Supply ID {supply_id}")
                raise ModelNotFoundError(f"No inventory record exists for Supply ID {supply_id}")

            # Get transaction history from the inventory record
            history = supply.inventory.transaction_history or []

            # Sort by date (most recent first)
            history = sorted(history,
                             key=lambda x: x.get('date', ''),
                             reverse=True)

            # Apply limit if specified
            if limit is not None and limit > 0:
                history = history[:limit]

            logger.debug(f"Retrieved {len(history)} transaction records for Supply ID {supply_id}")
            return history

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supply inventory history: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supply inventory history: {str(e)}")

    def get_low_stock_supplies(self,
                               material_type: Optional[MaterialType] = None,
                               threshold: Optional[float] = None) -> List[Supplies]:
        """
        Get all supplies with low stock.

        Args:
            material_type (Optional[MaterialType]): Optional specific material type to filter
            threshold (Optional[float]): Override the defined min_stock_level

        Returns:
            List[Supplies]: List of supply objects with low stock

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Start with base query
            query = self._build_base_supplies_query(material_type)

            # Join with inventory to check stock levels
            query = query.join(
                Inventory,
                and_(
                    Inventory.item_id == Supplies.id,
                    Inventory.item_type == 'material'
                )
            )

            # Apply stock level conditions
            if threshold is not None:
                # Use provided threshold
                query = query.where(
                    and_(
                        Inventory.quantity <= threshold,
                        Inventory.quantity > 0
                    )
                )
            else:
                # Use each item's defined min_stock_level or fallback to LOW_STOCK status
                query = query.where(
                    or_(
                        and_(
                            Inventory.min_stock_level.is_not(None),
                            Inventory.quantity <= Inventory.min_stock_level,
                            Inventory.quantity > 0
                        ),
                        Inventory.status == InventoryStatus.LOW_STOCK
                    )
                )

            # Order by current quantity
            query = query.order_by(Inventory.quantity)

            # Execute query
            result = self.session.execute(query).scalars().unique().all()
            logger.debug(f"Retrieved {len(result)} supplies with low stock")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving low stock supplies: {str(e)}")
            raise RepositoryError(f"Failed to retrieve low stock supplies: {str(e)}")

    def get_out_of_stock_supplies(self,
                                  material_type: Optional[MaterialType] = None) -> List[Supplies]:
        """
        Get all supplies that are out of stock.

        Args:
            material_type (Optional[MaterialType]): Optional specific material type to filter

        Returns:
            List[Supplies]: List of supply objects with zero quantity

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Start with base query
            query = self._build_base_supplies_query(material_type)

            # Join with inventory to check stock status
            query = query.join(
                Inventory,
                and_(
                    Inventory.item_id == Supplies.id,
                    Inventory.item_type == 'material',
                    or_(
                        Inventory.status == InventoryStatus.OUT_OF_STOCK,
                        Inventory.quantity == 0
                    )
                )
            )

            # Execute query
            result = self.session.execute(query.order_by(Supplies.name)).scalars().unique().all()
            logger.debug(f"Retrieved {len(result)} out of stock supplies")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving out of stock supplies: {str(e)}")
            raise RepositoryError(f"Failed to retrieve out of stock supplies: {str(e)}")

    def create_supply(self, supply_data: Dict[str, Any]) -> Supplies:
        """
        Create a new supply with validation.

        Args:
            supply_data (Dict[str, Any]): Data for the new supply

        Returns:
            Supplies: Created supply instance

        Raises:
            ModelValidationError: If validation fails
            RepositoryError: If a database error occurs
        """
        try:
            # Ensure the material_type is one of the valid supply types
            material_type = supply_data.get('material_type')
            if not material_type or material_type not in [t.value for t in SUPPLY_MATERIAL_TYPES]:
                valid_types = [t.name for t in SUPPLY_MATERIAL_TYPES]
                logger.error(f"Invalid material type for supply: {material_type}")
                raise ModelValidationError(
                    f"Invalid material type for supply. Must be one of: {', '.join(valid_types)}"
                )

            # Create new Supplies instance
            supply = Supplies(**supply_data)

            # Validate the supply
            supply.validate()

            # Add to session and commit
            self.session.add(supply)
            self.session.commit()

            logger.info(f"Created new supply: {supply.name} (ID: {supply.id})")
            return supply

        except ModelValidationError:
            # Re-raise validation errors
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating supply: {str(e)}")
            raise RepositoryError(f"Failed to create supply: {str(e)}")

    def get_supplies_by_ids(self, supply_ids: List[int]) -> List[Supplies]:
        """
        Get multiple supplies by their IDs.

        Args:
            supply_ids (List[int]): List of supply IDs

        Returns:
            List[Supplies]: List of found supply objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            if not supply_ids:
                return []

            query = select(Supplies).where(
                and_(
                    Supplies.id.in_(supply_ids),
                    Supplies.material_type.in_([t.value for t in SUPPLY_MATERIAL_TYPES]),
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} supplies by IDs")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supplies by IDs: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supplies by IDs: {str(e)}")

    def get_supplies_by_supplier(self, supplier_id: int,
                                 material_type: Optional[MaterialType] = None) -> List[Supplies]:
        """
        Get supplies from a specific supplier.

        Args:
            supplier_id (int): ID of the supplier
            material_type (Optional[MaterialType]): Optional specific material type to filter

        Returns:
            List[Supplies]: List of supply objects from the supplier

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Determine material types to search
            if material_type:
                material_types = [material_type]
            else:
                material_types = SUPPLY_MATERIAL_TYPES

            query = select(Supplies).where(
                and_(
                    Supplies.material_type.in_([t.value for t in material_types]),
                    Supplies.supplier_id == supplier_id,
                    Supplies.is_deleted == False
                )
            ).options(
                joinedload(Supplies.inventory),
                joinedload(Supplies.supplier)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} supplies from supplier ID {supplier_id}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving supplies by supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve supplies by supplier: {str(e)}")

    # Enhanced methods for dashboard and metrics functionality

    def get_inventory_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive inventory metrics for dashboard display.

        Returns:
            Dict[str, Any]: Dictionary with various metrics

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Initialize metrics structure
            metrics = {
                "total_items": 0,
                "total_value": 0.0,
                "low_stock_count": 0,
                "out_of_stock_count": 0,
                "by_type": {},
                "reorder_needed": [],
                "supplies_by_type": {}
            }

            # Get all supplies with inventory
            supplies = self.get_all_supplies()

            for supply in supplies:
                if not supply.inventory:
                    continue

                metrics["total_items"] += 1

                # Track supplies by type
                supplies_type = getattr(supply, 'supplies_type', supply.material_type)
                metrics["supplies_by_type"][supplies_type] = metrics["supplies_by_type"].get(supplies_type, 0) + 1

                # Value calculations
                if supply.inventory.unit_cost:
                    value = supply.inventory.calculate_value()
                    metrics["total_value"] += value

                    # Group by type
                    type_name = supply.material_type
                    if type_name not in metrics["by_type"]:
                        metrics["by_type"][type_name] = {
                            "count": 0,
                            "value": 0.0
                        }
                    metrics["by_type"][type_name]["count"] += 1
                    metrics["by_type"][type_name]["value"] += value

                # Stock status
                if supply.inventory.status == InventoryStatus.LOW_STOCK:
                    metrics["low_stock_count"] += 1
                elif supply.inventory.status == InventoryStatus.OUT_OF_STOCK:
                    metrics["out_of_stock_count"] += 1

                # Reorder needed
                if supply.inventory.needs_reorder():
                    metrics["reorder_needed"].append({
                        "id": supply.id,
                        "name": supply.name,
                        "current_quantity": supply.inventory.quantity,
                        "reorder_quantity": supply.inventory.reorder_quantity,
                        "type": getattr(supply, 'supplies_type', supply.material_type)
                    })

            # Calculate percentages
            if metrics["total_items"] > 0:
                metrics["low_stock_percentage"] = (metrics["low_stock_count"] / metrics["total_items"]) * 100
                metrics["out_of_stock_percentage"] = (metrics["out_of_stock_count"] / metrics["total_items"]) * 100
            else:
                metrics["low_stock_percentage"] = 0
                metrics["out_of_stock_percentage"] = 0

            return metrics

        except SQLAlchemyError as e:
            logger.error(f"Database error calculating inventory metrics: {str(e)}")
            raise RepositoryError(f"Failed to calculate inventory metrics: {str(e)}")

    def get_usage_rate_by_supply(self, supply_id: int, days: int = 30) -> Optional[float]:
        """
        Calculate the average daily usage rate for a specific supply.

        Args:
            supply_id: ID of the supply
            days: Number of days to analyze

        Returns:
            Optional[float]: Average daily usage or None if no data

        Raises:
            ModelNotFoundError: If supply not found
            RepositoryError: If a database error occurs
        """
        try:
            # Get supply with inventory
            supply = self.get_supply_with_inventory(supply_id)
            if not supply:
                raise ModelNotFoundError(f"Supply with ID {supply_id} not found")

            if not supply.inventory or not supply.inventory.transaction_history:
                return None

            # Get usage transactions within the time period
            history = supply.inventory.transaction_history
            now = datetime.now()
            cutoff_date = now - timedelta(days=days)

            usage_transactions = []
            for transaction in history:
                if transaction.get('transaction_type') == TransactionType.USAGE.name:
                    try:
                        transaction_date = datetime.fromisoformat(transaction.get('date'))
                        if transaction_date >= cutoff_date:
                            usage_transactions.append(transaction)
                    except (ValueError, TypeError):
                        # Skip transactions with invalid dates
                        continue

            if not usage_transactions:
                return None

            # Calculate total usage (use absolute value of negative changes)
            total_usage = sum(abs(t.get('change', 0)) for t in usage_transactions if t.get('change', 0) < 0)

            # Calculate daily rate
            daily_rate = total_usage / days

            return daily_rate

        except ModelNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error calculating usage rate: {str(e)}")
            raise RepositoryError(f"Failed to calculate usage rate: {str(e)}")

    def estimate_depletion_date(self, supply_id: int) -> Optional[datetime]:
        """
        Estimate when a supply will be depleted based on usage rate.

        Args:
            supply_id: ID of the supply

        Returns:
            Optional[datetime]: Estimated depletion date or None if can't be determined

        Raises:
            ModelNotFoundError: If supply not found
            RepositoryError: If a database error occurs
        """
        try:
            # Get supply with inventory
            supply = self.get_supply_with_inventory(supply_id)
            if not supply:
                raise ModelNotFoundError(f"Supply with ID {supply_id} not found")

            if not supply.inventory:
                return None

            # Get current quantity
            current_quantity = supply.inventory.quantity
            if current_quantity <= 0:
                return None  # Already depleted

            # Calculate usage rate
            usage_rate = self.get_usage_rate_by_supply(supply_id)
            if not usage_rate or usage_rate <= 0:
                return None  # No usage data or invalid rate

            # Calculate days until depletion
            days_remaining = current_quantity / usage_rate

            # Calculate depletion date
            depletion_date = datetime.now() + timedelta(days=days_remaining)

            return depletion_date

        except ModelNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error estimating depletion date: {str(e)}")
            raise RepositoryError(f"Failed to estimate depletion date: {str(e)}")

    def batch_update(self, updates: List[Dict[str, Any]]) -> List[Supplies]:
        """
        Update multiple supply records in a batch.

        Args:
            updates (List[Dict[str, Any]]): List of dictionaries with 'id' and fields to update

        Returns:
            List[Supplies]: List of updated supply objects

        Raises:
            ModelNotFoundError: If any supply ID is not found
            ModelValidationError: If any of the updates fail validation
            RepositoryError: If a database error occurs
        """
        try:
            updated_supplies = []

            for update_data in updates:
                supply_id = update_data.pop('id', None)
                inventory_data = update_data.pop('inventory', None)

                if not supply_id:
                    logger.error("Missing supply ID in batch update")
                    raise ModelValidationError("Supply ID is required for batch update")

                supply = self.get_by_id(supply_id)
                if not supply:
                    logger.error(f"Supply ID {supply_id} not found in batch update")
                    raise ModelNotFoundError(f"Supply with ID {supply_id} not found")

                # Ensure this is a supply type
                if supply.material_type not in [t.value for t in SUPPLY_MATERIAL_TYPES]:
                    logger.error(f"Material ID {supply_id} is not a valid supply type")
                    raise ModelValidationError(f"Material ID {supply_id} is not a valid supply type")

                # Update supply fields
                for key, value in update_data.items():
                    setattr(supply, key, value)

                # Update inventory if provided
                if inventory_data and supply.inventory:
                    for key, value in inventory_data.items():
                        setattr(supply.inventory, key, value)

                    # Update status based on new quantities
                    supply.inventory._update_status()

                supply.validate()
                updated_supplies.append(supply)

            # Commit all updates
            self.session.commit()
            logger.info(f"Batch updated {len(updated_supplies)} supplies")
            return updated_supplies

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
            raise RepositoryError(f"Failed to batch update supplies: {str(e)}")