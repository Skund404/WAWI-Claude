# gui/app.py
"""
Main application entry point for the Leatherworking GUI application.
Initializes the dependency injection system and creates the main window.
"""

import logging
import sys
import tkinter as tk
from gui.theme import fix_button_styles
from di import initialize, Container, verify_container, resolve
from gui.main_window import MainWindow
from gui.theme import apply_theme
from gui import config
from gui.utils.gui_logger import setup_gui_logger
from gui.utils.error_manager import ErrorManager


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
                # Use ErrorManager for consistent error handling
                ErrorManager.handle_exception(
                    self,
                    ValueError("Failed to initialize required services"),
                    context="Dependency Injection Verification"
                )
                return False
            return True
        except Exception as e:
            # Use ErrorManager for consistent error handling
            ErrorManager.handle_exception(
                self,
                e,
                context="Dependency Injection Initialization"
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
            # Log warning instead of using ErrorManager for non-critical issue
            self.logger.warning(f"Could not load application icon: {str(e)}")

        # Apply the application theme
        try:
            apply_theme()
        except Exception as e:
            # Use ErrorManager for theme application errors
            ErrorManager.handle_exception(
                self,
                e,
                context="Theme Application"
            )

        # Fix button styles to ensure consistent text colors
        try:
            fix_button_styles()
        except Exception as e:
            # Use ErrorManager for button style errors
            ErrorManager.handle_exception(
                self,
                e,
                context="Button Style Fixing"
            )

        self.logger.info("Theme and button styles applied")

    def handle_global_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception handler for uncaught exceptions.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Traceback object
        """
        # Use ErrorManager for consistent logging and user feedback
        ErrorManager.handle_exception(
            self,
            exc_value,
            context={
                "exception_type": exc_type.__name__,
                "source": "Global Exception Handler"
            }
        )

        # Optional: Log to a file for more detailed tracking
        try:
            with open('error_log.txt', 'a') as error_file:
                import traceback
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=error_file)
        except Exception as log_error:
            self.logger.error(f"Failed to write to error log: {log_error}")

    def create_main_window(self):
        """Create the main application window."""
        try:
            self.logger.info("Creating main window")
            self.main_window = MainWindow(self.root)
            self.main_window.build()
        except Exception as e:
            # Use ErrorManager for main window creation errors
            ErrorManager.handle_exception(
                self,
                e,
                context="Main Window Initialization"
            )
            # Optionally, raise to prevent further application startup
            raise

    def on_closing(self):
        """Handle application closing."""
        # Use ErrorManager's confirmation dialog
        if ErrorManager.confirm_action("Quit", "Do you want to quit the application?"):
            self.logger.info("Application closing")
            # Perform cleanup if needed
            if self.root:
                self.root.destroy()

    def run(self):
        """Run the application."""
        try:
            # Setup logging
            self.setup_logging()
            self.logger.info("Starting Leatherworking Management System")

            # Initialize components
            if not self.initialize_di():
                # If DI initialization fails, exit the application
                return

            # Setup root window
            self.setup_root_window()

            # Create main window
            self.create_main_window()

            # Set up global exception handler
            sys.excepthook = self.handle_global_exception

            # Set up window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Start the application
            self.logger.info("Application ready, starting main loop")
            self.root.mainloop()
            self.logger.info("Application terminated")

        except Exception as e:
            # Catch any unexpected errors during startup or runtime
            ErrorManager.handle_exception(
                self,
                e,
                context="Application Startup/Runtime"
            )
            # Attempt to close application if critical error occurs
            if self.root and self.root.winfo_exists():
                self.root.destroy()


def main():
    """Application entry point."""
    app = LeatherworkingApp()
    app.run()


if __name__ == "__main__":
    main()