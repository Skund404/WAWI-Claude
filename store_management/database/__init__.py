# database/__init__.py
"""Database package initialization."""

import logging
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from .models.base import Base, BaseModel
from .models.transaction import TransactionType
from .models.transaction import InventoryTransaction, LeatherTransaction
from .models.supplier import Supplier
from .models.part import Part
from .models.leather import Leather
from .sqlalchemy.session import get_db_session, init_database, close_db_session
from .models.leather import Leather #add this import
from .models.part import Part #add this import
from .models.project import Project #add this import
from .models.project_component import ProjectComponent #add this import
from .models.transaction import LeatherTransaction, InventoryTransaction, TransactionType #add this import

logger = logging.getLogger(__name__)


def initialize_database(drop_existing: bool = False) -> None:
    """
    Initialize the database schema and add initial data.

    Args:
        drop_existing: If True, drops all existing tables before recreating
    """
    try:
        logger.info("Creating database tables...")

        # Initialize the database engine and session
        engine = init_database()
        if engine is None:
            raise RuntimeError("Failed to initialize database engine")

        if drop_existing:
            logger.info("Dropping existing tables...")
            Base.metadata.drop_all(engine)

        # Create all tables
        Base.metadata.create_all(engine)

        try:
            # Add initial data
            _add_initial_data()
        except Exception as e:
            logger.error(f"Error adding initial data: {str(e)}")
            raise

        logger.info("Database initialization completed successfully.")

    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        close_db_session()


def _add_initial_data() -> None:
    """Add initial data to the database."""
    session = get_db_session()
    try:
        # Check if we already have data
        if session.query(Supplier).first() is not None:
            logger.info("Initial data already exists, skipping...")
            return

        # Add initial supplier
        initial_supplier = Supplier(
            name="Default Supplier",
            notes="Default system supplier"
        )
        session.add(initial_supplier)

        # Add more initial data as needed

        session.commit()
        logger.info("Initial data added successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding initial data: {str(e)}")
        raise
    finally:
        session.close()


__all__ = [
    'Base',
    'BaseModel',
    'InventoryTransaction',
    'LeatherTransaction',
    'Supplier',
    'Part',
    'Leather',
    'initialize_database',
    'get_db_session',
    'close_db_session'
]