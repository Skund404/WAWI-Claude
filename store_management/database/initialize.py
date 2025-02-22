"""
File: database/initialize.py
Database initialization functions.
Creates database tables and adds initial data.
"""
import logging
from typing import Optional, Union
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Import from the consolidated model location
from database.models.base import Base
# We don't need to import all models explicitly since they register with Base.metadata

def initialize_database(drop_existing: Optional[bool] = False) -> None:
    """
    Initialize the database by creating all defined tables.

    Args:
        drop_existing: If True, drops all existing tables before creating new ones

    Raises:
        SQLAlchemyError: If database initialization fails
    """
    try:
        from database.sqlalchemy.config import get_database_url
        db_url = get_database_url()
        engine = create_engine(db_url)

        if drop_existing:
            logging.info("Dropping all existing tables...")
            Base.metadata.drop_all(engine)

        logging.info("Creating database tables...")
        Base.metadata.create_all(engine)

        # Optionally add initial data
        add_initial_data(engine)

        logging.info("Database initialization complete")
    except SQLAlchemyError as e:
        logging.error(f"Database initialization failed: {str(e)}")
        raise

def add_initial_data(engine) -> None:
    """
    Add initial data to the database if needed.

    Args:
        engine: SQLAlchemy engine instance
    """
    # Example implementation - adjust according to your needs
    try:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Example: Create default storage locations if none exist
            from database.models.storage import Storage

            if session.query(Storage).count() == 0:
                logging.info("Adding default storage locations...")

                default_storage = [
                    Storage(name="Main Warehouse", location="Building A",
                            description="Main storage area", capacity=1000.0),
                    Storage(name="Production Floor", location="Building B",
                            description="Production area storage", capacity=500.0),
                    Storage(name="Retail Storage", location="Store Front",
                            description="Retail area storage", capacity=200.0)
                ]

                session.add_all(default_storage)
                session.commit()

            # Add other initial data as needed

        except Exception as e:
            session.rollback()
            logging.error(f"Failed to add initial data: {str(e)}")
            raise
        finally:
            session.close()
    except Exception as e:
        logging.error(f"Error in add_initial_data: {str(e)}")