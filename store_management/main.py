# File: main.py
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_log_path
from utils.logger import setup_logging
from application import Application

def setup_exception_handler(root):
    """
    Set up a global exception handler.

    Args:
        root: The root application object.
    """
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exceptions.

        Args:
            exc_type (type): Exception type.
            exc_value (Exception): Exception instance.
            exc_traceback (traceback): Traceback object.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        # Optional: Show error dialog or take specific action
        # root.show_error_dialog(str(exc_value))

    sys.excepthook = global_exception_handler

def initialize_app():
    """
    Initialize the application.

    Returns:
        Application: Initialized application instance.
    """
    # Initialize logging
    setup_logging(
        log_level=logging.INFO,
        log_dir=get_log_path()
    )

    # Create and return the application
    app = Application()
    setup_exception_handler(app)
    return app

def main():
    """
    Main application entry point.
    """
    try:
        app = initialize_app()
        app.run()
    except Exception as e:
        logging.error(f"Application initialization failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()