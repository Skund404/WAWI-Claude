# database/sqlalchemy/core/base_manager.py
"""
Base manager module for SQLAlchemy models.

This module provides the core functionality for database model managers,
including basic CRUD operations, transaction management, and error handling.
"""

import contextlib
import logging
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Import the circular import resolver correctly
from utils.circular_import_resolver import CircularImportResolver

# Import service interfaces
from services.interfaces import MaterialService

# Define a type variable for generic typing of models
T = TypeVar('T')

# Set up logger for this module
logger = logging.getLogger(__name__)

# Import DatabaseError from database.exceptions
# Using a try-except block to handle potential import errors
try:
    from database.exceptions import DatabaseError
except ImportError:
    # If that doesn't work, define a simple DatabaseError class
    class DatabaseError(Exception):
        """Base exception for database-related errors."""

        def __init__(self, message: str, context: Dict[str, Any] = None):
            self.context = context or {}
            super().__init__(message)


class BaseManager(Generic[T]):
    """
    Base manager class for SQLAlchemy models.

    Provides common database operations and transaction management
    for all model types. This class is generic and can be used with
    any SQLAlchemy model.
    """

    def __init__(self, model_class: Type[T], session_factory: Callable[[], Session]):
        """
        Initialize the base manager with a model class and session factory.

        Args:
            model_class: The SQLAlchemy model class this manager operates on
            session_factory: A callable that returns a database session
        """
        self.model_class = model_class
        self.session_factory = session_factory
        self.model_name = model_class.__name__
        logger.debug(f"Initialized BaseManager for {self.model_name}")

    @contextlib.contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: Active database session

        Raises:
            DatabaseError: If session management fails
        """
        session = self.session_factory()
        try:
            logger.debug(f"Starting new transaction for {self.model_name}")
            yield session
            session.commit()
            logger.debug(f"Transaction committed for {self.model_name}")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Transaction error for {self.model_name}: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")
        finally:
            session.close()
            logger.debug(f"Session closed for {self.model_name}")

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            data: Dictionary with field values for the new record

        Returns:
            The newly created model instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                instance = self.model_class(**data)
                session.add(instance)
                session.flush()  # Flush to get the ID
                logger.info(f"Created {self.model_name} with ID {getattr(instance, 'id', None)}")
                return instance
        except Exception as e:
            logger.error(f"Failed to create {self.model_name}: {str(e)}")
            raise DatabaseError(f"Failed to create {self.model_name}: {str(e)}")

    def get_by_id(self, id_value: Any) -> Optional[T]:
        """
        Get a record by its ID.

        Args:
            id_value: ID value to look up

        Returns:
            The record if found, or None

        Raises:
            DatabaseError: If lookup fails
        """
        try:
            with self.session_scope() as session:
                instance = session.get(self.model_class, id_value)
                return instance
        except Exception as e:
            logger.error(f"Failed to get {self.model_name} by ID {id_value}: {str(e)}")
            raise DatabaseError(f"Failed to get {self.model_name} by ID: {str(e)}")

    def get_all(self) -> List[T]:
        """
        Get all records.

        Returns:
            List of all records

        Raises:
            DatabaseError: If lookup fails
        """
        try:
            with self.session_scope() as session:
                stmt = select(self.model_class)
                result = session.execute(stmt).scalars().all()
                return list(result)
        except Exception as e:
            logger.error(f"Failed to get all {self.model_name} records: {str(e)}")
            raise DatabaseError(f"Failed to get all {self.model_name} records: {str(e)}")

    def update(self, id_value: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a record.

        Args:
            id_value: ID of the record to update
            data: Dictionary with updated field values

        Returns:
            The updated record, or None if not found

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                instance = session.get(self.model_class, id_value)
                if instance:
                    for key, value in data.items():
                        setattr(instance, key, value)
                    session.flush()
                    logger.info(f"Updated {self.model_name} with ID {id_value}")
                    return instance
                return None
        except Exception as e:
            logger.error(f"Failed to update {self.model_name} with ID {id_value}: {str(e)}")
            raise DatabaseError(f"Failed to update {self.model_name}: {str(e)}")

    def delete(self, id_value: Any) -> bool:
        """
        Delete a record.

        Args:
            id_value: ID of the record to delete

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.session_scope() as session:
                instance = session.get(self.model_class, id_value)
                if instance:
                    session.delete(instance)
                    logger.info(f"Deleted {self.model_name} with ID {id_value}")
                    return True
                logger.warning(f"{self.model_name} with ID {id_value} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Failed to delete {self.model_name} with ID {id_value}: {str(e)}")
            raise DatabaseError(f"Failed to delete {self.model_name}: {str(e)}")

    def execute_with_result(self, operation: Callable[[Session], T]) -> T:
        """
        Execute a custom operation with a session and return the result.

        Args:
            operation: Function that takes a session and returns a result

        Returns:
            The result of the operation

        Raises:
            DatabaseError: If the operation fails
        """
        try:
            with self.session_scope() as session:
                return operation(session)
        except Exception as e:
            logger.error(f"Failed to execute operation on {self.model_name}: {str(e)}")
            raise DatabaseError(f"Failed to execute operation: {str(e)}")

    def count(self) -> int:
        """
        Count the total number of records.

        Returns:
            The total number of records

        Raises:
            DatabaseError: If counting fails
        """
        try:
            with self.session_scope() as session:
                stmt = select(func.count()).select_from(self.model_class)
                return session.execute(stmt).scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count {self.model_name} records: {str(e)}")
            raise DatabaseError(f"Failed to count records: {str(e)}")

    def exists(self, id_value: Any) -> bool:
        """
        Check if a record exists.

        Args:
            id_value: ID of the record to check

        Returns:
            True if the record exists, False otherwise

        Raises:
            DatabaseError: If check fails
        """
        try:
            with self.session_scope() as session:
                stmt = select(self.model_class).filter_by(id=id_value)
                return session.execute(stmt).first() is not None
        except Exception as e:
            logger.error(f"Failed to check existence of {self.model_name} with ID {id_value}: {str(e)}")
            raise DatabaseError(f"Failed to check record existence: {str(e)}")

    def filter_by(self, **kwargs) -> List[T]:
        """
        Filter records by exact attribute matches.

        Args:
            **kwargs: Field name and value pairs for filtering

        Returns:
            List of matching records

        Raises:
            DatabaseError: If filtering fails
        """
        try:
            with self.session_scope() as session:
                stmt = select(self.model_class).filter_by(**kwargs)
                result = session.execute(stmt).scalars().all()
                return list(result)
        except Exception as e:
            logger.error(f"Failed to filter {self.model_name} records: {str(e)}")
            raise DatabaseError(f"Failed to filter records: {str(e)}")

    def search(self, search_term: str, columns: List[str]) -> List[T]:
        """
        Search for records matching a search term in specified columns.

        Args:
            search_term: Search term to look for
            columns: List of column names to search in

        Returns:
            List of matching records

        Raises:
            DatabaseError: If search fails
        """
        try:
            with self.session_scope() as session:
                filters = []
                for column_name in columns:
                    if hasattr(self.model_class, column_name):
                        column = getattr(self.model_class, column_name)
                        filters.append(column.ilike(f"%{search_term}%"))

                if not filters:
                    logger.warning(f"No searchable columns found for {self.model_name}")
                    return []

                stmt = select(self.model_class).filter(or_(*filters))
                result = session.execute(stmt).scalars().all()
                return list(result)
        except Exception as e:
            logger.error(f"Failed to search {self.model_name} records: {str(e)}")
            raise DatabaseError(f"Failed to search records: {str(e)}")