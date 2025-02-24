# main.py

import sys
import logging
from pathlib import Path
from typing import Optional
import tkinter as tk
from application import Application
from utils.logger import setup_logging
from database import initialize_database


def setup_exception_handler(root: tk.Tk) -> None:
    """
    Set up global exception handler for the application.

    Args:
        root: Root tkinter window
    """

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions by logging them."""
        logging.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        root.quit()

    sys.excepthook = handle_exception


def initialize_app() -> Optional[Application]:
    """
    Initialize the application and its dependencies.

    Returns:
        Optional[Application]: Initialized application instance if successful, None otherwise
    """
    try:
        # Set up logging
        setup_logging()
        logging.info("GUI initialization started")

        # Initialize database
        initialize_database(drop_existing=False)

        # Create and configure application
        app = Application()
        return app

    except Exception as e:
        logging.error(f"Failed to initialize application: {e}")
        return None


def main():
    """Main application entry point."""
    try:
        # Initialize application
        app = initialize_app()
        if not app:
            logging.error("Application initialization failed")
            sys.exit(1)

        # Run the application
        app.run()

    except Exception as e:
        logging.error(f"Critical error in main: {e}")
        sys.exit(1)
    finally:
        logging.info("Application shutdown complete")


if __name__ == "__main__":
    main()