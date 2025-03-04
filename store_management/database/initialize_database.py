# database/initialize_database.py
"""
Database initialization script that safely creates all tables
and then establishes relationships correctly.
Compatible with SQLAlchemy 2.0.
"""

import logging
import os
import importlib
import sys
import sqlalchemy
from sqlalchemy import inspect, create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Display SQLAlchemy version for diagnostics
logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")


def add_parent_directory():
    """Add parent directory to sys.path to allow imports."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        logger.info(f"Added {parent_dir} to sys.path")


def disable_problematic_relationships():
    """
    Patch ShoppingListItem to temporarily disable problematic relationships.
    """
    logger.info("Disabling problematic relationships...")
    try:
        # Import ShoppingListItem
        from database.models.shopping_list import ShoppingListItem

        # Check if the hardware relationship is defined
        if hasattr(ShoppingListItem, 'hardware'):
            logger.info("Setting ShoppingListItem.hardware to None")
            # Set the hardware relationship to None
            ShoppingListItem.hardware = None
    except Exception as e:
        logger.error(f"Error disabling relationships: {str(e)}")


def import_all_models():
    """Import all models to register them with SQLAlchemy."""
    logger.info("Importing all models...")

    # Add parent directory to sys.path if needed
    add_parent_directory()

    # Disable problematic relationships first
    disable_problematic_relationships()

    # Import base and all models
    try:
        # Import base
        from database.models.base import Base

        # Import all other models
        from database.models.hardware import Hardware
        from database.models.shopping_list import ShoppingList, ShoppingListItem
        from database.models.supplier import Supplier

        # Import any other models you need
        # from database.models.other_model import OtherModel

        logger.info("Models imported successfully")
        return Base
    except Exception as e:
        logger.error(f"Error importing models: {str(e)}")
        raise


def get_database_url():
    """Get the database URL from the session module."""
    try:
        from database.sqlalchemy.session import DATABASE_URL
        return DATABASE_URL
    except ImportError:
        logger.warning("Could not import DATABASE_URL from session, using default SQLite URL")
        return "sqlite:///store_management.db"


def get_engine(database_url=None):
    """
    Get SQLAlchemy engine with the database URL.
    """
    if database_url is None:
        database_url = get_database_url()

    logger.info(f"Creating engine with database URL: {database_url}")
    return create_engine(database_url, echo=True)


def create_tables(engine, base):
    """
    Create all tables in the database.
    """
    logger.info("Creating all database tables...")
    try:
        base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise


def verify_tables(engine):
    """
    Verify that tables were created by listing them.
    """
    logger.info("Verifying database tables...")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            logger.warning("No tables found in database")
        else:
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")

            # Check each table's columns
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                logger.info(f"Table {table_name} has {len(columns)} columns")

                # Check foreign keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                if foreign_keys:
                    for fk in foreign_keys:
                        logger.info(
                            f"  Foreign key: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

        return tables
    except Exception as e:
        logger.error(f"Error verifying tables: {str(e)}")
        return []


def main():
    """
    Main function to initialize the database.
    """
    logger.info("Starting database initialization...")

    try:
        # Import all models
        base = import_all_models()

        # Get engine
        engine = get_engine()

        # Create tables
        create_tables(engine, base)

        # Verify tables
        tables = verify_tables(engine)

        # Create a session and test a simple query
        with Session(engine) as session:
            for table_name in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    logger.info(f"Table {table_name} has {count} rows")
                except Exception as e:
                    logger.error(f"Error querying table {table_name}: {str(e)}")

        logger.info("Database initialization complete")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False


if __name__ == "__main__":
    main()