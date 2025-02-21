# Path: store_management/main.py
import tkinter as tk
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the necessary modules
from store_management.application import Application
from store_management.gui.main_window import MainWindow
from store_management.di.config import ApplicationConfig

def main():
    """
    Main entry point of the application.

    This function initializes the main application window and starts the GUI event loop.
    """
    try:
        # Initialize Tkinter root window
        root = tk.Tk()

        # Configure dependency injection container
        app_config = ApplicationConfig()
        container = app_config.configure_container()

        # Create main application window
        main_window = MainWindow(root, container)

        # Start the main event loop
        main_window.run()

    except Exception as e:
        # Log any unhandled exceptions
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()