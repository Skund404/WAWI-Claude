# config.py
from pathlib import Path

# Application Settings
APP_NAME = "Store Management System"
WINDOW_SIZE = "1200x800"
APP_VERSION = "1.0.0"

# Database
DATABASE_PATH = Path(__file__).parent / 'database' / 'store_management.db'

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
    'WARNING': '#ffcccc',
    'SUCCESS': '#ccffcc',
    'NORMAL': '#ffffff',
    'HEADER': '#f0f0f0',
    'PRIMARY': '#007bff',
    'SECONDARY': '#6c757d',
}

# UI Settings
DEFAULT_PADDING = 5
MINIMUM_COLUMN_WIDTH = 50
DEFAULT_FONT = ('Arial', 10)
HEADER_FONT = ('Arial', 11, 'bold')

# File paths
BACKUP_DIR = Path(__file__).parent / 'backups'
LOG_DIR = Path(__file__).parent / 'logs'

# Ensure required directories exist
BACKUP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)