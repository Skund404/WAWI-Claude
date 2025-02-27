# config/__init__.py
"""
Configuration package initialization for the Leatherworking Store Management application.
"""

from .settings import (
    ConfigurationManager,
    Environment,
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DEVELOPMENT,
    PRODUCTION,
    TESTING
)

# Import the new path resolution functions
from .paths import (
    get_database_path,
    get_log_path,
    get_backup_path,
    get_backup_dir,
    get_config_path,
    _find_project_root
)

__all__ = [
    # Configuration classes and constants
    'ConfigurationManager',
    'Environment',
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    'DEVELOPMENT',
    'PRODUCTION',
    'TESTING',

    # Path resolution functions
    'get_database_path',
    'get_log_path',
    'get_backup_path',
    'get_backup_dir',
    'get_config_path',
    '_find_project_root'
]