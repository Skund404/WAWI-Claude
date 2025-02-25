# storage_view.py
"""
Storage view implementation that displays storage locations.
This is a simplified version that directly accesses the database.
"""

import os
import sqlite3
import logging
from typing import Optional

import tkinter as tk
from tkinter import ttk

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from gui.base_view import BaseView

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class StorageView(BaseView):
    """View for displaying and managing storage locations."""

    @inject(MaterialService)
    def __init__(self, parent: ttk.Frame, app: tk.Tk):
        """
        Initialize the storage view.

        Args:
            parent (ttk.Frame): Parent widget.
            app (tk.Tk): Application instance.
        """
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(f"StorageView initialized with database: {self.db_path}")
        self.setup_ui()
        self.load_data()

    @inject(MaterialService)
    def _find_database_file(self) -> Optional[str]:
        """Find the SQLite database file."""
        possible_locations = [
            "store_management.db",
            "data/store_management.db",
            "database/store_management.db",
            "config/database/store_management.db",
        ]
        for location in possible_locations:
            if os.path.exists(location):
                return location

        logger.info("Searching for database file...")
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith(".db"):
                    path = os.path.join(root, file)
                    logger.info(f"Found database file: {path}")
                    return path

        return None

    @inject(MaterialService)
    def setup_ui(self) -> None:
        """Set up the user interface components."""
        self.create_toolbar()
        self.create_treeview()

    @inject(MaterialService)
    def create_toolbar(self) -> None:
        """Create the toolbar with buttons."""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Add Storage", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        logger.debug("Toolbar created")

    @inject(MaterialService)
    def create_treeview(self) -> None:
        """Create the treeview for displaying storage locations."""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "name", "location", "capacity", "occupancy", "type", "status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("location", text="Location")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("occupancy", text="Occupancy")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50)
        self.tree.column("name", width=150)
        self.tree.column("location", width=150)
        self.tree.column("capacity", width=100)
        self.tree.column("occupancy", width=100)
        self.tree.column("type", width=100)
        self.tree.column("status", width=100)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.on_double_click)

        logger.debug("Treeview created")

    @inject(MaterialService)
    def load_data(self) -> None:
        """Load storage locations from the database and display them."""
        try:
            logger.info("Loading storage data directly from database")
            self.tree.delete(*self.tree.get_children())

            if not self.db_path:
                logger.error("Database file not found")
                self.set_status("Error: Database file not found")
                return

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='storage';
                    """
                )
                if not cursor.fetchone():
                    logger.error("Storage table doesn't exist in the database")
                    self.set_status("Error: Storage table not found")
                    return

                try:
                    cursor.execute(
                        "SELECT id, name, location, capacity, current_occupancy, type, status FROM storage;"
                    )
                except sqlite3.OperationalError:
                    logger.warning("Error with expected columns, trying to get available columns")
                    cursor.execute("PRAGMA table_info(storage);")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    logger.info(f"Available columns: {column_names}")

                    select_columns = []
                    if "id" in column_names:
                        select_columns.append("id")
                    else:
                        select_columns.append("'N/A' as id")

                    for col in ["name", "location", "capacity", "current_occupancy", "type", "status"]:
                        if col in column_names:
                            select_columns.append(col)
                        elif col == "current_occupancy":
                            select_columns.append("0 as current_occupancy")
                        else:
                            select_columns.append(f"'Unknown' as {col}")

                    query = f"SELECT {', '.join(select_columns)} FROM storage;"
                    logger.info(f"Using query: {query}")
                    cursor.execute(query)

                rows = cursor.fetchall()
                for row in rows:
                    self.tree.insert("", tk.END, values=row)

                self.set_status(f"Loaded {len(rows)} storage locations")
                logger.info(f"Loaded {len(rows)} storage locations")

        except Exception as e:
            logger.exception(f"Error loading storage data: {e}")
            self.show_error("Data Load Error", f"Failed to load storage data: {str(e)}")

    @inject(MaterialService)
    def show_add_dialog(self) -> None:
        """Show dialog to add a new storage location."""
        logger.debug("Add dialog requested but not implemented")
        self.show_info("Not Implemented", "Add storage functionality is not yet implemented.")

    @inject(MaterialService)
    def on_double_click(self, event: tk.Event) -> None:
        """Handle double-click on a storage item."""
        logger.debug("Double-click event received but not implemented")
        self.show_info("Not Implemented", "Edit storage functionality is not yet implemented.")

    @inject(MaterialService)
    def delete_selected(self) -> None:
        """Delete the selected storage location."""
        logger.debug("Delete requested but not implemented")
        self.show_info("Not Implemented", "Delete storage functionality is not yet implemented.")

    @inject(MaterialService)
    def show_search_dialog(self) -> None:
        """Show search dialog."""
        logger.debug("Search requested but not implemented")
        self.show_info("Not Implemented", "Search functionality is not yet implemented.")