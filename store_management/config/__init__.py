# config/__init__.py
"""
Configuration package initialization.
Provides access to application configuration settings.
"""

from .settings import (
    ConfigurationManager,
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DEVELOPMENT,
    PRODUCTION,
    TESTING
)

# Create a singleton configuration instance
config = ConfigurationManager()

# Expose key configuration functions
get_database_path = config.get_database_path
get_log_path = config.get_log_path
get_backup_path = config.get_backup_path
get_config_path = config.get_config_path

# Export key configuration variables
__all__ = [
    'config',
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    'DEVELOPMENT',
    'PRODUCTION',
    'TESTING',
    'get_database_path',
    'get_log_path',
    'get_backup_path',
    'get_config_path'
]