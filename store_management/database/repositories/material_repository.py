# database/repositories/material_repository.py
"""
Repository for material data access.
Provides database operations for material items.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import and_, or_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database.models.enums import MaterialType, InventoryStatus, TransactionType
from database.models.material import Material
from database.models.inventory import Inventory
from database.repositories.base_repository import BaseRepository
from database.models.base import ModelValidationError
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError
from utils.logger import get_logger

logger = get_logger(__name__)


class MaterialRepository(BaseRepository[Material]):
    """
    Repository for material data access operations.
    Provides methods for CRUD operations and complex queries on materials.
    """

    def __init__(self, session: Session):
        """
        Initialize the Material Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Material)
        logger.debug("Initialized MaterialRepository")

    def get_all_materials(self,
                          include_deleted: bool = False,
                          status: Optional[InventoryStatus] = None,
                          material_type: Optional[MaterialType] = None,
                          quality: Optional[str] = None,
                          supplier_id: Optional[int] = None) -> List[Material]:
        """
        Get all materials with optional filtering.

        Args:
            include_deleted (bool): Whether to include soft-deleted materials
            status (Optional[InventoryStatus]): Filter by inventory status
            material_type (Optional[MaterialType]): Filter by material type
            quality (Optional[str]): Filter by quality
            supplier_id (Optional[int]): Filter by supplier ID

        Returns:
            List[Material]: List of material objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Join with inventory to filter by status if needed
            if status:
                query = select(Material).join(
                    Inventory,
                    and_(
                        Inventory.item_id == Material.id,
                        Inventory.item_type == 'material'
                    )
                )
            else:
                query = select(Material)

            # Build filter conditions
            conditions = []

            if not include_deleted:
                conditions.append(Material.is_deleted == False)

            if status:
                conditions.append(Inventory.status == status)

            if material_type:
                conditions.append(Material.material_type == material_type)

            if quality:
                conditions.append(Material.quality.ilike(f"%{quality}%"))

            if supplier_id:
                conditions.append(Material.supplier_id == supplier_id)

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Optionally load inventory relationship
            if status:
                query = query.options(joinedload(Material.inventory))
            else:
                query = query.options(joinedload(Material.inventory))

            # Execute query
            result = self.session.execute(query.order_by(Material.name)).scalars().all()
            logger.debug(f"Retrieved {len(result)} materials with filters: {locals()}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving materials: {str(e)}")
            raise RepositoryError(f"Failed to retrieve materials: {str(e)}")

    def search_materials(self, search_term: str, include_deleted: bool = False) -> List[Material]:
        """
        Search for materials by name, description, or other text fields.

        Args:
            search_term (str): Search term to look for
            include_deleted (bool): Whether to include soft-deleted materials

        Returns:
            List[Material]: List of matching material objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Create base query
            query = select(Material)

            # Add search conditions
            search_conditions = [
                Material.name.ilike(f"%{search_term}%"),
                Material.description.ilike(f"%{search_term}%")
            ]

            query = query.where(or_(*search_conditions))

            # Filter deleted if needed
            if not include_deleted:
                query = query.where(Material.is_deleted == False)

            # Load inventory information
            query = query.options(joinedload(Material.inventory))

            # Execute query
            result = self.session.execute(query.order_by(Material.name)).scalars().all()
            logger.debug(f"Search for '{search_term}' returned {len(result)} materials")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error searching materials: {str(e)}")
            raise RepositoryError(f"Failed to search materials: {str(e)}")

    def get_material_with_inventory(self, material_id: int) -> Optional[Material]:
        """
        Get a material by ID with related inventory information.

        Args:
            material_id (int): ID of the material

        Returns:
            Optional[Material]: Material object with loaded inventory or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).where(
                and_(
                    Material.id == material_id,
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.inventory)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved material ID {material_id} with inventory info")
            else:
                logger.debug(f"No material found with ID {material_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving material with inventory: {str(e)}")
            raise RepositoryError(f"Failed to retrieve material with inventory: {str(e)}")

    def get_material_with_supplier(self, material_id: int) -> Optional[Material]:
        """
        Get a material by ID with supplier information.

        Args:
            material_id (int): ID of the material

        Returns:
            Optional[Material]: Material object with loaded supplier or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).where(
                and_(
                    Material.id == material_id,
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.supplier)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved material ID {material_id} with supplier info")
            else:
                logger.debug(f"No material found with ID {material_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving material with supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve material with supplier: {str(e)}")

    def get_materials_by_status(self, status: InventoryStatus) -> List[Material]:
        """
        Get materials filtered by inventory status.

        Args:
            status (InventoryStatus): Status to filter by

        Returns:
            List[Material]: List of material objects with the specified status

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).join(
                Inventory,
                and_(
                    Inventory.item_id == Material.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Inventory.status == status,
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} materials with status {status.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving materials by status: {str(e)}")
            raise RepositoryError(f"Failed to retrieve materials by status: {str(e)}")

    def get_materials_by_type(self, material_type: MaterialType) -> List[Material]:
        """
        Get materials of a specific type.

        Args:
            material_type (MaterialType): Type of material to filter by

        Returns:
            List[Material]: List of material objects of the specified type

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).where(
                and_(
                    Material.material_type == material_type,
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} materials of type {material_type.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving materials by type: {str(e)}")
            raise RepositoryError(f"Failed to retrieve materials by type: {str(e)}")

    def get_materials_by_supplier(self, supplier_id: int) -> List[Material]:
        """
        Get materials from a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Material]: List of material objects from the supplier

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).where(
                and_(
                    Material.supplier_id == supplier_id,
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.inventory),
                joinedload(Material.supplier)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} materials from supplier ID {supplier_id}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving materials by supplier: {str(e)}")
            raise RepositoryError(f"Failed to retrieve materials by supplier: {str(e)}")

    def get_material_inventory_value(self) -> Dict[str, Any]:
        """
        Calculate the total inventory value of all material items.

        Returns:
            Dict[str, Any]: Dictionary with total value and breakdowns by type

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).join(
                Inventory,
                and_(
                    Inventory.item_id == Material.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                Material.is_deleted == False
            ).options(
                joinedload(Material.inventory)
            )

            materials = self.session.execute(query).scalars().all()

            # Calculate totals
            total_value = 0.0
            by_type = {}

            for material in materials:
                if material.inventory and material.inventory.unit_cost is not None:
                    # Calculate value based on inventory
                    value = material.inventory.calculate_value()
                    total_value += value

                    # Group by type
                    type_name = material.material_type.name if material.material_type else "Unknown"
                    by_type[type_name] = by_type.get(type_name, 0.0) + value

            result = {
                "total_value": total_value,
                "by_material_type": by_type
            }

            logger.debug(f"Calculated material inventory value: {total_value:.2f}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error calculating material inventory value: {str(e)}")
            raise RepositoryError(f"Failed to calculate material inventory value: {str(e)}")

    def update_inventory_quantity(self, material_id: int, quantity_change: float,
                                  transaction_type: TransactionType,
                                  reference_type: Optional[str] = None,
                                  reference_id: Optional[int] = None,
                                  notes: Optional[str] = None) -> Inventory:
        """
        Update the inventory quantity for a material item.

        Args:
            material_id (int): ID of the material
            quantity_change (float): Quantity to add (positive) or remove (negative)
            transaction_type (TransactionType): Type of transaction
            reference_type (Optional[str]): Type of reference document
            reference_id (Optional[int]): ID of the reference document
            notes (Optional[str]): Optional notes about the transaction

        Returns:
            Inventory: The updated inventory record

        Raises:
            ModelNotFoundError: If the material or inventory does not exist
            ModelValidationError: If quantity would go negative
            RepositoryError: If a database error occurs
        """
        try:
            # Get the material with inventory
            material = self.get_material_with_inventory(material_id)
            if not material:
                logger.error(f"Cannot update inventory: Material ID {material_id} not found")
                raise ModelNotFoundError(f"Material with ID {material_id} not found")

            # Check if inventory exists
            if not material.inventory:
                logger.error(f"No inventory record exists for Material ID {material_id}")
                raise ModelNotFoundError(f"No inventory record exists for Material ID {material_id}")

            # Update the inventory quantity
            try:
                material.inventory.update_quantity(
                    change=quantity_change,
                    transaction_type=transaction_type,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    notes=notes
                )
            except ModelValidationError as e:
                raise ModelValidationError(str(e))

            self.session.commit()

            logger.info(f"Updated inventory for Material ID {material_id}. "
                        f"Quantity change: {quantity_change}, New quantity: {material.inventory.quantity}")

            return material.inventory

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except ModelValidationError:
            # Re-raise to be handled at the service level
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating material inventory: {str(e)}")
            raise RepositoryError(f"Failed to update material inventory: {str(e)}")

    def get_material_inventory_history(self, material_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for a specific material's inventory.

        Args:
            material_id (int): ID of the material
            limit (Optional[int]): Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of transaction records

        Raises:
            ModelNotFoundError: If the material or inventory does not exist
            RepositoryError: If a database error occurs
        """
        try:
            # Get the material with inventory
            material = self.get_material_with_inventory(material_id)
            if not material:
                logger.error(f"Cannot get history: Material ID {material_id} not found")
                raise ModelNotFoundError(f"Material with ID {material_id} not found")

            # Check if inventory exists
            if not material.inventory:
                logger.error(f"No inventory record exists for Material ID {material_id}")
                raise ModelNotFoundError(f"No inventory record exists for Material ID {material_id}")

            # Get transaction history from the inventory record
            history = material.inventory.transaction_history or []

            # Sort by date (most recent first)
            history = sorted(history,
                             key=lambda x: x.get('date', ''),
                             reverse=True)

            # Apply limit if specified
            if limit is not None and limit > 0:
                history = history[:limit]

            logger.debug(f"Retrieved {len(history)} transaction records for Material ID {material_id}")
            return history

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving material inventory history: {str(e)}")
            raise RepositoryError(f"Failed to retrieve material inventory history: {str(e)}")

    def get_low_stock_materials(self, threshold: Optional[float] = None) -> List[Material]:
        """
        Get all materials with low stock.

        Args:
            threshold (Optional[float]): Override the defined min_stock_level

        Returns:
            List[Material]: List of material objects with low stock

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).join(
                Inventory,
                and_(
                    Inventory.item_id == Material.id,
                    Inventory.item_type == 'material'
                )
            )

            conditions = [
                Material.is_deleted == False
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
                joinedload(Material.inventory)
            ).order_by(Inventory.quantity)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} materials with low stock")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving low stock materials: {str(e)}")
            raise RepositoryError(f"Failed to retrieve low stock materials: {str(e)}")

    def get_out_of_stock_materials(self) -> List[Material]:
        """
        Get all materials that are out of stock.

        Returns:
            List[Material]: List of material objects with zero quantity

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Material).join(
                Inventory,
                and_(
                    Inventory.item_id == Material.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    or_(
                        Inventory.status == InventoryStatus.OUT_OF_STOCK,
                        Inventory.quantity == 0
                    ),
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.inventory)
            ).order_by(Material.name)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} out of stock materials")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving out of stock materials: {str(e)}")
            raise RepositoryError(f"Failed to retrieve out of stock materials: {str(e)}")

    def batch_update(self, updates: List[Dict[str, Any]]) -> List[Material]:
        """
        Update multiple material records in a batch.

        Args:
            updates (List[Dict[str, Any]]): List of dictionaries with 'id' and fields to update

        Returns:
            List[Material]: List of updated material objects

        Raises:
            ModelNotFoundError: If any material ID is not found
            ModelValidationError: If any of the updates fail validation
            RepositoryError: If a database error occurs
        """
        try:
            updated_materials = []

            for update_data in updates:
                material_id = update_data.pop('id', None)
                inventory_data = update_data.pop('inventory', None)

                if not material_id:
                    logger.error("Missing material ID in batch update")
                    raise ModelValidationError("Material ID is required for batch update")

                material = self.get_by_id(material_id)
                if not material:
                    logger.error(f"Material ID {material_id} not found in batch update")
                    raise ModelNotFoundError(f"Material with ID {material_id} not found")

                # Update material fields
                for key, value in update_data.items():
                    setattr(material, key, value)

                # Update inventory if provided
                if inventory_data and material.inventory:
                    for key, value in inventory_data.items():
                        setattr(material.inventory, key, value)

                    # Update status based on new quantities
                    material.inventory._update_status()

                material.validate()
                updated_materials.append(material)

            # Commit all updates
            self.session.commit()
            logger.info(f"Batch updated {len(updated_materials)} materials")
            return updated_materials

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
            raise RepositoryError(f"Failed to batch update materials: {str(e)}")

    def get_materials_by_ids(self, material_ids: List[int]) -> List[Material]:
        """
        Get multiple materials by their IDs.

        Args:
            material_ids (List[int]): List of material IDs

        Returns:
            List[Material]: List of found material objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            if not material_ids:
                return []

            query = select(Material).where(
                and_(
                    Material.id.in_(material_ids),
                    Material.is_deleted == False
                )
            ).options(
                joinedload(Material.inventory)
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} materials by IDs")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving materials by IDs: {str(e)}")
            raise RepositoryError(f"Failed to retrieve materials by IDs: {str(e)}")

    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material with validation.

        Args:
            material_data (Dict[str, Any]): Data for the new material

        Returns:
            Material: Created material instance

        Raises:
            ModelValidationError: If validation fails
            RepositoryError: If a database error occurs
        """
        try:
            # Create new material instance
            material = Material(**material_data)

            # Validate the material
            material.validate()

            # Add to session and commit
            self.session.add(material)
            self.session.commit()

            logger.info(f"Created new material: {material.name} (ID: {material.id})")
            return material

        except ModelValidationError:
            # Re-raise validation errors
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating material: {str(e)}")
            raise RepositoryError(f"Failed to create material: {str(e)}")