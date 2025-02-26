# Path: utils/database/database_manager.py

"""
Database Manager for the Leatherworking Store Management Application.

This module provides a centralized database management utility
with comprehensive error handling and logging.
"""

import logging
import os
from typing import Optional, Dict, Any, Union

import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from config.settings import get_database_path
from database.models.base import Base
from utils.logger import get_logger


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

            # Create SQLAlchemy engine
            self._engine = sqlalchemy.create_engine(
                f'sqlite:///{self._db_path}',
                echo=echo,
                connect_args={'check_same_thread': False}
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

    def get_session(self) -> Session:
        """
        Provide a new database session.

        Returns:
            Session: A new SQLAlchemy database session

        Raises:
            OperationalError: If session creation fails
        """
        try:
            return self._session_factory()
        except OperationalError as e:
            self._logger.error(f"Failed to create database session: {e}")
            raise

    def execute_query(self,
                      query_func,
                      *args,
                      **kwargs) -> Any:
        """
        Execute a database query within a session.

        Args:
            query_func (Callable): Function to execute with a session
            *args: Positional arguments for the query function
            **kwargs: Keyword arguments for the query function

        Returns:
            Any: Result of the query execution

        Raises:
            Exception: If query execution fails
        """
        session = None
        try:
            session = self.get_session()
            result = query_func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            if session:
                session.rollback()
            self._logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if session:
                session.close()

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

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retrieve basic statistics about the database.

        Returns:
            Dict[str, Any]: Database statistics
        """
        try:
            with self.get_session() as session:
                stats = {}
                for table in Base.metadata.tables:
                    count = session.query(Base.metadata.tables[table]).count()
                    stats[table] = count
                return stats
        except Exception as e:
            self._logger.error(f"Failed to retrieve database stats: {e}")
            return {}


# Create a singleton instance for dependency injection
database_manager = DatabaseManager()