from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database
from store_management.database.sqlalchemy.models.base import Base
from store_management.utils.logger import logger
import os
from typing import Optional

# Database URL configuration - keep existing code
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'store.db')}"
)

# Engine and session factory setup
engine = create_engine(DATABASE_URL, echo=False)
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)


def init_database():
    """Initialize database if it doesn't exist"""
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """Provide a transactional scope around database operations.

    Usage:
        with get_db_session() as session:
            # Perform database operations
            session.add(some_object)

    Yields:
        SQLAlchemy Session object
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()


def get_session():
    """Create and return a new database session for compatibility with existing code.

    Note: This function is provided for backward compatibility.
    New code should use get_db_session() context manager instead.

    Returns:
        SQLAlchemy Session object
    """
    logger.warning("Using deprecated get_session() - consider migrating to get_db_session()")
    return SessionLocal()