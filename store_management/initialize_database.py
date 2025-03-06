# database/initialize_database.py
import logging
import os
import sys
from datetime import datetime
from typing import Optional, List
from sqlalchemy import inspect, text, create_engine, Column, Integer, ForeignKey
from sqlalchemy.orm import Session, sessionmaker
from pathlib import Path

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Utility function to get database path
def get_database_path(self=None):
    """
    Determine the path for the SQLite database.

    Returns:
        str: Absolute path to the database file
    """
    # Simple implementation to avoid circular imports
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / 'data'
    os.makedirs(data_dir, exist_ok=True)
    return str(data_dir / 'database.db')


def import_all_models():
    """
    Dynamically import all database models to ensure they are registered.

    This helps resolve circular import issues and ensures all models
    are loaded before creating tables.
    """
    from database.models import (
        base, customer, components, hardware,
        inventory, leather, material, sale,
        sale_item, pattern, picking_list,
        product, project, shopping_list,
        storage, supplier, transaction
    )
    logger.info("All models imported successfully")


def check_table_structures(engine):
    """
    Verify and fix database table structures to match model definitions.

    Args:
        engine: SQLAlchemy engine instance
    """
    inspector = inspect(engine)

    # Column checks
    column_checks = [
        {
            'table': 'materials',
            'column': 'storage_id',
            'definition': 'INTEGER REFERENCES storages(id)',
            'added': False
        },
        {
            'table': 'materials',
            'column': 'is_deleted',
            'definition': 'BOOLEAN DEFAULT 0',
            'added': False
        },
        {
            'table': 'materials',
            'column': 'deleted_at',
            'definition': 'DATETIME',
            'added': False
        },
        {
            'table': 'materials',
            'column': 'uuid',
            'definition': 'VARCHAR(36)',
            'added': False
        }
    ]

    # Check and add missing columns
    with engine.begin() as conn:
        for check in column_checks:
            if check['table'] in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns(check['table'])]
                if check['column'] not in columns:
                    try:
                        sql = f"ALTER TABLE {check['table']} ADD COLUMN {check['column']} {check['definition']}"
                        conn.execute(text(sql))
                        logger.info(f"Added {check['column']} to {check['table']}")
                        check['added'] = True
                    except Exception as e:
                        logger.error(f"Error adding {check['column']} to {check['table']}: {e}")

    # Check if picking_lists table exists
    if 'picking_lists' not in inspector.get_table_names():
        logger.warning("picking_lists table not found in database")
        try:
            from database.models.picking_list import PickingList
            from database.models.base import Base
            # Create just the picking_lists table
            PickingList.__table__.create(engine)
            logger.info("Created picking_lists table")
        except Exception as e:
            logger.error(f"Error creating picking_lists table: {e}")


