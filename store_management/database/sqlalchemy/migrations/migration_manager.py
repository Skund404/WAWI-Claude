import os
import sys
from logging.config import fileConfig
from typing import Optional, Union

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.declarative import DeclarativeMeta
from alembic import context

# Dynamic path resolution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)


# Lazy import to prevent circular dependencies
def get_base_metadata():
    from store_management.database.sqlalchemy.models import Base
    return Base.metadata


def run_migrations_offline(config, target_metadata=None):
    """Run migrations in 'offline' mode."""
    if target_metadata is None:
        target_metadata = get_base_metadata()

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(config, target_metadata=None):
    """Run migrations in 'online' mode."""
    if target_metadata is None:
        target_metadata = get_base_metadata()

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


def main(config_file: Optional[str] = None) -> None:
    """
    Run database migrations with advanced configuration options.

    Args:
        config_file (Optional[str]): Path to Alembic configuration file.
    """
    # Configure logging
    fileConfig(config_file or 'alembic.ini')

    # Get Alembic configuration
    config = context.config

    # Set SQLAlchemy URL dynamically
    from store_management.database.sqlalchemy.session import DATABASE_URL
    config.set_main_option('sqlalchemy.url', DATABASE_URL)

    # Determine migration mode
    if context.is_offline_mode():
        run_migrations_offline(config)
    else:
        run_migrations_online(config)


if __name__ == '__main__':
    main()


# Advanced Migration CLI Helper
class MigrationCLI:
    @staticmethod
    def create_migration(message: str) -> None:
        """
        Create a new database migration

        Args:
            message (str): Description of migration changes
        """
        import subprocess
        import sys

        subprocess.run([
            sys.executable,
            '-m', 'alembic',
            'revision',
            '--autogenerate',
            '-m',
            message
        ], check=True)

    @staticmethod
    def upgrade(revision: str = 'head') -> None:
        """
        Upgrade database to specific or latest revision

        Args:
            revision (str, optional): Target migration revision. Defaults to 'head'.
        """
        import subprocess
        import sys

        subprocess.run([
            sys.executable,
            '-m', 'alembic',
            'upgrade',
            revision
        ], check=True)

    @staticmethod
    def downgrade(revision: str = '-1') -> None:
        """
        Downgrade database to previous migration

        Args:
            revision (str, optional): Target migration revision. Defaults to previous migration.
        """
        import subprocess
        import sys

        subprocess.run([
            sys.executable,
            '-m', 'alembic',
            'downgrade',
            revision
        ], check=True)


# Utility for tracking migrations
class MigrationTracker:
    @staticmethod
    def get_current_version() -> str:
        """
        Get current database migration version

        Returns:
            str: Current migration revision
        """
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine

        from store_management.database.sqlalchemy.session import DATABASE_URL

        alembic_cfg = Config('alembic.ini')
        script = ScriptDirectory.from_config(alembic_cfg)

        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        return current_rev or 'Base'


# Usage Example
if __name__ == '__main__':
    # CLI-style migration management
    from sys import argv

    if len(argv) > 1:
        command = argv[1]
        if command == 'create':
            MigrationCLI.create_migration(argv[2] if len(argv) > 2 else 'Unnamed Migration')
        elif command == 'upgrade':
            MigrationCLI.upgrade(argv[2] if len(argv) > 2 else 'head')
        elif command == 'downgrade':
            MigrationCLI.downgrade(argv[2] if len(argv) > 2 else '-1')
        elif command == 'version':
            print(f"Current Migration Version: {MigrationTracker.get_current_version()}")