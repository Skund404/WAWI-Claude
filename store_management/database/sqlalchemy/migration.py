"""
Database Migration and Initialization Utility

This script provides a comprehensive solution for:
- Creating a new database schema
- Dropping existing tables
- Initializing the database with the latest model definitions
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Dynamically adjust Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# SQLAlchemy imports
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Import your project models
from database.sqlalchemy.models import Base

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'logs', 'database_migration.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """
    Comprehensive database initialization and migration utility
    """

    def __init__(self, db_url: str, backup_dir: Optional[str] = None):
        """
        Initialize database initialization process

        Args:
            db_url (str): SQLAlchemy database URL
            backup_dir (str, optional): Directory for database backups
        """
        # Normalize paths
        self.db_url = db_url

        # Set backup directory
        self.backup_dir = backup_dir or os.path.join(
            project_root, 'database', 'backups'
        )
        os.makedirs(self.backup_dir, exist_ok=True)

        # Create engine and session
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_backup(self) -> Optional[str]:
        """
        Create a backup of the existing database if it exists

        Returns:
            Optional[str]: Path to the backup file, or None if no backup created
        """
        try:
            # Check if database file exists (for SQLite)
            if 'sqlite' in self.db_url:
                db_path = self.db_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    # Generate backup filename
                    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_filename = os.path.join(
                        self.backup_dir,
                        f"database_backup_{backup_timestamp}.db"
                    )

                    # Copy database file
                    import shutil
                    shutil.copy(db_path, backup_filename)

                    logger.info(f"Database backup created: {backup_filename}")
                    return backup_filename

            return None

        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return None

    def drop_all_tables(self):
        """
        Drop all existing tables in the database
        """
        try:
            # Get inspector to list existing tables
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()

            # Create a connection
            with self.engine.connect() as connection:
                # Disable foreign key constraints
                try:
                    connection.execute("PRAGMA foreign_keys=OFF")
                except Exception:
                    # Ignore if PRAGMA is not supported
                    pass

                # Begin a transaction
                trans = connection.begin()

                try:
                    # Drop all tables
                    for table in tables:
                        connection.execute(f"DROP TABLE IF EXISTS {table}")

                    # Commit the transaction
                    trans.commit()
                    logger.info(f"Dropped {len(tables)} existing tables")

                except Exception as drop_error:
                    # Rollback if there's an error
                    trans.rollback()
                    logger.error(f"Failed to drop tables: {drop_error}")
                    raise

        except Exception as e:
            logger.error(f"Error during table dropping: {e}")
            raise

    def initialize_database(self):
        """
        Complete database initialization process

        1. Create backup of existing database
        2. Drop all existing tables
        3. Create new tables based on current model definitions
        """
        try:
            # 1. Create backup
            backup_path = self.create_backup()

            # 2. Drop existing tables
            try:
                Base.metadata.drop_all(bind=self.engine)
            except Exception as drop_error:
                logger.warning(f"Alternative table dropping method failed: {drop_error}")
                try:
                    self.drop_all_tables()
                except Exception as alt_error:
                    logger.error(f"Failed to drop tables: {alt_error}")
                    raise

            # 3. Create new tables
            Base.metadata.create_all(bind=self.engine)

            logger.info("Database successfully initialized with new schema")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False


def run_database_initialization(
    db_url: Optional[str] = "sqlite:///./store_management.db",
    backup_dir: Optional[str] = None,
    force: bool = False
) -> bool:
    """
    Execute database initialization

    Args:
        db_url (str, optional): SQLAlchemy database URL
        backup_dir (str, optional): Directory for database backups
        force (bool, optional): Force initialization even if database exists

    Returns:
        bool: Initialization success status
    """
    try:
        # Create initializer
        initializer = DatabaseInitializer(db_url, backup_dir)

        # Validate database URL
        if 'sqlite' not in db_url and not force:
            logger.warning("Non-SQLite database detected. Use force=True to proceed.")
            return False

        # Run initialization
        initialization_success = initializer.initialize_database()

        if initialization_success:
            logger.info("Database initialization completed successfully")
        else:
            logger.error("Database initialization encountered issues")

        return initialization_success

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


# Main execution block
if __name__ == "__main__":
    # Set default paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    backup_dir = os.path.join(project_root, 'database', 'backups')

    # Default database URL
    db_url = "sqlite:///./store_management.db"

    # Run initialization with force option
    success = run_database_initialization(
        db_url=db_url,
        backup_dir=backup_dir,
        force=True  # Force initialization
    )

    # Exit with appropriate status code
    sys.exit(0 if success else 1)