# main.py
"""
Main entry point for the leatherworking store management application.
Initializes the database, dependency injection container, and UI.
"""

import logging
import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Type

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import logging configuration
from utils.logging_config import setup_logging

# Configure logging before importing other modules
setup_logging()

# Import other application modules
from config.settings import get_database_path
from database.initialize import initialize_database
from di.container import DependencyContainer
from di.setup import setup_dependency_injection
from gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class Application:
    """Main application class that initializes the environment and UI."""

    def __init__(self):
        """Initialize the application, database, and dependency injection."""
        self.root = None
        self.main_window = None
        self.container = DependencyContainer()

        # Initialize database
        try:
            db_path = get_database_path()
            logger.info(f"Database path: {db_path}")
            initialize_database(db_path)
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}", exc_info=True)
            self._show_startup_error("Database Error",
                                    f"Failed to initialize database: {str(e)}")
            sys.exit(1)

        # Setup dependency injection
        try:
            setup_dependency_injection(self.container)
        except Exception as e:
            logger.error(f"Dependency injection setup error: {str(e)}", exc_info=True)
            self._show_startup_error("Setup Error",
                                    f"Failed to setup dependency injection: {str(e)}")
            sys.exit(1)

    def get_service(self, service_type: Type):
        """Retrieve a service from the dependency injection container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            The requested service implementation
        """
        try:
            return self.container.get_service(service_type)
        except Exception as e:
            logger.error(f"Error getting service {service_type.__name__}: {str(e)}", exc_info=True)
            messagebox.showerror("Service Error",
                                f"Failed to get service {service_type.__name__}: {str(e)}")
            return None

    def run(self):
        """Run the application and display the main window."""
        try:
            # Initialize Tkinter root
            self.root = tk.Tk()
            self.root.title("Leatherworking Store Management")
            self.root.geometry("1200x800")

            # Set application icon
            icon_path = os.path.join(project_root, "assets", "icon.ico")
            if os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                except Exception as icon_error:
                    logger.warning(f"Could not set application icon: {icon_error}")

            # Create main window
            self.main_window = MainWindow(self.root, self.container)
            self.main_window.pack(fill=tk.BOTH, expand=True)

            # Start the Tkinter event loop
            logger.info("Starting application main event loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Application startup error: {str(e)}", exc_info=True)
            self._show_startup_error("Startup Error",
                                    f"Failed to start application: {str(e)}")
            sys.exit(1)

    def quit(self):
        """Close the application."""
        logger.info("Closing application")
        if self.root:
            self.root.destroy()

    def _show_startup_error(self, title: str, message: str):
        """Show startup error message using either Tkinter or console.

        Args:
            title (str): Error title
            message (str): Error message
        """
        try:
            # Try to use Tkinter messagebox
            messagebox.showerror(title, message)
        except:
            # Fall back to console output
            print(f"ERROR: {title}\n{message}")

def main():
    """Main entry point for running the leatherworking store management application."""
    logger.info("Starting Leatherworking Store Management v0.1.0")

    # Initialize and run the application
    app = Application()
    app.run()

if __name__ == "__main__":
    main()