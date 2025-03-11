# main.py
import logging
import os
import sys
import time
import traceback
import tkinter as tk
import tkinter.messagebox
from pathlib import Path

from di.container import DependencyContainer
from di.setup import setup_dependency_injection
from gui.main_window import MainWindow
from utils.circular_import_resolver import register_lazy_import
from utils.logging_config import setup_logging
from config.settings import ConfigurationManager, Environment, get_database_path
from database.initialize import initialize_database


def _register_lazy_component_imports():
    """Register lazy imports for component models to resolve circular dependencies."""
    component_model_paths = [
        "database.models.component",
        "database.models.component_material",
    ]

    for path in component_model_paths:
        register_lazy_import(path)


def _configure_python_path():
    """Add project root to Python path to ensure proper module imports."""
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def _validate_environment():
    """Perform pre-startup environment validation.

    Raises:
        EnvironmentError: If critical environment requirements are not met
    """
    database_path = get_database_path()
    if not Path(database_path).exists():
        logging.warning(f"Database file not found at: {database_path}.  Attempting to initialize...")


def main():
    """Main application entry point with comprehensive error handling.
    Manages the entire application lifecycle from startup to shutdown.
    """
    try:
        start_time = time.time()

        # Configure Logging
        setup_logging()
        logging.info("Application starting...")

        # Configure Python Path for Module Resolution
        _configure_python_path()

        # Resolve circular import issues
        _register_lazy_component_imports()

        # Initialize Configuration and validate environment settings
        ConfigurationManager()  # Initialize configuration manager (singleton)
        _validate_environment()

        # Dependency Injection Setup
        container = DependencyContainer()
        setup_dependency_injection(container)

        # Initialize Database (Create if not exist)
        database_path = get_database_path()
        if not Path(database_path).exists():
            logging.info("Database does not exist, creating and seeding...")
            initialize_database()
            logging.info("Database creation and seeding complete.")
        else:
            logging.info("Database exists, skipping initialization.")

        # Tkinter GUI Setup
        root = tk.Tk()
        root.title(ConfigurationManager().APP_NAME)

        main_window = MainWindow(root)
        main_window.pack(fill=tk.BOTH, expand=True)

        # Calculate Startup Time
        startup_time = time.time() - start_time
        logging.info(f"Application started in {startup_time:.4f} seconds.")

        # Start Tkinter main loop
        root.mainloop()

    except Exception as e:
        # Global Exception Handling
        logging.critical("Unhandled exception during application runtime:", exc_info=True)
        traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        print(traceback_str)  # Ensure error is visible in console
        tk.messagebox.showerror(
            "Fatal Error",
            f"The application encountered a critical error and will now terminate.\n\nDetails: {str(e)}"
        )
        sys.exit(1)  # Exit application with an error code

    finally:
        # Shutdown Procedures
        logging.info("Application shutting down...")
        # Add any necessary cleanup code here (e.g., closing database connections)
        logging.info("Application shutdown complete.")


if __name__ == "__main__":
    main()