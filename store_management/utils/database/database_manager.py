# Path: utils/database/database_manager.py

"""
Database Manager for the Leatherworking Store Management Application.

This module provides a centralized database management utility
with comprehensive error handling and logging.
"""

import logging
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, Union, Callable, Generator, TypeVar

import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import NullPool

from config.settings import get_database_path
from database.models.base import Base
from utils.logger import get_logger

# Type variable for query function return type
T = TypeVar('T')

class DatabaseManager:
    """
    A comprehensive database management utility for the leatherworking application.

    Provides methods for database connection, session management,
    and basic database operations with robust error handling.

    Attributes:
        _engine (sqlalchemy.engine.base.Engine): SQLAlchemy database engine
        _session_factory (sessionmaker): SQLAlchemy session factory
        _logger (logging.Logger): Logger instance for tracking database operations
    """

    def __init__(self,
                 database_path: Optional[str] = None,
                 echo: bool = False):
        """
        Initialize the DatabaseManager with a specific database path.

        Args:
            database_path (Optional[str]): Path to the SQLite database file.
                If None, uses the default path from settings.
            echo (bool, optional): Enable SQLAlchemy query logging. Defaults to False.

        Raises:
            RuntimeError: If database initialization fails
        """
        self._logger = get_logger(__name__)

        try:
            # Use provided path or get default database path
            self._db_path = database_path or get_database_path()

            # Ensure database directory exists
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

            # Create SQLAlchemy engine with connection pooling
            self._engine = sqlalchemy.create_engine(
                f'sqlite:///{self._db_path}',
                echo=echo,
                poolclass=NullPool,  # Disable connection pooling for SQLite
                connect_args={
                    'check_same_thread': False,  # Required for SQLite in multithreaded environments
                    'timeout': 30  # Increase connection timeout
                }
            )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )

            # Log successful initialization
            self._logger.info(f"Database Manager initialized. Database path: {self._db_path}")

        except Exception as e:
            self._logger.error(f"Failed to initialize database: {e}")
            raise RuntimeError(f"Database initialization failed: {e}")

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: A database session with commit/rollback handling

        Raises:
            Exception: If session management fails
        """
        session = None
        try:
            session = self._session_factory()
            yield session
            session.commit()
        except Exception:
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    def create_tables(self):
        """
        Create all database tables defined in the models.

        Raises:
            SQLAlchemyError: If table creation fails
        """
        try:
            Base.metadata.create_all(self._engine)
            self._logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            self._logger.error(f"Failed to create database tables: {e}")
            raise

    def drop_tables(self):
        """
        Drop all database tables.

        Caution: This will delete ALL data in the database.

        Raises:
            SQLAlchemyError: If table deletion fails
        """
        try:
            Base.metadata.drop_all(self._engine)
            self._logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            self._logger.error(f"Failed to drop database tables: {e}")
            raise

    def execute_query(self,
                      query_func: Callable[[Session], T],
                      *args,
                      **kwargs) -> T:
        """
        Execute a database query within a session.

        Args:
            query_func (Callable[[Session], T]): Function to execute with a session
            *args: Positional arguments for the query function
            **kwargs: Keyword arguments for the query function

        Returns:
            T: Result of the query execution

        Raises:
            Exception: If query execution fails
        """
        with self.session_scope() as session:
            try:
                return query_func(session, *args, **kwargs)
            except Exception as e:
                self._logger.error(f"Query execution failed: {e}")
                raise

    def backup_database(self,
                        backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the current database.

        Args:
            backup_path (Optional[str]): Path to save the backup.
                If None, generates a timestamped backup in a backup directory.

        Returns:
            str: Path to the created backup file

        Raises:
            IOError: If backup creation fails
        """
        import shutil
        from datetime import datetime

        try:
            if not backup_path:
                backup_dir = os.path.join(
                    os.path.dirname(self._db_path),
                    'backups'
                )
                os.makedirs(backup_dir, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(
                    backup_dir,
                    f'database_backup_{timestamp}.sqlite'
                )

            shutil.copy2(self._db_path, backup_path)
            self._logger.info(f"Database backed up to {backup_path}")
            return backup_path

        except Exception as e:
            self._logger.error(f"Database backup failed: {e}")
            raise IOError(f"Could not create database backup: {e}")

    def get_database_stats(self) -> Dict[str, int]:
        """
        Retrieve basic statistics about the database.

        Returns:
            Dict[str, int]: Database table record counts
        """
        try:
            with self.session_scope() as session:
                stats = {}
                for table in Base.metadata.tables:
                    try:
                        count = session.query(Base.metadata.tables[table]).count()
                        stats[table] = count
                    except Exception as table_error:
                        self._logger.warning(f"Could not count records for table {table}: {table_error}")
                        stats[table] = -1
                return stats
        except Exception as e:
            self._logger.error(f"Failed to retrieve database stats: {e}")
            return {}

    def __repr__(self) -> str:
        """
        String representation of the DatabaseManager.

        Returns:
            str: Description of the database manager
        """
        return f"DatabaseManager(path={self._db_path})"

# Create a singleton instance for dependency injection
database_manager = DatabaseManager()