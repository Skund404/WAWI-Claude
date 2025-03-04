# initialize_db.py
"""
Initialize database with fixed models.
"""

import logging
import os
import sys
import sqlalchemy

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def initialize_database():
    """Initialize database with all tables."""
    try:
        # Import Base
        from database.models.base import Base

        # Get database engine
        from sqlalchemy import create_engine

        # Try to get database URL from session module
        try:
            from database.sqlalchemy.session import DATABASE_URL
            if DATABASE_URL is None:
                DATABASE_URL = "sqlite:///store_management.db"
                logger.warning(f"DATABASE_URL was None, using default: {DATABASE_URL}")
        except (ImportError, AttributeError):
            # If import fails or attribute doesn't exist, use a default SQLite URL
            DATABASE_URL = "sqlite:///store_management.db"
            logger.warning(f"Could not import DATABASE_URL, using default: {DATABASE_URL}")

        logger.info(f"Using database URL: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL, echo=True)

        # Create all tables
        logger.info("Creating all tables...")
        Base.metadata.create_all(engine)

        # Verify tables
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    initialize_database()