def initialize_database(recreate: bool = False):
    """
    Initialize the database, optionally recreating it from scratch.

    Args:
        recreate: If True, drop all tables and recreate them

    Returns:
        The SQLAlchemy engine
    """
    try:
        import_all_models()
        from database.models.base import Base

        db_path = get_database_path()
        logger.info(f"Using database path: {db_path}")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        engine = create_engine(f"sqlite:///{db_path}",
                               echo=False,
                               connect_args={'check_same_thread': False})

        if recreate:
            logger.info("Recreating database from scratch")
            # Drop all tables first
            Base.metadata.drop_all(engine)
            # Recreate all tables
            Base.metadata.create_all(engine)
            logger.info("Database tables dropped and recreated")
        else:
            # Check if tables exist first and create them if they don't
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables: {existing_tables}")

            # Create tables that don't exist yet
            Base.metadata.create_all(engine)
            logger.info("Created missing tables")

            # Check and fix table structures
            check_table_structures(engine)

        return engine
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def add_sample_data(session: Optional[Session] = None):
    """
    Adds comprehensive sample data to the database for testing and demonstration.

    Args:
        session (Optional[Session]): Existing database session. If None, a new session is created.
    """
    # Ensure models are imported
    from database.models import (
        supplier, leather, hardware,
        storage, project, sale,
        shopping_list, enums, customer
    )

    # Create session if not provided
    if session is None:
        engine = create_engine(f"sqlite:///{get_database_path()}", echo=True)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        own_session = True
    else:
        own_session = False

    try:
        # Create sample suppliers
        logger.info("Adding Sample Suppliers")
        supplier1 = supplier.Supplier(
            name="Tandy Leather",
            contact_name="John Doe",
            email="john.doe@tandyleather.com",
            phone="555-123-4567",
            address="123 Main St",
            notes="Main leather supplier"
        )
        supplier2 = supplier.Supplier(
            name="Buckle Guy",
            contact_name="Jane Smith",
            email="jane.smith@buckleguy.com",
            phone="555-987-6543",
            address="456 Elm St",
            notes="Hardware supplier"
        )
        session.add_all([supplier1, supplier2])
        session.commit()

        # Create sample customers
        logger.info("Adding Sample Customers")
        customer1 = customer.Customer(
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            phone="555-111-2222",
            address="789 Oak St",
            notes="Frequent customer"
        )
        customer2 = customer.Customer(
            first_name="Bob",
            last_name="Williams",
            email="bob.williams@example.com",
            phone="555-333-4444",
            address="101 Pine St",
            notes="New customer"
        )
        session.add_all([customer1, customer2])
        session.commit()

        # Create Sample Materials
        logger.info("Adding Sample Materials")
        leather1 = leather.Leather(
            name="Veg Tan Leather",
            type=enums.LeatherType.VEG_TAN,
            grade=enums.MaterialQualityGrade.PREMIUM,
            quantity=10,
            unit_price=50.0,
            color="Natural"
        )
        hardware1 = hardware.Hardware(
            name="Brass Buckles",
            type=enums.HardwareType.BUCKLE,
            material=enums.HardwareMaterial.BRASS,
            finish=enums.HardwareFinish.POLISHED,
            quantity=50,
            unit_price=5.0
        )
        session.add_all([leather1, hardware1])
        session.commit()

        # Create Sample Storage Locations
        logger.info("Adding Sample Storage Locations")
        storage1 = storage.Storage(
            location_name="Warehouse A",
            type=enums.StorageLocationType.SHELF,
            capacity=100,
            description="Main warehouse shelves"
        )
        storage2 = storage.Storage(
            location_name="Retail Display",
            type=enums.StorageLocationType.DISPLAY_CASE,
            capacity=20,
            description="Retail display case for showcasing finished products"
        )
        session.add_all([storage1, storage2])
        session.commit()

        # Create Sample Projects
        logger.info("Adding Sample Projects")
        project1 = project.Project(
            name="Leather Wallet",
            project_type=enums.ProjectType.WALLET,
            skill_level=enums.SkillLevel.INTERMEDIATE,
            description="A simple leather wallet project",
            status=enums.ProjectStatus.IN_PROGRESS
        )
        project2 = project.Project(
            name="Leather Belt",
            project_type=enums.ProjectType.BELT,
            skill_level=enums.SkillLevel.BEGINNER,
            description="A classic leather belt project",
            status=enums.ProjectStatus.COMPLETED
        )
        session.add_all([project1, project2])
        session.commit()

        # Create sample sales
        logger.info("Adding Sample Sales")
        sale1 = sale.Sale(
            customer_id=customer1.id,
            sale_date=datetime.now(),
            status=enums.SaleStatus.PENDING,
            payment_status=enums.PaymentStatus.UNPAID,
            total=100.00,
            sale_number="SALE-001",
            customer_name=f"{customer1.first_name} {customer1.last_name}",
            customer_email=customer1.email,
            shipping_address=customer1.address,
            notes="Sample sale"
        )
        session.add(sale1)
        session.commit()

        # Add sample shopping lists
        logger.info("Adding Sample Shopping Lists")
        shopping_list1 = shopping_list.ShoppingList(
            name="Restock Leather",
            priority=enums.Priority.HIGH,
            description="Restock on common leather types."
        )
        session.add(shopping_list1)
        session.commit()

        logger.info("Sample data added successfully!")
    except Exception as e:
        logger.error(f"An error occurred while adding sample data: {e}")
        session.rollback()
        raise
    finally:
        if own_session:
            session.close()


def main():
    """
    Main function to initialize database and optionally seed with sample data.
    """
    # Get environment variables
    recreate_db = os.environ.get("RECREATE_DB", "false").lower() == "true"
    seed_db = os.environ.get("SEED_DB", "false").lower() == "true"
    fix_columns = os.environ.get("FIX_COLUMNS", "true").lower() == "true"

    # Initialize database
    engine = initialize_database(recreate=recreate_db)

    # Add sample data if requested
    if seed_db:
        logger.info("Seeding database with sample data...")
        # Create a new session for adding sample data
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            add_sample_data(session)
            logger.info("Database seeding complete.")
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
        finally:
            session.close()
    else:
        logger.info("Skipping sample data seeding (SEED_DB not set to 'true').")

    logger.info("Database initialization completed.")


if __name__ == "__main__":
    main()