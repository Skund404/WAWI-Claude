# Path: tools/debug_view.py
"""
Diagnostic script to check view loading and data retrieval in the application.
This script can be used to debug why views are empty in the application.
"""
import sys
import os
import logging
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("view_debugger")


def check_database_connectivity():
    """
    Verifies database connectivity and checks if there's data in the Storage table.

    Returns:
        bool: True if connection is successful and data exists, False otherwise
    """
    try:
        # Import here to avoid the table redefinition issue
        from database.session import get_db_session

        session = get_db_session()
        logger.info("Database session created successfully")

        # Use raw SQL query to avoid model import issues
        result = session.execute("SELECT COUNT(*) FROM storage")
        storage_count = result.scalar()
        logger.info(f"Found {storage_count} storage locations in database")

        if storage_count > 0:
            # Get the first one to verify data retrieval
            result = session.execute("SELECT * FROM storage LIMIT 1")
            first_storage = result.fetchone()
            logger.info(f"Sample storage: {first_storage}")
            return True
        else:
            logger.warning("No storage locations found in database")
            return False
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return False
    finally:
        if 'session' in locals():
            session.close()


def check_view_loading():
    """
    Checks if views can be properly loaded in the main window.

    Returns:
        bool: True if views load correctly, False otherwise
    """
    try:
        import tkinter as tk
        from application import Application

        # Create a test application instance
        app = Application()

        # Initialize a root window without showing it
        root = tk.Tk()
        root.withdraw()

        # Try to create the main window
        from gui.main_window import MainWindow
        main_window = MainWindow(root, app)
        logger.info("Main window created successfully")

        # Check if we can access the notebook tabs
        if hasattr(main_window, 'notebook') and main_window.notebook is not None:
            tabs = main_window.notebook.tabs()
            logger.info(f"Main window has {len(tabs)} tabs")

            # Try to select each tab
            for i, tab in enumerate(tabs):
                main_window.notebook.select(i)
                tab_name = main_window.notebook.tab(i, "text")
                logger.info(f"Selected tab {i}: {tab_name}")

            return True
        else:
            logger.warning("Main window notebook not found or is None")
            return False

    except Exception as e:
        logger.error(f"Error checking view loading: {str(e)}")
        return False


def main():
    """
    Runs diagnostic checks and reports results.
    """
    logger.info("Starting view diagnostics")

    # Check database connectivity
    db_ok = check_database_connectivity()
    logger.info(f"Database connectivity check: {'PASSED' if db_ok else 'FAILED'}")

    # Check view loading
    view_ok = check_view_loading()
    logger.info(f"View loading check: {'PASSED' if view_ok else 'FAILED'}")

    # Output overall result
    if db_ok and view_ok:
        logger.info("All checks passed. The issue might be in specific view implementations.")
    else:
        logger.warning("Some checks failed. See above for details.")


if __name__ == "__main__":
    main()