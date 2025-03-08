from database.models.base import metadata
# Relative path: store_management/database/sqlalchemy/migration.py

"""
Database Migration and Initialization Utility

Provides comprehensive solutions for:
- Creating a new database schema
- Dropping existing tables
- Initializing the database with the latest model definitions
- Managing database backups
"""

import os
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Ensure project root is in the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'logs', 'database_migration.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseInitializationError(Exception):
    """
    Custom exception for database initialization failures.
    """
    pass


class DatabaseInitializer:
    """
    Comprehensive database initialization and migration utility.

    Provides robust methods for backing up, dropping, and creating database schemas.
    """

    def __init__(self, db_url: str, backup_dir: Optional[str] = None):
        """
        Initialize database initialization process.

        Args:
            db_url (str): SQLAlchemy database URL
            backup_dir (Optional[str]): Directory for database backups

        Raises:
            DatabaseInitializationError: If initialization fails
        """
        try:
            # Set up backup directory
            self.db_url = db_url
            self.backup_dir = backup_dir or os.path.join(project_root, 'database', 'backups')
            os.makedirs(self.backup_dir, exist_ok=True)

            # Create database engine and session factory
            self.engine = create_engine(db_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
        except Exception as e:
            error_msg = f"Failed to initialize DatabaseInitializer: {e}"
            logger.error(error_msg)
            raise DatabaseInitializationError(error_msg)

    def create_backup(self) -> Optional[str]:
        """
        Create a backup of the existing database if it exists.

        Returns:
            Optional[str]: Path to the backup file, or None if no backup created
        """
        try:
            # Only support SQLite backups for now
            if 'sqlite' in self.db_url:
                db_path = self.db_url.replace('sqlite:///', '')

                if os.path.exists(db_path):
                    # Generate unique backup filename
                    backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_filename = os.path.join(
                        self.backup_dir,
                        f'database_backup_{backup_timestamp}.db'
                    )

                    # Copy the database file
                    shutil.copy(db_path, backup_filename)

                    logger.info(f'Database backup created: {backup_filename}')
                    return backup_filename

            return None

        except Exception as e:
            logger.error(f'Failed to create database backup: {e}')
            return None

    def drop_all_tables(self) -> List[str]:
        """
        Drop all existing tables in the database.

        Returns:
            List[str]: Names of tables that were dropped

        Raises:
            DatabaseInitializationError: If table dropping fails
        """
        try:
            # Use SQLAlchemy inspector to get table names
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()

            # Disable foreign key constraints
            with self.engine.connect() as connection:
                try:
                    connection.execute('PRAGMA foreign_keys=OFF')
                except Exception:
                    logger.warning("Could not disable foreign key constraints")

                # Start a transaction
                trans = connection.begin()
                try:
                    # Drop each table
                    for table in tables:
                        connection.execute(f'DROP TABLE IF EXISTS {table}')

                    # Commit the transaction
                    trans.commit()

                    logger.info(f'Dropped {len(tables)} existing tables')
                    return tables

                except Exception as drop_error:
                    trans.rollback()
                    logger.error(f'Failed to drop tables: {drop_error}')
                    raise DatabaseInitializationError(f"Table dropping failed: {drop_error}")

        except Exception as e:
            logger.error(f'Error during table dropping: {e}')
            raise DatabaseInitializationError(f"Comprehensive table drop failed: {e}")

    def initialize_database(self) -> bool:
        """
        Complete database initialization process.

        Steps:
        1. Create backup of existing database
        2. Drop all existing tables
        3. Create new tables based on current model definitions

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Create backup of existing database
            backup_path = self.create_backup()

            # Attempt to drop tables using multiple methods
            try:
                # First, try SQLAlchemy metadata drop
                from database.models import Base
                Base.metadata.drop_all(bind=self.engine)
            except Exception as drop_error:
                logger.warning(f'Alternative table dropping method failed: {drop_error}')

                try:
                    # Fallback to manual table dropping
                    self.drop_all_tables()
                except Exception as alt_error:
                    logger.error(f'Failed to drop tables: {alt_error}')
                    raise DatabaseInitializationError("Could not drop existing tables")

            # Create new tables
            from database.models import Base
            Base.metadata.create_all(bind=self.engine)

            logger.info('Database successfully initialized with new schema')
            return True

        except Exception as e:
            logger.error(f'Database initialization failed: {e}')
            return False


def run_database_initialization(
        db_url: Optional[str] = 'sqlite:///./store_management.db',
        backup_dir: Optional[str] = None,
        force: bool = False
) -> bool:
    """
    Execute database initialization.

    Args:
        db_url (Optional[str]): SQLAlchemy database URL
        backup_dir (Optional[str]): Directory for database backups
        force (bool): Force initialization even if database exists

    Returns:
        bool: Initialization success status
    """
    try:
        # Create initializer
        initializer = DatabaseInitializer(db_url, backup_dir)

        # Additional safety for non-SQLite databases
        if 'sqlite' not in db_url and not force:
            logger.warning('Non-SQLite database detected. Use force=True to proceed.')
            return False

        # Run initialization
        initialization_success = initializer.initialize_database()

        if initialization_success:
            logger.info('Database initialization completed successfully')
        else:
            logger.error('Database initialization encountered issues')

        return initialization_success

    except Exception as e:
        logger.error(f'Database initialization failed: {e}')
        return False


# Script execution when run directly
if __name__ == '__main__':
    # Set up paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    backup_dir = os.path.join(project_root, 'database', 'backups')
    db_url = 'sqlite:///./store_management.db'

    # Run initialization
    success = run_database_initialization(
        db_url=db_url,
        backup_dir=backup_dir,
        force=True
    )

    # Exit with appropriate status code
    sys.exit(0 if success else 1)