# store_management/database/repositories/base_repository.py
"""
Base repository module for standard database operations.

This module provides a generic base repository class that implements 
common CRUD (Create, Read, Update, Delete) operations using SQLAlchemy.
"""

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar
)
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

# Configure logging
logger = logging.getLogger(__name__)

# Generic type variable for the model
T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    A generic base repository for database operations.

    Provides standard CRUD methods for database models with error handling
    and logging.

    Attributes:
        session (Session): SQLAlchemy database session
        model_class (Type[T]): The SQLAlchemy model class being managed
    """

    def __init__(self, session: Session, model_class: Type[T]):
        """
        Initialize the base repository.

        Args:
            session (Session): SQLAlchemy database session
            model_class (Type[T]): The model class for this repository
        """
        self.session = session
        self.model_class = model_class

    def get_by_id(self, model_id: int) -> Optional[T]:
        """
        Retrieve a single record by its ID.

        Args:
            model_id (int): The unique identifier of the record

        Returns:
            Optional[T]: The retrieved record or None if not found

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            return self.session.query(self.model_class).get(model_id)
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving {self.model_class.__name__} with ID {model_id}: {e}')
            raise

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Retrieve all records with optional pagination.

        Args:
            limit (Optional[int], optional): Maximum number of records to return
            offset (Optional[int], optional): Number of records to skip

        Returns:
            List[T]: List of retrieved records

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            query = self.session.query(self.model_class)

            if offset is not None:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving all {self.model_class.__name__}: {e}')
            raise

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            data (Dict[str, Any]): Dictionary of field values for the new record

        Returns:
            T: The created record

        Raises:
            SQLAlchemyError: If there's a database-related error during creation
            ValueError: If required fields are missing
        """
        try:
            # Validate required fields if needed
            instance = self.model_class(**data)

            self.session.add(instance)
            self.session.commit()

            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating {self.model_class.__name__}: {e}')
            raise
        except TypeError as e:
            logger.error(f'Invalid data for {self.model_class.__name__}: {e}')
            raise ValueError(f'Invalid data for {self.model_class.__name__}')

    def update(self, model_id: int, data: Dict[str, Any]) -> T:
        """
        Update an existing record.

        Args:
            model_id (int): The ID of the record to update
            data (Dict[str, Any]): Dictionary of field values to update

        Returns:
            T: The updated record

        Raises:
            SQLAlchemyError: If there's a database-related error
            ValueError: If the record is not found
        """
        try:
            # Retrieve the existing instance
            instance = self.get_by_id(model_id)

            if instance is None:
                raise ValueError(f'{self.model_class.__name__} with ID {model_id} not found')

            # Update instance attributes
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
                else:
                    logger.warning(f'Attempted to set non-existent attribute {key} on {self.model_class.__name__}')

            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating {self.model_class.__name__} with ID {model_id}: {e}')
            raise

    def delete(self, model_id: int) -> bool:
        """
        Delete a record.

        Args:
            model_id (int): The ID of the record to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            SQLAlchemyError: If there's a database-related error
            ValueError: If the record is not found
        """
        try:
            # Retrieve the instance to delete
            instance = self.get_by_id(model_id)

            if instance is None:
                raise ValueError(f'{self.model_class.__name__} with ID {model_id} not found')

            self.session.delete(instance)
            self.session.commit()

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error deleting {self.model_class.__name__} with ID {model_id}: {e}')
            raise

    def filter_by(self, **kwargs) -> List[T]:
        """
        Filter records by specific criteria.

        Args:
            **kwargs: Keyword arguments representing filter conditions

        Returns:
            List[T]: List of records matching the filter conditions

        Raises:
            SQLAlchemyError: If there's a database-related error
        """
        try:
            return self.session.query(self.model_class).filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            logger.error(f'Error filtering {self.model_class.__name__} by {kwargs}: {e}')
            raise

    def search(self, search_term: str, fields: List[str]) -> List[T]:
        """
        Perform a case-insensitive search across specified fields.

        Args:
            search_term (str): The term to search for
            fields (List[str]): The fields to search in

        Returns:
            List[T]: List of records matching the search term

        Raises:
            SQLAlchemyError: If there's a database-related error
            ValueError: If no valid search conditions are found
        """
        try:
            # Validate input
            if not search_term or not fields:
                return []

            # Build search conditions
            conditions = []
            for field in fields:
                if hasattr(self.model_class, field):
                    attr = getattr(self.model_class, field)
                    conditions.append(attr.ilike(f'%{search_term}%'))

            # Ensure at least one valid condition exists
            if not conditions:
                raise ValueError(f'No valid search fields found for {self.model_class.__name__}')

            # Execute search query
            return self.session.query(self.model_class).filter(or_(*conditions)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching {self.model_class.__name__} for '{search_term}' in {fields}: {e}")
            raise