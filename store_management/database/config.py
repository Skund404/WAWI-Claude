# File: store_management/database/config.py
import os
import typing
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
    # Default to SQLite database in the project root
    project_root = _find_project_root()
    default_db_path = project_root / 'store_management.db'

    # Priority 1: Passed configuration
    if config and 'database_url' in config:
        return config['database_url']

    # Priority 2: Environment variable
    env_db_url = os.environ.get('DATABASE_URL')
    if env_db_url:
        return env_db_url

    # Priority 3: Default SQLite database
    return f'sqlite:///{default_db_path}'


def _find_project_root() -> Path:
    """
    Dynamically find the project root directory.

    Returns:
        Path to the project root
    """
    current_path = Path(__file__).resolve()
    # Go up multiple levels to find project root
    for _ in range(3):  # Adjust this if needed
        current_path = current_path.parent
    return current_path


def get_database_config() -> Dict[str, Any]:
    """
    Retrieve comprehensive database configuration.

    Combines configuration from multiple sources.

    Returns:
        Dictionary with database configuration
    """
    return {
        'database_url': get_database_url(),
        'project_root': str(_find_project_root()),
        # Add more configuration parameters as needed
    }


# Create a default database manager configuration
database_manager = {
    'url': get_database_url(),
    'echo': False,  # Set to True for SQLAlchemy logging
    'pool_size': 5,
    'max_overflow': 10
}