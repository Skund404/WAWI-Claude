from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/tools/manual_migration.py

Script to manually create database schema without using Alembic.
"""
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_project_root() ->Path:
    """
    Find the project root directory.

    Returns:
        Path object pointing to the project root.
    """
    current_dir = Path(__file__).resolve().parent
    while current_dir != current_dir.parent:
        if (current_dir / 'pyproject.toml').exists() or (current_dir /
            'setup.py').exists():
            return current_dir
        current_dir = current_dir.parent
    return Path(__file__).resolve().parent.parent


def create_database_schema(reset_db=False):
    """Create database schema using SQLAlchemy models directly."""
    project_root = find_project_root()
    sys.path.insert(0, str(project_root))
    try:
        from sqlalchemy import create_engine
        from database.models.base import Base
        from database.config import DatabaseConfig
        from database.models.supplier import Supplier
        from database.models.storage import Storage
        from database.models.product import Product
    except ImportError as e:
        logger.error(f'Failed to import required modules: {e}')
        return False
    try:
        database_url = DatabaseConfig.get_database_url()
        logger.info(f'Database URL: {database_url}')
        if reset_db:
            if database_url.startswith('sqlite:///'):
                db_path = database_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    backup_dir = project_root / 'data' / 'backups'
                    os.makedirs(backup_dir, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_path = (backup_dir /
                        f'db_backup_before_manual_migration_{timestamp}.db')
                    shutil.copy2(db_path, backup_path)
                    logger.info(f'Created database backup at {backup_path}')
            else:
                logger.warning(
                    'Database backup only supported for SQLite databases')
        engine = create_engine(database_url)
        if reset_db:
            logger.warning('Dropping all existing tables')
            Base.metadata.drop_all(engine)
        logger.info('Creating all tables')
        Base.metadata.create_all(engine)
        try:
            from database.initialize import add_sample_data
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            session = Session()
            logger.info('Adding sample data')
            add_sample_data(session)
            session.close()
        except Exception as e:
            logger.error(f'Failed to add sample data: {e}')
            return False
        logger.info('Database schema created successfully')
        return True
    except Exception as e:
        logger.error(f'Failed to create database schema: {e}')
        return False


def main():
    """Main entry point."""
    logger.info('Starting manual database migration...')
    reset_db = input('Reset database (drop all tables)? (y/N): ').strip(
        ).lower() == 'y'
    success = create_database_schema(reset_db=reset_db)
    if success:
        logger.info('Manual migration completed successfully')
    else:
        logger.error('Manual migration failed')
        sys.exit(1)


if __name__ == '__main__':
    main()
