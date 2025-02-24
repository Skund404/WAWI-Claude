from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Database configuration.
"""
logger = logging.getLogger(__name__)


def get_database_url() ->str:
    """
    Get database URL from configuration.

    Returns:
        Database URL string
    """
    db_path = os.getenv('DATABASE_PATH')
    if not db_path:
        project_root = _find_project_root()
        db_path = str(project_root / 'data' / 'store.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    logger.debug(f'Using database path: {db_path}')
    return f'sqlite:///{db_path}'


def _find_project_root() ->Path:
    """
    Find the project root directory.

    Returns:
        Path to project root
    """
    current_dir = Path(__file__).resolve().parent
    while current_dir.parent != current_dir:
        if (current_dir / 'setup.py').exists() or (current_dir / '.git'
            ).exists():
            return current_dir
        current_dir = current_dir.parent
    return Path.cwd()
