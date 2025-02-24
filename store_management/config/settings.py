# Relative path: store_management/config/settings.py

"""
Configuration Settings Module

Provides utility functions and constants for application configuration.
"""

import os
import sys
from typing import Optional

# Application Constants
APP_NAME = "Store Management"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Inventory and Store Management System"


def _find_project_root() -> str:
"""
Find the root directory of the project.

Returns:
str: Absolute path to the project root directory.
"""
# Start from the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Traverse up until we find a distinctive project marker
while current_dir:
    pass
# Check for a distinctive file or directory that indicates project root
if os.path.exists(os.path.join(current_dir, 'main.py')) or \
os.path.exists(os.path.join(current_dir, 'pyproject.toml')):
return current_dir

# Move up one directory
parent_dir = os.path.dirname(current_dir)
if parent_dir == current_dir:
    pass
# Reached the filesystem root
break
current_dir = parent_dir

# Fallback to the directory of the current script
return os.path.dirname(os.path.abspath(__file__))


def get_database_path() -> str:
"""
Get the path to the SQLite database file.

Returns:
str: Absolute path to the database file.
"""
project_root = _find_project_root()

# Create a 'data' directory if it doesn't exist
data_dir = os.path.join(project_root, 'data')
os.makedirs(data_dir, exist_ok=True)

# Define database path
return os.path.join(data_dir, 'store_management.db')


def get_log_path() -> str:
"""
Get the path to the log directory.

Returns:
str: Absolute path to the log directory.
"""
project_root = _find_project_root()

# Create a 'logs' directory if it doesn't exist
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)

return log_dir


def get_backup_path() -> str:
"""
Get the path to the backup directory.

Returns:
str: Absolute path to the backup directory.
"""
project_root = _find_project_root()

# Create a 'backups' directory if it doesn't exist
backup_dir = os.path.join(project_root, 'backups')
os.makedirs(backup_dir, exist_ok=True)

return backup_dir


def get_config_path() -> str:
"""
Get the path to the configuration directory.

Returns:
str: Absolute path to the configuration directory.
"""
project_root = _find_project_root()

return os.path.join(project_root, 'config')


def add_project_to_path():
    pass
"""
Add the project root to Python's system path to enable absolute imports.
"""
project_root = _find_project_root()
if project_root not in sys.path:
    pass
sys.path.insert(0, project_root)
