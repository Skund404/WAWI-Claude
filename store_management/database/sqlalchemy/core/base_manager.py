# database/sqlalchemy/core/base_manager.py
"""
database/sqlalchemy/core/base_manager.py
Core database manager providing unified access patterns for database operations.
"""

from typing import Type, List, Dict, Any, Optional, TypeVar, Generic, Union, Callable
import logging
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import select, inspect, and_, or_, func
from sqlalchemy.exc import SQLAlchemyError

from utils.error_handling import DatabaseError

# Type variable for the model class
T = TypeVar('T')


class BaseManager(Generic[T]):
    """
    Comprehensive base manager for database operations.

    Provides a generic, type-safe implementation of common database operations
    with extensive error handling and transaction management.
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
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @contextmanager
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
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Database error: {str(e)}", exc_info=True)
            raise DatabaseError(f"Database operation failed: {str(e)}", str(e))
        except Exception as e:
            session.rollback()
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise e
        finally:
            session.close()

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record in the database.

        Args:
            data: Dictionary of attributes for the new record

        Returns:
            The created record

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                instance = self.model_class(**data)
                session.add(instance)
                session.flush()  # Flush to get the ID without committing
                # Refresh the instance to get any database-generated values
                session.refresh(instance)
                return instance
        except Exception as e:
            raise DatabaseError(f"Failed to create {self.model_class.__name__}", str(e))

    def get(self, id: Any) -> Optional[T]:
        """
        Retrieve a record by its primary key.

        Args:
            id: Primary key value

        Returns:
            The record if found, None otherwise

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                return session.get(self.model_class, id)
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve {self.model_class.__name__} with id {id}", str(e))

    def get_all(self, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        """
        Retrieve all records, with optional ordering and limit.

        Args:
            order_by: Optional column to order by
            limit: Optional maximum number of records to return

        Returns:
            List of records

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(self.model_class)

                if order_by:
                    # Get the actual column from the model class
                    if hasattr(self.model_class, order_by):
                        column = getattr(self.model_class, order_by)
                        query = query.order_by(column)

                if limit:
                    query = query.limit(limit)

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve all {self.model_class.__name__} records", str(e))

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record.

        Args:
            id: Primary key of the record to update
            data: Dictionary of attributes to update

        Returns:
            The updated record, or None if not found

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                instance = session.get(self.model_class, id)
                if not instance:
                    return None

                # Update the instance
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

                session.flush()
                return instance
        except Exception as e:
            raise DatabaseError(f"Failed to update {self.model_class.__name__} with id {id}", str(e))

    def delete(self, id: Any) -> bool:
        """
        Delete a record by its primary key.

        Args:
            id: Primary key of the record to delete

        Returns:
            True if deletion was successful, False if record not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.session_scope() as session:
                instance = session.get(self.model_class, id)
                if not instance:
                    return False

                session.delete(instance)
                return True
        except Exception as e:
            raise DatabaseError(f"Failed to delete {self.model_class.__name__} with id {id}", str(e))

    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists with the given criteria.

        Args:
            **kwargs: Filter criteria

        Returns:
            True if a matching record exists, False otherwise

        Raises:
            DatabaseError: If check fails
        """
        try:
            with self.session_scope() as session:
                query = select(self.model_class)

                # Add filter conditions
                conditions = []
                for key, value in kwargs.items():
                    if hasattr(self.model_class, key):
                        column = getattr(self.model_class, key)
                        conditions.append(column == value)

                if conditions:
                    query = query.where(and_(*conditions))

                result = session.execute(query.exists().select())
                return result.scalar()
        except Exception as e:
            raise DatabaseError(f"Failed to check existence of {self.model_class.__name__}", str(e))

    def count(self, **kwargs) -> int:
        """
        Count records matching the given criteria.

        Args:
            **kwargs: Filter criteria

        Returns:
            Count of matching records

        Raises:
            DatabaseError: If count fails
        """
        try:
            with self.session_scope() as session:
                query = select(func.count()).select_from(self.model_class)

                # Add filter conditions
                conditions = []
                for key, value in kwargs.items():
                    if hasattr(self.model_class, key):
                        column = getattr(self.model_class, key)
                        conditions.append(column == value)

                if conditions:
                    query = query.where(and_(*conditions))

                result = session.execute(query)
                return result.scalar()
        except Exception as e:
            raise DatabaseError(f"Failed to count {self.model_class.__name__} records", str(e))

    def filter_by(self, **kwargs) -> List[T]:
        """
        Retrieve records matching the given criteria.

        Args:
            **kwargs: Filter criteria

        Returns:
            List of matching records

        Raises:
            DatabaseError: If filtering fails
        """
        try:
            with self.session_scope() as session:
                query = select(self.model_class)

                # Add filter conditions
                conditions = []
                for key, value in kwargs.items():
                    if hasattr(self.model_class, key):
                        column = getattr(self.model_class, key)
                        conditions.append(column == value)

                if conditions:
                    query = query.where(and_(*conditions))

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to filter {self.model_class.__name__} records", str(e))

    def search(self, term: str, fields: Optional[List[str]] = None) -> List[T]:
        """
        Search for records where any of the specified fields contain the search term.

        Args:
            term: Search term
            fields: List of fields to search in (if None, searches all string fields)

        Returns:
            List of matching records

        Raises:
            DatabaseError: If search fails
        """
        try:
            with self.session_scope() as session:
                # If no fields specified, get all string fields
                if not fields:
                    mapper = inspect(self.model_class)
                    fields = [column.key for column in mapper.columns if column.type.python_type == str]

                # Build search query
                query = select(self.model_class)

                # Add search conditions
                conditions = []
                for field in fields:
                    if hasattr(self.model_class, field):
                        column = getattr(self.model_class, field)
                        conditions.append(column.ilike(f"%{term}%"))

                if conditions:
                    query = query.where(or_(*conditions))

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to search {self.model_class.__name__} records", str(e))

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in a single transaction.

        Args:
            items: List of dictionaries with record data

        Returns:
            List of created records

        Raises:
            DatabaseError: If bulk creation fails
        """
        try:
            with self.session_scope() as session:
                instances = []
                for data in items:
                    instance = self.model_class(**data)
                    session.add(instance)
                    instances.append(instance)

                session.flush()
                return instances
        except Exception as e:
            raise DatabaseError(f"Failed to bulk create {self.model_class.__name__} records", str(e))

    def bulk_update(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Update multiple records in a single transaction.

        Args:
            items: List of dictionaries with record data including ID

        Returns:
            List of updated records

        Raises:
            DatabaseError: If bulk update fails
        """
        try:
            with self.session_scope() as session:
                updated_instances = []

                for data in items:
                    # Get ID from data
                    id_attr = inspect(self.model_class).primary_key[0].name
                    id_value = data.get(id_attr)

                    if id_value is None:
                        continue

                    # Get the instance
                    instance = session.get(self.model_class, id_value)
                    if not instance:
                        continue

                    # Update the instance
                    for key, value in data.items():
                        if key != id_attr and hasattr(instance, key):
                            setattr(instance, key, value)

                    updated_instances.append(instance)

                session.flush()
                return updated_instances
        except Exception as e:
            raise DatabaseError(f"Failed to bulk update {self.model_class.__name__} records", str(e))