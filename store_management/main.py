# Path: main.py

"""
Main entry point for the Leatherworking Store Management Application.

Initializes the application, sets up dependencies, and launches the GUI.
"""

import os
import sys
import logging
from typing import Optional

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import configuration and core modules
from config.settings import (
    setup_logging,
    get_database_path,
    APP_NAME,
    APP_VERSION
)

# Import database initialization
from database.initialize import initialize_database

# Import dependency injection and service setup
from di.container import DependencyContainer
from di.setup import setup_dependency_injection

# Import GUI components
from gui.main_window import MainWindow

# Configure logging
logger = logging.getLogger(__name__)


def add_project_to_path():
    """
    Add the project root directory to Python path to ensure proper imports.

    This helps resolve import issues and allows importing local modules.
    """
    try:
        # Ensure the project root is in the Python path
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        logger.info("Setting up project path...")
    except Exception as e:
        logger.error(f"Failed to set up project path: {e}")
        raise


def initialize_application(db_path: Optional[str] = None):
    """
    Initialize the application components.

    Args:
        db_path (Optional[str]): Custom database path.
                                 If None, uses the default path.

    Returns:
        DependencyContainer: Configured dependency injection container
    """
    try:
        # Initialize logging
        setup_logging()

        # Add project to Python path
        add_project_to_path()

        # Initialize database
        logger.info("Initializing database...")
        db_engine = initialize_database(db_path)

        # Setup dependency injection
        logger.info("Setting up dependency injection...")
        container = setup_dependency_injection()

        return container

    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        raise


def main():
    """
    Main application entry point.

    Handles application initialization and GUI launch.
    """
    try:
        # Log application start
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

        # Retrieve default database path
        db_path = get_database_path()

        # Initialize application components
        container = initialize_application(db_path)

        # Initialize GUI
        logger.info("GUI initialization started")
        root = tk.Tk()
        root.title(f"{APP_NAME} v{APP_VERSION}")

        # Create main window with dependency container
        main_window = MainWindow(root, container)

        # Start the GUI event loop
        root.mainloop()

    except Exception as e:
        logger.error(f"Unhandled exception in main application: {e}")
        # Optional: Show error dialog or perform cleanup
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure tkinter is imported here to avoid circular imports
    import tkinter as tk

    main()