# Path: config/settings.py
"""
Configuration settings for the store management application.

This module provides functions to locate important directories and files
within the application structure, such as database location, log paths,
backup directories, and configuration files.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any

# Configure logging with more comprehensive settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            filename=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..',
                'logs',
                f'store_management_{datetime.now().strftime("%Y-%m-%d")}.log'
            ),
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# Application Configuration
APP_NAME = "Leatherworking Store Management"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Comprehensive store management system for leatherworking businesses"


def _find_project_root() -> Path:
    """
    Find the project's root directory by looking for key marker files/directories.

    Returns:
        Path: The absolute path to the project root directory

    Raises:
        RuntimeError: If project root cannot be determined
    """
    try:
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

        # If we couldn't find project root, raise an error
        raise RuntimeError("Could not detect project root directory")

    except Exception as e:
        logger.error(f"Error finding project root: {e}")
        raise RuntimeError(f"Project root detection failed: {e}")


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory (Union[str, Path]): Path to the directory

    Returns:
        Path: Absolute path to the existing directory
    """
    dir_path = Path(directory)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path.absolute()
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise


def get_database_path() -> str:
    """
    Get the path to the SQLite database file.

    Returns:
        str: Absolute path to the database file
    """
    try:
        root_dir = _find_project_root()
        db_dir = ensure_directory_exists(root_dir / 'data')
        db_path = db_dir / 'store_management.db'

        logger.info(f"Database path: {db_path}")
        return str(db_path)

    except Exception as e:
        logger.error(f"Failed to get database path: {e}")
        raise


def get_log_path() -> str:
    """
    Get the path to the log directory.

    Returns:
        str: Absolute path to the log directory
    """
    try:
        root_dir = _find_project_root()
        log_dir = ensure_directory_exists(root_dir / 'logs')

        # Generate log filename with timestamp
        log_filename = f'store_management_{datetime.now().strftime("%Y-%m-%d")}.log'
        log_path = log_dir / log_filename

        logger.info(f"Log directory: {log_dir}")
        return str(log_path)

    except Exception as e:
        logger.error(f"Failed to get log path: {e}")
        raise


def get_backup_path() -> str:
    """
    Get the path to the backup directory.

    Returns:
        str: Absolute path to the backup directory
    """
    try:
        root_dir = _find_project_root()
        backup_dir = ensure_directory_exists(root_dir / 'backups')

        logger.info(f"Backup directory: {backup_dir}")
        return str(backup_dir)

    except Exception as e:
        logger.error(f"Failed to get backup path: {e}")
        raise


# Alias for backward compatibility
get_backup_dir = get_backup_path


def get_config_path() -> str:
    """
    Get the path to the configuration file directory.

    Returns:
        str: Absolute path to the configuration file directory
    """
    try:
        root_dir = _find_project_root()
        config_dir = ensure_directory_exists(root_dir / 'config')

        logger.info(f"Configuration directory: {config_dir}")
        return str(config_dir)

    except Exception as e:
        logger.error(f"Failed to get config path: {e}")
        raise


def get_application_config() -> Dict[str, Any]:
    """
    Retrieve comprehensive application configuration.

    Returns:
        Dict[str, Any]: Dictionary of application configuration settings
    """
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "paths": {
            "database": get_database_path(),
            "logs": get_log_path(),
            "backups": get_backup_path(),
            "config": get_config_path()
        }
    }


# Logging configuration
def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure application-wide logging with advanced settings.

    Args:
        log_level (int): Logging level. Defaults to logging.INFO
    """
    try:
        # Configure root logger
        logging.getLogger().setLevel(log_level)

        # Create log file handler
        log_path = get_log_path()
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Add file handler to root logger
        logging.getLogger().addHandler(file_handler)

        logger.info(f"Logging configured. Log file: {log_path}")

    except Exception as e:
        print(f"Failed to setup logging: {e}")
        logging.basicConfig(level=log_level)


# Setup logging when the module is imported
setup_logging()