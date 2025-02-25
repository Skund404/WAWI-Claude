# session_manager.py
# Relative path: database/session_manager.py

import logging
from contextlib import contextmanager
from typing import (
    Any, 
    Callable, 
    Generic, 
    Iterator, 
    Optional, 
    TypeVar
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import (
    MaterialService, 
    ProjectService, 
    InventoryService, 
    OrderService
)
from exceptions import TransactionError

# Type variable for generic return type
T = TypeVar('T')

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session manager for SQLAlchemy database operations.

    Provides context managers and utility methods for managing database sessions
    with robust error handling and transaction management.

    Attributes:
        session_factory (Callable[[], Session]): Function to create database sessions
    """

    @inject(MaterialService)
    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        """
        Initialize the SessionManager.

        Args:
            session_factory (Optional[Callable[[], Session]], optional): 
                Function that returns a new SQLAlchemy session. 
                Defaults to None, which will use a default session factory.
        """
        from database.sqlalchemy.session import get_db_session

        self.session_factory = session_factory or get_db_session

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """
        Provide a transactional scope around a series of operations.

        This context manager handles session creation, commits, and rollbacks,
        ensuring proper resource management and error handling.

        Yields:
            Session: A SQLAlchemy database session

        Raises:
            TransactionError: If a database transaction error occurs
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f'Database transaction error: {str(e)}')
            raise TransactionError(operation='session_scope', details=str(e)) from e
        finally:
            session.close()

    @contextmanager
    def read_only_session_scope(self) -> Iterator[Session]:
        """
        Provide a read-only transactional scope.

        This context manager is useful for operations that don't modify the database,
        such as querying or retrieving data.

        Yields:
            Session: A read-only SQLAlchemy database session

        Raises:
            TransactionError: If a database read transaction error occurs
        """
        session = self.session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f'Database read transaction error: {str(e)}')
            raise TransactionError(
                operation='read_only_session_scope', 
                details=str(e)
            ) from e
        finally:
            session.close()

    def execute_in_transaction(self, operation: Callable[[Session], T]) -> T:
        """
        Execute an operation within a database transaction.

        Args:
            operation (Callable[[Session], T]): Function that takes a session 
                and returns a result

        Returns:
            T: The result of the operation

        Raises:
            TransactionError: If a database transaction error occurs
        """
        with self.session_scope() as session:
            return operation(session)

    def execute_read_only(self, operation: Callable[[Session], T]) -> T:
        """
        Execute a read-only operation.

        Args:
            operation (Callable[[Session], T]): Function that takes a session 
                and returns a result

        Returns:
            T: The result of the operation

        Raises:
            TransactionError: If a database read transaction error occurs
        """
        with self.read_only_session_scope() as session:
            return operation(session)

    def execute_bulk_operation(self, operation: Callable[[Session], T]) -> T:
        """
        Execute a bulk operation in a transaction.

        This method is useful for operations that modify many records efficiently.

        Args:
            operation (Callable[[Session], T]): Function that takes a session 
                and returns a result

        Returns:
            T: The result of the operation

        Raises:
            TransactionError: If a database transaction error occurs
        """
        with self.session_scope() as session:
            # Configure session for bulk operations
            session.bulk_insert_mappings = True
            session.bulk_save_objects = True
            return operation(session)


# Create a default session manager instance
session_manager = SessionManager()