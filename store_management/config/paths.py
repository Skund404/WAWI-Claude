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


def get_database_path() -> str:
    """
    Get the path to the SQLite database file.

    Returns:
        str: Absolute path to the database file
    """
    root_dir = _find_project_root()
    db_dir = root_dir / 'data'

    # Ensure the data directory exists
    if not db_dir.exists():
        os.makedirs(db_dir, exist_ok=True)

    return str(db_dir / 'store_management.db')


def get_log_path() -> str:
    """
    Get the path to the log directory.

    Returns:
        str: Absolute path to the log directory
    """
    root_dir = _find_project_root()
    log_dir = root_dir / 'logs'

    # Ensure the log directory exists
    if not log_dir.exists():
        os.makedirs(log_dir, exist_ok=True)

    return str(log_dir)


def get_backup_path() -> str:
    """
    Get the path to the backup directory.

    Returns:
        str: Absolute path to the backup directory
    """
    root_dir = _find_project_root()
    backup_dir = root_dir / 'backups'

    # Ensure the backup directory exists
    if not backup_dir.exists():
        os.makedirs(backup_dir, exist_ok=True)

    return str(backup_dir)


# For backward compatibility
get_backup_dir = get_backup_path


def get_config_path() -> str:
    """
    Get the path to the configuration file.

    Returns:
        str: Absolute path to the configuration file directory
    """
    root_dir = _find_project_root()
    config_dir = root_dir / 'config'

    # Ensure the config directory exists
    if not config_dir.exists():
        os.makedirs(config_dir, exist_ok=True)

    return str(config_dir)