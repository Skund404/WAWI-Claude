# store_management/main.py
"""
Main application entrypoint for the Leatherworking Store Management Application.

This module handles application initialization, dependency injection setup,
and launching the main GUI window.
"""

import os
import sys
import logging
import traceback

from utils.circular_import_resolver import register_lazy_import

register_lazy_import("database.models.components.Component",
                     lambda: __import__("database.models.components", fromlist=["Component"]).Component)
register_lazy_import("database.models.components.PatternComponent",
                     lambda: __import__("database.models.components", fromlist=["PatternComponent"]).PatternComponent)
register_lazy_import("database.models.components.ProjectComponent",
                     lambda: __import__("database.models.components", fromlist=["ProjectComponent"]).ProjectComponent)

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import Tkinter first to ensure it's available
import tkinter as tk
from tkinter import messagebox

# Configuration and logging imports
from config.settings import get_database_path
from utils.logging_config import setup_logging

# Database and dependency injection imports
from database.initialize import initialize_database
from di.container import DependencyContainer
from di.setup import setup_dependency_injection

# GUI imports
from gui.main_window import MainWindow



def setup_application_context() -> tk.Tk:
    """
    Set up the application context, including logging, database, and dependency injection.

    Returns:
        tk.Tk: The root Tkinter window for the application
    """
    try:
        # Configure logging
        setup_logging()
        logger = logging.getLogger(__name__)

        # Log database path
        db_path = get_database_path()
        logger.info(f"Database path: {db_path}")

        # Initialize database
        initialize_database()
        logger.info("Database initialized successfully")

        # Reset and setup dependency injection
        container = DependencyContainer()
        container.reset()
        setup_dependency_injection()
        logger.info("Dependency injection setup completed")

        # Create root Tkinter window
        root = tk.Tk()
        root.withdraw()  # Hide initially

        return root

    except Exception as e:
        logging.error(f"Application startup error: {e}")
        logging.error(traceback.format_exc())
        raise


def main():
    """
    Main application entry point with comprehensive error handling.
    """
    try:
        # Set up application context
        root = setup_application_context()

        try:
            # Attempt to create main window
            main_window = MainWindow(root, DependencyContainer())
            main_window.mainloop()
        except Exception as main_window_error:
            logging.error(f"Failed to create main window: {main_window_error}")



    except Exception as startup_error:
        # Last resort error handling
        logging.error(f"Critical application startup error: {startup_error}")
        logging.error(traceback.format_exc())

        # Show error message box
        messagebox.showerror(
            "Application Startup Error",
            f"Could not start the application:\n{startup_error}\n\n"
            "Please check logs for more details."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()