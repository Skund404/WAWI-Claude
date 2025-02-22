# tkinter_test.py
import sys
import os

# Add the parent directory to Python path to ensure package imports work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import logging

# Add debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print Python path and sys.path for debugging
logger.debug(f"Python Path: {sys.path}")
logger.debug(f"Current Working Directory: {os.getcwd()}")


def print_import_chain():
    """
    Try to trace the import chain to identify circular import issues.
    """
    try:
        import database.sqlalchemy.models.storage
        logger.debug("Successfully imported storage module")
    except ImportError as e:
        logger.error(f"Import error in storage module: {e}")
        import traceback
        traceback.print_exc()


def test_tkinter():
    # Add import debugging
    print_import_chain()

    try:
        from application import Application

        # Create application instance
        app = Application()

        # Initialize the application
        app.initialize()

        # Run the application
        app.run()

    except Exception as e:
        logger.error(f"Error in test_tkinter: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print(f"Python Version: {sys.version}")
    print(f"SQLAlchemy Version: {__import__('sqlalchemy').__version__}")
    print(f"Python Path: {sys.path}")

    test_tkinter()