# File: store_management/database/config.py

import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy_utils import database_exists, create_database


class DatabaseConfig:
    """
    Centralized database configuration management
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize database configuration
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
        """
        current_file = Path(__file__)
        for parent in current_file.parents:
            if (parent / 'pyproject.toml').exists() or \
                    (parent / 'setup.py').exists():
                return parent
        return current_file.parent

    def _load_config(self) -> Dict[str, Any]:
        """
        Load database configuration

        Precedence:
        1. Environment Variables
        2. Configuration File
        3. Default Settings
        """
        config = {
            'DATABASE_TYPE': os.getenv('DATABASE_TYPE', 'sqlite'),
            'DATABASE_NAME': os.getenv('DATABASE_NAME', 'store_management'),
            'DATABASE_HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'DATABASE_PORT': os.getenv('DATABASE_PORT', ''),
            'DATABASE_USER': os.getenv('DATABASE_USER', ''),
            'DATABASE_PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
            'DATABASE_ECHO': os.getenv('DATABASE_ECHO', 'false').lower() == 'true',
            'DATABASE_POOL_SIZE': int(os.getenv('DATABASE_POOL_SIZE', '5')),
            'DATABASE_MAX_OVERFLOW': int(os.getenv('DATABASE_MAX_OVERFLOW', '10'))
        }
        return config

    def _get_database_url(self) -> str:
        """
        Generate database URL based on configuration
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
        """
        # Ensure database exists
        if not database_exists(self.database_url):
            create_database(self.database_url)

        # Create engine with advanced pooling and connection settings
        engine = create_engine(
            self.database_url,
            echo=self.config['DATABASE_ECHO'],
            pool_size=self.config['DATABASE_POOL_SIZE'],
            max_overflow=self.config['DATABASE_MAX_OVERFLOW'],
            pool_pre_ping=True,  # Test connection before using
            pool_recycle=3600,  # Reconnect after 1 hour
        )
        return engine

    def _create_session_factory(self):
        """
        Create thread-local scoped session factory
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
        """
        return self.session_factory()

    def close_session(self):
        """
        Close all sessions
        """
        self.session_factory.remove()

    def test_connection(self) -> bool:
        """
        Test database connection
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(sqlalchemy.text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False


# Singleton instance
database_config = DatabaseConfig()