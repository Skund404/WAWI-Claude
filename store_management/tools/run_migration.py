# tools/run_migrations.py

"""
Database migration utility for creating or updating database schema.
"""

import argparse
import logging
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.base import Base
from config.application_config import ApplicationConfig


def setup_logging():
    """Configure logging for migrations"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def run_migrations(db_url, drop_existing=False):
    """Run database migrations"""
    logger = setup_logging()
    logger.info(f"Running migrations on {db_url}")

    # Create engine
    engine = create_engine(db_url)

    if drop_existing:
        logger.warning("Dropping all existing tables")
        Base.metadata.drop_all(engine)

    # Create all tables
    logger.info("Creating tables")
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Add initial data if needed
        # This could be moved to a separate function or module
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.exception(f"Error during migration: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Database migration utility")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables before migration")
    parser.add_argument("--db-url", help="Database URL (overrides config)")
    args = parser.parse_args()

    # Get database URL from args or config
    config = ApplicationConfig()
    db_url = args.db_url or config.get("database", "url")

    if not db_url:
        print("Error: No database URL provided")
        sys.exit(1)

    # Run migrations
    success = run_migrations(db_url, args.drop)

    if success:
        print("Migrations completed successfully")
        sys.exit(0)
    else:
        print("Migrations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()