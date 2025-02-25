# main.py
import logging
import os
import sys
from database.initialize import initialize_database
from gui.main_window import launch_main_window
from services.service_registration import register_services


def initialize_application():
    """
    Initialize the application by setting up logging, database, and registering services.

    Returns:
        bool: True if initialization is successful, False otherwise
    """
    # Set up logging
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "store_management.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)

    try:
        # Initialize database
        logger.info("Initializing database...")
        initialize_database()

        # Register services
        logger.info("Registering services...")
        register_services()

        return True
    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        return False


def main():
    """
    Main entry point for the application.
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Store Management Application")

        # Initialize the application
        if initialize_application():
            # Launch the main window
            launch_main_window()
        else:
            logger.error("Application initialization failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception in main: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()