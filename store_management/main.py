# main.py
"""
Main entry point for the Leatherworking Store Management Application.

This module handles application initialization, dependency injection,
and launching the main GUI window.
"""

import os
import sys
import logging
import tkinter as tk

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import necessary modules
from utils.logger import setup_logging, get_logger
from di.setup import setup_dependency_injection
from di.container import DependencyContainer
from gui.main_window import MainWindow
from database.initialize import initialize_database
from config.settings import get_database_path


def add_project_to_path():
    """
    Add the project root directory to Python path to ensure proper imports.
    """
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def main():
    """
    Main application entry point.
    Handles initialization of logging, database, dependency injection, and GUI.
    """
    try:
        # Setup logging
        setup_logging(log_level=logging.INFO)
        logger = get_logger('main')

        logger.info("Setting up project path...")
        add_project_to_path()

        logger.info("Initializing database...")
        db_path = get_database_path()
        initialize_database(db_path)

        logger.info("Setting up dependency injection...")
        container = DependencyContainer()
        setup_dependency_injection(container)

        logger.info("Creating main application window...")
        root = tk.Tk()
        root.title("Leatherworking Store Management")

        # Set a reasonable default window size
        root.geometry("1200x800")

        # Create main window with dependency injection container
        main_window = MainWindow(root, container)

        logger.info("Starting application main loop...")
        root.mainloop()

    except Exception as e:
        logger.exception(f"Unhandled exception in main application: {e}")
        # Optional: Show error dialog
        import tkinter.messagebox as messagebox
        messagebox.showerror("Application Error",
                             f"An unexpected error occurred:\n{e}\n\n"
                             "Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()