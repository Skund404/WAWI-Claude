# Relative path: store_management/config/__init__.py

"""
Configuration Package Initialization

Exports key configuration constants and utilities.
"""

from .settings import (
APP_NAME,
APP_VERSION,
APP_DESCRIPTION,
get_database_path,
get_log_path,
get_backup_path,
get_config_path,
add_project_to_path,
_find_project_root
)

__all__ = [
'APP_NAME',
'APP_VERSION',
'APP_DESCRIPTION',
'get_database_path',
'get_log_path',
'get_backup_path',
'get_config_path',
'add_project_to_path',
'_find_project_root'
]
