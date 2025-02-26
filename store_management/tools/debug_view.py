from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
Diagnostic script to check view loading and data retrieval in the application.
This script can be used to debug why views are empty in the application.
"""
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(
level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("view_debugger")


def check_database_connectivity():
    pass
"""
Verifies database connectivity and checks if there's data in the Storage table.

Returns:
bool: True if connection is successful and data exists, False otherwise
"""
try:
    pass
from database.session import get_db_session

session = get_db_session()
logger.info("Database session created successfully")
result = session.execute("SELECT COUNT(*) FROM storage")
storage_count = result.scalar()
logger.info(f"Found {storage_count} storage locations in database")
if storage_count > 0:
    pass
result = session.execute("SELECT * FROM storage LIMIT 1")
first_storage = result.fetchone()
logger.info(f"Sample storage: {first_storage}")
return True
else:
logger.warning("No storage locations found in database")
return False
except Exception as e:
    pass
logger.error(f"Error connecting to database: {str(e)}")
return False
finally:
if "session" in locals():
    pass
session.close()


def check_view_loading():
    pass
"""
Checks if views can be properly loaded in the main window.

Returns:
bool: True if views load correctly, False otherwise
"""
try:
    pass
import tkinter as tk
from application import Application

app = Application()
root = tk.Tk()
root.withdraw()
from gui.main_window import MainWindow

main_window = MainWindow(root, app)
logger.info("Main window created successfully")
if hasattr(main_window, "notebook") and main_window.notebook is not None:
    pass
tabs = main_window.notebook.tabs()
logger.info(f"Main window has {len(tabs)} tabs")
for i, tab in enumerate(tabs):
    pass
main_window.notebook.select(i)
tab_name = main_window.notebook.tab(i, "text")
logger.info(f"Selected tab {i}: {tab_name}")
return True
else:
logger.warning("Main window notebook not found or is None")
return False
except Exception as e:
    pass
logger.error(f"Error checking view loading: {str(e)}")
return False


def main():
    pass
"""
Runs diagnostic checks and reports results.
"""
logger.info("Starting view diagnostics")
db_ok = check_database_connectivity()
logger.info(
f"Database connectivity check: {'PASSED' if db_ok else 'FAILED'}")
view_ok = check_view_loading()
logger.info(f"View loading check: {'PASSED' if view_ok else 'FAILED'}")
if db_ok and view_ok:
    pass
logger.info(
"All checks passed. The issue might be in specific view implementations."
)
else:
logger.warning("Some checks failed. See above for details.")


if __name__ == "__main__":
    pass
main()
