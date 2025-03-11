# gui/app.py
"""
Main application entry point for the Leatherworking GUI application.
Initializes the dependency injection system and creates the main window.
"""

import logging
import tkinter as tk
from tkinter import messagebox

from di import initialize, Container, verify_container, resolve
from gui.main_window import MainWindow
from gui.theme import apply_theme
from gui import config
from utils.gui_logger import setup_gui_logger

class LeatherworkingApp:
    """Main application class for the Leatherworking GUI application."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = None
        self.di_container = None
        self.main_window = None
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Set up the logging system for the GUI."""
        setup_gui_logger(level=config.LOG_LEVEL)
        self.logger.info("Logging initialized for GUI application")
    
    def initialize_di(self):
        """Initialize the dependency injection container."""
        self.logger.info("Initializing dependency injection")
        try:
            self.di_container = initialize()
            if not verify_container():
                messagebox.showerror(
                    "Initialization Error",
                    "Failed to initialize required services. The application cannot start."
                )
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error initializing DI container: {str(e)}")
            messagebox.showerror(
                "Initialization Error",
                f"Failed to initialize services: {str(e)}"
            )
            return False
    
    def setup_root_window(self):
        """Set up the root tkinter window."""
        self.logger.info("Setting up root window")
        self.root = tk.Tk()
        self.root.title("Leatherworking Management System")
        self.root.geometry(f"{config.DEFAULT_WINDOW_WIDTH}x{config.DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT)
        
        # Set window icon if available
        try:
            icon_path = f"{config.ICON_PATH}/app_icon.ico"
            self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Could not load application icon: {str(e)}")
        
        # Apply the application theme
        apply_theme()
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions globally."""
        # Log the exception
        self.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Show error dialog to user if GUI is running
        if self.root and self.root.winfo_exists():
            error_message = f"An unexpected error occurred:\n{str(exc_value)}"
            messagebox.showerror("Application Error", error_message)
    
    def create_main_window(self):
        """Create the main application window."""
        self.logger.info("Creating main window")
        self.main_window = MainWindow(self.root)
        self.main_window.build()
    
    def on_closing(self):
        """Handle application closing."""
        self.logger.info("Application closing")
        if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
            # Perform cleanup if needed
            if self.root:
                self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.setup_logging()
        self.logger.info("Starting Leatherworking Management System")
        
        # Initialize components
        if not self.initialize_di():
            return
        
        self.setup_root_window()
        self.create_main_window()
        
        # Set up global exception handler
        import sys
        sys.excepthook = self.handle_exception
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the application
        self.logger.info("Application ready, starting main loop")
        self.root.mainloop()
        self.logger.info("Application terminated")

def main():
    """Application entry point."""
    app = LeatherworkingApp()
    app.run()

if __name__ == "__main__":
    main()