# File: config/__init__.py
from .settings import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DATABASE_CONFIG,
    LOGGING_CONFIG,
    ENVIRONMENT_CONFIG,
    FEATURE_FLAGS,
    PERFORMANCE_CONFIG,
    get_database_path,
    get_log_path,
    get_backup_path,
    get_config_path,
)

__all__ = [
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    'DATABASE_CONFIG',
    'LOGGING_CONFIG',
    'ENVIRONMENT_CONFIG',
    'FEATURE_FLAGS',
    'PERFORMANCE_CONFIG',
    'get_database_path',
    'get_log_path',
    'get_backup_path',
    'get_config_path',
]