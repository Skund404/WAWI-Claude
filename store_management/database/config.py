# database/config.py
"""
Database configuration helpers
"""

import os
from config.settings import get_database_path


def get_database_url(config=None):
    """
    Get the database URL string based on configuration.

    Args:
        config (dict, optional): Configuration dictionary. If None, uses default config.

    Returns:
        str: SQLAlchemy database URL
    """
    # If specific config is provided, use it
    if config and 'database_url' in config:
        return config['database_url']

    # Otherwise, build URL from database path
    db_path = get_database_path()
    return f"sqlite:///{db_path}"


def _find_project_root():
    """
    Find the project root directory.

    Returns:
        str: Path to the project root directory
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up until we find the project root (where main.py is)
    while os.path.basename(current_dir) and not os.path.exists(os.path.join(current_dir, 'main.py')):
        parent = os.path.dirname(current_dir)
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent

    return current_dir


def get_database_config():
    """
    Get database configuration dictionary.

    Returns:
        dict: Database configuration
    """
    # You could read this from a JSON file or environment variables
    return {
        'dialect': 'sqlite',
        'database': get_database_path(),
        'echo': False
    }