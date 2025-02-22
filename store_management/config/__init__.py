# config/__init__.py
"""
Configuration module for the application.
Centralizes configuration imports and exports.
"""

# Import configuration constants and functions
from .settings import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DATABASE_TYPE,
    DATABASE_NAME,
    LOG_LEVEL,
    LOG_FORMAT,
    DEBUG_MODE,
    PRODUCTION_MODE,
    get_database_path,
    get_log_path,
    get_backup_path,
    get_config_path
)

# Import configuration classes
from .application_config import ApplicationConfig
from .environment import EnvironmentManager

# Export all imported names
__all__ = [
    # Constants
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    'DATABASE_TYPE',
    'DATABASE_NAME',
    'LOG_LEVEL',
    'LOG_FORMAT',
    'DEBUG_MODE',
    'PRODUCTION_MODE',

    # Path Functions
    'get_database_path',
    'get_log_path',
    'get_backup_path',
    'get_config_path',

    # Configuration Classes
    'ApplicationConfig',
    'EnvironmentManager'
]

print("Config init.py called")