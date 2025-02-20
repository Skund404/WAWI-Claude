# config.py
from pathlib import Path
import os


# Application Settings
APP_NAME = "Store Management System"
WINDOW_SIZE = "1200x800"
APP_VERSION = "1.0.0"

# Get the directory of the current file (config.py)
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# Database file name (without path)
DATABASE_FILENAME = 'store_management.db'

# Database path (private - not to be accessed directly)
_DATABASE_PATH = Path(os.path.join(CONFIG_DIR, 'database', DATABASE_FILENAME))

def get_database_path():
    """
    Returns the absolute path to the database file.

    Returns:
        Path: The absolute path to the database file.
    """
    return _DATABASE_PATH

# Table names
TABLES = {
    'SUPPLIER': 'supplier',
    'SHELF': 'shelf',
    'STORAGE': 'storage',
    'RECIPE_INDEX': 'recipe_index',
    'RECIPE_DETAILS': 'recipe_details',
    'SORTING_SYSTEM': 'sorting_system',
}

# Colors for UI
COLORS = {
    'WARNING': '#ffcccc',            # Light red for general warnings
    'CRITICAL': '#ff8080',           # Dark red for critical stock levels
    'WARNING_LIGHT': '#ffe6cc',      # Light orange for approaching warning threshold
    'SUCCESS': '#ccffcc',            # Green for success messages
    'NORMAL': '#ffffff',             # White for normal state
    'HEADER': '#f0f0f0',             # Light gray for headers
    'PRIMARY': '#007bff',            # Blue for primary actions
    'SECONDARY': '#6c757d',          # Gray for secondary actions
}

# UI Settings
DEFAULT_PADDING = 5
MINIMUM_COLUMN_WIDTH = 50
DEFAULT_FONT = ('Arial', 10)
HEADER_FONT = ('Arial', 11, 'bold')

# File paths
BACKUP_DIR = Path(os.path.join(CONFIG_DIR, 'backups'))
LOG_DIR = Path(os.path.join(CONFIG_DIR, 'logs'))

# Ensure required directories exist
BACKUP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


