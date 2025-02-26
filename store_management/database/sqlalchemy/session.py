# database/sqlalchemy/session.py
"""
Database Session Management for SQLAlchemy.
Provides utilities for creating and managing database sessions
in the Leatherworking Store Management Application.
"""
from contextlib import contextmanager
import logging
import os
from pathlib import Path
from typing import Any, Generator, Optional

import sqlalchemy
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from config.settings import get_database_path


def init_engine(
        database_url: Optional[str] = None,
        echo: bool = False,
        poolclass: Any = NullPool
) -> sqlalchemy.engine.base.Engine:
    """
    Initialize the SQLAlchemy database engine.

    Args:
        database_url (Optional[str]): Database connection URL
        echo (bool): Whether to log SQL statements
        poolclass (Any): SQLAlchemy connection pooling class

    Returns:
        sqlalchemy.engine.base.Engine: Configured database engine
    """
    # Use default database path if no URL provided
    if database_url is None:
        database_url = f"sqlite:///{get_database_path()}"

    try:
        # Create engine with specified parameters
        engine = sqlalchemy.create_engine(
            database_url,
            echo=echo,
            poolclass=poolclass
        )
        return engine
    except Exception as e:
        logging.error(f"Error initializing database engine: {e}")
        raise


# Global variables for session management
_engine = None
_SessionLocal = None


def get_db_session() -> Session:
    """
    Get a new database session.

    Returns:
        sqlalchemy.orm.Session: A new database session

    Raises:
        RuntimeError: If database engine is not initialized
    """
    global _engine, _SessionLocal

    # Lazy initialize engine and session factory
    if _engine is None:
        _engine = init_engine()

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

    return _SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Yields:
        sqlalchemy.orm.Session: A database session with commit/rollback handling

    Raises:
        Exception: If there's an error during the database transaction
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Database transaction error: {e}")
        raise
    finally:
        session.close()