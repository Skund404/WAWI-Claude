# database/repositories/base_repository.py
from logging import getLogger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

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
    """

    def __init__(self, session: Session, model_class: Type[T]):
        """Initialize the base repository.

        Args:
            session (Session): SQLAlchemy database session
            model_class (Type[T]): SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class
        self.logger = getLogger(__name__)

    def get_by_id(self, model_id: int) -> Optional[T]:
        """Get a model instance by its ID.

        Args:
            model_id: The ID of the model to retrieve

        Returns:
            The model instance or None if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            return self.session.query(self.model_class).filter_by(id=model_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving {self.model_class.__name__} with ID {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve {self.model_class.__name__}: {str(e)}")

    def get_all(self) -> List[T]:
        """Get all instances of the model.

        Returns:
            List of model instances

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            return self.session.query(self.model_class).filter_by(is_deleted=False).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving all {self.model_class.__name__} instances: {str(e)}")
            raise RepositoryError(f"Failed to retrieve {self.model_class.__name__} instances: {str(e)}")

    def create(self, data: Dict[str, Any]) -> T:
        """Create a new model instance with validation.

        Args:
            data: Dictionary of model attributes

        Returns:
            The created model instance

        Raises:
            ModelValidationError: If validation fails
            RepositoryError: If a database error occurs
        """
        try:
            # The model constructor now handles validation
            instance = self.model_class(**data)
            self.session.add(instance)
            self.session.commit()
            return instance
        except ModelValidationError as e:
            self.session.rollback()
            self.logger.error(f"Validation error creating {self.model_class.__name__}: {str(e)}")
            # Re-raise the validation error to be handled at the service level
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error creating {self.model_class.__name__}: {str(e)}")
            raise RepositoryError(f"Failed to create {self.model_class.__name__}: {str(e)}")

    def update(self, model_id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update a model instance with validation.

        Args:
            model_id: The ID of the model to update
            data: Dictionary of model attributes to update

        Returns:
            The updated model instance or None if not found

        Raises:
            ModelValidationError: If validation fails
            ModelNotFoundError: If the model is not found
            RepositoryError: If a database error occurs
        """
        try:
            instance = self.get_by_id(model_id)
            if not instance:
                raise ModelNotFoundError(f"{self.model_class.__name__} with ID {model_id} not found")

            # The model's update method now handles validation
            instance.update(**data)
            self.session.commit()
            return instance
        except ModelValidationError as e:
            self.session.rollback()
            self.logger.error(f"Validation error updating {self.model_class.__name__} {model_id}: {str(e)}")
            # Re-raise the validation error to be handled at the service level
            raise
        except ModelNotFoundError:
            # Re-raise not found error
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error updating {self.model_class.__name__} {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to update {self.model_class.__name__}: {str(e)}")

    def delete(self, model_id: int) -> bool:
        """Soft delete a model instance.

        Args:
            model_id: The ID of the model to delete

        Returns:
            True if successful, False if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            instance = self.get_by_id(model_id)
            if not instance:
                return False

            # Use the model's soft_delete method
            instance.soft_delete()
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting {self.model_class.__name__} {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}: {str(e)}")

    def hard_delete(self, model_id: int) -> bool:
        """Permanently delete a model instance.

        Args:
            model_id: The ID of the model to delete

        Returns:
            True if successful, False if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            instance = self.get_by_id(model_id)
            if not instance:
                return False

            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error hard deleting {self.model_class.__name__} {model_id}: {str(e)}")
            raise RepositoryError(f"Failed to hard delete {self.model_class.__name__}: {str(e)}")