# services/implementations/leather_service.py
"""
Service implementation for leather management operations.

This service handles business logic for leather inventory operations,
including CRUD operations, searching, filtering, and batch operations.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.models.enums import InventoryStatus, LeatherType, MaterialQualityGrade, MaterialType, TransactionType
from database.models.leather import Leather
from database.repositories.leather_repository import LeatherRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.leather_service import ILeatherService
from utils.logger import get_logger

logger = get_logger(__name__)


class LeatherService(BaseService, ILeatherService):
    """
    Service for leather management operations.

    This service provides business logic for leather inventory operations,
    managing the creation, querying, updating, and inventory management of
    leather materials.
    """

    def __init__(self, leather_repository: Optional[LeatherRepository] = None) -> None:
        """
        Initialize the leather service.

        Args:
            leather_repository (Optional[LeatherRepository]): Repository for leather data access.
                If not provided, a new one will be created.
        """
        super().__init__()
        logger.debug("Initializing LeatherService")

        self._session = get_db_session()
        self._repository = leather_repository or LeatherRepository(self._session)

    def get_materials(self, material_type: MaterialType = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Get materials with optional filtering. This method maintains compatibility
        with the IMaterialService interface for GUI integration.

        Args:
            material_type: Type of material to filter by
            **kwargs: Additional filter criteria

        Returns:
            List[Dict[str, Any]]: List of material dictionaries
        """
        if material_type != MaterialType.LEATHER:
            # If not specifically asking for leather, return empty list
            return []

        # Map common filter parameters to leather-specific filters
        filters = {}

        # Handle leather type filtering
        if 'type' in kwargs:
            try:
                if isinstance(kwargs['type'], str) and kwargs['type'] != 'All':
                    filters['leather_type'] = LeatherType(kwargs['type'].lower())
            except (ValueError, KeyError):
                logger.warning(f"Invalid leather type: {kwargs.get('type')}")

        # Handle quality grade filtering
        if 'quality_grade' in kwargs:
            try:
                if isinstance(kwargs['quality_grade'], str) and kwargs['quality_grade'] != 'All':
                    filters['grade'] = MaterialQualityGrade(kwargs['quality_grade'].lower())
            except (ValueError, KeyError):
                logger.warning(f"Invalid quality grade: {kwargs.get('quality_grade')}")

        # Handle price range filtering
        if 'min_price' in kwargs and kwargs['min_price'] is not None:
            filters['min_unit_price'] = float(kwargs['min_price'])
        if 'max_price' in kwargs and kwargs['max_price'] is not None:
            filters['max_unit_price'] = float(kwargs['max_price'])

        # Handle quantity range filtering
        if 'min_quantity' in kwargs and kwargs['min_quantity'] is not None:
            filters['min_quantity'] = int(kwargs['min_quantity'])
        if 'max_quantity' in kwargs and kwargs['max_quantity'] is not None:
            filters['max_quantity'] = int(kwargs['max_quantity'])

        # Get leathers from repository
        leathers = self._repository.get_all_leathers(include_deleted=False, **filters)

        # Convert to dictionaries
        result = [leather.to_dict() for leather in leathers]

        logger.info(f"Retrieved {len(result)} leathers with filters: {filters}")
        return result

    def search_materials(self, search_term: str, material_type: MaterialType = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for materials by name, description, etc. This method maintains compatibility
        with the IMaterialService interface for GUI integration.

        Args:
            search_term: Text to search for
            material_type: Type of material to filter by
            **kwargs: Additional search parameters

        Returns:
            List[Dict[str, Any]]: List of matching material dictionaries
        """
        if material_type and material_type != MaterialType.LEATHER:
            # If specifically asking for non-leather materials, return empty list
            return []

        try:
            # Search for leathers matching the term
            leathers = self._repository.search_leathers(search_term)

            # Convert to dictionaries
            result = [leather.to_dict() for leather in leathers]

            logger.info(f"Search for '{search_term}' returned {len(result)} leathers")
            return result

        except Exception as e:
            logger.error(f"Error searching leathers: {str(e)}")
            return []

    def get_all_leathers(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         leather_type: Optional[LeatherType] = None,
                         grade: Optional[MaterialQualityGrade] = None,
                         color: Optional[str] = None,
                         thickness_min: Optional[float] = None,
                         thickness_max: Optional[float] = None,
                         min_size: Optional[float] = None,
                         min_unit_price: Optional[float] = None,
                         max_unit_price: Optional[float] = None,
                         min_quantity: Optional[int] = None,
                         max_quantity: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all leathers with comprehensive filtering.

        Args:
            include_deleted: Whether to include soft-deleted leathers
            status: Filter by status
            leather_type: Filter by leather type
            grade: Filter by quality grade
            color: Filter by color
            thickness_min: Filter by minimum thickness
            thickness_max: Filter by maximum thickness
            min_size: Filter by minimum size in square feet
            min_unit_price: Filter by minimum unit price
            max_unit_price: Filter by maximum unit price
            min_quantity: Filter by minimum quantity
            max_quantity: Filter by maximum quantity

        Returns:
            List[Dict[str, Any]]: List of leather dictionaries
        """
        try:
            # Prepare repository parameters
            repo_params = {
                'include_deleted': include_deleted,
                'status': status,
                'leather_type': leather_type,
                'grade': grade,
                'color': color,
                'thickness_min': thickness_min,
                'thickness_max': thickness_max,
                'min_size': min_size
            }

            # Get leathers from repository
            leathers = self._repository.get_all_leathers(**repo_params)

            # Apply additional filters that the repository might not support directly
            filtered_leathers = leathers

            if min_unit_price is not None:
                filtered_leathers = [l for l in filtered_leathers if
                                     l.unit_price is not None and l.unit_price >= min_unit_price]

            if max_unit_price is not None:
                filtered_leathers = [l for l in filtered_leathers if
                                     l.unit_price is not None and l.unit_price <= max_unit_price]

            if min_quantity is not None:
                filtered_leathers = [l for l in filtered_leathers if l.quantity >= min_quantity]

            if max_quantity is not None:
                filtered_leathers = [l for l in filtered_leathers if l.quantity <= max_quantity]

            # Convert to dictionaries
            result = [leather.to_dict() for leather in filtered_leathers]

            logger.info(f"Retrieved {len(result)} leathers with filtering")
            return result

        except Exception as e:
            logger.error(f"Error retrieving leathers: {str(e)}")
            raise

    def get_by_id(self, leather_id: int) -> Dict[str, Any]:
        """
        Get a leather by its ID. This method maintains compatibility
        with the IMaterialService interface for GUI integration.

        Args:
            leather_id: ID of the leather to retrieve

        Returns:
            Dict[str, Any]: Leather as a dictionary

        Raises:
            NotFoundError: If the leather is not found
        """
        try:
            leather = self._repository.get_by_id(leather_id)

            if not leather or leather.deleted:
                logger.warning(f"Leather with ID {leather_id} not found")
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            logger.debug(f"Retrieved leather with ID {leather_id}")
            return leather.to_dict()

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leather: {str(e)}")
            raise ValidationError(f"Database error: {str(e)}")

    def create(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new leather item. This method maintains compatibility
        with the IMaterialService interface for GUI integration.

        Args:
            leather_data: Data for the new leather

        Returns:
            Dict[str, Any]: Created leather as a dictionary

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Convert string enum values if needed
            leather_data = self._prepare_leather_data(leather_data)

            # Create new leather
            leather = Leather(**leather_data)

            # Add to repository
            created_leather = self._repository.create(leather)

            # Commit changes
            self._session.commit()

            logger.info(f"Created new leather: {created_leather.name} (ID: {created_leather.id})")
            return created_leather.to_dict()

        except ValueError as e:
            logger.error(f"Validation error creating leather: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

        except Exception as e:
            logger.error(f"Error creating leather: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

    def update(self, leather_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing leather. This method maintains compatibility
        with the IMaterialService interface for GUI integration.

        Args:
            leather_id: ID of the leather to update
            update_data: Data to update

        Returns:
            Dict[str, Any]: Updated leather as a dictionary

        Raises:
            NotFoundError: If the leather is not found
            ValidationError: If validation fails
        """
        try:
            # Get existing leather
            leather = self._repository.get_by_id(leather_id)

            if not leather or leather.deleted:
                logger.warning(f"Leather with ID {leather_id} not found for update")
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Convert string enum values if needed
            update_data = self._prepare_leather_data(update_data)

            # Update leather
            leather.update(**update_data)

            # Commit changes
            self._session.commit()

            logger.info(f"Updated leather ID {leather_id}: {leather.name}")
            return leather.to_dict()

        except ValueError as e:
            logger.error(f"Validation error updating leather: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

        except NotFoundError:
            self._session.rollback()
            raise

        except Exception as e:
            logger.error(f"Error updating leather: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

    def delete(self, leather_id: int, permanent: bool = False) -> bool:
        """
        Delete a leather (soft delete by default). This method maintains compatibility
        with the IMaterialService interface for GUI integration.

        Args:
            leather_id: ID of the leather to delete
            permanent: Whether to permanently delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If the leather is not found
        """
        try:
            # Get existing leather
            leather = self._repository.get_by_id(leather_id)

            if not leather:
                logger.warning(f"Leather with ID {leather_id} not found for deletion")
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            if permanent:
                # Permanent delete
                self._repository.delete(leather_id)
                logger.info(f"Permanently deleted leather ID {leather_id}")
            else:
                # Soft delete
                leather.soft_delete()
                logger.info(f"Soft deleted leather ID {leather_id}: {leather.name}")

            # Commit changes
            self._session.commit()

            return True

        except NotFoundError:
            self._session.rollback()
            raise

        except Exception as e:
            logger.error(f"Error deleting leather: {str(e)}")
            self._session.rollback()
            return False

    def get_leather_by_id(self, leather_id: int) -> Dict[str, Any]:
        """
        Get a leather by its ID.

        Args:
            leather_id: ID of the leather to retrieve

        Returns:
            Dict[str, Any]: Leather as a dictionary

        Raises:
            NotFoundError: If the leather is not found
        """
        return self.get_by_id(leather_id)

    def create_leather(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new leather item.

        Args:
            leather_data: Data for the new leather

        Returns:
            Dict[str, Any]: Created leather as a dictionary

        Raises:
            ValidationError: If validation fails
        """
        return self.create(leather_data)

    def update_leather(self, leather_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing leather.

        Args:
            leather_id: ID of the leather to update
            update_data: Data to update

        Returns:
            Dict[str, Any]: Updated leather as a dictionary

        Raises:
            NotFoundError: If the leather is not found
            ValidationError: If validation fails
        """
        return self.update(leather_id, update_data)

    def delete_leather(self, leather_id: int, permanent: bool = False) -> bool:
        """
        Delete a leather (soft delete by default).

        Args:
            leather_id: ID of the leather to delete
            permanent: Whether to permanently delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If the leather is not found
        """
        return self.delete(leather_id, permanent)

    def restore_leather(self, leather_id: int) -> Dict[str, Any]:
        """
        Restore a soft-deleted leather.

        Args:
            leather_id: ID of the leather to restore

        Returns:
            Dict[str, Any]: Restored leather as a dictionary

        Raises:
            NotFoundError: If the leather is not found
            ValidationError: If the leather is not deleted
        """
        try:
            # Get existing leather
            leather = self._repository.get_by_id(leather_id)

            if not leather:
                logger.warning(f"Leather with ID {leather_id} not found for restoration")
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            if not leather.deleted:
                logger.warning(f"Leather ID {leather_id} is not deleted, cannot restore")
                raise ValidationError(f"Leather with ID {leather_id} is not deleted")

            # Restore leather
            leather.restore()

            # Commit changes
            self._session.commit()

            logger.info(f"Restored leather ID {leather_id}: {leather.name}")
            return leather.to_dict()

        except (NotFoundError, ValidationError):
            self._session.rollback()
            raise

        except Exception as e:
            logger.error(f"Error restoring leather: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

    def search_leathers(self, search_term: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Search for leathers by various fields.

        Args:
            search_term: Search term to look for
            include_deleted: Whether to include soft-deleted leathers

        Returns:
            List[Dict[str, Any]]: List of matching leather dictionaries
        """
        return self.search_materials(search_term, MaterialType.LEATHER)

    def adjust_leather_quantity(self, leather_id: int, quantity_change: int,
                                transaction_type: Union[TransactionType, str],
                                notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Adjust the quantity of a leather and create a transaction record.

        Args:
            leather_id: ID of the leather
            quantity_change: Amount to change quantity by (positive or negative)
            transaction_type: Type of transaction
            notes: Additional notes for the transaction

        Returns:
            Dict[str, Any]: Updated leather as a dictionary

        Raises:
            NotFoundError: If the leather is not found
            ValidationError: If validation fails
        """
        try:
            # Get existing leather
            leather = self._repository.get_by_id(leather_id)

            if not leather or leather.deleted:
                logger.warning(f"Leather with ID {leather_id} not found for quantity adjustment")
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Convert string to enum if needed
            if isinstance(transaction_type, str):
                try:
                    transaction_type = TransactionType[transaction_type.upper()]
                except KeyError:
                    raise ValidationError(f"Invalid transaction type: {transaction_type}")

            # For now, map quantity change to area change (future: improve this)
            # This is a simplification to maintain compatibility with the GUI
            area_change = float(quantity_change)

            # Create transaction and update leather
            is_addition = quantity_change > 0

            # Create transaction on the leather
            leather.adjust_quantity(area_change, transaction_type, notes)

            # Also update the quantity field for GUI compatibility
            new_quantity = leather.quantity + quantity_change
            if new_quantity < 0:
                raise ValidationError(f"Cannot reduce quantity below zero. Current quantity: {leather.quantity}")

            leather.quantity = new_quantity

            # Commit changes
            self._session.commit()

            # Refresh the leather from the database
            self._session.refresh(leather)

            logger.info(f"Adjusted leather ID {leather_id} quantity by {quantity_change}")
            return leather.to_dict()

        except ValueError as e:
            logger.error(f"Validation error adjusting leather quantity: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

        except (NotFoundError, ValidationError):
            self._session.rollback()
            raise

        except Exception as e:
            logger.error(f"Error adjusting leather quantity: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

    def get_transaction_history(self, leather_id: int,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for a specific leather.

        Args:
            leather_id: ID of the leather
            limit: Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of transactions as dictionaries

        Raises:
            NotFoundError: If the leather is not found
        """
        try:
            # Check if leather exists
            leather = self._repository.get_by_id(leather_id)

            if not leather:
                logger.warning(f"Leather with ID {leather_id} not found for transaction history")
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Get transactions
            transactions = self._repository.get_transaction_history(leather_id, limit)

            # Convert to dictionaries
            result = []
            for transaction in transactions:
                result.append({
                    'id': transaction.id,
                    'leather_id': transaction.leather_id,
                    'transaction_type': transaction.transaction_type.value,
                    'area_change': transaction.area_change,
                    'wastage': transaction.wastage,
                    'timestamp': transaction.timestamp.isoformat() if transaction.timestamp else None,
                    'notes': transaction.notes
                })

            logger.info(f"Retrieved {len(result)} transactions for leather ID {leather_id}")
            return result

        except NotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error retrieving leather transaction history: {str(e)}")
            raise ValidationError(str(e))

    def get_low_stock_leathers(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Get all leathers with quantity below a specified threshold.

        Args:
            threshold: Quantity threshold

        Returns:
            List[Dict[str, Any]]: List of low stock leathers as dictionaries
        """
        try:
            leathers = self._repository.get_low_stock_leathers(threshold)

            # Convert to dictionaries
            result = [leather.to_dict() for leather in leathers]
            logger.info(f"Retrieved {len(result)} leathers with low stock (threshold: {threshold})")
            return result

        except Exception as e:
            logger.error(f"Error retrieving low stock leathers: {str(e)}")
            raise ValidationError(str(e))

    def get_out_of_stock_leathers(self) -> List[Dict[str, Any]]:
        """
        Get all leathers that are out of stock.

        Returns:
            List[Dict[str, Any]]: List of out of stock leathers as dictionaries
        """
        try:
            leathers = self._repository.get_out_of_stock_leathers()

            # Convert to dictionaries
            result = [leather.to_dict() for leather in leathers]
            logger.info(f"Retrieved {len(result)} out of stock leathers")
            return result

        except Exception as e:
            logger.error(f"Error retrieving out of stock leathers: {str(e)}")
            raise ValidationError(str(e))

    def get_leather_inventory_value(self) -> Dict[str, Any]:
        """
        Calculate the total inventory value of all leather items.

        Returns:
            Dict[str, Any]: Dictionary with total value and breakdowns
        """
        try:
            result = self._repository.get_leather_inventory_value()
            logger.info(f"Calculated leather inventory value: ${result['total_value']:.2f}")
            return result

        except Exception as e:
            logger.error(f"Error calculating leather inventory value: {str(e)}")
            raise ValidationError(str(e))

    def batch_update_leathers(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple leather records in a batch.

        Args:
            updates: List of dictionaries with 'id' and fields to update

        Returns:
            List[Dict[str, Any]]: List of updated leathers as dictionaries
        """
        try:
            # Validate and convert each update
            for update in updates:
                if 'id' not in update:
                    raise ValidationError("Leather ID is required for batch update")
                update = self._prepare_leather_data(update)

            # Perform batch update
            updated_leathers = self._repository.batch_update(updates)

            # Commit changes
            self._session.commit()

            # Convert to dictionaries
            result = [leather.to_dict() for leather in updated_leathers]
            logger.info(f"Batch updated {len(result)} leathers")
            return result

        except ValueError as e:
            logger.error(f"Validation error in batch update: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

        except Exception as e:
            logger.error(f"Error in batch update: {str(e)}")
            self._session.rollback()
            raise ValidationError(str(e))

    def _prepare_leather_data(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare leather data by converting string enum values to actual enums
        and handling other necessary transformations.

        Args:
            leather_data: Leather data to prepare

        Returns:
            Dict[str, Any]: Prepared leather data

        Raises:
            ValidationError: If validation fails
        """
        # Make a copy to avoid modifying the original
        prepared_data = leather_data.copy()

        # Handle MaterialType -> LeatherType mapping
        if 'type' in prepared_data and prepared_data['type'] == MaterialType.LEATHER:
            # If type is MaterialType.LEATHER, convert to proper leather_type if missing
            if 'leather_type' not in prepared_data:
                prepared_data['leather_type'] = LeatherType.FULL_GRAIN  # Default

        # Convert leather_type from string to enum if needed
        if 'leather_type' in prepared_data and isinstance(prepared_data['leather_type'], str):
            try:
                if prepared_data['leather_type'] in [t.value for t in LeatherType]:
                    prepared_data['leather_type'] = LeatherType(prepared_data['leather_type'])
                elif prepared_data['leather_type'] in [t.name for t in LeatherType]:
                    prepared_data['leather_type'] = LeatherType[prepared_data['leather_type']]
                else:
                    valid_types = [t.value for t in LeatherType] + [t.name for t in LeatherType]
                    raise ValidationError(
                        f"Invalid leather type: {prepared_data['leather_type']}. Valid types: {valid_types}")
            except (ValueError, KeyError) as e:
                valid_types = [t.name for t in LeatherType]
                raise ValidationError(
                    f"Invalid leather type: {prepared_data['leather_type']}. Valid types: {valid_types}")

        # Convert grade/quality_grade from string to enum if needed
        if 'quality_grade' in prepared_data and 'grade' not in prepared_data:
            prepared_data['grade'] = prepared_data['quality_grade']

        if 'grade' in prepared_data and isinstance(prepared_data['grade'], str):
            try:
                if prepared_data['grade'] in [g.value for g in MaterialQualityGrade]:
                    prepared_data['grade'] = MaterialQualityGrade(prepared_data['grade'])
                elif prepared_data['grade'] in [g.name for g in MaterialQualityGrade]:
                    prepared_data['grade'] = MaterialQualityGrade[prepared_data['grade']]
                else:
                    valid_grades = [g.value for g in MaterialQualityGrade] + [g.name for g in MaterialQualityGrade]
                    raise ValidationError(f"Invalid grade: {prepared_data['grade']}. Valid grades: {valid_grades}")
            except (ValueError, KeyError) as e:
                valid_grades = [g.name for g in MaterialQualityGrade]
                raise ValidationError(f"Invalid grade: {prepared_data['grade']}. Valid grades: {valid_grades}")

        # Convert status from string to enum if needed
        if 'status' in prepared_data and isinstance(prepared_data['status'], str):
            try:
                if prepared_data['status'] in [s.value for s in InventoryStatus]:
                    prepared_data['status'] = InventoryStatus(prepared_data['status'])
                elif prepared_data['status'] in [s.name for s in InventoryStatus]:
                    prepared_data['status'] = InventoryStatus[prepared_data['status']]
                else:
                    valid_statuses = [s.value for s in InventoryStatus] + [s.name for s in InventoryStatus]
                    raise ValidationError(
                        f"Invalid status: {prepared_data['status']}. Valid statuses: {valid_statuses}")
            except (ValueError, KeyError) as e:
                valid_statuses = [s.name for s in InventoryStatus]
                raise ValidationError(f"Invalid status: {prepared_data['status']}. Valid statuses: {valid_statuses}")

        # Handle unit_price field
        if 'unit_price' in prepared_data and prepared_data['unit_price'] is not None:
            try:
                prepared_data['unit_price'] = float(prepared_data['unit_price'])
            except (ValueError, TypeError):
                raise ValidationError("Unit price must be a valid number")

        # Handle thickness field renamed to thickness_mm
        if 'thickness' in prepared_data and 'thickness_mm' not in prepared_data:
            prepared_data['thickness_mm'] = prepared_data['thickness']

        # Numeric field conversions
        numeric_fields = {
            'cost_per_sqft': float,
            'thickness_mm': float,
            'size_sqft': float,
            'quantity': int
        }

        for field, converter in numeric_fields.items():
            if field in prepared_data and prepared_data[field] is not None:
                try:
                    prepared_data[field] = converter(prepared_data[field])
                except (ValueError, TypeError):
                    raise ValidationError(f"{field} must be a valid number")

        return prepared_data