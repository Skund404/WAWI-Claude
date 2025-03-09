#!/usr/bin/env python
# initialize_database.py
"""
Database initialization script for the leatherworking application.

This script handles:
- Database creation and schema initialization
- Loading models in the correct dependency order
- Seeding the database with sample data
- Database verification and validation
"""

import argparse
import importlib
import json
import logging
import os
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_path() -> str:
    """
    Determine the path for the SQLite database.

    Returns:
        str: Absolute path to the database file
    """
    base_dir = Path(__file__).resolve().parent
    return str(base_dir / 'leatherworking_database.db')


def get_backup_path(operation: str) -> str:
    """
    Generate a path for database backup.

    Args:
        operation (str): The operation being performed, used in filename

    Returns:
        str: Path to the backup file
    """
    base_dir = Path(__file__).resolve().parent
    backup_dir = base_dir / 'database' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return str(backup_dir / f"db_backup_before_{operation}_{timestamp}.db")


def backup_database(db_path: str, operation: str) -> Optional[str]:
    """
    Create a backup of the database before potentially destructive operations.

    Args:
        db_path (str): Path to the database file
        operation (str): Name of the operation being performed

    Returns:
        Optional[str]: Path to the backup file or None if backup failed
    """
    import shutil

    try:
        if not os.path.exists(db_path):
            logger.warning(f"No database file at {db_path} to backup")
            return None

        backup_path = get_backup_path(operation)

        # Copy the database file
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")

        return backup_path
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None


def import_models() -> bool:
    """
    Safely import database models.

    Returns:
        bool: True if models were imported successfully, False otherwise
    """
    try:
        # Import the base model to ensure SQLAlchemy is working
        from database.models.base import Base

        # This will make the import easier to debug
        logger.info("Base model imported successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to import database models: {e}")
        traceback.print_exc()
        return False


def load_all_models() -> bool:
    """
    Load all model modules in dependency order to ensure they are registered with SQLAlchemy.

    Returns:
        bool: True if all essential models were loaded successfully
    """
    try:
        # Define model modules in order of dependency
        model_modules = [
            # Core/foundation modules first
            'database.models.base',
            'database.models.enums',
            'database.models.relationship_tables',

            # Independent entity models next
            'database.models.customer',
            'database.models.supplier',

            # Material and component models
            'database.models.material',
            'database.models.component',
            'database.models.component_material',

            # Pattern and product models
            'database.models.pattern',
            'database.models.product',

            # Tool models
            'database.models.tool',
            'database.models.tool_list',
            'database.models.tool_list_item',

            # Project models
            'database.models.project',
            'database.models.project_component',

            # Sales and purchase models
            'database.models.sales',
            'database.models.sales_item',
            'database.models.purchase',
            'database.models.purchase_item',

            # Picking list models
            'database.models.picking_list',
            'database.models.picking_list_item',

            # Inventory model
            'database.models.inventory',
        ]

        essential_models_loaded = True
        for module_name in model_modules:
            try:
                module = importlib.import_module(module_name)
                logger.debug(f"Loaded model module: {module_name}")

                # Check for any manual relationship initialization function
                if hasattr(module, 'initialize_relationships'):
                    module.initialize_relationships()
                    logger.debug(f"Initialized relationships for {module_name}")

            except ImportError as e:
                logger.warning(f"Could not import module {module_name}: {e}")
                if module_name in ['database.models.base', 'database.models.enums', 'database.models.customer']:
                    essential_models_loaded = False
            except Exception as e:
                logger.error(f"Error loading module {module_name}: {e}")
                if module_name in ['database.models.base', 'database.models.enums']:
                    essential_models_loaded = False

        if essential_models_loaded:
            logger.info("Model modules loaded successfully")
            return True
        else:
            logger.error("Failed to load essential model modules")
            return False

    except Exception as e:
        logger.error(f"Error loading model modules: {e}")
        traceback.print_exc()
        return False


