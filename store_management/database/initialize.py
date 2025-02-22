# Path: database/initialize.py
import logging
from typing import Optional
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.sqlalchemy.config import DatabaseConfig
from database.models.storage import Storage  # Adjust this import as needed
from utils.logger import log_error


def check_column_exists(table_name: str, column_name: str) -> bool:
    """
    Check if a specific column exists in a table.

    Args:
        table_name (str): Name of the table to check
        column_name (str): Name of the column to verify

    Returns:
        bool: True if column exists, False otherwise
    """
    try:
        config = DatabaseConfig()
        engine = config.get_engine()
        inspector = engine.dialect.inspector(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except Exception as e:
        log_error(f"Error checking column {column_name} in {table_name}", e)
        return False


def migrate_storage_table():
    """
    Perform migrations specific to the storage table.

    Checks and adds any missing columns to the storage table.
    Handles database session and potential errors.
    """
    try:
        config = DatabaseConfig()
        engine = config.get_engine()
        metadata = MetaData()
        metadata.reflect(bind=engine)

        # Get or create storage table
        storage_table = Table('storage', metadata, autoload_with=engine)

        # Start a session
        session = config.get_session()

        try:
            # Add migration logic here
            # Example: Add a new column if it doesn't exist
            if not check_column_exists('storage', 'capacity'):
                with engine.begin() as connection:
                    connection.execute(f'ALTER TABLE storage ADD COLUMN capacity REAL')
                logging.info("Added 'capacity' column to storage table")

            # Commit changes
            session.commit()
            logging.info("Storage table migration completed successfully")

        except SQLAlchemyError as migrate_err:
            # Rollback in case of migration error
            session.rollback()
            log_error("Storage table migration failed", migrate_err)
            raise

        finally:
            # Always close the session
            session.close()

    except Exception as e:
        log_error("Comprehensive storage table migration error", e)
        raise


def add_initial_data():
    """
    Add initial data to the database if it's empty.

    This function can be used to populate the database with default/seed data.
    """
    try:
        config = DatabaseConfig()
        session = config.get_session()

        try:
            # Check if storage locations exist
            existing_storage = session.query(Storage).count()

            if existing_storage == 0:
                # Add default storage locations
                default_locations = [
                    Storage(name='Main Warehouse', location='A1', max_capacity=1000),
                    Storage(name='Incoming Goods', location='B2', max_capacity=500),
                    Storage(name='Finished Products', location='C3', max_capacity=750)
                ]

                session.add_all(default_locations)
                session.commit()
                logging.info("Added initial storage locations")
            else:
                logging.info("Storage locations already exist")

        except SQLAlchemyError as data_err:
            session.rollback()
            log_error("Failed to add initial storage data", data_err)
            raise

        finally:
            session.close()

    except Exception as e:
        log_error("Comprehensive initial data addition error", e)
        raise


def initialize_database(drop_existing: bool = False):
    """
    Initialize the database, optionally dropping existing tables.

    Args:
        drop_existing (bool, optional): Whether to drop and recreate all tables.
                                        Defaults to False.
    """
    try:
        logging.info("Initializing database...")
        config = DatabaseConfig()
        engine = config.get_engine()

        # If drop_existing is True, drop all tables and recreate
        if drop_existing:
            logging.warning("Dropping all existing tables")
            from database.sqlalchemy.model_utils import get_model_classes
            from sqlalchemy.schema import DropTable

            # Get all model classes and their table metadata
            metadata = MetaData()
            metadata.reflect(bind=engine)

            # Drop all tables
            with engine.begin() as connection:
                for table in reversed(metadata.sorted_tables):
                    connection.execute(DropTable(table))
                logging.info("All tables dropped successfully")

        # Create all tables that haven't been created
        from database.sqlalchemy.base import Base  # Import Base from SQLAlchemy configuration
        Base.metadata.create_all(engine)
        logging.info("Database tables created successfully")

        # Run migrations
        migrate_storage_table()

        # Add initial data
        add_initial_data()

        logging.info("Database initialization completed successfully")

    except Exception as e:
        log_error("Database initialization failed", e)
        raise