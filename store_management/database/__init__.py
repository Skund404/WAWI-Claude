# database/initialize.py
"""
Database initialization script that creates all tables and adds initial data
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import importlib

from database.config import get_database_url
from database.session import get_db_session

# Import models explicitly to ensure they're registered
# Import order is important for foreign key dependencies
from database.models.base import Base, BaseModel
from database.models.supplier import Supplier
from database.models.leather import Leather
from database.models.part import Part
from database.models.storage import Storage
from database.models.product import Product
from database.models.recipe import Recipe, RecipeItem
from database.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.transaction import InventoryTransaction, LeatherTransaction, TransactionType


def initialize_database(drop_existing=False):
    """
    Initialize the database by creating all tables.

    Args:
        drop_existing (bool): If True, drop all existing tables before creating
    """
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)

        logging.info("Creating database tables...")

        if drop_existing:
            logging.warning("Dropping all existing tables!")
            Base.metadata.drop_all(engine)

        # Ensure all models are imported and registered
        # This is a safeguard to prevent missing tables
        _ensure_all_models_loaded()

        # Create all tables
        Base.metadata.create_all(engine)

        # Add initial data if needed
        add_initial_data(engine)

        logging.info("Database initialization completed successfully.")

    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
        raise


def _ensure_all_models_loaded():
    """
    Helper function to ensure all model modules are loaded.
    This helps prevent issues with missing tables due to modules not being imported.
    """
    model_modules = [
        'database.models.supplier',
        'database.models.leather',
        'database.models.part',
        'database.models.storage',
        'database.models.product',
        'database.models.recipe',
        'database.models.order',
        'database.models.shopping_list',
        'database.models.transaction'
    ]

    for module_name in model_modules:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            logging.warning(f"Could not import model module {module_name}: {e}")


def add_initial_data(engine):
    """
    Add initial data to the database

    Args:
        engine: SQLAlchemy engine instance
    """
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if we have any suppliers, if not add a default one
        if session.query(Supplier).count() == 0:
            default_supplier = Supplier(
                name="Default Supplier",
                contact_name="Contact Person",
                email="contact@supplier.com",
                phone="123-456-7890",
                address="123 Main St, Anytown, USA",
                notes="Default supplier for system initialization",
                is_active=True,
                rating=3.0
            )
            session.add(default_supplier)
            logging.info("Added default supplier")

        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Error adding initial data: {str(e)}")
    finally:
        session.close()