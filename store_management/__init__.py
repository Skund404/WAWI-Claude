# store_management/__init__.py

from store_management.database.sqlalchemy.config import (
    get_database_url,
    get_database_path
)
from store_management.database.sqlalchemy.session import (
    get_session
)
from store_management.utils.logger import logger


def initialize_application():
    """Central initialization method for the store management application."""
    logger.info("Initializing store management application...")

    # Initialize database connection
    try:
        db_url = get_database_url()
        session = get_session()
        logger.info("Database connection established successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False