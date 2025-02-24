# Relative path: store_management/database/sqlalchemy/session.py

"""
Database Session Management Module

Provides utilities for managing database sessions and connections.
"""

import contextlib
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from config.settings import get_database_path
from utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Create engine with connection pooling disabled for better resource management
engine = create_engine(
    f'sqlite:///{get_database_path()}',
    connect_args={'check_same_thread': False},
    poolclass=NullPool
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextlib.contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Yields:
        Session: A database session that will be rolled back if an exception occurs.

    Raises:
        Exception: Any database-related exceptions.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """
    Initialize the database, creating all tables defined in the models.
    """
    try:
        from database.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def drop_database():
    """
    Drop all tables in the database.

    Warning: This will delete all data!
    """
    try:
        from database.models import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database: {e}")
        raise
