# config.py
# Relative path: database/config.py

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """
    Database configuration class.

    Provides methods for getting database configuration settings and managing
    database connection parameters.
    """

    _default_config: Dict[str, Any] = {
        'dialect': 'sqlite',
        'database_name': 'store_management.db',
        'host': None,
        'port': None,
        'username': None,
        'password': None,
        'echo': False,
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'connect_args': {'check_same_thread': False}
    }

    @classmethod
    def _find_project_root(cls) -> Path:
        """
        Find the project root directory.

        Returns:
            Path object pointing to the project root.
        """
        current_dir = Path(__file__).resolve().parent
        while current_dir != current_dir.parent:
            if (current_dir / 'pyproject.toml').exists() or (current_dir / 'setup.py').exists():
                return current_dir
            current_dir = current_dir.parent

        return Path(__file__).resolve().parent.parent

    @classmethod
    def get_database_path(cls) -> str:
        """
        Get the full path to the SQLite database file.

        Returns:
            Full path to the database file.
        """
        project_root = cls._find_project_root()
        db_path = project_root / 'data' / cls._default_config['database_name']
        os.makedirs(db_path.parent, exist_ok=True)
        return str(db_path)

    @classmethod
    def get_database_url(cls, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Get the database URL from the config or generate a default SQLite URL.

        Args:
            config: Configuration dictionary (optional).

        Returns:
            Database URL string.
        """
        # If a full database URL is provided, return it
        if config and 'database_url' in config:
            return config['database_url']

        # Use provided config or default config
        config = config or {}
        dialect = config.get('dialect', cls._default_config['dialect'])

        # Handle SQLite database
        if dialect == 'sqlite':
            db_path = config.get('database_path', cls.get_database_path())
            return f'sqlite:///{db_path}'

        # Handle other database types (PostgreSQL, MySQL, etc.)
        host = config.get('host', cls._default_config['host'])
        port = config.get('port', cls._default_config['port'])
        username = config.get('username', cls._default_config['username'])
        password = config.get('password', cls._default_config['password'])
        database = config.get('database_name', cls._default_config['database_name'])

        # Validate required parameters for non-SQLite databases
        if not all([host, database, username, password]):
            raise ValueError('Missing required database configuration parameters')

        # Construct database URL
        port_str = f':{port}' if port else ''
        return f'{dialect}://{username}:{password}@{host}{port_str}/{database}'

    @classmethod
    def get_engine_config(cls, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the SQLAlchemy engine configuration.

        Args:
            config: Configuration dictionary (optional).

        Returns:
            Dictionary with engine configuration.
        """
        config = config or {}
        result = {}

        # Include only non-connection specific configuration
        for key, default_value in cls._default_config.items():
            if key not in ['dialect', 'host', 'port', 'username', 'password', 'database_name']:
                result[key] = config.get(key, default_value)

        return result

    @classmethod
    def get_database_config(cls, env_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the complete database configuration.

        Args:
            env_config: Environment-specific configuration (optional).

        Returns:
            Dictionary with complete database configuration.
        """
        env_config = env_config or {}
        engine_config = cls.get_engine_config(env_config)
        database_url = cls.get_database_url(env_config)

        result = {'database_url': database_url, **engine_config}
        return result