# main.py

import os
import sys
import logging
import tkinter as tk
from pathlib import Path
from store_management.application import Application
from store_management.gui.main_window import MainWindow


def setup_logging():
    """Configure logging for the application"""
    log_dir = Path.home() / ".store_management" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "store_management.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def main():
    """Main entry point for the application"""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting Store Management application")

    # Get database URL from environment or use default
    db_dir = Path.home() / ".store_management" / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "store_management.db"

    db_url = os.environ.get("SM_DATABASE_URL", f"sqlite:///{db_path}")
    logger.info(f"Using database URL: {db_url}")

    try:
        # Initialize application
        app = Application(db_url)
        app.initialize()

        # Create main window
        root = tk.Tk()
        main_window = MainWindow(root, app)
        app.main_window = main_window  # Store reference to main window

        # Start the application
        logger.info("Starting GUI main loop")
        main_window.run()
    except Exception as e:
        logger.exception(f"Error starting application: {str(e)}")
        if "root" in locals():
            tk.messagebox.showerror("Error", f"Application error: {str(e)}")
    finally:
        # Clean up resources
        if "app" in locals():
            logger.info("Cleaning up application resources")
            app.cleanup()


if __name__ == "__main__":
    main()