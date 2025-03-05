# database/initialize_database.py
import logging
import os
import sys
from datetime import datetime
from typing import Optional  # Added this import

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Utility function to get database path
def get_database_path():
    """
    Determine the path for the SQLite database.

    Returns:
        str: Absolute path to the database file
    """
    try:
        from config.paths import get_database_path
        return get_database_path()
    except ImportError:
        logger.warning("Could not import get_database_path from config.paths. Using default.")
        return os.path.abspath("store_management.db")


def import_all_models():
    """
    Dynamically import all database models to ensure they are registered.

    This helps resolve circular import issues and ensures all models
    are loaded before creating tables.
    """
    from database.models import (
        base, customer, components, hardware,
        inventory, leather, material, order,
        order_item, pattern, product,
        project, sales, shopping_list,
        storage, supplier, transaction
    )
    logger.info("All models imported successfully")


def initialize_database():
    try:
        import_all_models()
        from database.models.base import Base

        db_path = get_database_path()
        engine = create_engine(f"sqlite:///{db_path}", echo=True)  # Set echo to True to see SQL

        # Drop all tables first
        Base.metadata.drop_all(engine)

        # Recreate all tables
        Base.metadata.create_all(engine)

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
        storage, project, order,
        shopping_list, enums
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

        # Create sample orders
        logger.info("Adding Sample Orders")
        order1 = order.Order(
            customer_id=1,
            order_date=datetime.now(),
            status=enums.OrderStatus.PENDING,
            payment_status=enums.PaymentStatus.PENDING
        )
        session.add(order1)
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
    # Initialize database
    initialize_database()

    # Add sample data if the SEED_DB environment variable is set
    if os.environ.get("SEED_DB") == "true":
        logger.info("Seeding database with sample data...")
        # Create a new session for adding sample data
        engine = create_engine(f"sqlite:///{get_database_path()}", echo=False)
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