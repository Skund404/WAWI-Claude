#!/usr/bin/env python
# project_initializer.py
"""
Project initializer that ensures correct import paths and database setup.

This script ensures the project root directory is in sys.path and
initializes the database with proper handling of circular imports.
Run this script from any directory to properly set up the project.
"""

import logging
import os
import sys
import importlib
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("project_initializer")


def find_project_root():
    """
    Find the project root directory based on key files/folders.

    Returns:
        Path: Path to the project root directory
    """
    # Start from the script directory
    current_dir = Path(__file__).resolve().parent

    # Look for indicators of project root
    indicators = [
        "database/models",
        "utils/circular_import_resolver.py",
        "config/settings.py",
        "requirements.txt"
    ]

    # Try current directory first
    for indicator in indicators:
        if (current_dir / indicator).exists():
            logger.info(f"Project root found at: {current_dir}")
            return current_dir

    # Search parent directories
    for _ in range(5):  # Don't go too far up
        current_dir = current_dir.parent
        for indicator in indicators:
            if (current_dir / indicator).exists():
                logger.info(f"Project root found at: {current_dir}")
                return current_dir

    # Fallback to script directory if root not found
    logger.warning(f"Could not find project root, using script directory: {Path(__file__).parent}")
    return Path(__file__).parent


def setup_python_path(project_root):
    """
    Set up Python path to ensure imports work correctly.

    Args:
        project_root (Path): Path to the project root directory
    """
    # Add project root to sys.path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
        logger.info(f"Added {project_root_str} to sys.path")

    # Print Python path for debugging
    logger.debug(f"Python path: {sys.path}")


def configure_circular_imports():
    """
    Configure the circular import resolver specifically for Order and OrderItem.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import the circular import resolver
        from utils.circular_import_resolver import register_lazy_import, register_module_alias, register_class_alias

        # Register Order and OrderItem
        register_lazy_import('Order', 'database.models.order')
        register_lazy_import('OrderItem', 'database.models.order_item')
        register_lazy_import('database.models.order.Order', 'database.models.order')
        register_lazy_import('database.models.order_item.OrderItem', 'database.models.order_item')

        # Register module aliases
        register_module_alias('database.models.order.OrderItem', 'database.models.order_item')
        register_module_alias('database.models.order_item.Order', 'database.models.order')

        # Register class aliases
        register_class_alias('database.models.order', 'OrderItem', 'database.models.order_item')
        register_class_alias('database.models.order_item', 'Order', 'database.models.order')

        logger.info("Circular import resolver configured successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to configure circular import resolver: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_database(recreate=False):
    """
    Initialize the database with proper circular import handling.

    Args:
        recreate (bool): Whether to recreate the database

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First, configure circular imports
        if not configure_circular_imports():
            logger.error("Failed to configure circular imports")
            return False

        # Try to use your existing initialization
        try:
            logger.info("Attempting to initialize database with existing function...")
            from database.initialize import initialize_database as existing_init

            # Call the existing initialization function
            engine = existing_init(recreate)
            if engine:
                logger.info("Database initialized successfully using existing function")
                return True
        except (ImportError, Exception) as e:
            logger.warning(f"Could not use existing initialization function: {e}")

        # Fallback to basic initialization
        logger.info("Using basic initialization...")

        # Import Base model
        from database.models.base import Base

        # Get database path
        try:
            from config.settings import get_database_path
            db_path = get_database_path()
        except ImportError:
            # Fallback to default
            data_dir = Path(find_project_root()) / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "store_management.db")

        logger.info(f"Using database path: {db_path}")

        # Create SQLAlchemy engine
        from sqlalchemy import create_engine
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url, echo=False)

        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")

        # Resolve lazy relationships
        from utils.circular_import_resolver import resolve_lazy_relationships
        resolve_lazy_relationships()

        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_order_models():
    """
    Fix circular imports between Order and OrderItem models.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Configure circular imports first
        if not configure_circular_imports():
            return False

        # Import Order and OrderItem
        logger.info("Importing Order and OrderItem models...")
        try:
            from database.models.order import Order
            from database.models.order_item import OrderItem

            # Configure relationships
            from sqlalchemy.orm import relationship

            # Check if relationships already exist
            if not hasattr(Order, 'items'):
                logger.info("Adding items relationship to Order")
                Order.items = relationship(
                    'OrderItem',
                    back_populates='order',
                    cascade='all, delete-orphan',
                    lazy='selectin'
                )

            if not hasattr(OrderItem, 'order'):
                logger.info("Adding order relationship to OrderItem")
                OrderItem.order = relationship(
                    'Order',
                    back_populates='items',
                    lazy='selectin'
                )

            logger.info("Order models fixed successfully")
            return True
        except ImportError as e:
            logger.error(f"Could not import Order models: {e}")
            return False

    except Exception as e:
        logger.error(f"Error fixing Order models: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_database():
    """
    Verify that the database is properly set up.

    Returns:
        bool: True if verification passed, False otherwise
    """
    try:
        # Try to import key models
        logger.info("Verifying database models...")

        from database.models.base import Base
        logger.info("Base model imported successfully")

        from database.models.order import Order
        logger.info("Order model imported successfully")

        from database.models.order_item import OrderItem
        logger.info("OrderItem model imported successfully")

        # Verify database connection
        logger.info("Verifying database connection...")

        # Get database path
        try:
            from config.settings import get_database_path
            db_path = get_database_path()
        except ImportError:
            # Fallback to default
            data_dir = Path(find_project_root()) / "data"
            db_path = str(data_dir / "store_management.db")

        # Check if database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at: {db_path}")
            return False

        # Try to connect
        from sqlalchemy import create_engine, inspect, text
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result != 1:
                logger.error("Database connection test failed")
                return False

            # Check tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            logger.info(f"Found {len(tables)} tables in database")

            # Check for essential tables
            essential_tables = ['orders', 'order_items']
            missing_tables = [table for table in essential_tables if table not in tables]

            if missing_tables:
                logger.error(f"Missing essential tables: {missing_tables}")
                return False

        logger.info("Database verification passed")
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function for project initialization."""
    parser = argparse.ArgumentParser(description="Initialize the project and database")
    parser.add_argument("--recreate", action="store_true", help="Recreate the database")
    parser.add_argument("--verify", action="store_true", help="Verify database setup")
    parser.add_argument("--fix-order", action="store_true", help="Fix Order model circular imports")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    # Find project root and set up Python path
    project_root = find_project_root()
    setup_python_path(project_root)

    # Print system info
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Project root: {project_root}")

    # Fix Order model circular imports if requested
    if args.fix_order:
        logger.info("Fixing Order model circular imports...")
        if fix_order_models():
            logger.info("Order model circular imports fixed successfully")
        else:
            logger.error("Failed to fix Order model circular imports")
            return 1

    # Initialize database
    if not args.verify:
        logger.info("Initializing database...")
        if initialize_database(args.recreate):
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed")
            return 1

    # Verify database if requested
    if args.verify:
        logger.info("Verifying database...")
        if verify_database():
            logger.info("Database verification passed")
        else:
            logger.error("Database verification failed")
            return 1

    logger.info("Project initialization completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())