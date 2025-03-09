# database/repositories/base_repository.py
"""
Base repository for generic database operations with robust error handling.

Provides a generic, type-safe repository pattern implementation with
comprehensive CRUD operations and error management.
"""

from logging import getLogger

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Self
)

# Import the updated exception classes
from database.models.base import ModelValidationError
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError

# Define a generic type variable for models
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository for database operations with proper error handling.

    This class provides common database access methods for all repositories
    and properly handles model validation errors.

    Attributes:
        session (Session): SQLAlchemy database session
        model_class (Type[T]): SQLAlchemy model class
        logger (logging.Logger): Logger for the repository
    """

    def __init__(self, session: Session, model_class: Type[T]):
        """
        Initialize the base repository.

        Args:
            session (Session): SQLAlchemy database session
            model_class (Type[T]): SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class
        self.logger = getLogger(__name__)

    def get_by_id(self, model_id: int, include_deleted: bool = False) -> Optional[T]:
        """
        Get a model instance by its ID.

        Args:
            model_id (int): The ID of the model to retrieve
            include_deleted (bool, optional): Whether to include soft-deleted records.
                                              Defaults to False.

        Returns:
            Optional[T]: The model instance or None if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(self.model_class).filter_by(id=model_id)

            # Only filter by is_deleted if not explicitly including deleted records
            if not include_deleted and hasattr(self.model_class, 'is_deleted'):
                query = query.filter_by(is_deleted=False)

            return self.session.execute(query).scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving {self.model_class.__name__} with ID {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve {self.model_class.__name__}: {str(e)}")

    def get_all(self, include_deleted: bool = False) -> List[T]:
        """
        Get all instances of the model.

        Args:
            include_deleted (bool, optional): Whether to include soft-deleted records.
                                              Defaults to False.

        Returns:
            List[T]: List of model instances

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            query = select(self.model_class)

            # Only filter by is_deleted if the attribute exists and not including deleted records
            if not include_deleted and hasattr(self.model_class, 'is_deleted'):
                query = query.filter_by(is_deleted=False)

            return self.session.execute(query).scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving all {self.model_class.__name__} instances: {str(e)}")
            raise RepositoryError(f"Failed to retrieve {self.model_class.__name__} instances: {str(e)}")

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new model instance with validation.

        Args:
            data (Dict[str, Any]): Dictionary of model attributes

        Returns:
            T: The created model instance

        Raises:
            ModelValidationError: If validation fails
            RepositoryError: If a database error occurs
        """
        try:
            # Create instance using model constructor (which handles validation)
            instance = self.model_class(**data)

            self.session.add(instance)
            self.session.commit()

            return instance
        except ModelValidationError as e:
            self.session.rollback()
            self.logger.error(f"Validation error creating {self.model_class.__name__}: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error creating {self.model_class.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to create {self.model_class.__name__}: {str(e)}")

    def update(self, model_id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a model instance with validation.

        Args:
            model_id (int): The ID of the model to update
            data (Dict[str, Any]): Dictionary of model attributes to update

        Returns:
            Optional[T]: The updated model instance or None if not found

        Raises:
            ModelValidationError: If validation fails
            ModelNotFoundError: If the model is not found
            RepositoryError: If a database error occurs
        """
        try:
            # Retrieve the instance, raising an error if not found
            instance = self.get_by_id(model_id)
            if not instance:
                raise ModelNotFoundError(f"{self.model_class.__name__} with ID {model_id} not found")

            # Update the instance (assuming an update method exists)
            if hasattr(instance, 'update'):
                instance.update(**data)
            else:
                # Fallback to direct attribute setting if no update method
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

            self.session.commit()
            return instance
        except ModelValidationError as e:
            self.session.rollback()
            self.logger.error(f"Validation error updating {self.model_class.__name__} {model_id}: {str(e)}")
            raise
        except ModelNotFoundError:
            # Re-raise not found error
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error updating {self.model_class.__name__} {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to update {self.model_class.__name__}: {str(e)}")

    def delete(self, model_id: int) -> bool:
        """
        Soft delete a model instance.

        Args:
            model_id (int): The ID of the model to delete

        Returns:
            bool: True if successful, False if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            instance = self.get_by_id(model_id)
            if not instance:
                return False

            # Use the model's soft_delete method if available
            if hasattr(instance, 'soft_delete'):
                instance.soft_delete()
            elif hasattr(instance, 'is_deleted'):
                # Fallback to manually setting is_deleted
                instance.is_deleted = True
            else:
                # If no soft delete method exists, log a warning
                self.logger.warning(f"No soft delete method for {self.model_class.__name__}")
                return False

            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting {self.model_class.__name__} {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}: {str(e)}")

    def hard_delete(self, model_id: int) -> bool:
        """
        Permanently delete a model instance.

        Args:
            model_id (int): The ID of the model to delete

        Returns:
            bool: True if successful, False if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            instance = self.get_by_id(model_id, include_deleted=True)
            if not instance:
                return False

            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error hard deleting {self.model_class.__name__} {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to hard delete {self.model_class.__name__}: {str(e)}")

    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple model instances in a single transaction.

        Args:
            data_list (List[Dict[str, Any]]): List of dictionaries with model attributes

        Returns:
            List[T]: List of created model instances

        Raises:
            ModelValidationError: If validation fails
            RepositoryError: If a database error occurs
        """
        try:
            # Create instances using model constructor
            instances = [self.model_class(**data) for data in data_list]

            self.session.add_all(instances)
            self.session.commit()

            return instances
        except ModelValidationError as e:
            self.session.rollback()
            self.logger.error(f"Validation error creating multiple {self.model_class.__name__} instances: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error creating multiple {self.model_class.__name__} instances: {str(e)}")
            raise RepositoryError(f"Failed to create multiple {self.model_class.__name__} instances: {str(e)}")