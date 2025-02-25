# config/settings.py
"""
Configuration settings for the application.
"""

import os
import sys
from typing import Optional

# Application Details
APP_NAME = "Store Management"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Inventory and Project Management System"

def add_project_to_path() -> None:
    """
    Add the project root directory to the Python path.

    This ensures that modules can be imported properly regardless
    of the working directory when the application is run.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

def get_config_dir() -> str:
    """
    Get the configuration directory path.

    Returns:
        str: Absolute path to the configuration directory
    """
    return os.path.abspath(os.path.dirname(__file__))

def get_backup_dir() -> str:
    """
    Get the backup directory path.

    Returns:
        str: Absolute path to the backup directory
    """
    backup_dir = os.path.join(get_config_dir(), '..', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    return os.path.abspath(backup_dir)

def get_log_path() -> Optional[str]:
    """
    Get the log file path.

    Returns:
        Optional[str]: Absolute path to the log file, or None if not configured
    """
    log_dir = os.path.join(get_config_dir(), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'app.log')

def get_database_path() -> str:
    """
    Get the absolute path to the database file.

    Returns:
        str: Absolute path to the database file
    """
    db_dir = os.path.join(get_config_dir(), '..', 'database')
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, 'store_management.db')

# Automatically add project to path when module is imported
add_project_to_path()