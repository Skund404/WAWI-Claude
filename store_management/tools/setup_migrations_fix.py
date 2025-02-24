from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/tools/setup_migrations_fix.py

Fixed script to set up Alembic migrations.
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


def verify_migrations_setup() ->bool:
    """
    Verify that all required files for migrations are present.

    Returns:
        True if all files are present, False otherwise.
    """
    project_root = find_project_root()
    required_files = [project_root / 'alembic.ini', project_root /
        'database' / 'migrations' / 'env.py', project_root / 'database' /
        'migrations' / 'script.py.mako']
    versions_dir = project_root / 'database' / 'migrations' / 'versions'
    if not versions_dir.exists():
        os.makedirs(versions_dir, exist_ok=True)
        logger.info(f'Created versions directory: {versions_dir}')
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        logger.warning(
            f'Missing migration files: {[str(f) for f in missing_files]}')
        return False
    logger.info('All migration files are present')
    return True


def create_initial_migration():
    """
    Create the initial migration.

    Returns:
        True if successful, False otherwise.
    """
    try:
        project_root = find_project_root()
        os.chdir(project_root)
        result = subprocess.run(['alembic', 'revision', '--autogenerate',
            '-m', 'Initial migration'], check=True, capture_output=True,
            text=True)
        logger.info(f'Created initial migration: {result.stdout.strip()}')
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f'Failed to create initial migration: {e.stderr}')
        return False


def main():
    """Main entry point for migration setup."""
    logger.info('Setting up Alembic migrations...')
    if not verify_migrations_setup():
        logger.error(
            'Migration setup verification failed. Please ensure all required files are present.'
            )
        return
    create_migration = input('Create initial migration? (y/n): ').strip(
        ).lower()
    if create_migration == 'y':
        success = create_initial_migration()
        if success:
            logger.info('Initial migration created successfully')
        else:
            logger.error('Failed to create initial migration')
    logger.info('Migration setup complete')


if __name__ == '__main__':
    main()
