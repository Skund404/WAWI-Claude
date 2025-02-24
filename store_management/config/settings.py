

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
def _find_project_root() ->Path:
    """
    Find the root directory of the project.

    Returns:
        Path: Path to the project root directory.
    """
    current_file = Path(__file__)
    return current_file.parent.parent


APP_NAME = 'Store Management System'
APP_VERSION = '0.1.0'
APP_DESCRIPTION = 'Inventory and Project Management Application'
DATABASE_CONFIG: Dict[str, Any] = {'engine': 'sqlite', 'name': 'store.db',
    'path': None}


def get_database_path() ->str:
    """
    Get the path to the database file.

    Returns:
        str: Path to the database file.
    """
    project_root = _find_project_root()
    db_dir = project_root / 'data'
    db_dir.mkdir(exist_ok=True)
    DATABASE_CONFIG['path'] = str(db_dir / DATABASE_CONFIG['name'])
    return DATABASE_CONFIG['path']


def get_log_path() ->str:
    """
    Get the path to the log directory.

    Returns:
        str: Path to the log directory.
    """
    project_root = _find_project_root()
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    return str(log_dir)


def get_backup_path() ->str:
    """
    Get the path to the backup directory.

    Returns:
        str: Path to the backup directory.
    """
    project_root = _find_project_root()
    backup_dir = project_root / 'backups'
    backup_dir.mkdir(exist_ok=True)
    return str(backup_dir)


def get_config_path() ->str:
    """
    Get the path to the configuration directory.

    Returns:
        str: Path to the configuration directory.
    """
    project_root = _find_project_root()
    config_dir = project_root / 'config'
    return str(config_dir)


LOGGING_CONFIG: Dict[str, Any] = {'level': 'INFO', 'format':
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', 'filename':
    'app.log'}
ENVIRONMENT_CONFIG: Dict[str, Any] = {'debug': False, 'testing': False,
    'production': True}
FEATURE_FLAGS: Dict[str, bool] = {'inventory_tracking': True,
    'project_management': True, 'order_system': True, 'reporting': True}
PERFORMANCE_CONFIG: Dict[str, Any] = {'max_cache_size': 1000,
    'connection_timeout': 30, 'retry_attempts': 3}
__all__ = ['APP_NAME', 'APP_VERSION', 'APP_DESCRIPTION', 'DATABASE_CONFIG',
    'LOGGING_CONFIG', 'ENVIRONMENT_CONFIG', 'FEATURE_FLAGS',
    'PERFORMANCE_CONFIG', 'get_database_path', 'get_log_path',
    'get_backup_path', 'get_config_path']
