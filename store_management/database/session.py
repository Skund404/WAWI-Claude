# File: store_management/database/session.py
import os
import logging
from typing import Optional

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database

from ..config.settings import get_database_path
from ..utils.error_handling import DatabaseError

# Configure logging
logger = logging.getLogger(__name__)

# Global session factory and engine
engine = None
SessionLocal = None


def init_database(db_url: Optional[str] = None) -> None:
    """
    Initialize the database, creating it if it doesn't exist.

    Args:
        db_url: Optional database URL (uses default if not provided)

    Raises:
        DatabaseError: If database initialization fails
    """
    global engine, SessionLocal

    try:
        # Use default database path if no URL is provided
        if not db_url:
            db_path = get_database_path()
            db_url = f'sqlite:///{db_path}'

        # Ensure database exists
        if not database_exists(db_url):
            logger.info(f"Creating database at {db_url}")
            create_database(db_url)

        # Create engine
        engine = create_engine(
            db_url,
            echo=False,  # Set to True for SQLAlchemy logging
            connect_args={'check_same_thread': False}  # Important for SQLite
        )

        # Create session factory
        SessionLocal = scoped_session(sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False
        ))

        logger.info("Database initialized successfully")

    except Exception as e:
        # Log the full error
        logger.error(f"Database initialization failed: {e}", exc_info=True)

        # Raise a custom database error
        raise DatabaseError("Failed to initialize database", str(e))


def get_db_session():
    """
    Provide a database session.

    Yields:
        SQLAlchemy session object

    Raises:
        DatabaseError: If session creation fails
    """
    if SessionLocal is None:
        raise DatabaseError("Database not initialized", "Call init_database() first")

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def close_db_session():
    """
    Close all database sessions.
    """
    if SessionLocal:
        SessionLocal.remove()
        logger.info("Database sessions closed")