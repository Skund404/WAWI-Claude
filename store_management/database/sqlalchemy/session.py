# database/sqlalchemy/session.py
"""
Database session management module.

This module provides functionality for creating and managing database sessions,
including session factories, connection pools, and database initialization.
"""

import contextlib
import logging
from typing import Any, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from config.settings import get_database_path
from database.models.base import Base
from utils.logger import get_logger

# Configure module logger
logger = get_logger(__name__)

# Global database engine and session factory
_engine = None
_SessionFactory = None


def init_engine(database_url=None, echo=False, poolclass=NullPool):
    """
    Initialize the database engine.

    Args:
        database_url (str, optional): Database connection URL. If None, uses the default path.
        echo (bool, optional): Whether to echo SQL statements. Defaults to False.
        poolclass (Any, optional): SQLAlchemy connection pool class. Defaults to NullPool.

    Returns:
        The SQLAlchemy engine instance.
    """
    global _engine
    if _engine is None:
        if database_url is None:
            database_path = get_database_path()
            database_url = f"sqlite:///{database_path}"

        logger.info(f"Initializing database engine with URL: {database_url}")
        _engine = create_engine(
            database_url,
            echo=echo,
            poolclass=poolclass,
            connect_args={"check_same_thread": False}  # For SQLite
        )

    return _engine


def get_engine():
    """
    Get the SQLAlchemy engine.

    Returns:
        The SQLAlchemy engine.

    Raises:
        RuntimeError: If the database has not been initialized.
    """
    global _engine
    if _engine is None:
        raise RuntimeError("Database engine has not been initialized. Call init_engine() first.")
    return _engine


def init_session_factory(engine=None):
    """
    Initialize the session factory.

    Args:
        engine: SQLAlchemy engine, if None uses the global engine

    Returns:
        SQLAlchemy sessionmaker instance.
    """
    global _SessionFactory
    if _SessionFactory is None:
        if engine is None:
            engine = init_engine()

        logger.debug("Creating session factory")
        _SessionFactory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

    return _SessionFactory


def get_db_session() -> Session:
    """
    Get a database session.

    Returns:
        Session: A new SQLAlchemy session.

    Raises:
        RuntimeError: If the session factory has not been initialized.
    """
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = init_session_factory()

    return _SessionFactory()


@contextlib.contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Yields:
        Session: SQLAlchemy session.
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Session error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseSessionManager:
    """
    Manager class for database sessions.

    Provides methods for initializing and working with the database,
    including creating the schema and managing sessions.
    """

    def __init__(
            self,
            database_url: Optional[str] = None,
            echo: bool = False,
            poolclass: Optional[Any] = NullPool
    ):
        """
        Initialize the database session manager.

        Args:
            database_url: Database URL, if None uses the default path
            echo: Whether to echo SQL statements
            poolclass: SQLAlchemy connection pool class
        """
        self.database_url = database_url
        self.echo = echo
        self.poolclass = poolclass
        self.engine = init_engine(database_url, echo, poolclass)
        self.session_factory = init_session_factory(self.engine)
        logger.info("DatabaseSessionManager initialized")

    def init_database(self, base_class=None):
        """
        Initialize the database, creating all tables defined in the models.

        Args:
            base_class (Optional[Any]): SQLAlchemy declarative base class
        """
        base_class = base_class or Base
        logger.info("Creating database schema")
        base_class.metadata.create_all(self.engine)
        logger.info("Database schema created successfully")

    def drop_database(self, base_class=None):
        """
        Drop all tables in the database.

        Warning: This will delete all data!

        Args:
            base_class (Optional[Any]): SQLAlchemy declarative base class
        """
        base_class = base_class or Base
        logger.warning("Dropping all database tables!")
        base_class.metadata.drop_all(self.engine)
        logger.info("Database tables dropped successfully")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session
        """
        return self.session_factory()

    @contextlib.contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: SQLAlchemy session.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Session error: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()