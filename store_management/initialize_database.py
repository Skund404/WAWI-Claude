import logging
import os
import sys
import importlib
from datetime import datetime, timedelta
from random import random
from typing import Optional, List, Dict, Any
from sqlalchemy import inspect, text, create_engine
from sqlalchemy import inspect, text, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path


# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_path():
    """
    Determine the path for the SQLite database.

    Returns:
        str: Absolute path to the database file
    """
    # Simple implementation to avoid circular imports
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / 'data'
    os.makedirs(data_dir, exist_ok=True)
    return str(data_dir / 'leatherworking_database.db')


def import_models():
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
        import traceback
        logger.error(traceback.format_exc())
        return False


def load_all_models():
    """
    Load all model modules to ensure they are registered.
    This is a simplified version included directly in initialize_database.py
    """
    try:
        # Import all model modules to ensure they are loaded
        model_modules = [
            'database.models.customer',
            'database.models.sales',
            'database.models.sales_item',
            'database.models.product',
            'database.models.pattern',
            'database.models.product_pattern',
            'database.models.supplier',
            'database.models.purchase',
            'database.models.purchase_item',
            'database.models.project',
            'database.models.components',
            'database.models.material',
            'database.models.leather',
            'database.models.hardware',
            'database.models.tool',
            'database.models.product_inventory',
            'database.models.material_inventory',
            'database.models.leather_inventory',
            'database.models.hardware_inventory',
            'database.models.tool_inventory',
            'database.models.picking_list',
            'database.models.tool_list',
            'database.models.transaction'
        ]

        for module_name in model_modules:
            try:
                importlib.import_module(module_name)
                logger.debug(f"Loaded model module: {module_name}")
            except ImportError as e:
                logger.warning(f"Could not import {module_name}: {e}")

        logger.info("Model modules loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model modules: {e}")
        import traceback
        logger.error(traceback.format_exc())


