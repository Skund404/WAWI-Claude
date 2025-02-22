# Path: database/sqlalchemy/config.py
import os
import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config.settings import get_database_path


def get_database_url(config: Optional[dict] = None) -> str:
    """
    Generate the database URL based on configuration or default settings.

    Args:
        config (dict, optional): Database configuration dictionary

    Returns:
        str: SQLAlchemy database connection URL
    """
    if config:
        # Use provided configuration if available
        db_type = config.get('type', 'sqlite')
        host = config.get('host', '')
        port = config.get('port', '')
        username = config.get('username', '')
        password = config.get('password', '')
        database = config.get('database', '')
    else:
        # Default to SQLite if no config provided
        db_type = 'sqlite'
        database = get_database_path()

    # Construct database URL based on type
    if db_type == 'sqlite':
        return f'sqlite:///{database}'
    elif db_type == 'postgresql':
        return f'postgresql://{username}:{password}@{host}:{port}/{database}'
    elif db_type == 'mysql':
        return f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


class DatabaseConfig:
    """
    Singleton class for managing database configuration and connections.
    """
    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        """
        Implement singleton pattern for database configuration.

        Returns:
            DatabaseConfig: Singleton instance
        """
        if not cls._instance:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize database engine and session factory.
        """
        try:
            # Get database URL and create engine
            db_url = get_database_url()
            self._engine = create_engine(
                db_url,
                echo=False,  # Set to True for SQL query logging
                pool_pre_ping=True,  # Test connections before using
                pool_recycle=3600  # Recycle connections every hour
            )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
        except SQLAlchemyError as e:
            logging.error(f"Database initialization error: {e}")
            raise

    def get_engine(self):
        """
        Get the SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy database engine
        """
        if not self._engine:
            self._initialize()
        return self._engine

    def get_session(self) -> Session:
        """
        Create and return a new database session.

        Returns:
            Session: SQLAlchemy database session
        """
        if not self._session_factory:
            self._initialize()
        return self._session_factory()

    def close_session(self, session: Session):
        """
        Close the given database session.

        Args:
            session (Session): SQLAlchemy session to close
        """
        try:
            session.close()
        except Exception as e:
            logging.error(f"Error closing database session: {e}")

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            with self._engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except SQLAlchemyError as e:
            logging.error(f"Database connection test failed: {e}")
            return False