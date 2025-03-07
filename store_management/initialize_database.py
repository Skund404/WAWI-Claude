import logging
import os
import sys
import importlib
from datetime import datetime
from typing import Optional, List, Dict, Any
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

    This function checks for missing columns in existing tables and adds them
    if needed. It also verifies critical tables exist.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        bool: True if all critical tables exist, False otherwise
    """
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        logger.info(f"Existing tables: {existing_tables}")

        # Check and add missing columns
        column_checks = get_column_checks()
        with engine.begin() as conn:
            for check in column_checks:
                if check['table'] in existing_tables:
                    columns = [col['name'] for col in inspector.get_columns(check['table'])]
                    if check['column'] not in columns:
                        try:
                            sql = f"ALTER TABLE {check['table']} ADD COLUMN {check['column']} {check['definition']}"
                            conn.execute(text(sql))
                            logger.info(f"Added {check['column']} to {check['table']}")
                            check['added'] = True
                        except Exception as e:
                            logger.error(f"Error adding {check['column']} to {check['table']}: {e}")

        # Verify critical tables exist
        critical_tables = get_critical_tables()
        all_critical_tables_exist = True

        missing_tables = [table for table in critical_tables if table not in existing_tables]
        if missing_tables:
            logger.warning(f"Missing critical tables: {missing_tables}")
            all_critical_tables_exist = False

        return all_critical_tables_exist

    except Exception as e:
        logger.error(f"Error checking table structures: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def initialize_database(recreate: bool = False):
    """
    Initialize the database, optionally recreating it from scratch.

    Args:
        recreate: If True, drop all tables and recreate them

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

        db_path = get_database_path()
        logger.info(f"Using database path: {db_path}")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Create engine with improved error handling
        connection_string = f"sqlite:///{db_path}"
        try:
            engine = create_engine(
                connection_string,
                echo=False,
                connect_args={'check_same_thread': False}
            )
            # Test connection
            with engine.connect() as conn:
                pass
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
                # Recreate all tables
                Base.metadata.create_all(engine)
                logger.info("Database tables dropped and recreated")
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
            if not check_and_fix_table_structures(engine):
                logger.warning("Some critical tables might be missing or incorrect")

        # Initialize relationships in models after database creation
        initialize_all_relationships()

        return engine
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def add_sample_data(session: Optional[Session] = None):
    """
    Adds comprehensive sample data to the database for testing and demonstration.

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

        # Import enums
        from database.models.enums import (
            SupplierStatus, CustomerStatus, CustomerTier, LeatherType,
            MaterialQualityGrade, HardwareMaterial, HardwareFinish,
            HardwareType, MaterialType, SaleStatus, PaymentStatus,
            ProjectType, ProjectStatus, SkillLevel, InventoryStatus,
            PurchaseStatus
        )

        # Create sample suppliers
        logger.info("Adding Sample Suppliers")
        supplier1 = Supplier(
            name="Tandy Leather Supply",
            contact_name="John Doe",
            contact_email="john.doe@tandyleather.com",
            phone="555-123-4567",
            address="123 Leather Lane",
            status=SupplierStatus.ACTIVE,
            notes="Premium leather and hardware supplier"
        )
        supplier2 = Supplier(
            name="Hardware Specialists Inc.",
            contact_name="Jane Smith",
            contact_email="jane.smith@hardwarespecialists.com",
            phone="555-987-6543",
            address="456 Metal Road",
            status=SupplierStatus.ACTIVE,
            notes="Specialized hardware supplier"
        )
        session.add_all([supplier1, supplier2])
        session.commit()

        # Create sample customers
        logger.info("Adding Sample Customers")
        customer1 = Customer(
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            phone="555-111-2222",
            address="789 Crafting Street",
            status=CustomerStatus.ACTIVE,
            customer_tier=CustomerTier.STANDARD,
            notes="Frequent leatherwork enthusiast"
        )
        customer2 = Customer(
            first_name="Bob",
            last_name="Williams",
            email="bob.williams@example.com",
            phone="555-333-4444",
            address="101 Artisan Avenue",
            status=CustomerStatus.ACTIVE,
            customer_tier=CustomerTier.PREMIUM,
            notes="Custom project specialist"
        )
        session.add_all([customer1, customer2])
        session.commit()

        # Create sample materials
        logger.info("Adding Sample Materials")
        leather1 = Leather(
            name="Full Grain Veg Tan",
            type=LeatherType.VEG_TAN,
            quality=MaterialQualityGrade.PREMIUM,
            supplier_id=supplier1.id,
            color="Natural Tan",
            thickness=3.0,  # mm
            origin="Italy"
        )
        hardware1 = Hardware(
            name="Brass Buckles",
            type=HardwareType.BUCKLE,
            supplier_id=supplier2.id,
            material=HardwareMaterial.BRASS,
            finish=HardwareFinish.POLISHED,
            size="1 inch"
        )
        material1 = Material(
            name="Strong Polyester Thread",
            type=MaterialType.THREAD,
            supplier_id=supplier1.id,
            color="Black",
            thickness=0.8  # mm
        )
        session.add_all([leather1, hardware1, material1])
        session.commit()

        # Create sample products
        logger.info("Adding Sample Products")
        product1 = Product(
            name="Classic Leather Wallet",
            description="Handcrafted full-grain leather wallet",
            price=89.99
        )
        session.add(product1)
        session.commit()

        # Create sample pattern
        logger.info("Adding Sample Pattern")
        pattern1 = Pattern(
            name="Minimalist Wallet Pattern",
            description="Simple, elegant wallet design",
            skill_level=SkillLevel.INTERMEDIATE
        )
        session.add(pattern1)
        session.commit()

        # Link product to pattern
        product_pattern1 = ProductPattern(
            product_id=product1.id,
            pattern_id=pattern1.id
        )
        session.add(product_pattern1)

        # Create sample project
        logger.info("Adding Sample Project")
        project1 = Project(
            name="Custom Leather Wallet Project",
            description="Personalized wallet for customer",
            type=ProjectType.WALLET,
            status=ProjectStatus.IN_PROGRESS,
            skill_level=SkillLevel.INTERMEDIATE
        )
        session.add(project1)
        session.commit()

        # Create sample sales
        logger.info("Adding Sample Sales")
        sale1 = Sales(
            customer_id=customer1.id,
            total_amount=89.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID,
            sale_date=datetime.now()
        )
        session.add(sale1)
        session.commit()

        # Create sales item
        sales_item1 = SalesItem(
            sales_id=sale1.id,
            product_id=product1.id,
            quantity=1,
            price=89.99
        )
        session.add(sales_item1)

        # Create sample purchase
        logger.info("Adding Sample Purchase")
        purchase1 = Purchase(
            supplier_id=supplier1.id,
            total_amount=200.00,
            status=PurchaseStatus.COMPLETED,
            purchase_date=datetime.now()
        )
        session.add(purchase1)
        session.commit()

        # Create purchase items
        purchase_item1 = PurchaseItem(
            purchase_id=purchase1.id,
            leather_id=leather1.id,
            quantity=5,
            price=40.00
        )
        session.add(purchase_item1)

        # Manage inventory
        logger.info("Adding Sample Inventory")
        product_inv = ProductInventory(
            product_id=product1.id,
            quantity=10,
            status=InventoryStatus.IN_STOCK
        )
        leather_inv = LeatherInventory(
            leather_id=leather1.id,
            quantity=25.5,  # sq ft
            status=InventoryStatus.IN_STOCK
        )
        session.add_all([product_inv, leather_inv])

        # Commit all changes
        session.commit()

        logger.info("Sample data added successfully!")
        return True
    except Exception as e:
        logger.error(f"An error occurred while adding sample data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        session.rollback()
        return False
    finally:
        if own_session and session:
            session.close()


def main():
    """
    Main function to initialize database and optionally seed with sample data.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Get environment variables
        recreate_db = os.environ.get("RECREATE_DB", "false").lower() == "true"
        seed_db = os.environ.get("SEED_DB", "false").lower() == "true"

        # Initialize database
        engine = initialize_database(recreate=recreate_db)
        if not engine:
            logger.error("Database initialization failed")
            return False

        # Add sample data if requested
        if seed_db:
            logger.info("Seeding database with sample data...")
            # Create a new session for adding sample data
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()

            try:
                success = add_sample_data(session)
                if success:
                    logger.info("Database seeding complete.")
                else:
                    logger.error("Database seeding failed.")
            except Exception as e:
                logger.error(f"Database seeding failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
            finally:
                session.close()
        else:
            logger.info("Skipping sample data seeding (SEED_DB not set to 'true').")

        logger.info("Database initialization completed.")
        return True
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)