# database/sqlalchemy/migrations/manager.py

from typing import List, Optional
import logging
from pathlib import Path
from datetime import datetime
import alembic.config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.utils.error_handler import DatabaseError
from store_management.utils.logger import logger


class MigrationManager:
    """Handles database migrations and schema updates."""

    def __init__(self, database_url: str, migrations_path: Optional[Path] = None):
        """Initialize migration manager.

        Args:
            database_url: Database connection URL
            migrations_path: Optional custom path to migrations directory
        """
        self.database_url = database_url
        self.migrations_path = migrations_path or Path(__file__).parent / 'versions'
        self.engine = create_engine(database_url)
        self.alembic_cfg = self._create_alembic_config()

    def _create_alembic_config(self) -> alembic.config.Config:
        """Create Alembic configuration."""
        cfg = alembic.config.Config()
        cfg.set_main_option('script_location', str(self.migrations_path.parent))
        cfg.set_main_option('sqlalchemy.url', self.database_url)
        return cfg

    def check_current_version(self) -> str:
        """Get current database version.

        Returns:
            Current revision identifier
        """
        with self.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return context.get_current_revision() or 'base'

    def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations.

        Returns:
            List of pending migration identifiers
        """
        current = self.check_current_version()
        script = ScriptDirectory.from_config(self.alembic_cfg)
        pending = []

        for rev in script.walk_revisions():
            if rev.revision != current:
                pending.append(rev.revision)
            else:
                break

        return pending

    def create_backup(self) -> Path:
        """Create database backup before migration.

        Returns:
            Path to backup file
        """
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'pre_migration_{timestamp}.sqlite'

        # Create backup using database specific method
        if self.database_url.startswith('sqlite'):
            import shutil
            db_path = self.database_url.replace('sqlite:///', '')
            shutil.copy2(db_path, backup_path)
        else:
            # Add support for other databases as needed
            raise NotImplementedError("Backup only supported for SQLite")

        return backup_path

    def run_migrations(self, target: Optional[str] = 'head') -> None:
        """Run pending migrations.

        Args:
            target: Target revision (defaults to latest)
        """
        try:
            # Create backup
            backup_path = self.create_backup()
            logger.info(f"Created backup at {backup_path}")

            # Run migrations
            with self.engine.begin() as connection:
                # Update alembic_version table if it doesn't exist
                if not inspect(self.engine).has_table('alembic_version'):
                    command.stamp(self.alembic_cfg, 'base')

                command.upgrade(self.alembic_cfg, target)

            logger.info(f"Successfully migrated database to {target}")

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise DatabaseError(f"Failed to run migrations: {str(e)}")

    def revert_migration(self, revision: str) -> None:
        """Revert to a specific migration.

        Args:
            revision: Target revision to revert to
        """
        try:
            # Create backup
            backup_path = self.create_backup()
            logger.info(f"Created backup at {backup_path}")

            # Downgrade to specified revision
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Successfully reverted database to {revision}")

        except Exception as e:
            logger.error(f"Reversion failed: {str(e)}")
            raise DatabaseError(f"Failed to revert migration: {str(e)}")

    def verify_migration(self) -> bool:
        """Verify database schema matches models.

        Returns:
            True if verification passes
        """
        try:
            # Get model metadata
            from store_management.database.sqlalchemy.models import Base
            expected_tables = Base.metadata.tables.keys()

            # Get actual database tables
            inspector = inspect(self.engine)
            actual_tables = inspector.get_table_names()

            # Compare tables
            missing_tables = set(expected_tables) - set(actual_tables)
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                return False

            # Verify columns for each table
            for table_name in expected_tables:
                expected_columns = {
                    c.name: c for c in Base.metadata.tables[table_name].columns
                }
                actual_columns = {
                    c['name']: c for c in inspector.get_columns(table_name)
                }

                missing_columns = set(expected_columns) - set(actual_columns)
                if missing_columns:
                    logger.warning(
                        f"Missing columns in {table_name}: {missing_columns}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            raise DatabaseError(f"Failed to verify migration: {str(e)}")