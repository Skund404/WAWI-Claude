# verify_db.py
import logging
import os
import sys
from pathlib import Path
import sqlalchemy
from sqlalchemy import create_engine, inspect  # Corrected import
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


# Get database path from settings
def get_database_path():
    """
    Determine the database path.

    Returns:
        str: Absolute path to the database file
    """
    try:
        from config.paths import get_database_path
        return get_database_path()
    except ImportError:
        logger.error("Could not import `get_database_path` from `config.paths`.")
        return os.path.abspath("store_management.db")


def verify_database():
    """
    Verifies the existence of the database file.

    Returns:
        bool: True if database exists and is valid, False otherwise
    """
    db_path = get_database_path()
    logger.info(f"Verifying database at: {db_path}")

    if not os.path.exists(db_path):
        logger.error("Database file does not exist.")
        return False

    try:
        # Attempt to connect to the database
        engine = create_engine(f"sqlite:///{db_path}")

        # Test the connection
        with engine.connect() as connection:
            connection.execute(sqlalchemy.text("SELECT 1"))  # Simple test query
            logger.info("Database file exists and is a valid SQLite database.")
        return True
    except Exception as e:
        logger.error(f"An error occurred while verifying the database: {e}")
        return False


def display_table_details():
    """
    Display detailed information about the tables and their columns.
    """
    db_path = get_database_path()
    try:
        # Dynamically import all models
        model_prefixes = [
            'database.models.base',
            'database.models.customer',
            'database.models.components',
            'database.models.hardware',
            'database.models.inventory',
            'database.models.leather',
            'database.models.material',
            'database.models.project',
            'database.models.transaction',
            'database.models.supplier',
            'database.models.sales',
            'database.models.order',
            'database.models.part',
            'database.models.pattern',
            'database.models.product',
            'database.models.production',
            'database.models.shopping_list',
            'database.models.storage'
        ]

        # Import modules to ensure models are registered
        for prefix in model_prefixes:
            try:
                __import__(prefix)
            except ImportError as e:
                logger.warning(f"Could not import {prefix}: {e}")

        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")

        # Use sqlalchemy.inspect directly
        inspector = inspect(engine)

        table_names = inspector.get_table_names()
        logger.info("Database Schema Analysis:")

        if not table_names:
            logger.warning("No tables found in the database.")
            return

        for table_name in table_names:
            logger.info(f"  Table: {table_name}")
            columns = inspector.get_columns(table_name)
            for column in columns:
                # Safely handle different types of column information
                col_info = [f"{column['name']} ({column['type']})"]

                # Add additional column details safely
                if column.get('primary_key', False):
                    col_info.append("Primary Key")
                if column.get('nullable', False):
                    col_info.append("Nullable")
                if column.get('default') is not None:
                    col_info.append(f"Default: {column['default']}")

                logger.info("    - " + ", ".join(col_info))

    except Exception as e:
        logger.error(f"Error displaying table details: {e}")
        import traceback
        traceback.print_exc()  # This will print the full stack trace


if __name__ == "__main__":
    if verify_database():
        logger.info("Database verification passed.")
        display_table_details()
    else:
        logger.error("Database verification failed.")