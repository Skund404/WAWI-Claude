# Path: gui/shopping_list/shopping_list_view.py
"""
Shopping list view implementation that displays shopping lists.
"""
import tkinter as tk
from tkinter import ttk
import logging
import sqlite3
import os
from datetime import datetime

from gui.base_view import BaseView
from services.interfaces.shopping_list_service import IShoppingListService

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ShoppingListView(BaseView):
    """
    View for displaying and managing shopping lists.
    """

    def __init__(self, parent, app):
        """
        Initialize the shopping list view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(f"ShoppingListView initialized with database: {self.db_path}")
        self.setup_ui()
        self.load_data()

    def _find_database_file(self):
        """Find the SQLite database file."""
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

    def setup_ui(self):
        """Set up the user interface components."""
        self.create_toolbar()
        self.create_treeview()

    def create_toolbar(self):
        """Create the toolbar with buttons."""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Add buttons
        ttk.Button(toolbar, text="Add List", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", command=lambda e=None: self.delete_selected(e)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        logger.debug("Toolbar created")

    def create_treeview(self):
        """Create the treeview for displaying shopping lists."""
        # Create a frame to hold the treeview and scrollbar
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("id", "name", "date", "status", "priority", "items", "total")

        # Create the treeview
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Status")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("items", text="Items")
        self.tree.heading("total", text="Total")

        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("name", width=200)
        self.tree.column("date", width=100)
        self.tree.column("status", width=100)
        self.tree.column("priority", width=80)
        self.tree.column("items", width=80)
        self.tree.column("total", width=100)

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

    def load_data(self):
        """Load shopping lists from the database and display them."""
        try:
            logger.info("Loading shopping list data")

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

            # Check if shopping_list table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='shopping_list';
            """)

            if not cursor.fetchone():
                logger.info("Shopping list table doesn't exist. Creating sample data.")
                self.set_status("Shopping list table doesn't exist - showing sample data")

                # Add sample data since table doesn't exist
                today = datetime.now().strftime("%Y-%m-%d")

                sample_data = [
                    (1, "Weekly Groceries", today, "Active", "High", 15, "$125.50"),
                    (2, "Office Supplies", today, "Pending", "Medium", 8, "$45.75"),
                    (3, "Party Supplies", today, "Complete", "Low", 12, "$78.25"),
                    (4, "Emergency Items", today, "Active", "Urgent", 5, "$32.99"),
                    (5, "Home Improvement", today, "Draft", "Low", 3, "$215.00")
                ]

                # Add to treeview
                for shopping_list in sample_data:
                    self.tree.insert("", tk.END, values=shopping_list)

                return

            # Get shopping list data
            cursor.execute("SELECT id, name, date, status, priority, items, total FROM shopping_list;")
            rows = cursor.fetchall()

            # Add to treeview
            for row in rows:
                self.tree.insert("", tk.END, values=row)

            self.set_status(f"Loaded {len(rows)} shopping lists")
            logger.info(f"Loaded {len(rows)} shopping lists")

        except Exception as e:
            logger.error(f"Error loading shopping list data: {str(e)}", exc_info=True)
            self.show_error("Data Load Error", f"Failed to load shopping list data: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def show_add_dialog(self):
        """Show dialog to add a new shopping list."""
        # Implementation would go here
        logger.debug("Add dialog requested but not implemented")
        self.show_info("Not Implemented", "Add shopping list functionality is not yet implemented.")

    def on_double_click(self, event):
        """Handle double-click on a shopping list item."""
        # Implementation would go here
        logger.debug("Double-click event received but not implemented")
        self.show_info("Not Implemented", "Edit shopping list functionality is not yet implemented.")

    def delete_selected(self, event):
        """Delete the selected shopping list."""
        # Implementation would go here
        logger.debug("Delete requested but not implemented")
        self.show_info("Not Implemented", "Delete shopping list functionality is not yet implemented.")

    def show_search_dialog(self):
        """Show search dialog."""
        # Implementation would go here
        logger.debug("Search requested but not implemented")
        self.show_info("Not Implemented", "Search functionality is not yet implemented.")