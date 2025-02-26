"""
Main application entry point for Leatherworking Store Management System.

This module handles the application initialization, dependency injection setup,
and launches the main GUI window.
"""

import os
import sys
import logging
from typing import Optional, Type


# Add project root to Python path
def add_project_to_path() -> None:
    """
    Add the project root directory to Python path to ensure proper imports.

    This helps resolve import issues and allows importing local modules.
    """
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    logging.info("Setting up project path...")


# Dependency Injection Container
from di.container import DependencyContainer
from di.setup import setup_dependency_injection

# Database Initialization
from database.initialize import initialize_database
from config.settings import get_database_path

# GUI Import
from gui.main_window import MainWindow

# Tkinter
import tkinter as tk


class Application:
    """
    Main application class that manages application lifecycle.

    Responsible for:
    - Dependency injection setup
    - Database initialization
    - GUI creation and management
    """

    def __init__(self) -> None:
        """
        Initialize the application.

        Sets up logging, dependency injection, and prepares for GUI launch.
        """
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Setup dependency container
        self._container = DependencyContainer()

        # Root tkinter window
        self._root: Optional[tk.Tk] = None

        logging.info(f"Starting Leatherworking Store Management v0.1.0")

    def _register_services(self) -> None:
        """
        Register services with the dependency injection container.

        Uses the setup_dependency_injection function to register
        all required services.
        """
        logging.info("Setting up dependency injection...")
        setup_dependency_injection(self._container)

    def get_service(self, service_type: Type):
        """
        Retrieve a service from the dependency injection container.

        Args:
            service_type (Type): The type of service to retrieve

        Returns:
            The requested service implementation
        """
        try:
            return self._container.get(service_type)
        except ValueError as e:
            logging.error(f"Failed to retrieve service {service_type}: {e}")
            raise

    def run(self) -> None:
        """
        Launch the application.

        Initializes database, sets up services, and creates the main GUI window.
        """
        try:
            # Add project to Python path
            add_project_to_path()

            # Initialize database
            logging.info("Initializing database...")
            db_path = get_database_path()
            logging.info(f"Database path: {db_path}")
            initialize_database()

            # Reset and setup dependency container
            self._container.reset()
            self._register_services()

            # Create main GUI window
            logging.info("GUI initialization started")
            self._root = tk.Tk()
            self._root.title("Leatherworking Store Management")

            # Create main window with dependency container
            MainWindow(self._root, self._container)

            # Start the Tkinter event loop
            self._root.mainloop()

        except Exception as e:
            logging.error(f"Application initialization failed: {e}", exc_info=True)
            # Optionally show a messagebox to the user
            import tkinter.messagebox as messagebox
            messagebox.showerror("Initialization Error", str(e))
            raise

    def quit(self) -> None:
        """
        Gracefully quit the application.

        Closes the main window and performs any necessary cleanup.
        """
        if self._root:
            self._root.quit()
            self._root.destroy()
        logging.info("Application closed")


def main() -> None:
    """
    Entry point for the Leatherworking Store Management application.

    Creates and runs the main application instance.
    """
    try:
        app = Application()
        app.run()
    except Exception as e:
        logging.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()