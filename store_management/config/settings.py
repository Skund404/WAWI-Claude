# config/settings.py
"""
Application configuration settings and path utilities.
"""

import os
import sys
from pathlib import Path

# Application Configuration Constants
APP_NAME = "Store Management"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Inventory and Order Management System"

# Database Configuration
DATABASE_TYPE = "sqlite"
DATABASE_NAME = "store_management.db"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Environment Configuration
DEBUG_MODE = False
PRODUCTION_MODE = False


def _find_project_root() -> Path:
    """
    Find the root directory of the project.

    Returns:
        Path: Absolute path to the project root directory.
    """
    # Start from the current file's directory
    current_file = Path(__file__)

    # Navigate up until we find a distinctive project marker
    # This could be a specific file like pyproject.toml, setup.py, or a directory
    while current_file.parent != current_file:
        # Check for markers of project root
        if (current_file.parent / 'main.py').exists() or \
                (current_file.parent / 'setup.py').exists() or \
                (current_file.parent / '.git').exists():
            return current_file.parent
        current_file = current_file.parent

    # Fallback to the directory of the current script
    return Path(__file__).parent


def get_database_path() -> str:
    """
    Get the path to the database file.

    Returns:
        str: Absolute path to the database file.
    """
    project_root = _find_project_root()
    data_dir = project_root / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / DATABASE_NAME)


def get_log_path() -> str:
    """
    Get the path to the log directory.

    Returns:
        str: Absolute path to the log directory.
    """
    project_root = _find_project_root()
    log_dir = project_root / 'logs'

    # Ensure the log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    return str(log_dir)


def get_backup_path() -> str:
    """
    Get the path to the backup directory.

    Returns:
        str: Absolute path to the backup directory.
    """
    project_root = _find_project_root()
    backup_dir = project_root / 'backups'

    # Ensure the backup directory exists
    backup_dir.mkdir(parents=True, exist_ok=True)

    return str(backup_dir)


def get_config_path() -> str:
    """
    Get the path to the configuration directory.

    Returns:
        str: Absolute path to the configuration directory.
    """
    project_root = _find_project_root()
    config_dir = project_root / 'config'

    return str(config_dir)


# Export configuration constants
__all__ = [
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    'DATABASE_TYPE',
    'DATABASE_NAME',
    'LOG_LEVEL',
    'LOG_FORMAT',
    'DEBUG_MODE',
    'PRODUCTION_MODE',
    'get_database_path',
    'get_log_path',
    'get_backup_path',
    'get_config_path'
]