# File: store_management/database/config.py

import os

from typing import Dict, Any



from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy_utils import database_exists, create_database
from pathlib import Path

class DatabaseConfig:
    """
    Centralized database configuration management with singleton pattern
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize database configuration with comprehensive setup
        """
        # Project root detection
        self.project_root = self._find_project_root()

        # Load configuration
        self.config = self._load_config()

        # Create database URL
        self.database_url = self._get_database_url()

        # Engine and session factory
        self.engine = self._create_engine()
        self.session_factory = self._create_session_factory()

    def _find_project_root(self) -> Path:
        """
        Dynamically find the project root directory
        
        Returns:
            Path: Project root directory
        """
        current_file = Path(__file__)
        for parent in current_file.parents:
            if (parent / 'pyproject.toml').exists() or \
               (parent / 'setup.py').exists() or \
               (parent / 'manage.py').exists():
                return parent
        return current_file.parent

    def _load_config(self) -> Dict[str, Any]:
        """
        Load database configuration with environment variable precedence

        Returns:
            Dict[str, Any]: Configured database settings
        """
        return {
            'DATABASE_TYPE': os.getenv('DATABASE_TYPE', 'sqlite'),
            'DATABASE_NAME': os.getenv('DATABASE_NAME', 'store_management'),
            'DATABASE_HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'DATABASE_PORT': os.getenv('DATABASE_PORT', ''),
            'DATABASE_USER': os.getenv('DATABASE_USER', ''),
            'DATABASE_PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
            'DATABASE_ECHO': os.getenv('DATABASE_ECHO', 'false').lower() == 'true',
            'DATABASE_POOL_SIZE': int(os.getenv('DATABASE_POOL_SIZE', '5')),
            'DATABASE_MAX_OVERFLOW': int(os.getenv('DATABASE_MAX_OVERFLOW', '10')),
            'DATABASE_POOL_RECYCLE': int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        }

    def _get_database_url(self) -> str:
        """
        Generate database URL based on configuration

        Returns:
            str: Fully qualified database connection URL
        """
        db_type = self.config['DATABASE_TYPE']

        if db_type == 'sqlite':
            # Use a path in the project root for SQLite
            db_path = self.project_root / 'data' / f'{self.config["DATABASE_NAME"]}.db'
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f'sqlite:///{db_path}'

        elif db_type == 'postgresql':
            return (
                f'postgresql://{self.config["DATABASE_USER"]}:'
                f'{self.config["DATABASE_PASSWORD"]}@'
                f'{self.config["DATABASE_HOST"]}:'
                f'{self.config["DATABASE_PORT"]}/'
                f'{self.config["DATABASE_NAME"]}'
            )

        elif db_type == 'mysql':
            return (
                f'mysql+pymysql://{self.config["DATABASE_USER"]}:'
                f'{self.config["DATABASE_PASSWORD"]}@'
                f'{self.config["DATABASE_HOST"]}:'
                f'{self.config["DATABASE_PORT"]}/'
                f'{self.config["DATABASE_NAME"]}'
            )

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _create_engine(self):
        """
        Create SQLAlchemy engine with comprehensive configuration

        Returns:
            Engine: Configured SQLAlchemy engine
        """
        # Ensure database exists
        if not database_exists(self.database_url):
            create_database(self.database_url)

        # Create engine with advanced pooling and connection settings
        try:
            engine = create_engine(
                self.database_url,
                echo=self.config['DATABASE_ECHO'],
                pool_size=self.config['DATABASE_POOL_SIZE'],
                max_overflow=self.config['DATABASE_MAX_OVERFLOW'],
                pool_pre_ping=True,  # Test connection before using
                pool_recycle=self.config['DATABASE_POOL_RECYCLE'],
            )
            return engine
        except Exception as e:
            print(f"Error creating database engine: {e}")
            raise

    def _create_session_factory(self):
        """
        Create thread-local scoped session factory

        Returns:
            scoped_session: Configured session factory
        """
        return scoped_session(
            sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        )

    def get_session(self) -> Session:
        """
        Get a database session

        Returns:
            Session: Active database session
        """
        return self.session_factory()

    def close_session(self):
        """
        Close all sessions and remove session factory
        """
        self.session_factory.remove()

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def get_database_url(self) -> str:
        """
        Public method to retrieve database URL

        Returns:
            str: Database connection URL
        """
        return self.database_url

# Create a singleton instance
database_config = DatabaseConfig()

# Expose the method for import
def get_database_url():
    """
    Function to get the database URL for direct import
    
    Returns:
        str: Database connection URL
    """
    return database_config.get_database_url()


# At the end of the existing config.py file

def get_database_path():
    """
    Get the absolute path to the database file

    Returns:
        Path: Absolute path to the database file
    """
    return Path(database_config.database_url.replace('sqlite:///', ''))


# Expose both methods for import
__all__ = [
    'database_config',
    'get_database_url',
    'get_database_path'
]