# scripts/init_db.py
"""
Simple script to initialize the database with all tables.
This bypasses the problematic relationship and creates the schema.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Initialize the database."""
    # Add parent directory to sys.path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        logger.info(f"Added {parent_dir} to sys.path")

    # Import required modules
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")

        # First, apply the patch to disable problematic relationships
        logger.info("Applying ShoppingListItem patch...")
        from database.models.shopping_list import ShoppingListItem

        # Disable the problematic relationship
        if hasattr(ShoppingListItem, 'hardware'):
            logger.info("Disabling ShoppingListItem.hardware relationship")
            ShoppingListItem.hardware = None

        # Import the Base class and all models to register them
        logger.info("Importing models...")
        from database.models.base import Base
        from database.models.hardware import Hardware
        from database.models.supplier import Supplier
        # Import other models as needed

        # Get database engine
        logger.info("Creating database engine...")
        from sqlalchemy import create_engine
        from database.sqlalchemy.session import DATABASE_URL

        engine = create_engine(DATABASE_URL, echo=True)

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)

        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")
        logger.info("Database initialization complete")

        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


if __name__ == "__main__":
    main()