# File: database/sqlalchemy/config.py
# Purpose: Centralized database configuration management

import os
from typing import Dict, Any, Optional
from pathlib import Path


def get_database_url(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate database connection URL with multiple configuration sources.

    Priority:
    1. Explicitly passed configuration
    2. Environment variables
    3. Default configuration

    Args:
        config: Optional configuration dictionary

    Returns:
        Database connection URL
    """
    # Check explicitly passed config first
    if config and 'database_url' in config:
        return config['database_url']

    # Check environment variables
    env_url = os.environ.get('DATABASE_URL')
    if env_url:
        return env_url

    # Default to SQLite in project root
    project_root = _find_project_root()
    default_path = project_root / 'store_management.db'

    return f'sqlite:///{default_path}'


def _find_project_root() -> Path:
    """
    Dynamically find the project root directory.

    Returns:
        Path to the project root
    """
    current_dir = Path(__file__).resolve()

    # Search up to 5 levels to find project root
    for _ in range(5):
        if (current_dir / 'pyproject.toml').exists() or \
                (current_dir / 'setup.py').exists():
            return current_dir
        current_dir = current_dir.parent

    # Fallback to current directory
    return Path.cwd()


def get_database_config() -> Dict[str, Any]:
    """
    Retrieve comprehensive database configuration.

    Combines configuration from multiple sources.

    Returns:
        Dictionary with database configuration
    """
    return {
        'url': get_database_url(),
        'echo': os.environ.get('DATABASE_ECHO', 'false').lower() == 'true',
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 5)),
        'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 10)),
        'pool_timeout': int(os.environ.get('DATABASE_POOL_TIMEOUT', 30)),
    }