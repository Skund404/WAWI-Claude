# database/sqlalchemy/core/base_manager.py
"""
Core database manager providing unified access patterns for database operations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Type, Generic
from contextlib import contextmanager

from sqlalchemy import select, and_, or_, func, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from core.exceptions import DatabaseError

# Generic type variable for the model
T = TypeVar('T')


class BaseManager(Generic[T]):
    """
    Comprehensive base manager for database operations.

    Provides a generic, type-safe implementation of common database operations
    with extensive error handling and transaction management.
    """

    @inject(MaterialService)
    def __init__(self, model_class: Type[T], session_factory: Callable[[], Session]):
        """
        Initialize the base manager with a model class and session factory.

        Args:
            model_class (Type[T]): The SQLAlchemy model class this manager operates on
            session_factory (Callable[[], Session]): A callable that returns a database session
        """
        self.model_class = model_class
        self.session_factory = session_factory
        self.logger = logging.getLogger(f'{self.__class__.__name__}')

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
            self.logger.error(f'Database error: {str(e)}', exc_info=True)
            raise DatabaseError(f'Database operation failed: {str(e)}', str(e))
        except Exception as e:
            session.rollback()
            self.logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            raise
        finally:
            session.close()

    @inject(MaterialService)
    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record in the database.

        Args:
            data (Dict[str, Any]): Dictionary of attributes for the new record

        Returns: