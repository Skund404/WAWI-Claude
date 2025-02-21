# File: database/sqlalchemy/session.py
# Purpose: Centralized database session management

import os
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

from .config import get_database_url
from ..utils.error_handling import DatabaseError


def init_database(db_url: Optional[str] = None):
    """
    Initialize the database, creating it if it doesn't exist.

    Args:
        db_url: Optional database URL (uses default if not provided)
    """
    try:
        # Use provided or default database URL
        url = db_url or get_database_url()

        # Create database if it doesn't exist
        if not database_exists(url):
            create_database(url)

        # Create engine
        engine = create_engine(url, poolclass=NullPool)

        # Import and create all tables
        from .models import Base
        Base.metadata.create_all(engine)
    except Exception as e:
        raise DatabaseError("Failed to initialize database", str(e))


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.

    Provides a transactional scope for database operations.
    Automatically handles session creation, commit, and rollback.

    Yields:
        SQLAlchemy session object

    Raises:
        DatabaseError: If session management fails
    """
    # Use global session factory or create a new one
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise DatabaseError("Database session error", str(e))
    finally:
        session.close()


def get_session_factory():
    """
    Get a thread-local scoped session factory.

    Returns:
        Scoped session factory
    """
    # Create engine
    engine = create_engine(
        get_database_url(),
        poolclass=NullPool  # Disable connection pooling for better thread safety
    )

    # Create session factory
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)


def close_all_sessions():
    """
    Close all active database sessions.
    Useful for cleanup and testing.
    """
    from sqlalchemy.orm import close_all_sessions
    close_all_sessions()