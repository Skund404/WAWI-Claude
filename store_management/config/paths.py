# path: config/paths.py
"""
Configuration settings for the store management application.

This module provides functions to locate important directories and files
within the application structure, such as database location, log paths,
backup directories, and configuration files.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

from config import ConfigurationManager

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _find_project_root() -> Path:
    """
    Find the project's root directory by looking for key marker files/directories.

    Returns:
        Path: The absolute path to the project root directory
    """
    # Start with the current file's directory
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Check if we're already at the project root
    if (current_dir / 'main.py').exists() or (current_dir / 'setup.py').exists():
        return current_dir

    # Navigate up until we find a marker file
    while current_dir != current_dir.parent:
        # Look for common project root markers
        if (current_dir / 'main.py').exists() or (current_dir / 'setup.py').exists():
            return current_dir
        current_dir = current_dir.parent

    # If we couldn't find project root, default to parent of this file
    logger.warning("Could not detect project root directory. Using parent of config directory.")
    return Path(os.path.dirname(os.path.abspath(__file__))).parent


def get_base_directory():
    """
    Get the base directory for the project.

    Returns:
        str: Absolute path to the project's base directory
    """
    return str(_find_project_root())


def get_database_directory():
    """
    Get the directory for storing database files.

    Returns:
        str: Absolute path to the database directory
    """
    base_dir = _find_project_root()
    database_dir = base_dir / 'data'

    # Create the directory if it doesn't exist
    os.makedirs(database_dir, exist_ok=True)

    return str(database_dir)


def get_database_path(self) -> str:
    """
    Get the full path to the database file.

    Returns:
        str: Path to the database file
    """
    return str(Path(self._config['data_dir']) / 'database.db')


def get_log_directory():
    """
    Get the directory for storing log files.

    Returns:
        str: Absolute path to the logs directory
    """
    base_dir = _find_project_root()
    log_dir = base_dir / 'logs'

    # Create the directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    return str(log_dir)


def get_log_path() -> str:
    """
    Get the path to the log directory.

    Returns:
        str: Absolute path to the log directory
    """
    return get_log_directory()


def get_backup_path(self) -> str:
    """
    Get the full path to the backups directory.

    Returns:
        str: Path to the backups directory
    """
    return self._config['backups_dir']


def get_config_path(self) -> str:
    """
    Get the full path to the config directory.

    Returns:
        str: Path to the config directory
    """
    return str(Path(__file__).parent)

# Standalone path functions for backward compatibility




