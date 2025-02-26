# Path: database/initialize.py

"""
Enhanced Database Initialization Module for Store Management Application.

Provides comprehensive database setup using SQLAlchemy ORM with robust path handling.
"""

import os
import sys
import logging
from typing import Optional, Union

import sqlalchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from config.settings import get_database_path

# Configure logging
logger = logging.getLogger(__name__)

# Global variables for session management
_engine = None
_SessionFactory = None


def _ensure_database_directory(db_path: str) -> str:
    """
    Ensure the database directory exists with proper permissions.

    Args:
        db_path (str): Path to the database file

    Returns:
        str: Absolute, normalized path to the database file

    Raises:
        PermissionError: If unable to create or access the directory
        OSError: If there are file system issues
    """
    try:
        # Normalize and expand the path
        abs_path = os.path.abspath(os.path.normpath(db_path))
        directory = os.path.dirname(abs_path)

        # Create directory with full read/write permissions
        os.makedirs(directory, mode=0o755, exist_ok=True)

        # Verify directory permissions
        if not os.access(directory, os.W_OK):
            raise PermissionError(f"No write permission for directory: {directory}")

        return abs_path

    except (PermissionError, OSError) as e:
        logger.error(f"Failed to prepare database directory: {e}")
        raise


def _generate_database_url(db_path: str) -> str:
    """
    Generate a SQLAlchemy-compatible database URL.

    Args:
        db_path (str): Path to the database file

    Returns:
        str: SQLAlchemy-compatible database URL
    """
    # Escape backslashes for Windows paths
    escaped_path = db_path.replace('\\', '/')
    return f'sqlite:///{escaped_path}'


def initialize_database(
        db_path: Optional[Union[str, os.PathLike]] = None,
        echo: bool = False
) -> sqlalchemy.engine.base.Engine:
    """
    Initialize the database with comprehensive setup and error handling.

    Args:
        db_path (Optional[Union[str, os.PathLike]]): Custom database path.
                                                     If None, uses default path.
        echo (bool, optional): Enable SQLAlchemy query logging. Defaults to False.

    Returns:
        sqlalchemy.engine.base.Engine: Initialized SQLAlchemy engine

    Raises:
        SQLAlchemyError: If database initialization fails
        PermissionError: If unable to access database directory
    """
    global _engine, _SessionFactory

    try:
        # Use provided path or get default
        if db_path is None:
            db_path = get_database_path()

        # Ensure directory exists and is accessible
        sanitized_path = _ensure_database_directory(str(db_path))

        # Generate SQLAlchemy-compatible URL
        database_url = _generate_database_url(sanitized_path)

        logger.info(f"Initializing database with URL: {database_url}")

        # Create SQLAlchemy engine with comprehensive configuration
        _engine = create_engine(
            database_url,
            echo=echo,
            connect_args={
                'check_same_thread': False,
                'timeout': 30  # Increased connection timeout
            }
        )

        # Create session factory
        _SessionFactory = sessionmaker(bind=_engine)

        # Verify database connectivity
        try:
            # Attempt to connect and close immediately
            with _engine.connect() as connection:
                connection.close()
        except Exception as conn_error:
            logger.error(f"Database connection test failed: {conn_error}")
            raise

        logger.info("Database initialized successfully")
        return _engine

    except (SQLAlchemyError, PermissionError, OSError) as e:
        logger.error(f"Database initialization failed: {e}")

        # Provide more context for debugging
        logger.error(f"Database path attempted: {db_path}")
        logger.error(f"Current working directory: {os.getcwd()}")

        # Additional system information for troubleshooting
        logger.error(f"Python version: {sys.version}")
        logger.error(f"Platform: {sys.platform}")

        raise


def get_db_session() -> Session:
    """
    Create and return a new database session.

    Returns:
        Session: A new SQLAlchemy database session

    Raises:
        RuntimeError: If database is not initialized
    """
    global _engine, _SessionFactory

    try:
        # Ensure database is initialized
        if _engine is None:
            initialize_database()

        # Create and return a new session
        return _SessionFactory()

    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise RuntimeError(f"Database session creation failed: {e}")


def create_session_factory(engine=None):
    """
    Create a session factory for database interactions.

    Args:
        engine (Optional[sqlalchemy.engine.base.Engine]): SQLAlchemy engine.
                                                          If None, uses global engine.

    Returns:
        scoped_session: A scoped session factory
    """
    global _engine

    try:
        # Use provided engine or global engine
        if engine is None:
            if _engine is None:
                initialize_database()
            engine = _engine

        # Create scoped session factory
        session_factory = sessionmaker(bind=engine)
        return scoped_session(session_factory)

    except Exception as e:
        logger.error(f"Failed to create session factory: {e}")
        raise


def verify_database_schema(session: Optional[Session] = None):
    """
    Verify the database schema and table structures.

    Args:
        session (Optional[Session]): SQLAlchemy session.
                                     If None, creates a new session.

    Returns:
        Dict[str, bool]: Verification results for each table
    """
    try:
        # Use provided session or create a new one
        if session is None:
            session = get_db_session()

        from database.models.base import Base

        # Get all table names from metadata
        table_names = Base.metadata.tables.keys()

        # Verify each table
        verification_results = {}
        for table_name in table_names:
            try:
                # Attempt to count records to verify table exists
                count = session.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                verification_results[table_name] = True
            except Exception:
                verification_results[table_name] = False
                logger.warning(f"Table {table_name} not found or inaccessible")

        return verification_results

    except Exception as e:
        logger.error(f"Database schema verification failed: {e}")
        raise
    finally:
        if session:
            session.close()