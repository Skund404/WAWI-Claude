from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/tools/setup_migrations.py

Script to set up Alembic migrations.
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


def create_migration_directories():
    """Create the necessary directories for migrations."""
    project_root = find_project_root()
    migrations_dir = project_root / 'database' / 'migrations'
    versions_dir = migrations_dir / 'versions'
    os.makedirs(migrations_dir, exist_ok=True)
    os.makedirs(versions_dir, exist_ok=True)
    logger.info(f'Created migrations directories: {migrations_dir}')


def copy_migration_files():
    """Copy the migration files to their correct locations."""
    project_root = find_project_root()
    source_dir = project_root
    source_env = source_dir / 'database' / 'migrations' / 'env.py'
    if source_env.exists():
        logger.info('env.py already exists, skipping copy')
    else:
        template_env = (project_root / 'database' / 'migrations' /
            'env.py.template')
        if template_env.exists():
            shutil.copy2(template_env, source_env)
            logger.info(f'Copied env.py template to {source_env}')
        else:
            logger.warning('env.py template not found')
    source_script = source_dir / 'database' / 'migrations' / 'script.py.mako'
    if source_script.exists():
        logger.info('script.py.mako already exists, skipping copy')
    else:
        template_script = (project_root / 'database' / 'migrations' /
            'script.py.mako.template')
        if template_script.exists():
            shutil.copy2(template_script, source_script)
            logger.info(f'Copied script.py.mako template to {source_script}')
        else:
            logger.warning('script.py.mako template not found')
    source_alembic = source_dir / 'alembic.ini'
    if source_alembic.exists():
        logger.info('alembic.ini already exists, skipping copy')
    else:
        template_alembic = project_root / 'alembic.ini.template'
        if template_alembic.exists():
            shutil.copy2(template_alembic, source_alembic)
            logger.info(f'Copied alembic.ini template to {source_alembic}')
        else:
            logger.warning('alembic.ini template not found')


def create_initial_migration():
    """Create the initial migration."""
    try:
        project_root = find_project_root()
        try:
            subprocess.run(['alembic', '--version'], check=True,
                capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(
                "Alembic command not found. Please install alembic using 'pip install alembic'."
                )
            return False
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
    create_migration_directories()
    copy_migration_files()
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
