# File: store_management/database/initialize.py

import logging
from sqlalchemy_utils import drop_database
from .config import database_manager
from .sqlalchemy.models import Base  # Import your Base and all models

logger = logging.getLogger(__name__)


def initialize_database(drop_existing: bool = False):
    """
    Comprehensive database initialization process

    Args:
        drop_existing (bool): Whether to drop existing database before creation
    """
    try:
        # Optional: Drop existing database
        if drop_existing:
            try:
                drop_database(database_manager.database_url)
                logger.warning("Existing database dropped")
            except Exception as drop_error:
                logger.error(f"Database drop failed: {drop_error}")

        # Create all tables
        Base.metadata.create_all(database_manager.engine)
        logger.info("Database tables created successfully")

        # Additional initialization steps can be added here
        # For example: create initial admin user, add default data

        # Verify connection
        if not database_manager.test_connection():
            raise Exception("Database connection verification failed")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def add_initial_data():
    """
    Optional method to add initial data to the database
    """
    try:
        with database_manager.session_scope() as session:
            # Example: Add initial data
            # session.add(SomeInitialData())
            pass
    except Exception as e:
        logger.error(f"Initial data insertion failed: {e}")
        raise


# Execution script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        # Interactive initialization
        print("Store Management Database Initialization")
        drop_choice = input("Drop existing database? (y/N): ").lower()

        initialize_database(drop_existing=(drop_choice == 'y'))

        add_initial_data_choice = input("Add initial data? (y/N): ").lower()
        if add_initial_data_choice == 'y':
            add_initial_data()

        print("Database initialization complete.")

    except Exception as e:
        print(f"Initialization failed: {e}")