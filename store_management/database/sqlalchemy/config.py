# Relative path: store_management/database/sqlalchemy/config.py

"""
Database configuration utility for managing database path and initialization.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

# Configure logging
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL from configuration.

    Generates a default SQLite database path if not explicitly set.

    Returns:
        str: Database URL string for SQLAlchemy connection
    """
    # Check for explicitly set database path
    db_path = os.getenv("DATABASE_PATH")

    if not db_path:
        # If no path is set, generate a default path
        try:
            project_root = _find_project_root()
            db_path = str(project_root / "data" / "store.db")

            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            logger.debug(f"Using default database path: {db_path}")
        except Exception as e:
            logger.error(f"Error determining database path: {e}")
            # Fallback to current working directory
            db_path = os.path.join(os.getcwd(), "store.db")
            logger.warning(f"Using fallback database path: {db_path}")

    # Construct SQLAlchemy database URL
    return f"sqlite:///{db_path}"


def _find_project_root() -> Path:
    """
    Find the project root directory by traversing up from the current file.

    Looks for indicators of project root like 'setup.py' or '.git' directory.

    Returns:
        Path: Absolute path to the project root directory
    """
    current_dir = Path(__file__).resolve().parent

    while current_dir.parent != current_dir:
        # Check for common project root indicators
        if (current_dir / "setup.py").exists() or (current_dir / ".git").exists():
            return current_dir

        # Move up one directory
        current_dir = current_dir.parent

    # If no definitive project root is found, return current working directory
    return Path.cwd()


def validate_database_configuration(db_url: Optional[str] = None) -> bool:
    """
    Validate the database configuration.

    Args:
        db_url (Optional[str], optional): Database URL to validate. 
                                          Defaults to using get_database_url().

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Use provided URL or get default
        url = db_url or get_database_url()

        # Check if it's a valid SQLite URL
        if not url.startswith('sqlite:///'):
            logger.error(f"Invalid database URL: {url}")
            return False

        # Ensure the path is writable
        db_path = url.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)

        # Check directory permissions
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
            except PermissionError:
                logger.error(f"Cannot create database directory: {db_dir}")
                return False

        if not os.access(db_dir, os.W_OK):
            logger.error(f"Database directory is not writable: {db_dir}")
            return False

        return True

    except Exception as e:
        logger.error(f"Database configuration validation failed: {e}")
        return False