# Path: database/repositories/base_repository.py

"""
Base Repository for common database operations.

Provides a generic implementation of basic CRUD operations
for SQLAlchemy models.
"""

import logging
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Type variable for the model
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """
    Base repository providing common database operations.

    Supports Create, Read, Update, and Delete (CRUD) operations
    for SQLAlchemy models.

    Attributes:
        session (Session): SQLAlchemy database session
        model_class (Type[T]): SQLAlchemy model class
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

    def get_by_id(self, id_value: int) -> Optional[T]:
        """
        Retrieve an entity by its primary key.

        Args:
            id_value (int): Primary key value

        Returns:
            Optional[T]: Entity if found, None otherwise
        """
        try:
            return self.session.query(self.model_class).get(id_value)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving {self.model_class.__name__} by ID {id_value}: {e}")
            raise

    def get_all(self,
                limit: Optional[int] = None,
                offset: Optional[int] = None) -> List[T]:
        """
        Retrieve all entities with optional pagination.

        Args:
            limit (Optional[int]): Maximum number of results to return
            offset (Optional[int]): Number of results to skip

        Returns:
            List[T]: List of entities
        """
        try:
            query = self.session.query(self.model_class)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all {self.model_class.__name__}: {e}")
            raise

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data (Dict[str, Any]): Entity creation data

        Returns:
            T: The newly created entity
        """
        try:
            # Create new entity instance
            new_entity = self.model_class(**data)

            # Add to session and commit
            self.session.add(new_entity)
            self.session.commit()

            logger.info(f"Created new {self.model_class.__name__}: {new_entity}")
            return new_entity
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise

    def update(self, id_value: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            id_value (int): Primary key of the entity to update
            data (Dict[str, Any]): Update data

        Returns:
            Optional[T]: Updated entity, or None if not found
        """
        try:
            # Find the existing entity
            entity = self.get_by_id(id_value)

            if entity is None:
                logger.warning(f"{self.model_class.__name__} with ID {id_value} not found")
                return None

            # Update entity attributes
            for key, value in data.items():
                setattr(entity, key, value)

            # Commit changes
            self.session.commit()

            logger.info(f"Updated {self.model_class.__name__} with ID {id_value}")
            return entity
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating {self.model_class.__name__} with ID {id_value}: {e}")
            raise

    def delete(self, id_value: int) -> bool:
        """
        Delete an entity by its primary key.

        Args:
            id_value (int): Primary key of the entity to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Find the existing entity
            entity = self.get_by_id(id_value)

            if entity is None:
                logger.warning(f"{self.model_class.__name__} with ID {id_value} not found")
                return False

            # Delete the entity
            self.session.delete(entity)
            self.session.commit()

            logger.info(f"Deleted {self.model_class.__name__} with ID {id_value}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting {self.model_class.__name__} with ID {id_value}: {e}")
            raise