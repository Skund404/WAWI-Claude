# Path: database/sqlalchemy/config.py
import os
import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine


class DatabaseConfig:
    """
    Centralized configuration management for database connections.

    This singleton class handles database configuration, connection creation,
    and session management.
    """
    _instance = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    def __new__(cls):
        """
        Implement singleton pattern to ensure only one configuration instance.

        Returns:
            DatabaseConfig: The singleton instance of DatabaseConfig
        """
        if not cls._instance:
            # Create new instance using object.__new__
            cls._instance = object.__new__(cls)
            # Call the initialization method
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        """
        Prevent reinitialization of the existing instance.
        """
        # This method does nothing to prevent multiple initializations
        pass

    def _initialize(self):
        """
        Initialize database configuration, creating engine and session factory.
        """
        try:
            # Prevent re-initialization if already done
            if self._engine is not None:
                return

            db_url = self._get_database_url()
            self._engine = self._create_engine(db_url)
            self._session_factory = sessionmaker(bind=self._engine)
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            raise

    def _find_project_root(self) -> str:
        """
        Find the project root directory.

        Returns:
            str: Path to the project root directory
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up three levels from database/sqlalchemy/config.py to project root
        return os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

    def _load_config(self) -> dict:
        """
        Load database configuration.

        Returns:
            dict: Database configuration parameters
        """
        # In a real-world scenario, this might load from a config file
        return {
            'database_type': 'sqlite',
            'database_name': 'store_management.db'
        }

    def _get_database_url(self) -> str:
        """
        Generate the database URL based on configuration.

        Returns:
            str: SQLAlchemy database connection URL
        """
        config = self._load_config()
        project_root = self._find_project_root()

        if config['database_type'] == 'sqlite':
            db_path = os.path.join(project_root, config['database_name'])
            return f'sqlite:///{db_path}'

        # Add support for other database types if needed
        raise ValueError("Unsupported database type")

    def _create_engine(self, db_url: str) -> Engine:
        """
        Create SQLAlchemy engine for database connection.

        Args:
            db_url (str): Database connection URL

        Returns:
            Engine: SQLAlchemy database engine
        """
        try:
            engine = create_engine(
                db_url,
                echo=False,  # Set to True for SQL query logging
                connect_args={'check_same_thread': False}  # Needed for SQLite
            )
            return engine
        except Exception as e:
            logging.error(f"Failed to create database engine: {e}")
            raise

    def get_engine(self) -> Engine:
        """
        Get the database engine.

        Returns:
            Engine: Configured SQLAlchemy database engine

        Raises:
            RuntimeError: If engine has not been initialized
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine

    def get_session(self) -> Session:
        """
        Create and return a new database session.

        Returns:
            Session: SQLAlchemy database session

        Raises:
            RuntimeError: If session factory has not been initialized
        """
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory()

    def close_session(self, session: Optional[Session] = None):
        """
        Close the provided session or all sessions.

        Args:
            session (Optional[Session], optional): Specific session to close. Defaults to None.
        """
        if session:
            session.close()
        elif self._session_factory:
            self._session_factory.close_all()

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute('SELECT 1')
            return True
        except Exception as e:
            logging.error(f"Database connection test failed: {e}")
            return False


def get_database_url() -> str:
    """
    Global function to get database URL.

    Returns:
        str: Database connection URL
    """
    return DatabaseConfig()._get_database_url()


def get_database_path() -> str:
    """
    Global function to get database file path.

    Returns:
        str: Path to the database file
    """
    config = DatabaseConfig()
    url = config._get_database_url()
    # Extract path from SQLite URL
    return url.replace('sqlite:///', '')