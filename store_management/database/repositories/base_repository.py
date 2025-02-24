# database/repositories/base_repository.py

from typing import TypeVar, Generic, List, Optional, Any, Dict
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Base repository class providing common CRUD operations.

    Generic base class that can be used with any model type inheriting from BaseModel.
    Provides basic database operations and error handling.

    Type Parameters:
        T: Model type inheriting from BaseModel
    """

    def __init__(self, session: Session, model_class: type[T]):
        """
        Initialize the repository.

        Args:
            session: SQLAlchemy session instance
            model_class: Class of the model this repository handles
        """
        self.session = session
        self.model_class = model_class
        self.logger = logging.getLogger(f"{__name__}.{model_class.__name__}")

    def get_by_id(self, id: Any) -> Optional[T]:
        """
        Get a record by ID.

        Args:
            id: Primary key value of the record

        Returns:
            Optional[T]: The record if found, None otherwise
        """
        try:
            return self.session.query(self.model_class).get(id)
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving {self.model_class.__name__} with id {id}: {e}")
            return None

    def get_all(self) -> List[T]:
        """
        Get all records.

        Returns:
            List[T]: List of all records
        """
        try:
            return self.session.query(self.model_class).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving all {self.model_class.__name__}s: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Optional[T]:
        """
        Create a new record.

        Args:
            data: Dictionary containing model field values

        Returns:
            Optional[T]: The created record if successful, None otherwise
        """
        try:
            instance = self.model_class(**data)
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {e}")
            self.session.rollback()
            return None

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record.

        Args:
            id: Primary key value of the record to update
            data: Dictionary containing updated field values

        Returns:
            Optional[T]: The updated record if successful, None otherwise
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None

            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            self.session.rollback()
            return None

    def delete(self, id: Any) -> bool:
        """
        Delete a record.

        Args:
            id: Primary key value of the record to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            instance = self.get_by_id(id)
            if instance:
                self.session.delete(instance)
                self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            self.session.rollback()
            return False

    def exists(self, id: Any) -> bool:
        """
        Check if a record exists.

        Args:
            id: Primary key value to check

        Returns:
            bool: True if record exists, False otherwise
        """
        try:
            return self.session.query(
                self.session.query(self.model_class).filter_by(id=id).exists()
            ).scalar()
        except SQLAlchemyError as e:
            self.logger.error(f"Error checking existence of {self.model_class.__name__} {id}: {e}")
            return False

    def count(self) -> int:
        """
        Get the total count of records.

        Returns:
            int: Total number of records
        """
        try:
            return self.session.query(self.model_class).count()
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting {self.model_class.__name__}s: {e}")
            return 0