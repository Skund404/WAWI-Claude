#!/usr/bin/env python3
# Path: fix_storage_view.py
"""
Fixes for the storage view to make it display data properly.

This script patches the storage_view.py file with a simpler version
that directly accesses the database instead of relying on services.
"""

import os
import sys
import logging
from typing import Optional, Union, List, Tuple
from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

# Add the parent directory to sys.path to ensure imports work correctly
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("storage_view_fix")


def find_database_file() -> Optional[str]:
    """Find the SQLite database file.

    Searches in common locations and then performs a recursive search if needed.

    Returns:
        Optional[str]: Path to the database file if found, None otherwise.
    """
    logger.info("Searching for database file in common locations...")
    possible_locations = [
        "store_management.db",
        "data/store_management.db",
        "database/store_management.db",
        "config/database/store_management.db",
    ]

    # Check common locations first
    for location in possible_locations:
        if os.path.exists(location):
            logger.info(f"Found database at predefined location: {location}")
            return location

    # If not found in common locations, search recursively
    logger.info("Searching for database file recursively...")
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".db"):
                path = os.path.join(root, file)
                logger.info(f"Found database file: {path}")
                return path

    logger.error("No database file found")
    return None


def patch_storage_view(override: bool = False) -> bool:
    """
    Patch the storage_view.py file with a simpler version that doesn't rely on services.

    Args:
        override (bool): If True, override the existing file without asking for confirmation

    Returns:
        bool: True if the patching was successful, False otherwise
    """
    storage_view_path = os.path.join("gui", "storage", "storage_view.py")

    # Check if file exists and handle override logic
    if os.path.exists(storage_view_path) and not override:
        logger.info(f"Storage view already exists at: {storage_view_path}")
        response = input("Storage view already exists. Override? (y/n): ")
        if response.lower() == "y":
            return patch_storage_view(override=True)
        else:
            logger.info("Storage view not patched")
            return False

    # Ensure directory exists
    os.makedirs(os.path.dirname(storage_view_path), exist_ok=True)

    # Define the content of the new storage_view.py file
    content = """
# Path: gui/storage/storage_view.py
\"\"\"
Storage view implementation that displays storage locations.
This is a simplified version that directly accesses the database.
\"\"\"
import tkinter as tk
from tkinter import ttk
import sqlite3
import logging
import os
import sys
from typing import List, Tuple, Optional, Dict, Any

from gui.base_view import BaseView

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StorageView(BaseView):
    \"\"\"
    View for displaying and managing storage locations.
    \"\"\"

    def __init__(self, parent, app):
        \"\"\"
        Initialize the storage view.

        Args:
            parent: Parent widget
            app: Application instance
        \"\"\"
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(f"StorageView initialized with database: {self.db_path}")
        self.setup_ui()
        self.load_data()

    def _find_database_file(self) -> Optional[str]:
        \"\"\"
        Find the SQLite database file.

        Returns:
            Optional[str]: Path to the database file if found, None otherwise
        \"\"\"
        # List of possible locations
        possible_locations = [
            "store_management.db",
            "data/store_management.db",
            "database/store_management.db",
            "config/database/store_management.db"
        ]

        for location in possible_locations:
            if os.path.exists(location):
                return location

        # If not found in the predefined locations, search for it
        logger.info("Searching for database file...")
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith('.db'):
                    path = os.path.join(root, file)
                    logger.info(f"Found database file: {path}")
                    return path

        return None

    def setup_ui(self) -> None:
        \"\"\"Set up the user interface components.\"\"\"
        self.create_toolbar()
        self.create_treeview()

    def create_toolbar(self) -> None:
        \"\"\"Create the toolbar with buttons.\"\"\"
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Add buttons
        ttk.Button(toolbar, text="Add Storage", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", command=lambda e=None: self.delete_selected(e)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        logger.debug("Toolbar created")

    def create_treeview(self) -> None:
        \"\"\"Create the treeview for displaying storage locations.\"\"\"
        # Create a frame to hold the treeview and scrollbar
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("id", "name", "location", "capacity", "occupancy", "type", "status")

        # Create the treeview
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("location", text="Location")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("occupancy", text="Occupancy")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")

        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("name", width=150)
        self.tree.column("location", width=150)
        self.tree.column("capacity", width=100)
        self.tree.column("occupancy", width=100)
        self.tree.column("type", width=100)
        self.tree.column("status", width=100)

        # Add scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Pack scrollbars and treeview
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)

        logger.debug("Treeview created")

    def load_data(self) -> None:
        \"\"\"Load storage locations from the database and display them.\"\"\"
        try:
            logger.info("Loading storage data directly from database")

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            if not self.db_path:
                logger.error("Database file not found")
                self.set_status("Error: Database file not found")
                return

            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if storage table exists
            cursor.execute(\"\"\"
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='storage';
            \"\"\")
            if not cursor.fetchone():
                logger.error("Storage table doesn't exist in the database")
                self.set_status("Error: Storage table not found")
                return

            # Get storage data
            try:
                # Try first with current_occupancy column
                cursor.execute("SELECT id, name, location, capacity, current_occupancy, type, status FROM storage;")
            except sqlite3.OperationalError:
                # Fallback to possible different column name or structure
                logger.warning("Error with expected columns, trying to get available columns")
                cursor.execute("PRAGMA table_info(storage);")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                logger.info(f"Available columns: {column_names}")

                # Construct a query based on available columns
                select_columns = []

                # ID column is required
                if 'id' in column_names:
                    select_columns.append('id')
                else:
                    select_columns.append("'N/A' as id")

                # Other columns
                for col in ['name', 'location', 'capacity', 'current_occupancy', 'type', 'status']:
                    if col in column_names:
                        select_columns.append(col)
                    else:
                        # Use placeholder for missing columns
                        if col == 'current_occupancy':
                            select_columns.append("0 as current_occupancy")
                        else:
                            select_columns.append(f"'Unknown' as {col}")

                # Execute query with available columns
                query = f"SELECT {', '.join(select_columns)} FROM storage;"
                logger.info(f"Using query: {query}")
                cursor.execute(query)

            rows = cursor.fetchall()

            # Add to treeview
            for row in rows:
                self.tree.insert("", tk.END, values=row)

            self.set_status(f"Loaded {len(rows)} storage locations")
            logger.info(f"Loaded {len(rows)} storage locations")

        except Exception as e:
            logger.error(f"Error loading storage data: {str(e)}", exc_info=True)
            self.show_error("Data Load Error", f"Failed to load storage data: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def show_add_dialog(self) -> None:
        \"\"\"Show dialog to add a new storage location.\"\"\"
        # Implementation would go here
        logger.debug("Add dialog requested but not implemented")
        self.show_info("Not Implemented", "Add storage functionality is not yet implemented.")

    def on_double_click(self, event) -> None:
        \"\"\"
        Handle double-click on a storage item.

        Args:
            event: The event that triggered this handler
        \"\"\"
        # Implementation would go here
        logger.debug("Double-click event received but not implemented")
        self.show_info("Not Implemented", "Edit storage functionality is not yet implemented.")

    def delete_selected(self, event=None) -> None:
        \"\"\"
        Delete the selected storage location.

        Args:
            event: Optional event that triggered this handler
        \"\"\"
        # Implementation would go here
        logger.debug("Delete requested but not implemented")
        self.show_info("Not Implemented", "Delete storage functionality is not yet implemented.")

    def show_search_dialog(self) -> None:
        \"\"\"Show search dialog.\"\"\"
        # Implementation would go here
        logger.debug("Search requested but not implemented")
        self.show_info("Not Implemented", "Search functionality is not yet implemented.")
"""

    # Write the updated content to the file
    try:
        with open(storage_view_path, "w") as f:
            f.write(content.lstrip())
        logger.info(f"Created/patched storage view at: {storage_view_path}")
        return True
    except Exception as e:
        logger.error(f"Error patching storage view: {str(e)}")
        return False


def main() -> None:
    """
    Main function to patch the storage view.

    Executes the patching process and reports the result.
    """
    logger.info("Starting storage view fix...")
    if patch_storage_view():
        logger.info("Storage view patched successfully.")
    else:
        logger.info("Storage view not patched.")


if __name__ == "__main__":
    main()