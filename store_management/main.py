# Path: main.py
"""
Main entry point for the store management application.
"""
import os
import sys
import logging
from typing import List, Optional

from application import Application
import database.initialize as db_init
from config.environment import EnvironmentManager


def setup_logging():
    """Set up logging configuration."""
    log_level = EnvironmentManager.get_log_level()

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/application.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {log_level}")
    return logger


def create_necessary_directories():
    """Create necessary directories for the application."""
    directories = ["logs", "data", "backups", "exports", "config"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def main():
    """Main entry point for the application."""
    # Set up logging
    logger = setup_logging()

    try:
        # Create necessary directories
        create_necessary_directories()

        # Initialize database
        logger.info("Initializing database...")
        db_init.initialize_database(drop_existing=False)

        # Start the application
        logger.info("Starting application...")
        app = Application()
        app.run()

        return 0
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())