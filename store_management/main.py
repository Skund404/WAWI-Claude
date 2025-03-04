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

# Circular import resolution
from utils.circular_import_resolver import register_lazy_import


# Lazy import registration for complex models
def _register_lazy_component_imports():
    """Register lazy imports for component models to resolve circular dependencies."""
    register_lazy_import("database.models.components.Component",
                         lambda: __import__("database.models.components", fromlist=["Component"]).Component)
    register_lazy_import("database.models.components.PatternComponent",
                         lambda: __import__("database.models.components",
                                            fromlist=["PatternComponent"]).PatternComponent)
    register_lazy_import("database.models.components.ProjectComponent",
                         lambda: __import__("database.models.components",
                                            fromlist=["ProjectComponent"]).ProjectComponent)


# Ensure the project root is in the Python path
def _configure_python_path():
    """Add project root to Python path to ensure proper module imports."""
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)


# Import core dependencies
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


def _validate_environment():
    """
    Perform pre-startup environment validation.

    Raises:
        EnvironmentError: If critical environment requirements are not met
    """
    # Add any critical environment checks here
    # Examples:
    # - Python version check
    # - Required libraries check
    # - Minimum system requirements
    pass


def setup_application_context() -> tk.Tk:
    """
    Set up the comprehensive application context.

    Configures logging, initializes database, sets up dependency injection,
    and prepares the root Tkinter window.

    Returns:
        tk.Tk: The root Tkinter window for the application

    Raises:
        Exception: For any critical initialization failures
    """
    try:
        # Validate environment before proceeding
        _validate_environment()

        # Configure circular import resolution
        _register_lazy_component_imports()
        _configure_python_path()

        # Configure logging
        setup_logging()
        logger = logging.getLogger(__name__)

        # Log database configuration
        db_path = get_database_path()
        logger.info(f"Initializing database at: {db_path}")

        # Initialize database
        try:
            initialize_database()
            logger.info("Database initialized successfully")
        except Exception as db_error:
            logger.error(f"Database initialization failed: {db_error}")
            raise

        # Reset and setup dependency injection
        container = DependencyContainer()
        container.clear_cache()  # Ensure clean slate
        setup_dependency_injection()
        logger.info("Dependency injection setup completed")

        # Create root Tkinter window
        root = tk.Tk()
        root.withdraw()  # Hide initially

        return root

    except Exception as setup_error:
        logging.error(f"Application context setup failed: {setup_error}")
        logging.error(traceback.format_exc())
        raise


def main():
    """
    Main application entry point with comprehensive error handling.
    Manages the entire application lifecycle from startup to shutdown.
    """
    try:
        # Set up application context
        root = setup_application_context()

        try:
            # Create and launch main window
            main_window = MainWindow(root, DependencyContainer())
            main_window.mainloop()

        except Exception as window_error:
            logging.error(f"Main window initialization failed: {window_error}")
            messagebox.showerror(
                "Window Initialization Error",
                f"Could not create main application window:\n{window_error}\n\n"
                "Please check logs for more details."
            )
            raise

    except Exception as critical_error:
        # Last resort error handling for unrecoverable errors
        logging.critical(f"Unrecoverable application startup error: {critical_error}")
        logging.critical(traceback.format_exc())

        # Show comprehensive error message
        messagebox.showerror(
            "Critical Application Error",
            f"A critical error prevented the application from starting:\n\n"
            f"{critical_error}\n\n"
            "Possible causes:\n"
            "- Database connection issues\n"
            "- Dependency injection failures\n"
            "- Missing configuration\n\n"
            "Please check application logs and consult documentation."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()