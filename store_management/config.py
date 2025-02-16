# config.py
import os
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent

# Database
DATABASE_PATH = ROOT_DIR / 'store_management.db'

# Application settings
APP_NAME = "Store Management System"
APP_VERSION = "1.0.0"

# Table names
TABLES = {
    'SHELF': 'shelf',
    'STORAGE': 'storage',
    'RECIPE_INDEX': 'recipe_index',
    'RECIPE_DETAILS': 'recipe_details',
    'SORTING_SYSTEM': 'sorting_system',
    'SAVED_VIEWS': 'saved_views',
    'AUDIT_LOG': 'audit_log'
}

# Default window size
WINDOW_SIZE = "1200x800"

# Colors
COLORS = {
    'ERROR': '#ffebee',
    'WARNING': '#fff3e0',
    'SUCCESS': '#e8f5e9',
    'PRIMARY': '#e3f2fd'
}