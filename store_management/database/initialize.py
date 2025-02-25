# database/initialize.py
import shutil
import logging
from .models.base import Base
from .models.product import Product
from .models.storage import Storage
from .models.supplier import Supplier


# Import needed model classes
# Add all models that should be created in the database

def initialize_database():
    """
    Initialize the database with all tables.

    This function creates all tables defined in the SQLAlchemy models
    and optionally seeds the database with initial data.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        from sqlalchemy import create_engine
        from config.settings import get_database_path

        logger.info("Initializing database...")

        # Get database connection
        db_path = get_database_path()
        logger.info(f"Database path: {db_path}")

        # Create engine and tables
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        logger.info("Database tables created successfully")

        # Optionally seed the database with initial data
        seed_database(engine)

        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def seed_database(engine):
    """
    Seed the database with initial data.

    Args:
        engine: SQLAlchemy engine object
    """
    logger = logging.getLogger(__name__)

    try:
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)
        session = Session()

        # Check if we already have data
        if session.query(Storage).count() == 0:
            logger.info("Seeding database with initial data...")

            # Create sample storage locations
            storage1 = Storage(name="Main Warehouse", location="Building A", capacity=1000)
            storage2 = Storage(name="Store Front", location="Building B", capacity=200)

            session.add_all([storage1, storage2])

            # Create sample suppliers
            supplier1 = Supplier(name="Quality Supplies Inc", contact_email="contact@qualitysupplies.com")
            supplier2 = Supplier(name="Best Materials Ltd", contact_email="info@bestmaterials.com")

            session.add_all([supplier1, supplier2])

            # Create sample products
            product1 = Product(name="Leather Type A", description="Premium leather", price=50.00)
            product2 = Product(name="Metal Buckle", description="High-quality buckle", price=5.00)

            session.add_all([product1, product2])

            session.commit()
            logger.info("Database seeded successfully")
        else:
            logger.info("Database already contains data, skipping seed")

    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        session.rollback()


def backup_database():
    """
    Create a backup of the database file.

    Returns:
        str: Path to the backup file if successful, None otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        from datetime import datetime
        from config.settings import get_database_path, get_backup_dir

        # Get paths
        db_path = get_database_path()
        backup_dir = get_backup_dir()

        # Create timestamp for the backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/backup_{timestamp}.db"

        # Create the backup
        shutil.copy2(db_path, backup_path)

        logger.info(f"Database backed up to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up database: {str(e)}")
        return None