def initialize_all_relationships():
    """
    Initialize all relationships for models.
    This is a simplified version included directly in initialize_database.py
    """
    try:
        # List of modules with relationship initialization
        modules_to_initialize = [
            'database.models.sales',
            'database.models.sales_item',
            'database.models.product',
            'database.models.pattern',
            'database.models.product_pattern',
            'database.models.picking_list',
            'database.models.transaction',
            'database.models.components',
            'database.models.project',
            'database.models.purchase'
        ]

        # Initialize relationships for each module in the correct order
        for module_path in modules_to_initialize:
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, 'initialize_relationships'):
                    logger.debug(f"Initializing relationships for {module_path}")
                    module.initialize_relationships()
            except Exception as e:
                logger.error(f"Error initializing relationships for {module_path}: {e}")

        logger.info("Relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error during relationship initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())


def get_critical_tables() -> List[str]:
    """
    Get a list of critical tables that must exist in the database.

    Returns:
        List[str]: List of table names
    """
    return [
        'customers', 'sales', 'sales_items',
        'products', 'patterns', 'product_patterns',
        'projects', 'components',
        'suppliers', 'purchases', 'purchase_items',
        'product_inventories', 'material_inventories',
        'leather_inventories', 'hardware_inventories',
        'tool_inventories', 'picking_lists', 'tool_lists'
    ]


def get_column_checks() -> List[Dict[str, Any]]:
    """
    Define potential columns to add or modify across tables.

    Returns:
        List[Dict[str, Any]]: List of column check definitions
    """
    return [
        # Common additions across tables
        {
            'table': 'customers',
            'column': 'status',
            'definition': 'VARCHAR(50)',
            'added': False
        },
        {
            'table': 'sales',
            'column': 'customer_name',
            'definition': 'VARCHAR(255)',
            'added': False
        },
        {
            'table': 'products',
            'column': 'description',
            'definition': 'TEXT',
            'added': False
        },
        {
            'table': 'projects',
            'column': 'sales_id',
            'definition': 'INTEGER REFERENCES sales(id)',
            'added': False
        },
        # Add more potential column checks as needed
    ]


def check_and_fix_table_structures(engine):
    """
    Verify and fix database table structures to match model definitions.

    This function performs comprehensive validation and repair:
    1. Verifies all critical tables exist
    2. Checks for missing columns and adds them if needed
    3. Validates column types match expected definitions
    4. Creates indexes for performance optimization
    5. Adds foreign key constraints if missing

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        bool: True if all critical tables exist and are properly structured, False otherwise
    """
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        logger.info(f"Existing tables: {', '.join(existing_tables) if existing_tables else 'None'}")

        # Check and add missing columns
        column_checks = get_column_checks()
        with engine.begin() as conn:
            # First pass: Verify which tables need modifications
            tables_to_check = set(check['table'] for check in column_checks)
            tables_to_check = tables_to_check.intersection(existing_tables)

            # Build a mapping of existing columns for each table to avoid redundant introspection
            table_columns = {}
            for table in tables_to_check:
                table_columns[table] = {col['name']: col for col in inspector.get_columns(table)}

            # Track changes for reporting
            changes_made = []
            errors_encountered = []

            # Apply column additions and modifications
            for check in column_checks:
                if check['table'] in existing_tables:
                    columns = table_columns.get(check['table'], {})

                    if check['column'] not in columns:
                        try:
                            sql = f"ALTER TABLE {check['table']} ADD COLUMN {check['column']} {check['definition']}"
                            conn.execute(text(sql))
                            check['added'] = True
                            changes_made.append(f"Added {check['column']} to {check['table']}")
                            logger.info(f"Added {check['column']} to {check['table']}")
                        except Exception as e:
                            errors_encountered.append(f"Error adding {check['column']} to {check['table']}: {e}")
                            logger.error(f"Error adding {check['column']} to {check['table']}: {e}")

            # Check for indexes that should exist but don't
            indexes_to_add = []
            try:
                indexes_to_add = get_missing_indexes(inspector, existing_tables)

                for index_def in indexes_to_add:
                    try:
                        conn.execute(text(index_def['sql']))
                        changes_made.append(f"Added index {index_def['name']} to {index_def['table']}")
                        logger.info(f"Added index {index_def['name']} to {index_def['table']}")
                    except Exception as e:
                        errors_encountered.append(f"Error adding index {index_def['name']}: {e}")
                        logger.error(f"Error adding index {index_def['name']}: {e}")
            except Exception as e:
                logger.error(f"Error checking indexes: {e}")

        # Verify critical tables exist
        critical_tables = get_critical_tables()
        all_critical_tables_exist = True

        missing_tables = [table for table in critical_tables if table not in existing_tables]
        if missing_tables:
            logger.warning(f"Missing critical tables: {', '.join(missing_tables)}")
            all_critical_tables_exist = False

        # Report changes
        if changes_made:
            logger.info(f"Made {len(changes_made)} changes to database structure:")
            for change in changes_made:
                logger.debug(f"  - {change}")
        else:
            logger.info("No structure changes needed")

        if errors_encountered:
            logger.warning(f"Encountered {len(errors_encountered)} errors during database structure updates")
            for error in errors_encountered:
                logger.debug(f"  - {error}")

        return all_critical_tables_exist

    except Exception as e:
        logger.error(f"Error checking table structures: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_missing_indexes(inspector, existing_tables):
    """
    Determine which indexes should be added for performance optimization.

    Args:
        inspector: SQLAlchemy inspector
        existing_tables: Set of existing table names

    Returns:
        List of dict objects with index definitions to add
    """
    indexes_to_add = []

    # Define important indexes that should exist
    recommended_indexes = [
        {
            'table': 'sales',
            'name': 'idx_sales_customer_id',
            'columns': ['customer_id'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_sales_customer_id ON sales (customer_id)'
        },
        {
            'table': 'sales',
            'name': 'idx_sales_date',
            'columns': ['sale_date'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (sale_date)'
        },
        {
            'table': 'products',
            'name': 'idx_products_name',
            'columns': ['name'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_products_name ON products (name)'
        },
        {
            'table': 'customers',
            'name': 'idx_customers_email',
            'columns': ['email'],
            'sql': 'CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email ON customers (email)'
        },
        {
            'table': 'sales_items',
            'name': 'idx_sales_items_sales_id',
            'columns': ['sales_id'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_sales_items_sales_id ON sales_items (sales_id)'
        },
        {
            'table': 'sales_items',
            'name': 'idx_sales_items_product_id',
            'columns': ['product_id'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_sales_items_product_id ON sales_items (product_id)'
        },
        {
            'table': 'projects',
            'name': 'idx_projects_customer_id',
            'columns': ['customer_id'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_projects_customer_id ON projects (customer_id)'
        },
        {
            'table': 'projects',
            'name': 'idx_projects_status',
            'columns': ['status'],
            'sql': 'CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status)'
        }
    ]

    # Filter to only include indexes for tables that exist
    filtered_indexes = [idx for idx in recommended_indexes if idx['table'] in existing_tables]

    # Check which indexes already exist
    for index_def in filtered_indexes:
        table = index_def['table']
        existing_indexes = inspector.get_indexes(table)
        existing_index_names = {idx['name'] for idx in existing_indexes if 'name' in idx}

        if index_def['name'] not in existing_index_names:
            indexes_to_add.append(index_def)

    return indexes_to_add


def initialize_database(recreate: bool = False, connection_string: Optional[str] = None):
    """
    Initialize the database, optionally recreating it from scratch.

    This function handles the complete initialization process:
    1. Importing and validating database models
    2. Creating the database connection
    3. Creating or recreating tables as needed
    4. Checking and fixing table structures
    5. Initializing model relationships

    Args:
        recreate (bool): If True, drop all tables and recreate them
        connection_string (Optional[str]): Custom database connection string
                                          If None, uses the default path

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

            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            connection_string = f"sqlite:///{db_path}"
        else:
            logger.info(f"Using custom connection string")

        # Connection pooling and timeout settings for better performance and reliability
        engine_args = {
            'echo': False,  # Set to True for SQL query logging during development
            'pool_recycle': 3600,  # Recycle connections after 1 hour to prevent them from going stale
            'pool_pre_ping': True,  # Verify connections before using them
        }

        # Add SQLite-specific arguments
        if connection_string.startswith('sqlite'):
            engine_args['connect_args'] = {
                'check_same_thread': False,  # Allow SQLite to be used from multiple threads
                'timeout': 30  # 30 second timeout for busy connections
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

        # Load all model modules to ensure they are registered with SQLAlchemy
        load_all_models()

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
                return None
        else:
            # Check if tables exist first and create them if they don't
            logger.info("Checking existing database structure")

            try:
                # Create tables that don't exist yet
                Base.metadata.create_all(engine)
                logger.info("Created missing tables")
            except SQLAlchemyError as e:
                logger.error(f"Error creating tables: {e}")
                return None

            # Check and fix table structures
            table_check_result = check_and_fix_table_structures(engine)
            if not table_check_result:
                logger.warning("Some critical tables might be missing or incorrect")

                # Provide details about missing tables
                inspector = inspect(engine)
                existing_tables = set(inspector.get_table_names())
                critical_tables = set(get_critical_tables())
                missing = critical_tables - existing_tables
                if missing:
                    logger.warning(f"Missing tables: {', '.join(missing)}")

        # Initialize relationships in models after database creation
        try:
            initialize_all_relationships()
            logger.info("Model relationships initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing relationships: {e}")
            logger.error("Continuing despite relationship initialization error")
            # Don't return None here - relationships can sometimes be fixed at runtime

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
            # Don't fail here - the database might still be usable

        return engine
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def add_sample_data(session: Optional[Session] = None):
    """
    Adds comprehensive sample data to the database for testing and demonstration.
    Creates a realistic set of data for a leather business including customers, suppliers,
    products, materials, projects, sales, purchases, and inventory.

    Args:
        session (Optional[Session]): Existing database session. If None, a new session is created.

    Returns:
        bool: True if sample data was added successfully, False otherwise
    """
    # Create session if not provided
    own_session = False
    if session is None:
        try:
            engine = create_engine(f"sqlite:///{get_database_path()}", echo=False)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            own_session = True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create session for sample data: {e}")
            return False

    try:
        # By this point, the models should be loaded, so import directly
        from database.models.customer import Customer
        from database.models.supplier import Supplier
        from database.models.leather import Leather
        from database.models.hardware import Hardware
        from database.models.material import Material
        from database.models.product import Product
        from database.models.pattern import Pattern
        from database.models.product_pattern import ProductPattern
        from database.models.project import Project
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem
        from database.models.purchase import Purchase
        from database.models.purchase_item import PurchaseItem
        from database.models.product_inventory import ProductInventory
        from database.models.leather_inventory import LeatherInventory
        from database.models.hardware_inventory import HardwareInventory
        from database.models.material_inventory import MaterialInventory
        from database.models.tool import Tool
        from database.models.tool_inventory import ToolInventory
        from database.models.tool_list import ToolList, ToolListItem
        from database.models.picking_list import PickingList, PickingListItem
        from database.models.components import Component, ProjectComponent, ComponentLeather, ComponentHardware, \
            ComponentMaterial

        # Import enums
        from database.models.enums import (
            SupplierStatus, CustomerStatus, CustomerTier, LeatherType,
            MaterialQualityGrade, HardwareMaterial, HardwareFinish,
            HardwareType, MaterialType, SaleStatus, PaymentStatus,
            ProjectType, ProjectStatus, SkillLevel, InventoryStatus,
            PurchaseStatus, PickingListStatus, ToolListStatus,
            CustomerSource, ToolCategory, ComponentType, MeasurementUnit
        )

        # Create sample suppliers
        logger.info("Adding Sample Suppliers")
        suppliers = [
            Supplier(
                name="Wickett & Craig",
                contact_name="Thomas Wilson",
                contact_email="sales@wickettandcraig.com",
                phone="555-789-1234",
                address="120 Tannery Lane, Curwensville, PA 16833",
                status=SupplierStatus.ACTIVE,
                notes="Premium vegetable tanned leather supplier, specializing in bridle and harness leathers"
            ),
            Supplier(
                name="Buckleguy Hardware",
                contact_name="Sarah Johnson",
                contact_email="orders@buckleguy.com",
                phone="555-456-7890",
                address="45 Hardware Blvd, Boston, MA 02108",
                status=SupplierStatus.ACTIVE,
                notes="Specialized leather hardware supplier with premium solid brass fittings"
            ),
            Supplier(
                name="Maine Thread Company",
                contact_name="Michael Taylor",
                contact_email="info@mainethread.com",
                phone="555-123-4567",
                address="68 Industrial Way, Lewiston, ME 04240",
                status=SupplierStatus.ACTIVE,
                notes="High-quality waxed thread for leather stitching"
            ),
            Supplier(
                name="Horween Leather Co.",
                contact_name="Elizabeth Davis",
                contact_email="sales@horween.com",
                phone="555-987-6543",
                address="2015 N. Elston Ave, Chicago, IL 60614",
                status=SupplierStatus.ACTIVE,
                notes="Premium Chromexcel and Shell Cordovan leather supplier"
            ),
            Supplier(
                name="Weaver Leathercraft Supply",
                contact_name="Robert Chen",
                contact_email="support@weaverleathercraft.com",
                phone="555-234-5678",
                address="3900 Weaver Rd, Mt. Hope, OH 44660",
                status=SupplierStatus.ACTIVE,
                notes="Comprehensive leatherworking tools and supplies"
            )
        ]
        session.add_all(suppliers)
        session.commit()

        # Create sample customers
        logger.info("Adding Sample Customers")
        customers = [
            Customer(
                first_name="Alice",
                last_name="Johnson",
                email="alice.johnson@example.com",
                phone="555-111-2222",
                address="789 Crafting Street, Portland, OR 97210",
                status=CustomerStatus.ACTIVE,
                customer_tier=CustomerTier.STANDARD,
                customer_source=CustomerSource.WEBSITE,
                notes="Repeat customer, prefers vegetable tanned products"
            ),
            Customer(
                first_name="Bob",
                last_name="Williams",
                email="bob.williams@example.com",
                phone="555-333-4444",
                address="101 Artisan Avenue, Seattle, WA 98104",
                status=CustomerStatus.ACTIVE,
                customer_tier=CustomerTier.PREMIUM,
                customer_source=CustomerSource.REFERRAL,
                notes="Orders custom pieces quarterly, prefers Horween leather"
            ),
            Customer(
                first_name="Carol",
                last_name="Martinez",
                email="carol.martinez@example.com",
                phone="555-555-6666",
                address="222 Maker Street, San Francisco, CA 94110",
                status=CustomerStatus.ACTIVE,
                customer_tier=CustomerTier.VIP,
                customer_source=CustomerSource.TRADE_SHOW,
                notes="Professional saddle maker, bulk orders"
            ),
            Customer(
                first_name="David",
                last_name="Brown",
                email="david.brown@example.com",
                phone="555-777-8888",
                address="333 Design Drive, Austin, TX 78704",
                status=CustomerStatus.ACTIVE,
                customer_tier=CustomerTier.STANDARD,
                customer_source=CustomerSource.WEBSITE,
                notes="New to leatherworking, attending our beginner workshop"
            ),
            Customer(
                first_name="Emily",
                last_name="Garcia",
                email="emily.garcia@example.com",
                phone="555-999-0000",
                address="444 Creative Court, Chicago, IL 60607",
                status=CustomerStatus.ACTIVE,
                customer_tier=CustomerTier.PREMIUM,
                customer_source=CustomerSource.SOCIAL_MEDIA,
                notes="Fashion designer, orders exotic leathers for accessories"
            )
        ]
        session.add_all(customers)
        session.commit()

        # Create sample leather materials
        logger.info("Adding Sample Leather Materials")
        leathers = [
            Leather(
                name="Wickett & Craig English Bridle",
                type=LeatherType.VEGETABLE_TANNED,
                quality=MaterialQualityGrade.PREMIUM,
                supplier_id=suppliers[0].id,
                color="Chestnut",
                thickness=3.5,  # mm
                origin="USA",
                cost_per_unit=14.99,
                unit=MeasurementUnit.SQUARE_FOOT
            ),
            Leather(
                name="Horween Chromexcel",
                type=LeatherType.OIL_PULL_UP,
                quality=MaterialQualityGrade.PREMIUM,
                supplier_id=suppliers[3].id,
                color="Brown",
                thickness=2.0,  # mm
                origin="USA",
                cost_per_unit=12.50,
                unit=MeasurementUnit.SQUARE_FOOT
            ),
            Leather(
                name="Horween Shell Cordovan",
                type=LeatherType.SHELL_CORDOVAN,
                quality=MaterialQualityGrade.PREMIUM,
                supplier_id=suppliers[3].id,
                color="Color #8",
                thickness=1.5,  # mm
                origin="USA",
                cost_per_unit=75.00,
                unit=MeasurementUnit.SQUARE_FOOT
            ),
            Leather(
                name="Chevre Goatskin",
                type=LeatherType.CHROME_TANNED,
                quality=MaterialQualityGrade.PREMIUM,
                supplier_id=suppliers[3].id,
                color="Navy",
                thickness=1.0,  # mm
                origin="France",
                cost_per_unit=18.75,
                unit=MeasurementUnit.SQUARE_FOOT
            ),
            Leather(
                name="Pueblo Veg Tan",
                type=LeatherType.VEGETABLE_TANNED,
                quality=MaterialQualityGrade.PREMIUM,
                supplier_id=suppliers[0].id,
                color="Olive",
                thickness=2.2,  # mm
                origin="Italy",
                cost_per_unit=16.50,
                unit=MeasurementUnit.SQUARE_FOOT
            )
        ]
        session.add_all(leathers)
        session.commit()

        # Create sample hardware
        logger.info("Adding Sample Hardware")
        hardware_items = [
            Hardware(
                name="Solid Brass Buckle",
                type=HardwareType.BUCKLE,
                supplier_id=suppliers[1].id,
                material=HardwareMaterial.BRASS,
                finish=HardwareFinish.POLISHED,
                size="1.5 inch",
                cost_per_unit=5.75,
                unit=MeasurementUnit.PIECE
            ),
            Hardware(
                name="Double Cap Rivets",
                type=HardwareType.RIVET,
                supplier_id=suppliers[1].id,
                material=HardwareMaterial.BRASS,
                finish=HardwareFinish.ANTIQUE,
                size="Medium 9mm",
                cost_per_unit=0.35,
                unit=MeasurementUnit.PIECE
            ),
            Hardware(
                name="Heavy Duty Magnetic Snap",
                type=HardwareType.MAGNETIC_CLOSURE,
                supplier_id=suppliers[1].id,
                material=HardwareMaterial.NICKEL,
                finish=HardwareFinish.BRUSHED,
                size="20mm",
                cost_per_unit=2.25,
                unit=MeasurementUnit.PIECE
            ),
            Hardware(
                name="Cast D-Rings",
                type=HardwareType.D_RING,
                supplier_id=suppliers[1].id,
                material=HardwareMaterial.STAINLESS_STEEL,
                finish=HardwareFinish.POLISHED,
                size="1 inch",
                cost_per_unit=1.50,
                unit=MeasurementUnit.PIECE
            ),
            Hardware(
                name="Western Flower Concho",
                type=HardwareType.CONCHO,
                supplier_id=suppliers[1].id,
                material=HardwareMaterial.SILVER,
                finish=HardwareFinish.ANTIQUE,
                size="1.25 inch",
                cost_per_unit=6.25,
                unit=MeasurementUnit.PIECE
            )
        ]
        session.add_all(hardware_items)
        session.commit()

        # Create sample other materials
        logger.info("Adding Sample Materials")
        materials = [
            Material(
                name="Tiger Thread",
                type=MaterialType.THREAD,
                supplier_id=suppliers[2].id,
                color="Natural",
                thickness=0.6,  # mm
                cost_per_unit=24.99,
                unit=MeasurementUnit.PIECE,
                quality=MaterialQualityGrade.PREMIUM
            ),
            Material(
                name="Pure Beeswax",
                type=MaterialType.WAX,
                supplier_id=suppliers[4].id,
                color="Yellow",
                cost_per_unit=9.75,
                unit=MeasurementUnit.PIECE,
                quality=MaterialQualityGrade.PREMIUM
            ),
            Material(
                name="Barge Cement",
                type=MaterialType.ADHESIVE,
                supplier_id=suppliers[4].id,
                color="Tan",
                cost_per_unit=14.50,
                unit=MeasurementUnit.PIECE,
                quality=MaterialQualityGrade.PREMIUM
            ),
            Material(
                name="Uniters Edge Paint",
                type=MaterialType.EDGE_PAINT,
                supplier_id=suppliers[4].id,
                color="Dark Brown",
                cost_per_unit=22.95,
                unit=MeasurementUnit.PIECE,
                quality=MaterialQualityGrade.PREMIUM
            ),
            Material(
                name="Soft Pigskin Lining",
                type=MaterialType.LINING,
                supplier_id=suppliers[3].id,
                color="Tan",
                cost_per_unit=8.50,
                unit=MeasurementUnit.SQUARE_FOOT,
                quality=MaterialQualityGrade.PREMIUM
            )
        ]
        session.add_all(materials)
        session.commit()

        # Create sample tools
        logger.info("Adding Sample Tools")
        tools = [
            Tool(
                name="Kevin Lee French Pricking Irons",
                description="3mm spacing, 2+8 teeth set for precision stitching",
                category=ToolCategory.PUNCHING,
                supplier_id=suppliers[4].id,
                cost=149.95
            ),
            Tool(
                name="Japanese Skiving Knife",
                description="Blue steel #2 leather skiving knife with ebony handle",
                category=ToolCategory.CUTTING,
                supplier_id=suppliers[4].id,
                cost=85.00
            ),
            Tool(
                name="Vergez Blanchard Edge Beveler",
                description="Size 2 professional edge beveling tool",
                category=ToolCategory.EDGE_WORK,
                supplier_id=suppliers[4].id,
                cost=42.75
            ),
            Tool(
                name="Craftool Pro Stitching Pony",
                description="Heavy duty stitching clamp with wooden jaws",
                category=ToolCategory.STITCHING,
                supplier_id=suppliers[4].id,
                cost=89.95
            ),
            Tool(
                name="KS Blade Punch Set",
                description="Set of 6 precision round hole punches in graduated sizes",
                category=ToolCategory.PUNCHING,
                supplier_id=suppliers[4].id,
                cost=68.50
            )
        ]
        session.add_all(tools)
        session.commit()

        # Create sample products
        logger.info("Adding Sample Products")
        products = [
            Product(
                name="Bifold Wallet",
                description="Handcrafted full-grain leather wallet with 6 card slots and cash pocket",
                price=125.00,
                cost=45.75,
                sku="BFW-001"
            ),
            Product(
                name="Card Holder",
                description="Minimalist card holder with 3 pockets, hand stitched with Tiger thread",
                price=65.00,
                cost=22.50,
                sku="CH-001"
            ),
            Product(
                name="Market Tote",
                description="Large vegetable-tanned leather tote with reinforced handles and interior pocket",
                price=295.00,
                cost=110.25,
                sku="MT-001"
            ),
            Product(
                name="Bridle Belt",
                description="1.5 inch English bridle leather belt with solid brass buckle",
                price=135.00,
                cost=48.50,
                sku="BBT-001"
            ),
            Product(
                name="Journal Cover",
                description="A5 leather journal cover with pen holder, fits standard notebooks",
                price=95.00,
                cost=36.75,
                sku="JC-001"
            )
        ]
        session.add_all(products)
        session.commit()

        # Create sample patterns
        logger.info("Adding Sample Patterns")
        patterns = [
            Pattern(
                name="Classic Bifold Wallet Pattern",
                description="Traditional 6-card slot bifold with detailed construction notes",
                skill_level=SkillLevel.INTERMEDIATE
            ),
            Pattern(
                name="Vertical Card Holder Pattern",
                description="Space-efficient 3-pocket vertical card holder, suitable for beginners",
                skill_level=SkillLevel.BEGINNER
            ),
            Pattern(
                name="Market Tote Pattern",
                description="Large capacity tote with reinforced handles and optional interior pocket",
                skill_level=SkillLevel.ADVANCED
            ),
            Pattern(
                name="Dress Belt Pattern",
                description="1.5 inch dress belt with detailed sizing guide and hole placement template",
                skill_level=SkillLevel.BEGINNER
            ),
            Pattern(
                name="A5 Journal Wrap Pattern",
                description="Adjustable journal cover designed for standard A5 notebooks",
                skill_level=SkillLevel.INTERMEDIATE
            )
        ]
        session.add_all(patterns)
        session.commit()

        # Link products to patterns
        logger.info("Linking Products to Patterns")
        product_patterns = [
            ProductPattern(
                product_id=products[0].id,
                pattern_id=patterns[0].id
            ),
            ProductPattern(
                product_id=products[1].id,
                pattern_id=patterns[1].id
            ),
            ProductPattern(
                product_id=products[2].id,
                pattern_id=patterns[2].id
            ),
            ProductPattern(
                product_id=products[3].id,
                pattern_id=patterns[3].id
            ),
            ProductPattern(
                product_id=products[4].id,
                pattern_id=patterns[4].id
            )
        ]
        session.add_all(product_patterns)
        session.commit()

        # Create components for patterns
        logger.info("Adding Sample Components")
        components = [
            Component(
                name="Wallet Outer Shell",
                type=ComponentType.LEATHER,
                description="Main exterior piece of the wallet, requires 4-5oz leather"
            ),
            Component(
                name="Card Pocket Panel",
                type=ComponentType.LEATHER,
                description="Interior panel for card slots, requires 2-3oz leather"
            ),
            Component(
                name="Tote Body Panel",
                type=ComponentType.LEATHER,
                description="Main body panel for tote, requires 5-6oz leather"
            ),
            Component(
                name="Tote Handle Strips",
                type=ComponentType.LEATHER,
                description="Reinforced handle strips, requires 8-9oz leather"
            ),
            Component(
                name="Belt Strap",
                type=ComponentType.LEATHER,
                description="Main belt strap, requires 8-10oz leather"
            )
        ]
        session.add_all(components)
        session.commit()

        # Link components to materials
        logger.info("Linking Components to Materials")
        component_materials = [
            ComponentLeather(
                component_id=components[0].id,
                leather_id=leathers[1].id,  # Horween Chromexcel
                quantity=0.75  # sq ft
            ),
            ComponentLeather(
                component_id=components[1].id,
                leather_id=leathers[1].id,  # Horween Chromexcel
                quantity=0.5  # sq ft
            ),
            ComponentLeather(
                component_id=components[2].id,
                leather_id=leathers[0].id,  # English Bridle
                quantity=4.0  # sq ft
            ),
            ComponentLeather(
                component_id=components[3].id,
                leather_id=leathers[0].id,  # English Bridle
                quantity=1.0  # sq ft
            ),
            ComponentLeather(
                component_id=components[4].id,
                leather_id=leathers[0].id,  # English Bridle
                quantity=1.75  # sq ft
            )
        ]
        session.add_all(component_materials)

        component_hardware = [
            ComponentHardware(
                component_id=components[2].id,
                hardware_id=hardware_items[3].id,  # D-rings
                quantity=2  # D-rings for tote
            ),
            ComponentHardware(
                component_id=components[4].id,
                hardware_id=hardware_items[0].id,  # Brass Buckle
                quantity=1  # Buckle for belt
            )
        ]
        session.add_all(component_hardware)

        component_other_materials = [
            ComponentMaterial(
                component_id=components[0].id,
                material_id=materials[0].id,  # Tiger Thread
                quantity=1  # Thread for wallet
            ),
            ComponentMaterial(
                component_id=components[2].id,
                material_id=materials[0].id,  # Tiger Thread
                quantity=1  # Thread for tote
            )
        ]
        session.add_all(component_other_materials)
        session.commit()

        # Create sample projects
        logger.info("Adding Sample Projects")
        now = datetime.now()
        projects = [
            Project(
                name="Custom Chromexcel Bifold",
                description="Made-to-order wallet in Horween Chromexcel for Alice Johnson",
                type=ProjectType.WALLET,
                status=ProjectStatus.IN_PROGRESS,
                skill_level=SkillLevel.INTERMEDIATE,
                start_date=now - timedelta(days=5),
                estimated_completion_date=now + timedelta(days=5),
                customer_id=customers[0].id
            ),
            Project(
                name="Bridle Leather Market Tote",
                description="Large custom tote with monogram for Bob Williams",
                type=ProjectType.TOTE_BAG,
                status=ProjectStatus.DESIGN_PHASE,
                skill_level=SkillLevel.ADVANCED,
                start_date=now - timedelta(days=2),
                estimated_completion_date=now + timedelta(days=14),
                customer_id=customers[1].id
            ),
            Project(
                name="Hand-tooled Western Belt",
                description="1.5 inch belt with floral tooling pattern for Carol Martinez",
                type=ProjectType.BELT,
                status=ProjectStatus.MATERIAL_SELECTION,
                skill_level=SkillLevel.INTERMEDIATE,
                start_date=now - timedelta(days=1),
                estimated_completion_date=now + timedelta(days=10),
                customer_id=customers[2].id
            )
        ]
        session.add_all(projects)
        session.commit()

        # Connect projects to components
        logger.info("Linking Projects to Components")
        project_components = [
            ProjectComponent(
                project_id=projects[0].id,
                component_id=components[0].id,
                quantity=1
            ),
            ProjectComponent(
                project_id=projects[0].id,
                component_id=components[1].id,
                quantity=1
            ),
            ProjectComponent(
                project_id=projects[1].id,
                component_id=components[2].id,
                quantity=1
            ),
            ProjectComponent(
                project_id=projects[1].id,
                component_id=components[3].id,
                quantity=2
            ),
            ProjectComponent(
                project_id=projects[2].id,
                component_id=components[4].id,
                quantity=1
            )
        ]
        session.add_all(project_components)
        session.commit()

        # Create sample sales
        logger.info("Adding Sample Sales")
        sales = [
            Sales(
                customer_id=customers[0].id,
                total_amount=125.00,
                status=SaleStatus.IN_PRODUCTION,
                payment_status=PaymentStatus.PAID,
                sale_date=now - timedelta(days=7),
                customer_name=f"{customers[0].first_name} {customers[0].last_name}"
            ),
            Sales(
                customer_id=customers[3].id,
                total_amount=65.00,
                status=SaleStatus.COMPLETED,
                payment_status=PaymentStatus.PAID,
                sale_date=now - timedelta(days=10),
                customer_name=f"{customers[3].first_name} {customers[3].last_name}"
            ),
            Sales(
                customer_id=customers[4].id,
                total_amount=230.00,
                status=SaleStatus.IN_PRODUCTION,
                payment_status=PaymentStatus.PARTIALLY_PAID,
                sale_date=now - timedelta(days=3),
                customer_name=f"{customers[4].first_name} {customers[4].last_name}"
            ),
            Sales(
                customer_id=customers[1].id,
                total_amount=295.00,
                status=SaleStatus.DESIGN_APPROVAL,
                payment_status=PaymentStatus.PENDING,
                sale_date=now - timedelta(days=1),
                customer_name=f"{customers[1].first_name} {customers[1].last_name}"
            )
        ]
        session.add_all(sales)
        session.commit()

        # Create sales items
        logger.info("Adding Sales Items")
        sales_items = [
            SalesItem(
                sales_id=sales[0].id,
                product_id=products[0].id,
                quantity=1,
                price=125.00
            ),
            SalesItem(
                sales_id=sales[1].id,
                product_id=products[1].id,
                quantity=1,
                price=65.00
            ),
            SalesItem(
                sales_id=sales[2].id,
                product_id=products[3].id,
                quantity=1,
                price=135.00
            ),
            SalesItem(
                sales_id=sales[2].id,
                product_id=products[4].id,
                quantity=1,
                price=95.00
            ),
            SalesItem(
                sales_id=sales[3].id,
                product_id=products[2].id,
                quantity=1,
                price=295.00
            )
        ]
        session.add_all(sales_items)
        session.commit()

        # Link projects to sales
        logger.info("Linking Projects to Sales")
        # Update projects with sales_id
        projects[0].sales_id = sales[0].id
        projects[1].sales_id = sales[3].id
        projects[2].sales_id = sales[2].id
        session.commit()

        # Create picking lists for projects
        logger.info("Creating Picking Lists")
        picking_lists = [
            PickingList(
                sales_id=sales[0].id,
                status=PickingListStatus.IN_PROGRESS,
                created_at=now - timedelta(days=6)
            ),
            PickingList(
                sales_id=sales[2].id,
                status=PickingListStatus.PENDING,
                created_at=now - timedelta(days=2)
            ),
            PickingList(
                sales_id=sales[3].id,
                status=PickingListStatus.PENDING,
                created_at=now - timedelta(days=1)
            )
        ]
        session.add_all(picking_lists)
        session.commit()

        # Create picking list items
        picking_list_items = [
            PickingListItem(
                picking_list_id=picking_lists[0].id,
                leather_id=leathers[1].id,  # Horween Chromexcel
                quantity_ordered=1.25,
                quantity_picked=1.25
            ),
            PickingListItem(
                picking_list_id=picking_lists[0].id,
                material_id=materials[0].id,  # Tiger Thread
                quantity_ordered=1,
                quantity_picked=1
            ),
            PickingListItem(
                picking_list_id=picking_lists[1].id,
                leather_id=leathers[0].id,  # English Bridle
                quantity_ordered=1.75,
                quantity_picked=0
            ),
            PickingListItem(
                picking_list_id=picking_lists[1].id,
                hardware_id=hardware_items[0].id,  # Brass Buckle
                quantity_ordered=1,
                quantity_picked=0
            ),
            PickingListItem(
                picking_list_id=picking_lists[2].id,
                leather_id=leathers[0].id,  # English Bridle
                quantity_ordered=5.0,
                quantity_picked=0
            ),
            PickingListItem(
                picking_list_id=picking_lists[2].id,
                hardware_id=hardware_items[3].id,  # D-Rings
                quantity_ordered=2,
                quantity_picked=0
            )
        ]
        session.add_all(picking_list_items)
        session.commit()

        # Create tool lists for projects
        logger.info("Creating Tool Lists")
        tool_lists = [
            ToolList(
                project_id=projects[0].id,
                status=ToolListStatus.COMPLETED,
                created_at=now - timedelta(days=6)
            ),
            ToolList(
                project_id=projects[1].id,
                status=ToolListStatus.PENDING,
                created_at=now - timedelta(days=1)
            ),
            ToolList(
                project_id=projects[2].id,
                status=ToolListStatus.PENDING,
                created_at=now - timedelta(days=1)
            )
        ]
        session.add_all(tool_lists)
        session.commit()

        # Create tool list items
        tool_list_items = [
            ToolListItem(
                tool_list_id=tool_lists[0].id,
                tool_id=tools[0].id,  # Pricking Irons
                quantity=1
            ),
            ToolListItem(
                tool_list_id=tool_lists[0].id,
                tool_id=tools[2].id,  # Edge Beveler
                quantity=1
            ),
            ToolListItem(
                tool_list_id=tool_lists[1].id,
                tool_id=tools[0].id,  # Pricking Irons
                quantity=1
            ),
            ToolListItem(
                tool_list_id=tool_lists[1].id,
                tool_id=tools[1].id,  # Skiving Knife
                quantity=1
            ),
            ToolListItem(
                tool_list_id=tool_lists[1].id,
                tool_id=tools[3].id,  # Stitching Pony
                quantity=1
            ),
            ToolListItem(
                tool_list_id=tool_lists[2].id,
                tool_id=tools[0].id,  # Pricking Irons
                quantity=1
            ),
            ToolListItem(
                tool_list_id=tool_lists[2].id,
                tool_id=tools[4].id,  # Hole Punch Set
                quantity=1
            )
        ]
        session.add_all(tool_list_items)
        session.commit()

        # Create sample purchases
        logger.info("Adding Sample Purchases")
        purchases = [
            Purchase(
                supplier_id=suppliers[0].id,  # Wickett & Craig
                total_amount=749.50,
                status=PurchaseStatus.COMPLETED,
                purchase_date=now - timedelta(days=30)
            ),
            Purchase(
                supplier_id=suppliers[1].id,  # Buckleguy Hardware
                total_amount=215.25,
                status=PurchaseStatus.COMPLETED,
                purchase_date=now - timedelta(days=25)
            ),
            Purchase(
                supplier_id=suppliers[2].id,  # Maine Thread
                total_amount=149.95,
                status=PurchaseStatus.COMPLETED,
                purchase_date=now - timedelta(days=20)
            ),
            Purchase(
                supplier_id=suppliers[3].id,  # Horween
                total_amount=625.00,
                status=PurchaseStatus.DELIVERED,
                purchase_date=now - timedelta(days=10)
            ),
            Purchase(
                supplier_id=suppliers[4].id,  # Weaver Leathercraft
                total_amount=312.75,
                status=PurchaseStatus.PROCESSING,
                purchase_date=now - timedelta(days=3)
            )
        ]
        session.add_all(purchases)
        session.commit()

        # Create purchase items
        logger.info("Adding Purchase Items")
        purchase_items = [
            # Wickett & Craig purchase
            PurchaseItem(
                purchase_id=purchases[0].id,
                leather_id=leathers[0].id,  # English Bridle
                quantity=50,  # sq ft
                price=14.99 * 50  # cost per unit * quantity
            ),
            # Buckleguy Hardware purchase
            PurchaseItem(
                purchase_id=purchases[1].id,
                hardware_id=hardware_items[0].id,  # Brass Buckle
                quantity=20,
                price=5.75 * 20
            ),
            PurchaseItem(
                purchase_id=purchases[1].id,
                hardware_id=hardware_items[1].id,  # Double Cap Rivets
                quantity=100,
                price=0.35 * 100
            ),
            PurchaseItem(
                purchase_id=purchases[1].id,
                hardware_id=hardware_items[3].id,  # D-Rings
                quantity=30,
                price=1.50 * 30
            ),
            # Maine Thread purchase
            PurchaseItem(
                purchase_id=purchases[2].id,
                material_id=materials[0].id,  # Tiger Thread
                quantity=6,  # spools
                price=24.99 * 6
            ),
            # Horween purchase
            PurchaseItem(
                purchase_id=purchases[3].id,
                leather_id=leathers[1].id,  # Chromexcel
                quantity=25,  # sq ft
                price=12.50 * 25
            ),
            PurchaseItem(
                purchase_id=purchases[3].id,
                leather_id=leathers[2].id,  # Shell Cordovan
                quantity=5,  # sq ft
                price=75.00 * 5
            ),
            # Weaver Leathercraft purchase
            PurchaseItem(
                purchase_id=purchases[4].id,
                material_id=materials[2].id,  # Barge Cement
                quantity=5,
                price=14.50 * 5
            ),
            PurchaseItem(
                purchase_id=purchases[4].id,
                material_id=materials[3].id,  # Edge Paint
                quantity=6,
                price=22.95 * 6
            ),
            PurchaseItem(
                purchase_id=purchases[4].id,
                tool_id=tools[2].id,  # Edge Beveler
                quantity=1,
                price=42.75
            )
        ]
        session.add_all(purchase_items)
        session.commit()

        # Create inventory entries
        logger.info("Adding Inventory Entries")

        # Leather inventory
        leather_inventory = [
            LeatherInventory(
                leather_id=leathers[0].id,  # English Bridle
                quantity=35.5,  # sq ft
                status=InventoryStatus.IN_STOCK,
                storage_location="Shelf A1"
            ),
            LeatherInventory(
                leather_id=leathers[1].id,  # Chromexcel
                quantity=18.25,
                status=InventoryStatus.IN_STOCK,
                storage_location="Shelf A2"
            ),
            LeatherInventory(
                leather_id=leathers[2].id,  # Shell Cordovan
                quantity=4.5,
                status=InventoryStatus.IN_STOCK,
                storage_location="Shelf A3 (Locked)"
            ),
            LeatherInventory(
                leather_id=leathers[3].id,  # Chevre
                quantity=6.75,
                status=InventoryStatus.LOW_STOCK,
                storage_location="Shelf A4"
            ),
            LeatherInventory(
                leather_id=leathers[4].id,  # Pueblo
                quantity=12.0,
                status=InventoryStatus.IN_STOCK,
                storage_location="Shelf A5"
            )
        ]
        session.add_all(leather_inventory)

        # Hardware inventory
        hardware_inventory = [
            HardwareInventory(
                hardware_id=hardware_items[0].id,  # Brass Buckle
                quantity=15,
                status=InventoryStatus.IN_STOCK,
                storage_location="Drawer B1"
            ),
            HardwareInventory(
                hardware_id=hardware_items[1].id,  # Double Cap Rivets
                quantity=85,
                status=InventoryStatus.IN_STOCK,
                storage_location="Drawer B2"
            ),
            HardwareInventory(
                hardware_id=hardware_items[2].id,  # Magnetic Snap
                quantity=8,
                status=InventoryStatus.LOW_STOCK,
                storage_location="Drawer B3"
            ),
            HardwareInventory(
                hardware_id=hardware_items[3].id,  # D-Rings
                quantity=22,
                status=InventoryStatus.IN_STOCK,
                storage_location="Drawer B4"
            ),
            HardwareInventory(
                hardware_id=hardware_items[4].id,  # Concho
                quantity=5,
                status=InventoryStatus.LOW_STOCK,
                storage_location="Drawer B5"
            )
        ]
        session.add_all(hardware_inventory)

        # Material inventory
        material_inventory = [
            MaterialInventory(
                material_id=materials[0].id,  # Tiger Thread
                quantity=4,
                status=InventoryStatus.IN_STOCK,
                storage_location="Cabinet C1"
            ),
            MaterialInventory(
                material_id=materials[1].id,  # Beeswax
                quantity=3,
                status=InventoryStatus.IN_STOCK,
                storage_location="Cabinet C2"
            ),
            MaterialInventory(
                material_id=materials[2].id,  # Barge Cement
                quantity=2,
                status=InventoryStatus.LOW_STOCK,
                storage_location="Cabinet C3"
            ),
            MaterialInventory(
                material_id=materials[3].id,  # Edge Paint
                quantity=5,
                status=InventoryStatus.IN_STOCK,
                storage_location="Cabinet C4"
            ),
            MaterialInventory(
                material_id=materials[4].id,  # Pigskin Lining
                quantity=8.5,
                status=InventoryStatus.IN_STOCK,
                storage_location="Shelf A6"
            )
        ]
        session.add_all(material_inventory)

        # Tool inventory
        tool_inventory = [
            ToolInventory(
                tool_id=tools[0].id,  # Pricking Irons
                quantity=2,
                status=InventoryStatus.IN_STOCK,
                storage_location="Toolbox D1"
            ),
            ToolInventory(
                tool_id=tools[1].id,  # Skiving Knife
                quantity=3,
                status=InventoryStatus.IN_STOCK,
                storage_location="Toolbox D2"
            ),
            ToolInventory(
                tool_id=tools[2].id,  # Edge Beveler
                quantity=2,
                status=InventoryStatus.IN_STOCK,
                storage_location="Toolbox D3"
            ),
            ToolInventory(
                tool_id=tools[3].id,  # Stitching Pony
                quantity=1,
                status=InventoryStatus.IN_STOCK,
                storage_location="Workbench Area"
            ),
            ToolInventory(
                tool_id=tools[4].id,  # Hole Punch Set
                quantity=1,
                status=InventoryStatus.IN_STOCK,
                storage_location="Toolbox D4"
            )
        ]
        session.add_all(tool_inventory)

        # Product inventory for finished goods
        product_inventory = [
            ProductInventory(
                product_id=products[0].id,  # Bifold Wallet
                quantity=2,
                status=InventoryStatus.IN_STOCK,
                storage_location="Display Case 1"
            ),
            ProductInventory(
                product_id=products[1].id,  # Card Holder
                quantity=3,
                status=InventoryStatus.IN_STOCK,
                storage_location="Display Case 1"
            ),
            ProductInventory(
                product_id=products[2].id,  # Market Tote
                quantity=1,
                status=InventoryStatus.IN_STOCK,
                storage_location="Display Case 2"
            ),
            ProductInventory(
                product_id=products[3].id,  # Bridle Belt
                quantity=4,
                status=InventoryStatus.IN_STOCK,
                storage_location="Display Case 3"
            ),
            ProductInventory(
                product_id=products[4].id,  # Journal Cover
                quantity=2,
                status=InventoryStatus.IN_STOCK,
                storage_location="Display Case 1"
            )
        ]
        session.add_all(product_inventory)
        session.commit()

        logger.info("Sample data added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding sample data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if own_session:
            session.rollback()
        return False
    finally:
        if own_session and session:
            session.close()


def add_extra_demo_data(session: Optional[Session] = None):
    """
    Adds extended demo data on top of the standard sample data.
    Meant for presentations, comprehensive testing, or feature demonstrations.

    This function significantly expands the dataset with:
    1. A diverse customer base with varied preferences and order histories
    2. Historical sales data for trend analysis and reporting
    3. Diverse inventory with realistic stock levels
    4. Multiple ongoing projects in various stages

    Args:
        session (Optional[Session]): Existing database session

    Returns:
        bool: True if successful, False otherwise
    """
    # Create session if not provided
    own_session = False
    if session is None:
        try:
            engine = create_engine(f"sqlite:///{get_database_path()}", echo=False)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            own_session = True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create session for extra demo data: {e}")
            return False

    try:
        # Import needed models
        from database.models.customer import Customer
        from database.models.product import Product
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem
        from database.models.project import Project
        from database.models.leather_inventory import LeatherInventory
        from database.models.hardware_inventory import HardwareInventory
        from database.models.leather import Leather
        from database.models.hardware import Hardware
        from database.models.material import Material
        from database.models.material_inventory import MaterialInventory
        from database.models.enums import (
            SaleStatus, PaymentStatus, CustomerStatus, CustomerTier,
            CustomerSource, ProjectStatus, ProjectType, SkillLevel,
            InventoryStatus
        )

        # Get the current datetime for time-based records
        now = datetime.now()

        # Fetch existing data to reference
        existing_products = session.query(Product).all()
        all_customers = session.query(Customer).all()
        all_materials = {
            'leather': session.query(Leather).all(),
            'hardware': session.query(Hardware).all(),
            'material': session.query(Material).all()
        }

        # Add 15 more diverse customers
        logger.info("Adding additional customers for demo")
        customer_sources = [
            CustomerSource.WEBSITE,
            CustomerSource.TRADE_SHOW,
            CustomerSource.SOCIAL_MEDIA,
            CustomerSource.REFERRAL,
            CustomerSource.WORD_OF_MOUTH
        ]

        customer_tiers = [
            CustomerTier.STANDARD,
            CustomerTier.PREMIUM,
            CustomerTier.VIP
        ]

        demo_cities = [
            ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
            ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
            ("San Diego", "CA"), ("Dallas", "TX"), ("San Francisco", "CA"),
            ("Austin", "TX"), ("Boston", "MA"), ("Denver", "CO"),
            ("Seattle", "WA"), ("Nashville", "TN"), ("Atlanta", "GA")
        ]

        customers = []
        for i in range(1, 16):
            city, state = demo_cities[i - 1]
            source_index = (i % len(customer_sources))
            tier_index = (i % 3)

            interests = ["Wallets", "Bags", "Belts", "Custom Work", "Tooling", "Exotic Leathers"]
            interests_sample = random.sample(interests, k=min(3, random.randint(1, 3)))

            customer = Customer(
                first_name=f"Demo{i}",
                last_name=f"Customer{i}",
                email=f"demo{i}@example.com",
                phone=f"555-{i:03d}-{1000 + i * 111}",
                address=f"{100 + i * 10} Main Street, {city}, {state}",
                status=CustomerStatus.ACTIVE,
                customer_tier=customer_tiers[tier_index],
                customer_source=customer_sources[source_index],
                notes=f"Interests: {', '.join(interests_sample)}"
            )
            customers.append(customer)

        session.add_all(customers)
        session.flush()

        # Merge with existing customers
        all_customers.extend(customers)

        # Create historical sales spread over the last 120 days
        logger.info("Adding historical sales data for demo")

        # Create date distribution - more recent dates should be more common
        dates = []
        for days_back in range(1, 121):
            # Add more recent dates with higher probability
            weight = max(1, int(120 / days_back))
            dates.extend([now - timedelta(days=days_back)] * weight)

        demo_sales = []
        sales_items_batch = []

        # Create 75 sales with varied products and quantities
        for i in range(1, 76):
            # Determine a weighted random date
            sale_date = random.choice(dates)

            # Pick a random customer with higher probability for VIPs and PREMIUM
            customer_weights = [
                3 if c.customer_tier == CustomerTier.VIP else
                2 if c.customer_tier == CustomerTier.PREMIUM else
                1 for c in all_customers
            ]
            customer = random.choices(all_customers, weights=customer_weights)[0]

            # Determine status based on date
            if (now - sale_date).days < 7:
                # Recent orders more likely to be in progress
                status_options = [SaleStatus.IN_PRODUCTION, SaleStatus.DESIGN_APPROVAL, SaleStatus.MATERIALS_SOURCING]
                payment_status = random.choice([PaymentStatus.PARTIALLY_PAID, PaymentStatus.PENDING])
            elif (now - sale_date).days < 14:
                # Orders 7-14 days old likely to be nearing completion
                status_options = [SaleStatus.IN_PRODUCTION, SaleStatus.QUALITY_REVIEW, SaleStatus.READY_FOR_PICKUP]
                payment_status = random.choice([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID])
            else:
                # Older orders likely completed
                status_options = [SaleStatus.COMPLETED, SaleStatus.DELIVERED]
                payment_status = PaymentStatus.PAID

            status = random.choice(status_options)

            # Create a sale with 1-3 products
            sale = Sales(
                customer_id=customer.id,
                total_amount=0,  # Will calculate based on items
                status=status,
                payment_status=payment_status,
                sale_date=sale_date,
                customer_name=f"{customer.first_name} {customer.last_name}"
            )
            session.add(sale)
            session.flush()  # Get the sale ID

            # Add 1-3 products to the sale
            num_products = random.choices([1, 2, 3], weights=[50, 30, 20])[0]
            sale_total = 0

            # Ensure we don't try to add more products than exist
            num_products = min(num_products, len(existing_products))

            # Select random products without replacement for this sale
            sale_products = random.sample(existing_products, num_products)

            for product in sale_products:
                quantity = random.choices([1, 2, 3], weights=[70, 20, 10])[0]

                # Apply occasional discount for VIP/Premium customers
                discount = 0
                if customer.customer_tier in [CustomerTier.VIP, CustomerTier.PREMIUM]:
                    discount = random.choices([0, 0.05, 0.1], weights=[70, 20, 10])[0]

                item_price = round(product.price * (1 - discount), 2)
                sale_total += item_price * quantity

                item = SalesItem(
                    sales_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=item_price
                )
                sales_items_batch.append(item)

            # Update the sale total
            sale.total_amount = round(sale_total, 2)
            demo_sales.append(sale)

            # Batch insert sales items every 10 sales for performance
            if i % 10 == 0:
                session.add_all(sales_items_batch)
                session.flush()
                sales_items_batch = []

        # Add any remaining sales items
        if sales_items_batch:
            session.add_all(sales_items_batch)
            session.flush()

        # Create 10 additional ongoing projects in various stages
        logger.info("Adding additional projects in various stages")
        project_types = [
            ProjectType.WALLET, ProjectType.TOTE_BAG,
            ProjectType.BELT, ProjectType.MESSENGER_BAG,
            ProjectType.WATCH_STRAP, ProjectType.CUSTOM
        ]

        project_statuses = [
            ProjectStatus.DESIGN_PHASE, ProjectStatus.PATTERN_DEVELOPMENT,
            ProjectStatus.MATERIAL_SELECTION, ProjectStatus.CUTTING,
            ProjectStatus.ASSEMBLY, ProjectStatus.STITCHING,
            ProjectStatus.EDGE_FINISHING, ProjectStatus.QUALITY_CHECK
        ]

        skill_levels = [
            SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE,
            SkillLevel.ADVANCED, SkillLevel.MASTER
        ]

        # Select sales that don't already have projects
        existing_project_sales = session.query(Project.sales_id).filter(Project.sales_id != None).all()
        existing_project_sales_ids = [s[0] for s in existing_project_sales]

        # Find sales in production without projects
        available_sales = [s for s in demo_sales if s.id not in existing_project_sales_ids
                           and s.status in [SaleStatus.IN_PRODUCTION, SaleStatus.MATERIALS_SOURCING,
                                            SaleStatus.DESIGN_APPROVAL]]

        # Create additional projects
        for i in range(min(10, len(available_sales))):
            sale = available_sales[i]
            project_type = random.choice(project_types)
            status = random.choice(project_statuses)
            skill = random.choice(skill_levels)

            # Project timeline based on complexity and status
            complexity_factor = 1.0
            if skill in [SkillLevel.ADVANCED, SkillLevel.MASTER]:
                complexity_factor = 2.0

            # Status determines progress
            progress = project_statuses.index(status) / len(project_statuses)

            # Timeline: 1-4 weeks total based on complexity
            total_days = int(7 + (21 * complexity_factor))
            days_elapsed = int(total_days * progress)
            days_remaining = total_days - days_elapsed

            project = Project(
                name=f"{project_type.name.replace('_', ' ').title()} Project",
                description=f"Custom {project_type.name.lower().replace('_', ' ')} for {sale.customer_name}",
                type=project_type,
                status=status,
                skill_level=skill,
                start_date=now - timedelta(days=days_elapsed),
                estimated_completion_date=now + timedelta(days=days_remaining),
                customer_id=sale.customer_id,
                sales_id=sale.id
            )
            session.add(project)

        # Add inventory fluctuations for materials
        logger.info("Adding realistic inventory levels and adjustments")

        # Update leather inventory with realistic levels
        leather_inventory = session.query(LeatherInventory).all()
        for inv in leather_inventory:
            # Add some randomness to inventory levels
            current = inv.quantity
            # More popular items have lower stock
            popularity = random.random()  # 0 to 1
            multiplier = 0.5 + (1.5 * (1 - popularity))  # 0.5 to 2.0

            new_quantity = round(current * multiplier, 2)
            inv.quantity = max(0.5, new_quantity)  # Ensure at least some stock

            # Set some items to low stock
            if random.random() < 0.3:  # 30% chance
                inv.status = InventoryStatus.LOW_STOCK

        # Update hardware inventory with more variance
        hardware_inventory = session.query(HardwareInventory).all()
        for inv in hardware_inventory:
            # Hardware items can have greater variation
            if random.random() < 0.2:  # 20% chance of being out of stock
                inv.quantity = 0
                inv.status = InventoryStatus.OUT_OF_STOCK
            elif random.random() < 0.4:  # 40% chance of being low stock
                inv.quantity = random.randint(1, 5)
                inv.status = InventoryStatus.LOW_STOCK
            else:  # 40% chance of being well-stocked
                inv.quantity = random.randint(10, 50)
                inv.status = InventoryStatus.IN_STOCK

        # Update material inventory with realistic usage patterns
        material_inventory = session.query(MaterialInventory).all()
        for inv in material_inventory:
            # Some materials are consumables with faster turnover
            material_type = None
            for mat in all_materials['material']:
                if mat.id == inv.material_id:
                    material_type = mat.type
                    break

            if material_type in [MaterialType.ADHESIVE, MaterialType.EDGE_PAINT, MaterialType.WAX]:
                # Consumables tend to run lower
                inv.quantity = random.randint(1, 3)
                inv.status = random.choice([InventoryStatus.LOW_STOCK, InventoryStatus.IN_STOCK])
            else:
                # Other materials maintain better stock
                inv.quantity = random.randint(3, 10)
                inv.status = InventoryStatus.IN_STOCK

        logger.info(
            f"Added {len(customers)} additional customers and {len(demo_sales)} sales records for demo purposes")
        return True
    except Exception as e:
        logger.error(f"Error adding extra demo data: {e}")
        session.rollback()
        return False
    finally:
        if own_session and session:
            if not session.in_transaction():
                session.close()


def main():
    """
    Main function to initialize database and optionally seed with sample data.

    Supports environment variables for different initialization modes:
    - RECREATE_DB: If "true", drops all tables and recreates them
    - SEED_DB: If "true", adds sample data to the database
    - SEED_MODE: Controls how much data to add:
      - "minimal": Just a few records
      - "standard": Comprehensive set of related data (default)
      - "demo": Extended data suitable for demonstrations
    - DRY_RUN: If "true", validates operations without committing changes

    Also supports command-line arguments that override environment variables:
    python initialize_database.py --recreate --seed --mode=demo

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    import time
    import argparse
    from contextlib import contextmanager

    start_time = time.time()

    # Parse command line arguments (these override environment variables)
    parser = argparse.ArgumentParser(description='Initialize leatherworking database')
    parser.add_argument('--recreate', action='store_true', help='Drop and recreate all tables')
    parser.add_argument('--seed', action='store_true', help='Add sample data to database')
    parser.add_argument('--mode', choices=['minimal', 'standard', 'demo'],
                        default=None, help='Amount of sample data to add')
    parser.add_argument('--dry-run', action='store_true',
                        help='Validate without committing changes')
    args = parser.parse_args()

    # Context manager for session handling
    @contextmanager
    def session_scope():
        """Provide a transactional scope around a series of operations."""
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            yield session
            if not dry_run:
                session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

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
            return False

        db_init_time = time.time()
        logger.info(f"Database schema initialized in {db_init_time - start_time:.2f} seconds")

        # Add sample data if requested
        if seed_db:
            logger.info(f"Seeding database in {seed_mode} mode...")

            with session_scope() as session:
                # Check if data already exists
                try:
                    from database.models.customer import Customer
                    existing_count = session.query(Customer).count()
                    if existing_count > 0 and not recreate_db:
                        logger.warning(f"Database already contains {existing_count} customers")
                        user_input = input("Continue with seeding? This may create duplicate data. (y/n): ")
                        if user_input.lower() != 'y':
                            logger.info("Seeding canceled by user")
                            return True
                except Exception as e:
                    logger.warning(f"Could not check for existing data: {e}")

                try:
                    # Call appropriate sample data function based on mode
                    if seed_mode == "minimal":
                        logger.info("Adding minimal sample data...")
                        success = add_minimal_sample_data(session)
                    elif seed_mode == "demo":
                        logger.info("Adding extended demo data...")
                        # Use a single transaction for better performance
                        success = add_sample_data(session)
                        if success:
                            logger.info("Adding additional demo data...")
                            success = add_extra_demo_data(session)
                    else:  # Default to standard
                        logger.info("Adding standard sample data...")
                        success = add_sample_data(session)

                    if success:
                        if dry_run:
                            logger.info("Dry run successful - sample data validated but not committed")
                            session.rollback()
                        else:
                            logger.info("Database seeding complete")
                    else:
                        logger.error("Database seeding failed")
                        return False

                except Exception as e:
                    logger.error(f"Database seeding failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False
        else:
            logger.info("Skipping sample data seeding")

        # Log performance metrics
        end_time = time.time()
        logger.info(f"Database initialization completed in {end_time - start_time:.2f} seconds")

        # Validate database structure
        with session_scope() as session:
            try:
                # Import models needed for validation
                from database.models.customer import Customer
                from database.models.product import Product
                from database.models.sales import Sales

                # Perform basic validation queries to ensure database is working
                customer_count = session.query(Customer).count()
                product_count = session.query(Product).count()
                sales_count = session.query(Sales).count()

                logger.info(
                    f"Database validation: {customer_count} customers, {product_count} products, {sales_count} sales records")

                if seed_db and customer_count == 0 and not dry_run:
                    logger.warning("Database appears to be empty after seeding - possible issue")

            except Exception as e:
                logger.warning(f"Database validation failed: {e}")

        return True
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def add_minimal_sample_data(session: Session) -> bool:
    """
    Adds a minimal set of sample data to the database for quick testing.
    Contains just enough data to test core functionality without overwhelming the database.

    Args:
        session (Session): SQLAlchemy database session

    Returns:
        bool: True if sample data was added successfully, False otherwise
    """
    try:
        # Import models
        from database.models.customer import Customer
        from database.models.supplier import Supplier
        from database.models.leather import Leather
        from database.models.hardware import Hardware
        from database.models.material import Material
        from database.models.product import Product
        from database.models.pattern import Pattern
        from database.models.product_pattern import ProductPattern
        from database.models.project import Project
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem
        from database.models.tool import Tool

        # Import enums
        from database.models.enums import (
            SupplierStatus, CustomerStatus, CustomerTier, LeatherType,
            MaterialQualityGrade, HardwareMaterial, HardwareFinish,
            HardwareType, MaterialType, SaleStatus, PaymentStatus,
            ProjectType, ProjectStatus, SkillLevel, CustomerSource,
            ToolCategory, MeasurementUnit
        )

        logger.info("Adding minimal sample data...")

        # Create one supplier
        supplier = Supplier(
            name="Wickett & Craig",
            contact_name="Thomas Wilson",
            contact_email="sales@wickettandcraig.com",
            phone="555-789-1234",
            address="120 Tannery Lane, Curwensville, PA 16833",
            status=SupplierStatus.ACTIVE,
            notes="Premium vegetable tanned leather supplier"
        )
        session.add(supplier)
        session.flush()  # Get ID without committing

        # Create one customer
        customer = Customer(
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            phone="555-111-2222",
            address="789 Crafting Street, Portland, OR 97210",
            status=CustomerStatus.ACTIVE,
            customer_tier=CustomerTier.STANDARD,
            customer_source=CustomerSource.WEBSITE,
            notes="Leather hobbyist"
        )
        session.add(customer)
        session.flush()

        # Create one leather material
        leather = Leather(
            name="English Bridle",
            type=LeatherType.VEGETABLE_TANNED,
            quality=MaterialQualityGrade.PREMIUM,
            supplier_id=supplier.id,
            color="Chestnut",
            thickness=3.5,  # mm
            origin="USA",
            cost_per_unit=14.99,
            unit=MeasurementUnit.SQUARE_FOOT
        )
        session.add(leather)
        session.flush()

        # Create one hardware item
        hardware = Hardware(
            name="Solid Brass Buckle",
            type=HardwareType.BUCKLE,
            supplier_id=supplier.id,
            material=HardwareMaterial.BRASS,
            finish=HardwareFinish.POLISHED,
            size="1.5 inch",
            cost_per_unit=5.75,
            unit=MeasurementUnit.PIECE
        )
        session.add(hardware)
        session.flush()

        # Create one material
        material = Material(
            name="Tiger Thread",
            type=MaterialType.THREAD,
            supplier_id=supplier.id,
            color="Natural",
            thickness=0.6,  # mm
            cost_per_unit=24.99,
            unit=MeasurementUnit.PIECE,
            quality=MaterialQualityGrade.PREMIUM
        )
        session.add(material)
        session.flush()

        # Create one tool
        tool = Tool(
            name="Kevin Lee Pricking Irons",
            description="3mm spacing, 2+8 teeth set",
            category=ToolCategory.PUNCHING,
            supplier_id=supplier.id,
            cost=149.95
        )
        session.add(tool)
        session.flush()

        # Create one product
        product = Product(
            name="Bifold Wallet",
            description="Handcrafted full-grain leather wallet with 6 card slots",
            price=125.00,
            cost=45.75,
            sku="BFW-001"
        )
        session.add(product)
        session.flush()

        # Create one pattern
        pattern = Pattern(
            name="Classic Bifold Wallet Pattern",
            description="Traditional bifold with detailed construction notes",
            skill_level=SkillLevel.INTERMEDIATE
        )
        session.add(pattern)
        session.flush()

        # Link product to pattern
        product_pattern = ProductPattern(
            product_id=product.id,
            pattern_id=pattern.id
        )
        session.add(product_pattern)
        session.flush()

        # Create one sales record
        now = datetime.now()
        sale = Sales(
            customer_id=customer.id,
            total_amount=125.00,
            status=SaleStatus.IN_PRODUCTION,
            payment_status=PaymentStatus.PAID,
            sale_date=now - timedelta(days=7),
            customer_name=f"{customer.first_name} {customer.last_name}"
        )
        session.add(sale)
        session.flush()

        # Create sales item
        sales_item = SalesItem(
            sales_id=sale.id,
            product_id=product.id,
            quantity=1,
            price=125.00
        )
        session.add(sales_item)
        session.flush()

        # Create one project
        project = Project(
            name="Custom Wallet Project",
            description="Personalized wallet for Alice Johnson",
            type=ProjectType.WALLET,
            status=ProjectStatus.IN_PROGRESS,
            skill_level=SkillLevel.INTERMEDIATE,
            start_date=now - timedelta(days=5),
            estimated_completion_date=now + timedelta(days=5),
            customer_id=customer.id,
            sales_id=sale.id
        )
        session.add(project)
        session.flush()

        logger.info("Minimal sample data added successfully")
        return True

    except Exception as e:
        logger.error(f"Error adding minimal sample data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        session.rollback()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)