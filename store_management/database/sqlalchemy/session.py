# database/sqlalchemy/session.py

"""
Database session management.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import Engine
from typing import Optional

from ..models.base import Base
from .config import get_database_url

logger = logging.getLogger(__name__)

# Global session factory
_session_factory = None
_engine = None


def init_database() -> Engine:
    """
    Initialize database engine and session factory.

    Returns:
        SQLAlchemy engine instance
    """
    global _session_factory, _engine

    try:
        # Get database URL from config
        db_url = get_database_url()
        logger.debug(f"Initializing database with URL: {db_url}")

        # Create engine
        _engine = create_engine(
            db_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600  # Recycle connections after 1 hour
        )

        # Create session factory
        session_factory = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False
        )

        # Create scoped session factory
        _session_factory = scoped_session(session_factory)

        return _engine

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db_session():
    """
    Get a database session.

    Returns:
        Scoped session instance

    Raises:
        RuntimeError: If database is not initialized
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _session_factory()


def close_db_session() -> None:
    """Close all sessions and clean up."""
    if _session_factory is not None:
        _session_factory.remove()