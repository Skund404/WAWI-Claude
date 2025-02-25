# Relative path: store_management/database/sqlalchemy/session.py

"""
Database Session Management Module

Provides comprehensive utilities for managing database sessions,
connections, and initialization.
"""

import contextlib
import logging
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from config.settings import get_database_path
from utils.logger import get_logger

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """
    Comprehensive database session management utility.

    Handles database engine creation, session management,
    and provides context managers for database operations.
    """

    def __init__(
            self,
            database_path: Optional[str] = None,
            connect_args: Optional[dict] = None,
            poolclass: Optional[Any] = NullPool
    ):
        """
        Initialize database session manager.

        Args:
            database_path (Optional[str]): Path to the database file
            connect_args (Optional[dict]): Additional connection arguments
            poolclass (Optional[Any]): SQLAlchemy connection pooling class
        """
        # Use provided database path or get default
        self.database_path = database_path or get_database_path()

        # Default connection arguments
        default_connect_args = {'check_same_thread': False}
        if connect_args:
            default_connect_args.update(connect_args)

        try:
            # Create SQLAlchemy engine
            self.engine = create_engine(
                f'sqlite:///{self.database_path}',
                connect_args=default_connect_args,
                poolclass=poolclass
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logger.info(f"Database session manager initialized for {self.database_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database session manager: {e}")
            raise

    @contextlib.contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: A database session that will be rolled back if an exception occurs.

        Raises:
            Exception: Any database-related exceptions.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def init_database(self, base_class=None):
        """
        Initialize the database, creating all tables defined in the models.

        Args:
            base_class (Optional[Any]): SQLAlchemy declarative base class
        """
        try:
            if base_class is None:
                from database.models import Base
                base_class = Base

            base_class.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def drop_database(self, base_class=None):
        """
        Drop all tables in the database.

        Warning: This will delete all data!

        Args:
            base_class (Optional[Any]): SQLAlchemy declarative base class
        """
        try:
            if base_class is None:
                from database.models import Base
                base_class = Base

            base_class.metadata.drop_all(bind=self.engine)
            logger.info("All database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
            raise


# Create a default session manager
default_session_manager = DatabaseSessionManager()

# Expose commonly used methods
get_db_session = default_session_manager.get_session
init_database = default_session_manager.init_database
drop_database = default_session_manager.drop_database