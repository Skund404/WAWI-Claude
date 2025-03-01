# database/sqlalchemy/session.py

import logging
import os
from pathlib import Path
from typing import Optional, Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Global session factory
_SESSION_FACTORY = None
DATABASE_URL = None


def get_database_url() -> str:
    """
    Get the SQLite database URL.

    Returns:
        str: SQLAlchemy database URL
    """
    from config.settings import get_database_path
    db_path = get_database_path()
    return f"sqlite:///{db_path}"


def create_session_factory(database_url: Optional[str] = None) -> Callable[[], Session]:
    """
    Create a session factory for database connections.

    Args:
        database_url (Optional[str]): Database URL for SQLAlchemy engine

    Returns:
        Callable[[], Session]: Session factory function
    """
    global _SESSION_FACTORY, DATABASE_URL

    if database_url is None:
        database_url = get_database_url()

    DATABASE_URL = database_url

    # Create the engine
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False  # Set to True for SQL query logging
    )

    # Create a configurable session factory
    factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )

    _SESSION_FACTORY = factory
    return factory


def get_db_session() -> Session:
    """
    Get a new database session.

    Returns:
        Session: A new SQLAlchemy session
    """
    global _SESSION_FACTORY

    if _SESSION_FACTORY is None:
        create_session_factory()

    return _SESSION_FACTORY()