from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
APP_NAME = 'Store Management System'
WINDOW_SIZE = '1200x800'
APP_VERSION = '1.0.0'
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILENAME = 'store_management.db'
_DATABASE_PATH = Path(os.path.join(CONFIG_DIR, 'database', DATABASE_FILENAME))

def get_database_path():
    """
Returns the absolute path to the database file.

Returns:
    Path: The absolute path to the database file.
"""
return _DATABASE_PATH
TABLES = {'SUPPLIER': 'supplier', 'SHELF': 'shelf', 'STORAGE': 'storage', 'RECIPE_INDEX': 'recipe_index', 'RECIPE_DETAILS': 'recipe_details', 'SORTING_SYSTEM': 'sorting_system'}
COLORS = {'WARNING': '#ffcccc', 'CRITICAL': '#ff8080', 'WARNING_LIGHT': '#ffe6cc', 'SUCCESS': '#ccffcc', 'NORMAL': '#ffffff', 'HEADER': '#f0f0f0', 'PRIMARY': '#007bff', 'SECONDARY': '#6c757d'}
DEFAULT_PADDING = 5
MINIMUM_COLUMN_WIDTH = 50
DEFAULT_FONT = ('Arial', 10)
HEADER_FONT = ('Arial', 11, 'bold')
BACKUP_DIR = Path(os.path.join(CONFIG_DIR, 'backups'))
LOG_DIR = Path(os.path.join(CONFIG_DIR, 'logs'))
BACKUP_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)