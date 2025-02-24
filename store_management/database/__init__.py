# Path: database/__init__.py

import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Import Base from models to ensure proper initialization
from .models.base import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database(database_url: str) -> Optional[Session]:
    """
    Initialize the database connection and return a session factory.

    Args:
        database_url (str): The database connection URL

    Returns:
        Optional[Session]: A SQLAlchemy session factory or None if initialization fails
    """
    try:
        # Create engine
        engine = create_engine(database_url, echo=False)

        # Create all tables defined in Base
        Base.metadata.create_all(engine)

        # Create and return session factory
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

        return SessionLocal

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return None


def get_db() -> Session:
    """
    Provide a database session.

    Returns:
        Session: A SQLAlchemy database session
    """
    try:
        # This assumes init_database has been called earlier
        SessionLocal = init_database('sqlite:///store_management.db')
        if SessionLocal:
            return SessionLocal()
        raise RuntimeError("Database session could not be created")
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        raise


# Initialize database on import
try:
    init_database('sqlite:///store_management.db')
except Exception as e:
    logger.error(f"Critical database initialization error: {e}")