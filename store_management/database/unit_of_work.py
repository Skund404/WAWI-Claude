# unit_of_work.py
# Relative path: database/unit_of_work.py

import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Iterator,
    Optional,
    TypeVar,
    Generic
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


class IUnitOfWork(ABC):
    """
    Interface for the Unit of Work pattern.

    Defines the methods that all unit of work implementations must provide
    to manage database transactions.
    """

    @abstractmethod
    @contextmanager
    def __enter__(self) -> 'IUnitOfWork':
        """Enter the context manager."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction."""
        pass


class SQLAlchemyUnitOfWork(IUnitOfWork, Generic[T]):
    """
    SQLAlchemy implementation of the Unit of Work pattern.

    Provides methods for transaction management using SQLAlchemy sessions,
    with support for different types of database repositories.
    """

    @inject(MaterialService)
    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        """
        Initialize a new SQLAlchemyUnitOfWork instance.

        Args:
            session_factory (Optional[Callable[[], Session]], optional): 
                Function that returns a new SQLAlchemy session. 
                Defaults to None, which will use the default session factory.
        """
        from database.sqlalchemy.session import get_db_session

        self.session_factory = session_factory or get_db_session
        self.session: Optional[Session] = None

    @contextmanager
    def __enter__(self) -> 'SQLAlchemyUnitOfWork':
        """
        Enter the context manager.

        Creates a new database session and prepares for transaction.

        Returns:
            SQLAlchemyUnitOfWork: The current unit of work instance
        """
        self.session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the context manager.

        Handles transaction commit or rollback based on exception status.

        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised
        """
        if self.session:
            try:
                if exc_type:
                    # If an exception occurred, rollback the transaction
                    self.rollback()
                else:
                    # If no exception, commit the transaction
                    self.commit()
            finally:
                # Always close the session
                self.session.close()
                self.session = None

    def commit(self) -> None:
        """
        Commit the transaction.

        Raises:
            RuntimeError: If no active session exists
            TransactionError: If commit fails
        """
        if not self.session:
            raise RuntimeError('Cannot commit - no active session')

        try:
            self.session.commit()
            logger.debug('Transaction committed successfully')
        except SQLAlchemyError as e:
            logger.error(f'Failed to commit transaction: {str(e)}')
            self.rollback()
            raise TransactionError(operation='commit', details=str(e)) from e

    def rollback(self) -> None:
        """
        Rollback the transaction.

        Raises:
            RuntimeError: If no active session exists
            TransactionError: If rollback fails
        """
        if not self.session:
            raise RuntimeError('Cannot rollback - no active session')

        try:
            self.session.rollback()
            logger.debug('Transaction rolled back')
        except SQLAlchemyError as e:
            logger.error(f'Failed to rollback transaction: {str(e)}')
            raise TransactionError(operation='rollback', details=str(e)) from e


def run_in_transaction(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run a function within a transaction.

    Args:
        func: The function to run
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function

    Raises:
        TransactionError: If transaction fails
    """
    with SQLAlchemyUnitOfWork() as uow:
        result = func(*args, **kwargs, session=uow.session)
        uow.commit()
        return result