# Path: database/initialize.py
import logging
from typing import Optional

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, NoSuchTableError
from sqlalchemy.schema import CreateTable

from config.settings import get_database_path
from database.sqlalchemy.config import get_database_url
from utils.logger import get_logger

# Dynamically import models to ensure they're loaded
from database.models.storage import Storage  # Ensure model is imported
from database.sqlalchemy.base import Base

logger = get_logger(__name__)


def create_storage_table(engine):
    """
    Create tables based on SQLAlchemy models, handling existing tables.

    Args:
        engine: SQLAlchemy engine
    """
    try:
        # Inspect existing tables
        inspector = inspect(engine)

        # Create tables, extending existing ones
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                # Create table if it doesn't exist
                table.create(engine)
                logger.info(f"Created table: {table.name}")
            else:
                # Check and add missing columns
                existing_columns = [col['name'] for col in inspector.get_columns(table.name)]
                for column in table.columns:
                    if column.name not in existing_columns:
                        try:
                            # Add missing column
                            add_column_sql = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column.type}"
                            with engine.connect() as connection:
                                connection.execute(add_column_sql)
                            logger.info(f"Added column {column.name} to table {table.name}")
                        except Exception as col_error:
                            logger.warning(f"Could not add column {column.name}: {col_error}")

        logger.info("Storage table created or verified successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating storage table: {e}")
        raise


def migrate_storage_table(engine) -> None:
    """
    Perform migration for the storage table.

    Args:
        engine: SQLAlchemy engine
    """
    try:
        # Create or update tables
        create_storage_table(engine)

        logger.info("Storage table migration completed successfully")
    except NoSuchTableError:
        logger.error("Storage table does not exist and could not be created")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Storage table migration error: {e}")
        raise


def add_initial_data(session) -> None:
    """
    Add initial data to the database tables.

    Args:
        session: SQLAlchemy session
    """
    try:
        # Add initial storage locations
        initial_storage_locations = [
            Storage(
                name='Main Warehouse',
                location='Central Storage Area',
                capacity=1000.0,
                current_occupancy=0.0,
                type='Warehouse',
                description='Primary storage location for inventory',
                status='active'
            ),
            Storage(
                name='Small Storage Room',
                location='Side Building',
                capacity=250.0,
                current_occupancy=0.0,
                type='Storage Room',
                description='Secondary storage for less-used items',
                status='active'
            )
        ]

        # Check and add initial storage locations
        for location in initial_storage_locations:
            existing = session.query(Storage).filter_by(name=location.name).first()
            if not existing:
                session.add(location)

        session.commit()
        logger.info("Initial storage locations added successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding initial storage locations: {e}")
        raise


def initialize_database(drop_existing: bool = False) -> None:
    """
    Initialize the entire database, creating tables and adding initial data.

    Args:
        drop_existing (bool): Whether to drop existing tables before recreation
    """
    try:
        logger.info("Initializing database...")

        # Get database URL and create engine
        db_url = get_database_url()
        engine = create_engine(db_url)

        # If drop_existing is True, drop all tables (use with caution)
        if drop_existing:
            Base.metadata.drop_all(bind=engine)

        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Perform migrations and table creation
            migrate_storage_table(engine)

            # Add initial data
            add_initial_data(session)
        except Exception as init_error:
            session.rollback()
            raise
        finally:
            session.close()

        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise