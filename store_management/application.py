# application.py

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Type, TypeVar
from di.config import ApplicationConfig
from gui.main_window import MainWindow
from utils.error_handler import setup_exception_handler

T = TypeVar('T')


class Application:
    """Main application class that sets up and manages the GUI application."""

    def __init__(self):
        """Initialize the application."""
        self.logger = logging.getLogger(__name__)
        self._setup_application()

    def _setup_application(self) -> None:
        """Set up the application components."""
        try:
            self.logger.info("Setting up application")

            # Initialize the root window
            self.root = tk.Tk()
            self.root.title("Store Management System")

            # Configure exception handling
            setup_exception_handler(self.root)

            # Configure dependency injection
            self._register_services()

            # Create main window
            self.main_window = MainWindow(self.root, self)

            # Configure window size and position
            self.root.geometry("1024x768")
            self.root.minsize(800, 600)

            self.logger.info("Application setup completed")

        except Exception as e:
            self.logger.error(f"Error during application setup: {e}")
            raise

    def _register_services(self) -> None:
        """Register application services."""
        try:
            self.logger.info("Registering services")
            ApplicationConfig.configure_container()
            self.logger.info("Services registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering services: {e}")
            raise

    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service instance by type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Instance of requested service type
        """
        try:
            return ApplicationConfig.get_service(service_type)
        except Exception as e:
            self.logger.error(f"Error getting service {service_type.__name__}: {e}")
            raise

    def run(self) -> None:
        """Run the application main loop."""
        try:
            self.logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error in application main loop: {e}")
            raise
        finally:
            self.logger.info("Application shut down")

    def quit(self) -> None:
        """Quit the application."""
        try:
            self.logger.info("Shutting down application")
            self.root.quit()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise