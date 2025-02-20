# store_management/config/settings.py

import os
from pathlib import Path

# Application Settings
APP_NAME = "Store Management"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1024x768"

# Directory Configuration
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATABASE_FILENAME = "store.db"
_DATABASE_PATH = PROJECT_ROOT / "data" / DATABASE_FILENAME
BACKUP_DIR = PROJECT_ROOT / "backups"
LOG_DIR = PROJECT_ROOT / "logs"

# Table Configurations
TABLES = {
    "shelf": ["id", "name", "location", "capacity"],
    "product": ["id", "name", "description", "quantity"],
    "supplier": ["id", "name", "contact", "address"],
    "order": ["id", "date", "supplier", "status"]
}

# UI Settings
COLORS = {
    "primary": "#007bff",
    "secondary": "#6c757d",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8"
}

DEFAULT_PADDING = 5
MINIMUM_COLUMN_WIDTH = 100
DEFAULT_FONT = ("Arial", 10)
HEADER_FONT = ("Arial", 12, "bold")

def get_database_path() -> Path:
    """Returns the absolute path to the database file.

    Returns:
        Path: The absolute path to the database file.
    """
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    return _DATABASE_PATH