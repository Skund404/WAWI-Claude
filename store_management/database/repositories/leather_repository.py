# database/repositories/leather_repository.py
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select, desc

from database.models.enums import InventoryStatus, LeatherType, MaterialQualityGrade
from database.models.leather import Leather
from database.models.transaction import LeatherTransaction, TransactionType
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
                         grade: Optional[MaterialQualityGrade] = None,
                         color: Optional[str] = None,
                         thickness_min: Optional[float] = None,
                         thickness_max: Optional[float] = None,
                         min_size: Optional[float] = None) -> List[Leather]:
        """
        Get all leathers with optional filtering.

        Args:
            include_deleted (bool): Whether to include soft-deleted leathers
            status (Optional[InventoryStatus]): Filter by status
            leather_type (Optional[LeatherType]): Filter by leather type
            grade (Optional[MaterialQualityGrade]): Filter by quality grade
            color (Optional[str]): Filter by color
            thickness_min (Optional[float]): Filter by minimum thickness
            thickness_max (Optional[float]): Filter by maximum thickness
            min_size (Optional[float]): Filter by minimum size in square feet

        Returns:
            List[Leather]: List of leather objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather)

            # Build filter conditions
            conditions = []

            if not include_deleted:
                conditions.append(Leather.is_deleted == False)

            if status:
                conditions.append(Leather.status == status)

            if leather_type:
                conditions.append(Leather.leather_type == leather_type)

            if grade:
                conditions.append(Leather.grade == grade)

            if color:
                conditions.append(Leather.color.ilike(f"%{color}%"))

            if thickness_min is not None:
                conditions.append(Leather.thickness_mm >= thickness_min)

            if thickness_max is not None:
                conditions.append(Leather.thickness_mm <= thickness_max)

            if min_size is not None:
                conditions.append(Leather.size_sqft >= min_size)

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Execute query
            result = self.session.execute(query.order_by(Leather.name)).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers with filters: {locals()}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leathers: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leathers: {str(e)}")

    def search_leathers(self, search_term: str, include_deleted: bool = False) -> List[Leather]:
        """
        Search for leathers by name, description, color, or notes.

        Args:
            search_term (str): Search term to look for
            include_deleted (bool): Whether to include soft-deleted leathers

        Returns:
            List[Leather]: List of matching leather objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Create base query
            query = select(Leather)

            # Add search conditions
            search_conditions = [
                Leather.name.ilike(f"%{search_term}%"),
                Leather.description.ilike(f"%{search_term}%"),
                Leather.color.ilike(f"%{search_term}%"),
                Leather.tannage.ilike(f"%{search_term}%"),
                Leather.finish.ilike(f"%{search_term}%"),
                Leather.notes.ilike(f"%{search_term}%")
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

    def get_leather_with_transactions(self, leather_id: int) -> Optional[Leather]:
        """
        Get a leather by ID with related transactions.

        Args:
            leather_id (int): ID of the leather

        Returns:
            Optional[Leather]: Leather object with loaded transactions or None

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).where(Leather.id == leather_id).options(
                joinedload(Leather.transactions)
            )

            result = self.session.execute(query).scalars().first()
            if result:
                logger.debug(f"Retrieved leather ID {leather_id} with {len(result.transactions)} transactions")
            else:
                logger.debug(f"No leather found with ID {leather_id}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leather with transactions: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leather with transactions: {str(e)}")

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
            query = select(Leather).where(Leather.id == leather_id).options(
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
            query = select(Leather).where(
                and_(
                    Leather.status == status,
                    Leather.is_deleted == False
                )
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers with status {status.name}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leathers by status: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leathers by status: {str(e)}")

    def get_leather_inventory_value(self) -> Dict[str, float]:
        """
        Calculate the total inventory value of all leather items.

        Returns:
            Dict[str, float]: Dictionary with total value and breakdowns by type and grade

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            # Get all non-deleted leathers
            leathers = self.get_all_leathers()

            # Calculate totals
            total_value = 0.0
            by_type = {}
            by_grade = {}

            for leather in leathers:
                # Use the model's calculate_total_value method from our updated model
                value = leather.calculate_total_value()
                total_value += value

                # Group by type
                type_name = leather.leather_type.name if leather.leather_type else "Unknown"
                by_type[type_name] = by_type.get(type_name, 0.0) + value

                # Group by grade
                grade_name = leather.grade.name if leather.grade else "Unknown"
                by_grade[grade_name] = by_grade.get(grade_name, 0.0) + value

            result = {
                "total_value": total_value,
                "by_leather_type": by_type,
                "by_grade": by_grade
            }

            logger.debug(f"Calculated leather inventory value: {total_value:.2f}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error calculating leather inventory value: {str(e)}")
            raise RepositoryError(f"Failed to calculate leather inventory value: {str(e)}")

    def create_transaction(self, leather_id: int, transaction_type: TransactionType,
                           quantity: float, is_addition: bool, notes: Optional[str] = None) -> LeatherTransaction:
        """
        Create a new leather transaction and update leather quantity.

        Args:
            leather_id (int): ID of the leather
            transaction_type (TransactionType): Type of transaction
            quantity (float): Quantity to add or remove
            is_addition (bool): Whether this is an addition or reduction
            notes (Optional[str]): Optional notes about the transaction

        Returns:
            LeatherTransaction: The created transaction

        Raises:
            ModelNotFoundError: If the leather does not exist
            ValidationError: If quantity would go negative
            RepositoryError: If a database error occurs
        """
        try:
            # Get the leather
            leather = self.get_by_id(leather_id)
            if not leather:
                logger.error(f"Cannot create transaction: Leather ID {leather_id} not found")
                raise ModelNotFoundError(f"Leather with ID {leather_id} not found")

            # Calculate quantity change
            area_change = quantity if is_addition else -quantity

            # Use the model's adjust_area method which handles validation and status updates
            try:
                leather.adjust_area(area_change, transaction_type, notes)
            except ValueError as e:
                # Convert ValueError to ModelValidationError for consistent error handling
                raise ModelValidationError(str(e))

            # Create a transaction record
            # Note: this step may be redundant if the adjust_area method already creates a transaction
            transaction = LeatherTransaction(
                leather_id=leather_id,
                transaction_type=transaction_type,
                quantity=quantity,
                is_addition=is_addition,
                notes=notes
            )

            self.session.add(transaction)

            logger.info(f"Created {transaction_type.name} transaction for Leather ID {leather_id}. "
                        f"Quantity change: {area_change}, New quantity: {leather.area_available_sqft}")

            return transaction

        except ModelNotFoundError:
            # Re-raise to be handled at the service level
            raise
        except ModelValidationError:
            # Re-raise to be handled at the service level
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating leather transaction: {str(e)}")
            raise RepositoryError(f"Failed to create leather transaction: {str(e)}")

    def get_transaction_history(self, leather_id: int,
                                limit: Optional[int] = None) -> List[LeatherTransaction]:
        """
        Get transaction history for a specific leather.

        Args:
            leather_id (int): ID of the leather
            limit (Optional[int]): Maximum number of transactions to return

        Returns:
            List[LeatherTransaction]: List of transactions in chronological sale

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(LeatherTransaction).where(
                LeatherTransaction.leather_id == leather_id
            ).order_by(desc(LeatherTransaction.created_at))  # Using created_at from BaseModelMixin

            if limit:
                query = query.limit(limit)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} transactions for Leather ID {leather_id}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leather transactions: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leather transactions: {str(e)}")

    def get_low_stock_leathers(self, threshold: float = 5.0) -> List[Leather]:
        """
        Get all leathers with quantity below a specified threshold.

        Args:
            threshold (float): Quantity threshold

        Returns:
            List[Leather]: List of leather objects with low stock

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(Leather).where(
                and_(
                    Leather.area_available_sqft <= threshold,
                    Leather.area_available_sqft > 0,  # Exclude out of stock
                    Leather.is_deleted == False
                )
            ).order_by(Leather.area_available_sqft)

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers with quantity <= {threshold}")
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
            query = select(Leather).where(
                and_(
                    Leather.area_available_sqft == 0,
                    Leather.is_deleted == False
                )
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
                if not leather_id:
                    logger.error("Missing leather ID in batch update")
                    raise ModelValidationError("Leather ID is required for batch update")

                leather = self.get_by_id(leather_id)
                if not leather:
                    logger.error(f"Leather ID {leather_id} not found in batch update")
                    raise ModelNotFoundError(f"Leather with ID {leather_id} not found")

                # Use the model's update method which handles validation
                leather.update(**update_data)
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
                    Leather.is_deleted == False
                )
            )

            result = self.session.execute(query).scalars().all()
            logger.debug(f"Retrieved {len(result)} leathers by IDs")
            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving leathers by IDs: {str(e)}")
            raise RepositoryError(f"Failed to retrieve leathers by IDs: {str(e)}")