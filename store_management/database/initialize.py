# database/initialize.py
"""
Database initialization module for the leatherworking store management system.

This module handles the initialization of the SQLAlchemy engine and session factory.
"""

import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import Any, Optional, Tuple
from sqlalchemy.exc import NoReferencedTableError

from database.models.base import Base

# Configure logger
logger = logging.getLogger(__name__)


def initialize_database(database_url: Optional[str] = None) -> Tuple[Any, Any]:
    """
    Initialize the database with the given connection URL.

    Args:
        database_url (str, optional): Database connection URL.
            Defaults to SQLite local file for leatherworking store.

    Returns:
        tuple: Engine and scoped session factory
    """
    if database_url is None:
        # Default to SQLite local file if no URL provided
        database_url = 'sqlite:///leatherworking_store.db'

    logger.info(f"Initializing database with URL: {database_url}")

    # Create engine with appropriate configuration
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for debugging SQL queries
        future=True,  # Use SQLAlchemy 2.0 behavior
        connect_args={"check_same_thread": False} if database_url.startswith('sqlite') else {}
    )

    # Create session factory
    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False
    )

    # Create scoped session for thread safety
    scoped_session_factory = scoped_session(session_factory)

    # Create tables if they don't exist
    try:
        # Import all models to ensure they're registered with Base.metadata
        import database.models

        # Create tables in the correct order
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except NoReferencedTableError as e:
        logger.error(f"Error creating tables: {str(e)}")
        # Try to create tables individually in a controlled order
        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables: {existing_tables}")

            # Create tables in a specific order to handle dependencies
            for table in [
                'supplier', 'storage', 'material', 'material_transaction',
                'part', 'leather', 'hardware', 'product', 'pattern',
                'project', 'project_component', 'order', 'order_item',
                'shopping_list', 'shopping_list_item'
            ]:
                if table not in existing_tables and hasattr(Base.metadata.tables, table):
                    Base.metadata.tables[table].create(engine)
                    logger.info(f"Created table '{table}'")

            logger.info("Database tables created in controlled order")
        except Exception as e2:
            logger.error(f"Error in controlled table creation: {str(e2)}")
            raise

    logger.info("Database initialized successfully")

    return engine, scoped_session_factory


# Global session variable
_session_factory = None


def get_session():
    """
    Get a database session.

    Returns:
        Session: Database session

    Raises:
        RuntimeError: If database is not initialized
    """
    global _session_factory
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _session_factory()