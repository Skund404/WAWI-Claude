# Relative path: store_management/database/sqlalchemy/manager.py

"""
Comprehensive Database Manager using SQLAlchemy ORM for store management system.
"""

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import (
    TypeVar,
    Type,
    Optional,
    List,
    Dict,
    Any,
    Union
)

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, Session, inspect
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService
)

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """
    Custom exception for database-related errors.
    Provides more detailed error information for database operations.
    """
    pass


class BaseManager:
    """
    Base manager class with common session and logging methods.
    Provides fundamental database session management capabilities.
    """

    def __init__(self, session_factory):
        """
        Initialize base manager with session factory.

        Args:
            session_factory: SQLAlchemy session factory for creating database sessions
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields a database session that will be automatically committed if no 
        exceptions occur, or rolled back if an exception is raised.

        Yields:
            Session: A database session

        Raises:
            Exception: Any database-related exceptions
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database transaction error: {e}")
            raise
        finally:
            session.close()


class DatabaseManagerSQLAlchemy:
    """
    Comprehensive database manager using SQLAlchemy ORM.
    Provides advanced database operations with robust error handling.
    """

    def __init__(self, database_url: str):
        """
        Initialize database manager with database URL.

        Args:
            database_url (str): SQLAlchemy database connection URL

        Raises:
            DatabaseError: If database initialization fails
        """
        try:
            self.engine = create_engine(database_url)
            self.SessionFactory = sessionmaker(bind=self.engine)
            self._session: Optional[Session] = None
        except Exception as e:
            error_msg = f'Failed to initialize database: {str(e)}'
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    @property
    def session(self) -> Session:
        """
        Get current session or create a new one.

        Returns:
            Session: Active SQLAlchemy session
        """
        if self._session is None:
            self._session = self.SessionFactory()
        return self._session

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: A database session that will be committed or rolled back

        Raises:
            DatabaseError: If transaction fails
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f'Transaction failed: {str(e)}')
        finally:
            session.close()

    def get_model_columns(self, model) -> List[str]:
        """
        Get column names for a specific model.

        Args:
            model: SQLAlchemy model class

        Returns:
            List[str]: List of column names
        """
        return [column.key for column in inspect(model).columns]

    def add_record(self, model, data: Dict[str, Any]) -> Any:
        """
        Add a new record to the database.

        Args:
            model: SQLAlchemy model class
            data (Dict[str, Any]): Record data

        Returns:
            Newly created record

        Raises:
            DatabaseError: If record creation fails
        """
        try:
            with self.session_scope() as session:
                record = model(**data)
                session.add(record)
                session.commit()
                session.refresh(record)
                return record
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to add record: {str(e)}')

    def update_record(self, model, record_id: int, data: Dict[str, Any]) -> Optional[Any]:
        """
        Update an existing record.

        Args:
            model: SQLAlchemy model class
            record_id (int): Record ID
            data (Dict[str, Any]): Updated data

        Returns:
            Updated record or None

        Raises:
            DatabaseError: If record update fails
        """
        try:
            with self.session_scope() as session:
                record = session.query(model).get(record_id)
                if record:
                    for key, value in data.items():
                        setattr(record, key, value)
                    record.modified_at = datetime.utcnow()
                    session.commit()
                    session.refresh(record)
                    return record
                return None
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to update record: {str(e)}')

    def delete_record(self, model, record_id: int) -> bool:
        """
        Delete a record from the database.

        Args:
            model: SQLAlchemy model class
            record_id (int): Record ID

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            DatabaseError: If record deletion fails
        """
        try:
            with self.session_scope() as session:
                record = session.query(model).get(record_id)
                if record:
                    session.delete(record)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to delete record: {str(e)}')

    def get_record(self, model, record_id: int) -> Optional[Any]:
        """
        Get a single record by ID.

        Args:
            model: SQLAlchemy model class
            record_id (int): Record ID

        Returns:
            Record or None

        Raises:
            DatabaseError: If record retrieval fails
        """
        try:
            with self.session_scope() as session:
                return session.query(model).get(record_id)
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to get record: {str(e)}')

    def get_all_records(self, model, **filters) -> List[Any]:
        """
        Get all records of a model, optionally filtered.

        Args:
            model: SQLAlchemy model class
            **filters: Optional filter conditions

        Returns:
            List of records

        Raises:
            DatabaseError: If record retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = session.query(model)
                if filters:
                    query = query.filter_by(**filters)
                return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to get records: {str(e)}')

    def search_records(self, model, search_term: str, *fields) -> List[Any]:
        """
        Search for records across specified fields.

        Args:
            model: SQLAlchemy model class
            search_term (str): Term to search for
            *fields: Fields to search in

        Returns:
            List of matching records

        Raises:
            DatabaseError: If record search fails
        """
        try:
            with self.session_scope() as session:
                query = session.query(model)
                conditions = [
                    getattr(model, field).ilike(f'%{search_term}%')
                    for field in fields
                ]
                return query.filter(or_(*conditions)).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to search records: {str(e)}')

    def bulk_update(self, model, updates: List[Dict[str, Any]]) -> bool:
        """
        Perform bulk updates on records.

        Args:
            model: SQLAlchemy model class
            updates (List[Dict]): List of update dictionaries

        Returns:
            bool: True if bulk update was successful

        Raises:
            DatabaseError: If bulk update fails
        """
        try:
            with self.session_scope() as session:
                for update in updates:
                    record_id = update.pop('id', None)
                    if record_id:
                        record = session.query(model).get(record_id)
                        if record:
                            for key, value in update.items():
                                setattr(record, key, value)
                            record.modified_at = datetime.utcnow()
                session.commit()
                return True
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to perform bulk update: {str(e)}')

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Any]:
        """
        Execute a raw SQL query.

        Args:
            query (str): SQL query string
            params (Optional[tuple]): Query parameters

        Returns:
            List of query results

        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.session_scope() as session:
                result = session.execute(query, params or {})
                return result.fetchall()
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to execute query: {str(e)}')