@contextmanager
def get_session(engine):
    """
    Context manager for database sessions.

    Args:
        engine: SQLAlchemy engine

    Yields:
        Session: SQLAlchemy session
    """
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
        # Session will be committed or rolled back by the caller
    except Exception as e:
        logger.error(f"Session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def load_sample_data_from_json(json_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load sample data from a JSON file.

    Args:
        json_path (Optional[str]): Path to the JSON file.
                                   If None, uses default location in the project root.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary of sample data categories
    """
    if json_path is None:
        # Default to the root directory
        json_path = 'sample_data.json'

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)

        logger.info(f"Successfully loaded sample data from {json_path}")
        return sample_data
    except FileNotFoundError:
        logger.error(f"Sample data file not found at {json_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {json_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading sample data: {e}")
        raise


def create_sample_suppliers(session: Session, suppliers_data: List[Dict[str, Any]]) -> List[Any]:
    """
    Create supplier records from sample data.

    Args:
        session (Session): SQLAlchemy database session
        suppliers_data (List[Dict[str, Any]]): List of supplier data dictionaries

    Returns:
        List[Supplier]: List of created supplier objects
    """
    try:
        from database.models.supplier import Supplier
        from database.models.enums import SupplierStatus

        suppliers = []
        for supplier_info in suppliers_data:
            # Convert status string to enum if present
            status = supplier_info.get('status', 'ACTIVE')
            if isinstance(status, str):
                status = getattr(SupplierStatus, status)

            # Remove status from dict if it exists to prevent duplicate key error
            supplier_info_copy = supplier_info.copy()
            if 'status' in supplier_info_copy:
                del supplier_info_copy['status']

            # Create supplier object
            supplier = Supplier(
                status=status,
                **supplier_info_copy
            )

            session.add(supplier)
            suppliers.append(supplier)

        session.flush()  # Get IDs without committing
        logger.info(f"Created {len(suppliers)} suppliers")
        return suppliers
    except Exception as e:
        logger.error(f"Error creating suppliers: {e}")
        session.rollback()
        raise


def create_sample_materials(session: Session, materials_data: List[Dict[str, Any]], suppliers: List[Any]) -> List[Any]:
    """
    Create material records from sample data.

    Args:
        session (Session): SQLAlchemy database session
        materials_data (List[Dict[str, Any]]): List of material data dictionaries
        suppliers (List[Any]): List of supplier objects for reference

    Returns:
        List[Material]: List of created material objects
    """
    try:
        from database.models.material import Material, Leather, Hardware, Supplies
        from database.models.enums import MaterialType, QualityGrade, LeatherType, HardwareType

        materials = []
        for material_info in materials_data:
            # Determine material type and appropriate class
            material_type = material_info.get('material_type', 'LEATHER')

            # Map supplier name to ID if supplier specified by name
            if 'supplier_name' in material_info and suppliers:
                supplier_name = material_info.pop('supplier_name')
                supplier = next((s for s in suppliers if s.name == supplier_name), None)
                if supplier:
                    material_info['supplier_id'] = supplier.id

            # Convert string enums to actual enum values
            if 'quality' in material_info and isinstance(material_info['quality'], str):
                material_info['quality'] = getattr(QualityGrade, material_info['quality'])

            # Create the appropriate material subclass
            if material_type == 'LEATHER':
                if 'leather_type' in material_info and isinstance(material_info['leather_type'], str):
                    material_info['leather_type'] = getattr(LeatherType, material_info['leather_type'])
                material = Leather(**material_info)
            elif material_type == 'HARDWARE':
                if 'hardware_type' in material_info and isinstance(material_info['hardware_type'], str):
                    material_info['hardware_type'] = getattr(HardwareType, material_info['hardware_type'])
                material = Hardware(**material_info)
            elif material_type == 'SUPPLIES':
                material = Supplies(**material_info)
            else:
                material = Material(**material_info)

            session.add(material)
            materials.append(material)

        session.flush()  # Get IDs without committing
        logger.info(f"Created {len(materials)} materials")
        return materials
    except Exception as e:
        logger.error(f"Error creating materials: {e}")
        traceback.print_exc()
        session.rollback()
        raise


def create_sample_customers(session: Session, customers_data: List[Dict[str, Any]]) -> List[Any]:
    """
    Create customer records from sample data.

    Args:
        session (Session): SQLAlchemy database session
        customers_data (List[Dict[str, Any]]): List of customer data dictionaries

    Returns:
        List[Customer]: List of created customer objects
    """
    try:
        from database.models.customer import Customer
        from database.models.enums import CustomerStatus, CustomerTier

        customers = []
        for customer_info in customers_data:
            # Convert string enums to actual enum values
            if 'status' in customer_info and isinstance(customer_info['status'], str):
                customer_info['status'] = getattr(CustomerStatus, customer_info['status'])

            if 'tier' in customer_info and isinstance(customer_info['tier'], str):
                customer_info['tier'] = getattr(CustomerTier, customer_info['tier'])

            customer = Customer(**customer_info)
            session.add(customer)
            customers.append(customer)

        session.flush()  # Get IDs without committing
        logger.info(f"Created {len(customers)} customers")
        return customers
    except Exception as e:
        logger.error(f"Error creating customers: {e}")
        session.rollback()
        raise


def add_sample_data_from_json(session: Session, json_path: Optional[str] = None, dry_run: bool = False) -> bool:
    """
    Add sample data to the database from a JSON file.

    Args:
        session (Session): SQLAlchemy database session
        json_path (Optional[str]): Path to the JSON file
        dry_run (bool): If True, validate data but don't commit

    Returns:
        bool: True if sample data was added successfully, False otherwise
    """
    try:
        # Load sample data from JSON
        sample_data = load_sample_data_from_json(json_path)

        # Create data in order of dependencies
        suppliers = []
        if 'suppliers' in sample_data:
            suppliers = create_sample_suppliers(session, sample_data['suppliers'])

        materials = []
        if 'materials' in sample_data:
            materials = create_sample_materials(session, sample_data['materials'], suppliers)

        customers = []
        if 'customers' in sample_data:
            customers = create_sample_customers(session, sample_data['customers'])

        # Add more sample data creation functions here as needed
        # e.g., components, patterns, products, etc.

        if dry_run:
            logger.info("Dry run complete - rolling back sample data")
            session.rollback()
        else:
            # Commit all changes
            session.commit()
            logger.info("Successfully added sample data from JSON")

        return True
    except Exception as e:
        logger.error(f"Error adding sample data from JSON: {e}")
        session.rollback()
        return False


def initialize_database(recreate: bool = False, connection_string: Optional[str] = None):
    """
    Initialize the database, optionally recreating it from scratch.

    Args:
        recreate (bool): If True, drop all tables and recreate them
        connection_string (Optional[str]): Custom database connection string

    Returns:
        The SQLAlchemy engine or None if initialization failed
    """
    try:
        # Import models first
        if not import_models():
            logger.error("Failed to initialize database: Could not import models")
            return None

        # Get Base from models
        from database.models.base import Base

        # Determine database path/connection string
        if connection_string is None:
            db_path = get_database_path()
            logger.info(f"Using database path: {db_path}")

            # Create a backup before making changes if the file exists
            if os.path.exists(db_path) and recreate:
                backup_database(db_path, "recreate")

            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            connection_string = f"sqlite:///{db_path}"
        else:
            logger.info(f"Using custom connection string")

        # Connection pooling and timeout settings
        engine_args = {
            'echo': False,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }

        # Add SQLite-specific arguments
        if connection_string.startswith('sqlite'):
            engine_args['connect_args'] = {
                'check_same_thread': False,
                'timeout': 30
            }

        # Create engine with improved error handling
        try:
            engine = create_engine(connection_string, **engine_args)

            # Test connection
            with engine.connect() as conn:
                logger.debug("Database connection test successful")

        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            return None

        # Load all model modules in the right order
        if not load_all_models():
            logger.error("Failed to load all required models")
            return None

        if recreate:
            logger.info("Recreating database from scratch")
            try:
                # Drop all tables first
                Base.metadata.drop_all(engine)
                logger.info("Existing tables dropped successfully")

                # Recreate all tables
                Base.metadata.create_all(engine)
                logger.info("Database tables recreated successfully")
            except SQLAlchemyError as e:
                logger.error(f"Error recreating database: {e}")
                traceback.print_exc()
                return None
        else:
            # Check if tables exist first and create them if they don't
            logger.info("Checking existing database structure")

            try:
                # Check which tables already exist
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                logger.debug(f"Existing tables: {existing_tables}")

                # Create tables that don't exist yet
                Base.metadata.create_all(engine)
                logger.info("Created missing tables")
            except SQLAlchemyError as e:
                logger.error(f"Error creating tables: {e}")
                traceback.print_exc()
                return None

        # Verify database is operational
        try:
            with engine.connect() as conn:
                # Check if we can execute a simple query
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("Database verification successful")
                else:
                    logger.warning("Database verification returned unexpected result")
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            traceback.print_exc()
            return None

        return engine
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        traceback.print_exc()
        return None


def create_minimal_sample_data():
    """
    Create a minimal sample data JSON file if it doesn't exist.

    This ensures there's always some seed data available even if the user doesn't have sample_data.json.
    """
    minimal_path = 'minimal_sample_data.json'
    if os.path.exists(minimal_path):
        return

    minimal_data = {
        "suppliers": [
            {
                "name": "Tandy Leather",
                "contact_email": "sales@tandyleather.com",
                "status": "ACTIVE"
            },
            {
                "name": "Rocky Mountain Leather Supply",
                "contact_email": "info@rmleathersupply.com",
                "status": "ACTIVE"
            }
        ],
        "materials": [
            {
                "name": "Hermann Oak Veg Tan",
                "description": "Premium vegetable tanned leather",
                "material_type": "LEATHER",
                "leather_type": "VEGETABLE_TANNED",
                "thickness": 3.5,
                "supplier_name": "Tandy Leather"
            },
            {
                "name": "Brass Buckle",
                "description": "Standard 1-inch brass buckle",
                "material_type": "HARDWARE",
                "hardware_type": "BUCKLE",
                "supplier_name": "Rocky Mountain Leather Supply"
            }
        ],
        "customers": [
            {
                "name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "555-123-4567",
                "status": "ACTIVE"
            }
        ]
    }

    with open(minimal_path, 'w', encoding='utf-8') as f:
        json.dump(minimal_data, f, indent=2)

    logger.info(f"Created minimal sample data file at {minimal_path}")


def main():
    """
    Main function to initialize database and optionally seed with sample data.
    Supports command-line arguments and environment variables.
    """
    start_time = time.time()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Initialize leatherworking database')
    parser.add_argument('--recreate', action='store_true', help='Drop and recreate all tables')
    parser.add_argument('--seed', action='store_true', help='Add sample data to database')
    parser.add_argument('--mode', choices=['minimal', 'standard', 'demo'],
                        default=None, help='Amount of sample data to add')
    parser.add_argument('--dry-run', action='store_true',
                        help='Validate without committing changes')
    args = parser.parse_args()

    try:
        # Get environment variables, override with command line args if provided
        recreate_db = os.environ.get("RECREATE_DB", "false").lower() == "true"
        seed_db = os.environ.get("SEED_DB", "false").lower() == "true"
        seed_mode = os.environ.get("SEED_MODE", "standard").lower()
        dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

        # Command line args override environment variables
        if args.recreate:
            recreate_db = True
        if args.seed:
            seed_db = True
        if args.mode:
            seed_mode = args.mode
        if args.dry_run:
            dry_run = True

        if dry_run:
            logger.info("Running in dry-run mode - no changes will be committed")

        # Initialize database
        logger.info(f"Initializing database (recreate={recreate_db})")
        engine = initialize_database(recreate=recreate_db)
        if not engine:
            logger.error("Database initialization failed")
            return 1

        db_init_time = time.time()
        logger.info(f"Database schema initialized in {db_init_time - start_time:.2f} seconds")

        # Create minimal sample data file if it doesn't exist
        if seed_db:
            create_minimal_sample_data()

        # Add sample data if requested
        if seed_db:
            logger.info(f"Seeding database in {seed_mode} mode...")

            with get_session(engine) as session:
                # Check if data already exists
                try:
                    from database.models.customer import Customer
                    existing_count = session.query(Customer).count()
                    if existing_count > 0 and not recreate_db:
                        logger.warning(f"Database already contains {existing_count} customers")
                        user_input = input("Continue with seeding? This may create duplicate data. (y/n): ")
                        if user_input.lower() != 'y':
                            logger.info("Seeding canceled by user")
                            return 0
                except Exception as e:
                    logger.warning(f"Could not check for existing data: {e}")

                # Determine sample data path
                default_json_path = 'sample_data.json'
                minimal_json_path = 'minimal_sample_data.json'

                # Call the appropriate sample data loading function
                if seed_mode == "minimal":
                    logger.info("Adding minimal sample data...")
                    success = add_sample_data_from_json(session, minimal_json_path, dry_run)
                elif seed_mode == "demo":
                    logger.info("Adding extended demo data...")
                    success = add_sample_data_from_json(session, default_json_path, dry_run)
                else:  # Default to standard
                    logger.info("Adding standard sample data...")
                    success = add_sample_data_from_json(session, default_json_path, dry_run)

                if success:
                    if not dry_run:
                        session.commit()
                        logger.info("Database seeding complete")
                    else:
                        logger.info("Dry run successful - sample data validated but not committed")
                else:
                    logger.error("Database seeding failed")
                    return 1

        else:
            logger.info("Skipping sample data seeding")

        # Log performance metrics
        end_time = time.time()
        logger.info(f"Database initialization completed in {end_time - start_time:.2f} seconds")

        # Basic database validation
        with get_session(engine) as session:
            try:
                # Import models needed for validation
                from database.models.customer import Customer
                from database.models.material import Material

                # Perform basic validation queries
                customer_count = session.query(Customer).count()
                material_count = session.query(Material).count()

                logger.info(f"Database validation: {customer_count} customers, {material_count} materials")

                if seed_db and customer_count == 0 and not dry_run:
                    logger.warning("Database appears to be empty after seeding - possible issue")

            except Exception as e:
                logger.warning(f"Database validation failed: {e}")
                traceback.print_exc()

        return 0
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)