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
BACKUP_DIR = Path(__file__).parent / 'backups'
LOG_DIR = Path(__file__).parent / 'logs'

# Ensure required directories exist
BACKUP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)