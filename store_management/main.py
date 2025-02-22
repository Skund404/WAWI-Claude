"""
File: main.py
Application entry point.
Initializes the application, sets up logging, and starts the main window.
"""
import sys
import logging
import tkinter as tk
from tkinter import ttk

from config.application_config import ApplicationConfig
from database.initialize import initialize_database
from di.config import ApplicationConfig as DIConfig
from gui.main_window import MainWindow


def setup_logging():
    """
    Configure logging for the application.
    Sets up console and file handlers with appropriate formats.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)

    # Optionally add file handler
    try:
        file_handler = logging.FileHandler('application.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {str(e)}")


def main():
    """
    Main application entry point.
    Initializes database, DI container, and GUI components.
    """
    # Set up logging
    setup_logging()

    try:
        # Initialize database
        initialize_database(drop_existing=False)

        # Create and configure DI container
        container = DIConfig.configure_container()

        # Create root Tkinter window
        root = tk.Tk()
        root.title("Store Management System")
        root.geometry("1200x800")

        # Apply a theme
        style = ttk.Style()
        try:
            style.theme_use('clam')  # You can try other themes like 'alt', 'default', 'classic'
        except tk.TclError:
            logging.warning("Theme 'clam' not available, using default theme")

        # Create main window
        main_window = MainWindow(root, container)

        # Start the application
        root.mainloop()

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        if 'root' in locals():
            # Show error message to the user if GUI has been initialized
            import tkinter.messagebox as messagebox
            messagebox.showerror("Application Error", f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()