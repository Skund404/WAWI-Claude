# File: store_management/database/initialize.py
"""
Database initialization and setup module.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .sqlalchemy.base import Base  # SQLAlchemy base declarative model
from .sqlalchemy.models.storage import Storage  # Import Storage model
from ..config.settings import get_database_path

# Configure logging
logger = logging.getLogger(__name__)

def initialize_database(drop_existing: bool = False):
    """
    Initialize the database, creating or resetting tables.

    Args:
        drop_existing (bool): Whether to drop existing tables before creation
    """
    try:
        # Ensure database is initialized
        db_path = get_database_path()
        db_url = f'sqlite:///{db_path}'

        # Create engine
        engine = create_engine(db_url, echo=False)

        # Drop tables if specified
        if drop_existing:
            logger.warning("Dropping all existing tables")
            Base.metadata.drop_all(engine)

        # Create all tables
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)

        # Optional: Add initial data
        add_initial_data(engine)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Database table creation failed: {e}", exc_info=True)
        raise

def add_initial_data(engine=None):
    """
    Add initial default data to the database.

    Args:
        engine: SQLAlchemy engine (optional)
    """
    try:
        # If no engine is provided, create one
        if engine is None:
            db_path = get_database_path()
            db_url = f'sqlite:///{db_path}'
            engine = create_engine(db_url)

        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Add default storage locations
            default_storages = [
                Storage(
                    location='Main Warehouse',
                    description='Primary storage location for main inventory',
                    capacity=1000.0,
                    current_usage=0.0
                ),
                Storage(
                    location='Backup Storage',
                    description='Secondary storage for overflow and backup items',
                    capacity=500.0,
                    current_usage=0.0
                ),
                Storage(
                    location='Production Storage',
                    description='Storage area near production line',
                    capacity=250.0,
                    current_usage=0.0
                )
            ]

            # Add default storage locations
            for storage in default_storages:
                # Check if storage location already exists
                existing_storage = session.query(Storage).filter_by(location=storage.location).first()
                if not existing_storage:
                    session.add(storage)

            # Commit the changes
            session.commit()
            logger.info("Initial storage locations added successfully")

        except Exception as data_error:
            session.rollback()
            logger.error(f"Failed to add initial data: {data_error}", exc_info=True)
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in add_initial_data: {e}", exc_info=True)