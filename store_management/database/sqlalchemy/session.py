# database/sqlalchemy/session.py

import os
from contextlib import contextmanager
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from store_management.database.sqlalchemy.base import Base
from store_management.utils.error_handling import DatabaseError

# Default database URL
DEFAULT_DATABASE_URL = "sqlite:///store_management.db"

# Global variables for engine and session factory
DATABASE_URL = None
engine = None
session_factory = None


def init_database(db_url: Optional[str] = None):
    """Initialize the database, creating it if it doesn't exist.

    Args:
        db_url: Optional database URL (uses default if not provided)

    Raises:
        DatabaseError: If database initialization fails
    """
    global DATABASE_URL, engine, session_factory

    try:
        # Use provided URL or default
        DATABASE_URL = db_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

        # Create engine
        engine = create_engine(
            DATABASE_URL,
            echo=False,  # Set to True for SQL logging
            pool_pre_ping=True,  # Check connection before using it
            poolclass=NullPool if DATABASE_URL.startswith("sqlite") else None
        )

        # Create database if it doesn't exist
        if not database_exists(engine.url):
            create_database(engine.url)

        # Create tables if they don't exist
        Base.metadata.create_all(engine)

        # Create session factory
        session_factory = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        ))

    except Exception as e:
        raise DatabaseError(f"Failed to initialize database: {str(e)}")


@contextmanager
def get_db_session():
    """Context manager for database sessions.

    Provides a transactional scope for database operations.
    Automatically handles session creation, commit, and rollback.

    Yields:
        SQLAlchemy session object

    Raises:
        DatabaseError: If session management fails
    """
    # Ensure database is initialized
    if session_factory is None:
        init_database()

    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise DatabaseError(f"Database session error: {str(e)}")
    finally:
        session.close()


def close_all_sessions():
    """Close all active database sessions.

    Useful for cleanup and testing.
    """
    if session_factory is not None:
        session_factory.remove()